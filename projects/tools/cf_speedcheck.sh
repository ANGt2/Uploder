#!/bin/bash

echo "IP,Ping,DownloadSpeed(MB/s),TimeTaken(s)" > results.csv

URL_PATH="https://speed.cloudflare.com/__down?bytes=5000000"

while IFS= read -r ip; do
    echo "🌐 در حال بررسی $ip ..."
    
    # پینگ گرفتن
    echo "📡 پینگ $ip در حال انجام..."
    ping -c 1 -W 1 $ip > /dev/null
    if [ $? -eq 0 ]; then
        echo "$ip ✅ پاسخ پینگ دارد"
        ping_status="✅"
        
        echo "🚀 تست سرعت دانلود برای $ip ..."
        START=$(date +%s%3N)
        curl -s -o /dev/null --resolve speed.cloudflare.com:443:$ip "$URL_PATH"
        END=$(date +%s%3N)

        # محاسبه زمان
        TIME_MS=$((END - START))
        TIME_SEC=$(echo "scale=3; $TIME_MS / 1000" | bc)

        # محاسبه سرعت
        SPEED=$(echo "scale=2; 5 / $TIME_SEC" | bc)

        echo "$ip ✅ سرعت: $SPEED MB/s ⏱ زمان: ${TIME_SEC}s"
        echo "$ip,$ping_status,$SPEED,$TIME_SEC" >> results.csv

    else
        echo "$ip ❌ بدون پاسخ پینگ"
        echo "$ip,❌,0,0" >> results.csv
    fi

    echo "-------------------------------"

done < iplist.txt
