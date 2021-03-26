#!/bin/bash

# Add LIRC configuration
cp lirc/* /etc/lirc/
rm /etc/lirc/lircd.conf.d/*.conf
wget -O /etc/lirc/lircd.conf.d/ https://sourceforge.net/p/lirc-remotes/code/ci/master/tree/remotes/apple/A1156.lircd.conf
