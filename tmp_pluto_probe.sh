#!/bin/bash
HOST=192.168.2.1
echo "=== ping ==="
ping -c 2 -W 2 $HOST
echo "=== route ==="
ip route get $HOST
echo "=== neigh ==="
ip neigh show $HOST
echo "=== ports ==="
for p in 22 23 2222 5555 80 443 30431 8080; do
  if timeout 2 bash -c "echo >/dev/tcp/$HOST/$p" 2>/dev/null; then
    echo "OPEN $p"
  else
    echo "closed/timeout $p"
  fi
done
echo "=== nmap ==="
command -v nmap >/dev/null && nmap -Pn -p 22,23,80,443,2222,5555 --open $HOST || echo "no nmap"
echo "=== ssh verbose ==="
ssh -v -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@$HOST 'uname -a' 2>&1 | tail -40
