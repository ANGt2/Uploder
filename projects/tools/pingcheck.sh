#!/bin/bash

> alive.txt

while IFS= read -r ip; do
    echo "در حال بررسی $ip ..."
    ping -c 1 -W 1 $ip > /dev/null
    if [ $? -eq 0 ]; then
        echo "$ip ✅ پاسخ می‌دهد"
        echo $ip >> alive.txt
    else
        echo "$ip ❌ بدون پاسخ"
    fi
done < iplist.txt
