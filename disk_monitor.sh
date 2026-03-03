#!/bin/bash
USAGE=$(df / | grep -vE '^Filesystem' | awk '{print $5}' | sed 's/%//g')
if [ $USAGE -gt 75 ]; then
    echo "$(date): WARNING - Disk usage is ${USAGE}%" >> /var/log/disk_monitor.log
fi
