#!/usr/bin/env python3

# run_sim.py <path to config.json>

import argparse
import logging
import json
import boto3
from pprint import pprint

logging.basicConfig(level=logging.DEBUG)

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
    logging.debug(pprint(response))



# Monitor progress
#
# For the sake of simplicity, we're just going to assume any job in the queue
# is working on this task.  When there are no more jobs in submitted, pending,
# runnable, starting, or running we'll say its complete and shut down.

# This process goes to monitor mode, displaying number of jobs in queue that
# are in the different states, e.g.:
#
# SUBMITTED: 0
#   PENDING: 3
#   RUNNING: 2
#    FAILED: 0
# SUCCEEDED: 5
#
# Chunks Complete: 5
# Last estimate of pi: 3.134567132 (delta .01...)

# Complete

# Print final estimate of pi - everything else (save S3) cleans itself up

