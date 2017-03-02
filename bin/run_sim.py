#!/usr/bin/env python3

# run_sim.py <path to config.json>

# Run simulations to estimate PI with monte carlo algorithm

# Pre-flight checks:
#   1. config OK? sufficient seeds for chunks?
#   1. s3 bucket ready? create or empty as appropriate.
#   1. do I have AWS credentials ready?
#   1. job definition ok?
#   

# Job submission
#
# submit <chunks> jobs with parameters seed, iterations, and results_uri

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

