#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "The following commands will be printed to the prompt, and executed after you press enter."
echo "ctrl+c at any time if you don't wish to run the next command!"

echo "About to run: cp poe-tracker-dev.service /etc/systemd/system/poe-tracker-dev.service"
# read
cp poe-tracker-dev.service /etc/systemd/system/poe-tracker-dev.service


echo "About to run: chmod 644 /etc/systemd/system/poe-tracker-dev.service"
# read
chmod 644 /etc/systemd/system/poe-tracker-dev.service

echo "About to run: systemctl daemon-reload"
# read
systemctl daemon-reload

echo "About to run: systemctl start poe-tracker-dev"
# read
systemctl restart poe-tracker-dev
systemctl status poe-tracker-dev

echo "About to run: systemctl enable poe-tracker-dev"
# read
systemctl enable poe-tracker-dev
systemctl status poe-tracker-dev