#!/bin/sh

tor -f /etc/tor/torrc &

/usr/sbin/sshd &

nginx -g "daemon off;"
