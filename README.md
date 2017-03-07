# Simulation Example for AWS Batch

> A proof-of-concept for using AWS Batch for computing PI using a
> [Monte Carlo simulation](http://mathfaculty.fullerton.edu/mathews/n2003/montecarlopimod.html)

The process for any one simulation is as follows:

  - create a configuration file containing:
    - the number of "chunks" to run
    - the number of iterations within each chunk
    - a seed for each chunk
  - use the script `run_sim.py` to submit batch jobs- it will
    create "chunks" jobs and queue them up on AWS batch
  - each job performs part of the Monte Carlo simulation, returning
    the number of "hits" for "iterations" inside the circle. The
    results are stored in S3
  - when the `run_sim` script sees all chunks complete (success
    or failure) it will download all the chunk results from S3 and
    finish the calculation

# Files

 - `bin/run_sim.py`
 
 This script manages submission of the PI simulation using the job configuration files.

 - `assets/pi_sim.R`
 
 This script is copied into the Docker image and is executed by Batch

 - `configs/pi_sim_config50.json`
 - `configs/pi_sim_config100.json`

 `run_sim` configuration files for 50 and 100 chunks.

 - `configs/packer-build.json`

 The Packer configuration file for building the docker image.

 - `scripts/packer-provision.sh`

 This is the script run by Packer to provision the docker image
