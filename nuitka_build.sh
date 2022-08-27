#!/bin/bash

rm wookiee_broadcaster
nuitka3 wookiee_broadcaster.py --standalone --onefile --remove-output
chmod +x wookiee_broadcaster.bin
mv wookiee_broadcaster.bin wookiee_broadcaster

