for i in `ifconfig -a |grep veth |awk -F: '{print $1}'` ;
   do
      echo "---------------"
      echo $i
      echo "Our ID: " `ip link show dev $i | grep $i | awk -F: '{print $1}'`
      echo "Peer ID: " `ethtool -S $i |  grep -i peer_ifindex | awk -F: '{print $2}'`
      echo "---------------"
done
