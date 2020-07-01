#!/bin/sh

display_logo()
{
  logo=$1
  if [ -f "$logo" ]; then
    cat "$logo"
  fi
}

dispaly_usage()
{
  echo 'Use start.sh to start your docker which will auto-mount your services'
}

########################################
# Main                                 #
########################################

display_logo /logo.txt

distribution=$(grep '^ID=' /etc/os-release | sed 's/ID=\(.*\)/\1/g')
if [ -z "$distribution" ]; then
  echo "Unkonw distribution, exit"
  exit 1
else
  echo "Distribution : $distribution"
fi

dispaly_usage
chmod +x gitmirror.py

./gitmirror.py --help

exec "$@"
