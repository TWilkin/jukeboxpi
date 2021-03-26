#!/bin/bash

# Install software
apt-get install i2c-tools
apt-get install mpd mpc
apt-get install lirc
apt-get install pipenv

# Update config.txt
cat boot/config.txt >> /boot/config.txt

# Add LIRC configuration
cp lirc/* /etc/lirc/
rm /etc/lirc/lircd.conf.d/*.conf
wget -O /etc/lirc/lircd.conf.d/ https://sourceforge.net/p/lirc-remotes/code/ci/master/tree/remotes/apple/A1156.lircd.conf
