#~/bin/bash

rm wookiee_broadcaster

nuitka3 wookiee_broadcaster.py --lto

rm -rf wookiee_broadcaster.build

mv wookiee_broadcaster.bin wookiee_broadcaster
