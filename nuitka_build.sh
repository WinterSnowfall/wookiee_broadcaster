#!/bin/bash

rm -rf wookiee_broadcaster

nuitka3 wookiee_broadcaster.py --follow-imports --lto

rm -rf wookiee_broadcaster.build

mv wookiee_broadcaster.bin wookiee_broadcaster
