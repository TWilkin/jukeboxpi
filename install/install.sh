#!/bin/bash

echo "JukeboxPi installer"

# Install software
apt-get install i2c-tools
apt-get install mpd mpc mpdscribble
apt-get install lirc
apt-get install pipenv

# Update config.txt
cat boot/config.txt >> /boot/config.txt

# Add MPD configuration
usermod -a -G i2c mpd
cp mpd/mpd.conf /etc/mpd.conf

# Add LIRC configuration
cp lirc/* /etc/lirc/
rm /etc/lirc/lircd.conf.d/*.conf
wget -O /etc/lirc/lircd.conf.d/A1156.lircd.conf https://sourceforge.net/p/lirc-remotes/code/ci/master/tree/remotes/apple/A1156.lircd.conf?format=raw
systemctl enable irexec

# Add Python LCD
mkdir /opt/jukebox
cp -r lcd/* /opt/jukebox
cat lcd.sh >> /etc/rc.local
chown -R pi.pi /opt/jukebox

echo "Install complete, restart your Pi!"
