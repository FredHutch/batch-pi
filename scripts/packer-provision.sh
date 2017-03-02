#!/bin/bash -xe

apt-get update

# r-base-core     : R for simulation script
# r-recommended   : R for simulation script
# libxml2-dev          : needed for cloudyr install
# libcurl4-openssl-dev : needed for cloudyr install
# libssl-dev           : needed for cloudyr install
# wget   : general utility
# sudo   : general utility
# vim    : general utility

apt-get -y install "r-base-core" "r-recommended" \
        "libxml2-dev" "libcurl4-openssl-dev" "libssl-dev" \
        "wget" "sudo" "vim"

echo "Configure CRAN default repository"
cat > /etc/R/Rprofile.site <<'EREH'
local({
  r <- getOption("repos")
  r["CRAN"] <- "http://cran.fhcrc.org"
  options(repos = r)
})
EREH

# install drat and cloudyr (former is required by latter)

R -e 'install.packages("drat")' 
R -e 'drat::addRepo("cloudyr", "http://cloudyr.github.io/drat"); install.packages("aws.s3")'

chmod ugo+x /usr/local/bin/pi_sim.R
