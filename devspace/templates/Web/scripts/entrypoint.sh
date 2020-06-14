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
  cache_root='/var/cache/cgit'
  service_list=$(ls /srv/git)
  for service in $service_list; do
   if [ ! -d "$cache_root/$service" ];then
      mkdir -p "$cache_root/$service"
      echo "cache $cache_root/$service created"
   else
      echo "cache $cache_root/$service existed"
   fi
  done
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

echo "Add hosts"
add_host cgit

echo "Create cache dir"
create_cache_dir

echo "Start service"
if [ "$distribution" = "alpine" ]; then
  /usr/bin/spawn-fcgi -M 666 -s /var/run/fcgiwrap.socket /usr/bin/fcgiwrap
else
  /usr/bin/spawn-fcgi -M 666 -s /var/run/fcgiwrap.socket /usr/sbin/fcgiwrap
fi
exec "$@"