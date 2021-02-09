#! /bin/bash

echo Installing C dependencies
sudo apt install gcc make pkg-config libyaml-dev libiio-dev gir1.2-gtk-3.0 libgtk-3-0

echo Installing Python3 version of used libs
sudo apt install python3 python3-yaml python3-paramiko python3-gi python3-tz python3-netifaces python3-dateutil python3-smbc

echo Installing Python2 version of used libs
sudo apt install python python-yaml python-paramiko python-mysql.connector python-gi python-tz python-netifaces python-dateutil python-smbc

