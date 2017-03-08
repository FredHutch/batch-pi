#!/usr/bin/env python3

# run_sim.py <path to config.json>

import argparse
import logging
import json
import boto3
from pprint import pprint
import time
from math import pi as pi_real

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

args = parser.parse_args()
logging.debug('using config file {}'.format(args.config_file))

# Run simulations to estimate PI with monte carlo algorithm

# Pre-flight checks:
#   1. config OK? sufficient seeds for chunks?
with open(args.config_file) as f:
    configs = json.load(f)

logging.debug('Loaded configuration')

logging.debug("Checking seeds")
if len(configs['seeds']) != configs['chunks']:
    logging.error('Incorrect number of seeds for number of chunks')
    raise ValueError

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
        'seed': configs['seeds'][chunk],
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
# For the sake of simplicity, we're just going to assume any job in the queue
# is working on this task.  When there are no more jobs in submitted, pending,
# runnable, starting, or running we'll say its complete and shut down.

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
while True:
    # get job descriptions from job_list
    response = client.describe_jobs(jobs=job_list)
    summary = {}  # stor jobs in states here

    for state in valid_job_states:
        summary[state] = list(
            (j for j in response['jobs'] if( j['status'] == state))
        )
        print("{}: {}".format(state, len(summary[state])))

    running = len(
        summary['SUBMITTED'] + summary['PENDING'] +
        summary['RUNNABLE'] + summary['STARTING'] +
        summary['RUNNING']
    )

    logging.debug('len(running) == {}'.format(running))

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
            pi_e = calculate_pi(
                s3r, int(job_parameters['iterations']), s3_keys
            )
            logging.info('pi estimate is {}'.format(str(pi_e)))

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
    '{} iterations, pi estimate is {}, delta is {}'.format(
        int(job_parameters['iterations'])*len(summary['SUCCEEDED']),
        str(pi_e),
        pi_e - pi_real
    )
)

