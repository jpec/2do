#!/bin/sh
echo "*******************"
echo "Installation of 2do"
echo "*******************"

sudo cp 2do.py /usr/bin/2do.py
sudo cp 2do.desktop /usr/share/applications/2do.desktop
sudo chmod a+x /usr/bin/2do.py
sudo chmod a+x /usr/share/applications/2do.desktop

echo "Installation done !"
