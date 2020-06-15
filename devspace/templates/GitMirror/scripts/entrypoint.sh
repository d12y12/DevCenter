#!/bin/sh

display_logo()
{
  logo=$1
  if [ -f "$logo" ]; then
    cat "$logo"
  fi
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

chmod +x gitmirror.py

./gitmirror.py --init

exec "$@"
