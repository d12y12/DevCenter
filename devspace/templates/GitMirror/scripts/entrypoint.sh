#!/bin/sh

display_logo()
{
  logo=$1
  if [ -f "$logo" ]; then
    cat "$logo"
  fi
}

add_host()
{
  domain=$1
  host_list=$(ls /etc/nginx/sites-enabled/ | grep "$domain")
  for host in $host_list; do
    existed=$(grep "$host" /etc/hosts)
    if [ -z "$existed" ]; then
      echo "127.0.0.1 $host " >>/etc/hosts
      echo "$host added in /etc/hosts"
    else
      echo "$host existed in /etc/hosts"
    fi
  done
}

create_cache_dir()
{
  extension=$1
  cache_root='/var/cache/cgit'
  service_list=$(ls /apps/database | grep "$extension")
  for service in $service_list; do
   name=$(basename "./database/$service" "$extension")
   if [ ! -d "$cache_root/$name" ];then
      mkdir -p "$cache_root/$name"
      echo "cache $cache_root/$name created"
   else
      echo "cache $cache_root/$name existed"
   fi
  done
}

########################################
# Main                                 #
########################################
logo='logo.txt'
display_logo "$logo"

distribution=$(grep '^ID=' /etc/os-release | sed 's/ID=\(.*\)/\1/g')
if [ -z "$distribution" ]; then
  echo "Unkonw distribution, exit"
  exit 1
else
  echo "Distribution : $distribution"
fi

USER_ID=${LOCAL_USER_ID:-1000}
echo "Starting with UID : $USER_ID"

echo "Add hosts"
add_host mirror

echo "Create cache dir"
create_cache_dir .db
create_cache_dir .sql

chmod +x gitmirror.py

echo "Start service"
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
