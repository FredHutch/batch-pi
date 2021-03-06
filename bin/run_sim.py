#!/usr/bin/env python3

# run_sim.py <path to config.json>

import argparse
import logging
import json
import boto3
from pprint import pprint
import time
from math import pi as pi_real
import random

# Can't currently retrieve more than 100 jobs via DescribeJobs
CHUNKS_MAX=1000

# Job State headers
state_header = {
    'SUBMITTED':'SUB',
    'PENDING':'PEND',
    'RUNNABLE':'QUE',
    'STARTING':'STRT',
    'RUNNING':'RUN',
    'PI': 'PI ESTIMATE',
    'DELTA': 'DELTA'
}

progress_format = '{SUBMITTED:>4} {PENDING:>4} {RUNNABLE:>4} ' \
        '{STARTING:>4} {RUNNING:>4}'

def calculate_pi( s3resource, throws, object_list ):
    # download objects from s3 and calculate PI from them
    total_hits = 0
    iterations = 0
    for x in object_list:
        # download results from each partial
        logging.debug(
            'download partial result {}'.format(x)
        )
        s3object = s3resource.Object( 'pi-simulation', x)
        hits = int(s3object.get()['Body'].read().decode('utf-8'))
        iterations = iterations + int(job_parameters['iterations'])
        total_hits = total_hits + hits
    return(4/(iterations/total_hits))

def describe_all_jobs( batch_client, job_list ):
    # chunk job_list into sections (100 max per section, describe_job
    # limit)
    all_jobs = {'jobs':[]}
    for c in range(0, len(job_list), 100):
        response = batch_client.describe_jobs(jobs=job_list[c:c+100])
        all_jobs['jobs'] = all_jobs['jobs'] + response['jobs']
    return all_jobs


logging.basicConfig(level=logging.INFO)
# Set log level for boto components
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('botocore').setLevel(logging.ERROR)

valid_job_states = [
    'SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING', 'RUNNING',
    'SUCCEEDED', 'FAILED'
]

parser = argparse.ArgumentParser(
    description="Run PI simulation via AWS Batch"
)
parser.add_argument(
    '--config', dest='config_file',
    help='path to configuration file',
    default='./pi_simulation_config.json'
)
parser.add_argument(
    '--job-name', dest='job_name',
    help='a name for this simulation',
    default='pi_sim'
)
parser.add_argument(
    '--random-seeds', dest='random_seed',
    action="store_true",
    help=(
        'use random values for chunk seeds. Warning: ' +
        'this will override values in the config file'
    )
)

args = parser.parse_args()
logging.debug('using config file {}'.format(args.config_file))

# Run simulations to estimate PI with monte carlo algorithm

# Pre-flight checks:
#   1. config OK? sufficient seeds for chunks?
with open(args.config_file) as f:
    configs = json.load(f)

logging.debug('Loaded configuration')

logging.debug('Checking chunks against CHUNKS_MAX={}'.format(CHUNKS_MAX))
if configs['chunks'] > CHUNKS_MAX:
    logging.error('Requested chunks exceeds CHUNKS_MAX({})'.format(CHUNKS_MAX))
    raise ValueError

logging.debug("Checking seeds")
if args.random_seed:
    logging.warning('Using random values for seed chunks')
    seeds = random.sample( range(10000,99999), configs['chunks'] )
else:
    seeds = configs['seeds']

# Everything downstream expects seeds to be string- this is probably a #FIXME
seeds = list(map(str, seeds))

if len(seeds) != configs['chunks']:
    logging.error('Incorrect number of seeds for number of chunks')
    raise ValueError

logging.debug("Seeds list is: {}".format(seeds))

#   1. s3 bucket ready? create or empty as appropriate.
#   TODO: Actually do this...
#   1. do I have AWS credentials ready?
#   TODO: Actually do this...

# Job submission
#
# submit <chunks> jobs with parameters seed, iterations, and results_uri

job_list = []  # will contain list of job names submitted
client = boto3.client('batch')


for chunk in range(0, configs['chunks']):
    # Creates a "folder" in s3 for this run's results
    results_uri = "/".join(['s3://pi-simulation', args.job_name])
    # The individual job name is the root plus _<chunk number>
    job_name = "_".join([args.job_name, str(chunk)])

    job_parameters = {
        'seed': seeds[chunk],
        'name': job_name,
        'iterations': configs['iterations_per_chunk'],
        'results_uri': results_uri

    }

    response = client.submit_job(
        jobName = job_name,
        jobQueue = 'pi-simulator-queue',
        jobDefinition = 'pi_simulation:5',
        parameters = job_parameters
    )
    job_list.append( response['jobId'] )
    logging.debug('Submitted job ID: {}'.format(response['jobId']))

logging.info('Submitted jobs- monitoring progress')

# Monitor progress
#
# This process goes to monitor mode, displaying number of jobs in queue that
# are in the different states, e.g.:
#
# SUB | PEND | RUN |  F | S | ITER      | PI        | DELTA
#   0 |    3 |   2 |  0 | 5 | 500000    | 3.141583+ | 0.000012
#   0 |    0 |   3 |  0 | 7 | 700000    | 3.141545+ | 0.000005
#
# Complete: 10000000 iterations in 10 chunks yeilds pi: 3.1415965090909093

running = -1
s3r = boto3.resource('s3')
print( (progress_format + ' {PI:<12.12s} {DELTA:<12.12s}').format(**state_header))

while True:
    # get job descriptions from job_list
    response = describe_all_jobs(client, job_list)
    summary = {}
    queue_stats = {
        'SUBMITTED':0,
        'PENDING':0,
        'RUNNABLE':0,
        'STARTING':0,
        'RUNNING':0,
        'PI':3,
        'DELTA':0
    }

    for state in valid_job_states:
        summary[state] = list(
            (j for j in response['jobs'] if( j['status'] == state))
        )
        queue_stats[state] = len(summary[state])

    running = len(
        summary['SUBMITTED'] + summary['PENDING'] +
        summary['RUNNABLE'] + summary['STARTING'] +
        summary['RUNNING']
    )

    if running == 0:
        print( "all jobs complete" )
        break
    else:
        # create running estimate of pi
        # get all created objects in result bucket if anything is done
        if len(summary['SUCCEEDED']) > 0:
            # generate list of objects to download
            s3_keys = list(
                ('/'.join([args.job_name,j['jobName']]) for 
                 j in summary['SUCCEEDED'])
            )
            queue_stats['PI'] = calculate_pi(
                s3r, int(job_parameters['iterations']), s3_keys
            )
            queue_stats['DELTA'] = queue_stats['PI'] - pi_real

        print((progress_format + " {PI:1.10f} {DELTA:+1.10f}").format( **queue_stats)) 
        time.sleep(15)

# Complete

# Print final estimate of pi - everything else (save S3) cleans itself up
# generate list of objects to download
s3_keys = list(
    ('/'.join([args.job_name,j['jobName']]) for 
     j in summary['SUCCEEDED'])
)
pi_e = calculate_pi(s3r, int(job_parameters['iterations']), s3_keys)
logging.info(
    '{} iterations, pi estimate is {}, delta is {:1.10f}'.format(
        int(job_parameters['iterations'])*len(summary['SUCCEEDED']),
        str(pi_e),
        pi_e - pi_real
    )
)

