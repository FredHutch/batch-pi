#!/usr/bin/env Rscript

# pi.R <seed> <iterations>

sim.pi <- function(iterations = 1000) {
    # Generate two vectors for random points in unit circle
    x.pos <- runif(iterations, min=-1, max=1)
    y.pos <- runif(iterations, min=-1, max=1)
    # Test if draws are inside the unit circle
    draw.pos <- ifelse(x.pos^2 + y.pos^2 <= 1, TRUE, FALSE)
    draws.in <- length(which(draw.pos == TRUE))
    return(draws.in)
}

# Call this as:
# pi_sim.R <simulation name> <seed> <number of iterations> <s3 upload uri>
args = commandArgs(trailingOnly=TRUE)

name = as.integer(args[1])
seed = as.integer(args[2])
iterations = as.integer(args[3])
results_uri = args[4]

# Gather <iteration> hits using <seed>
set.seed(seed)
hits = sim.pi(iterations=iterations)

cat(hits, file="/var/tmp/output", append=FALSE)

# Upload to S3 url using aws command line
# The container has the role with the necessary permissions... we hope.
# cmd <= 'aws s3 cp /var/tmp/output s3://pi-simulation/name'
# shell(cmd, '/bin/bash', mustWork=TRUE)
