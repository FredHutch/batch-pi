#!/bin/bash -xe

apt-get update

# r-base-core     : R for simulation script
# r-recommended   : R for simulation script
# python, python-pip: for AWS CLI
# wget   : general utility
# sudo   : general utility
# vim    : general utility

apt-get -y install "r-base-core" "r-recommended" \
        "python" "python-pip" \
        "wget" "sudo" "vim"

echo "Configure CRAN default repository"
cat > /etc/R/Rprofile.site <<'EREH'
local({
  r <- getOption("repos")
  r["CRAN"] <- "http://cran.fhcrc.org"
  options(repos = r)
})
EREH

echo "installing aws cli"
pip install --upgrade awscli

chmod ugo+x /usr/local/bin/pi_sim.R
