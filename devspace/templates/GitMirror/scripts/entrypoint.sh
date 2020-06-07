#!/bin/sh

logo='logo.txt'

if [ -f "$logo" ]; then
  cat "$logo"
fi

distribution=$(grep '^ID=' /etc/os-release | sed 's/ID=\(.*\)/\1/g')
if [ -z "$distribution" ]; then
  echo "Unkonw distribution, exit"
  exit 1
else
  echo "Distribution : $distribution"
fi

USER_ID=${LOCAL_USER_ID:-1000}
echo "Starting with UID : $USER_ID"

host_list=$(ls /etc/nginx/sites-enabled/ | grep 'mirror')
for host in $host_list; do
  existed=$(grep "$host" /etc/hosts)
  if [ -z "$existed" ]; then
    echo "127.0.0.1 $host " >>/etc/hosts
    echo "$host added in /etc/hosts"
  else
    echo "$host already in /etc/hosts"
  fi
done

chmod +x gitmirror.py

#start service
if [ "$distribution" = "alpine" ]; then
  /usr/bin/spawn-fcgi -M 666 -s /var/run/fcgiwrap.socket /usr/bin/fcgiwrap
  crond
  nginx

  adduser --disabled-password --home /home/yang --gecos "" --shell /bin/sh --uid $USER_ID yang
  su-exec yang ./gitmirror.py --init
  exec su-exec yang "$@"
else
  /usr/bin/spawn-fcgi -M 666 -s /var/run/fcgiwrap.socket /usr/sbin/fcgiwrap
  service cron start
  /usr/sbin/nginx

  useradd --shell /bin/bash -u $USER_ID -o -c "" -m yang
  /usr/sbin/gosu yang ./gitmirror.py --init
  exec /usr/sbin/gosu yang "$@"
fi
