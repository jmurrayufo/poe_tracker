#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "The following commands will be printed to the prompt, and executed after you press enter."
echo "ctrl+c at any time if you don't wish to run the next command!"

echo "About to run: cp poe-tracker.service /etc/systemd/system/poe-tracker.service"
read
cp poe-tracker.service /etc/systemd/system/poe-tracker.service


echo "About to run: chmod 644 /etc/systemd/system/poe-tracker.service"
read
chmod 644 /etc/systemd/system/poe-tracker.service

echo "About to run: systemctl daemon-reload"
read
systemctl reload-daemon

echo "About to run: systemctl start poe-tracker"
read
systemctl start poe-tracker
systemctl status poe-tracker

echo "About to run: systemctl enable poe-tracker"
read
systemctl enable poe-tracker
systemctl status poe-tracker