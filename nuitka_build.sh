#!/bin/bash

rm wookiee_broadcaster
nuitka3 wookiee_broadcaster.py --standalone --onefile --remove-output
mv wookiee_broadcaster.bin wookiee_broadcaster

