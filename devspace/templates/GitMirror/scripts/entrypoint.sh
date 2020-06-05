#!/bin/sh

host_list=$(ls /etc/nginx/sites-enabled/ | grep 'mirror')
for host in $host_list
do
  existed=$(grep "$host" /etc/hosts)
  if [ -z "$existed" ]; then
    echo "127.0.0.1 $host " >> /etc/hosts
    echo "$host added in /etc/hosts"
  else
    echo "$host already in /etc/hosts"
  fi
done


#start service
/usr/bin/spawn-fcgi -M 666 -s /var/run/fcgiwrap.socket /usr/sbin/fcgiwrap
service cron start
/usr/sbin/nginx

chmod +x gitmirror.py

USER_ID=${LOCAL_USER_ID:-1000}

echo "Starting with UID : $USER_ID"
useradd --shell /bin/bash -u $USER_ID -o -c "" -m yang
/usr/sbin/gosu yang ./gitmirror.py --init
exec /usr/sbin/gosu yang "$@"

