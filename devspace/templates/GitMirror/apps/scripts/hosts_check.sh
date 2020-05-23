host_list=$(ls /etc/nginx/sites-enabled/ | grep 'mirror')
for host in $host_list
do
  existed=$(grep $host /etc/hosts) 
  if [ -z "$existed" ]; then
    echo "127.0.0.1 $host " >> /etc/hosts
    echo "$host added in /etc/hosts"
  else
    echo "$host already in /etc/hosts"
  fi
done


