#!/bin/sh

sudo sed -i "s|# \(port =\) 7656|\1 8445|g" /etc/i2pd/i2pd.conf
sudo service i2pd start
