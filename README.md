# Simulation Example for AWS Batch

- core function is sim.pi(iterations)
  - returns the number of "hits" inside the circle

- number of hits saved into an output file

- when all jobs are done we sum up and perform the final calculation:
  - `4 / (sum(hits)/total_iterations)
  - lambda function monitoring a bucket- when results==reps sum up.

