#!/bin/bash

NUITKA_COMPILE_FLAGS="--standalone --onefile --remove-output --no-deployment-flag=self-execution"

rm bin/wookiee_broadcaster
nuitka3 wookiee_broadcaster.py $NUITKA_COMPILE_FLAGS
chmod +x wookiee_broadcaster.bin
mv wookiee_broadcaster.bin bin/wookiee_broadcaster

