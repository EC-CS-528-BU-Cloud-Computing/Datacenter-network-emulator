for i in `ifconfig -a |grep veth |awk -F: '{print $1}'` ;
   do
      echo "---------------"
      echo $i
      echo "Our ID: " `ip link show dev $i | grep $i | awk -F: '{print $1}'`
      echo "Peer ID: " `ethtool -S $i |  grep -i peer_ifindex | awk -F: '{print $2}'`
      echo "---------------"
done
docker exec f2ce707d306c ip link show | grep UP | grep -v eth0 | grep -v lo | awk -F: '{print $2}' | awk -F@ '{print $1}'
docker exec f2ce707d306c ip link show | grep UP | grep -v eth0 | grep -v lo | awk -F: '{print $2}' | awk -F@ '{print $1}' | tr -d ' '