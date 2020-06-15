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

USER_ID=${LOCAL_USER_ID:-1000}
echo "Starting with UID : $USER_ID"

echo "Start service"
if [ "$distribution" = "alpine" ]; then
  adduser --disabled-password --home /home/yang --gecos "" --shell /bin/sh --uid $USER_ID yang
  exec su-exec yang "$@"
else
  useradd --shell /bin/bash -u $USER_ID -o -c "" -m yang
  exec /usr/sbin/gosu yang "$@"
fi
