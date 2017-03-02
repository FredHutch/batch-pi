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

args = commandArgs(trailingOnly=TRUE)

seed = as.integer(args[1])
iters = as.integer(args[2])

set.seed(seed)

s <- 0
reps <- 5.0


for( i in 1:reps ) {
    s[i] = sim.pi(iterations=iters)
}

pie <- 4.0*(sum(s)/(reps*iters))
print(pie)
print(pi)
