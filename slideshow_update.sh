#!/bin/bash
cd /home/pi/slideshow
git clean -fd
git pull

pgrep -f "python3 slideshow.py" | xargs kill
DISPLAY=:0.0 python3 slideshow.py /home/pi/slideshow/photos 12 &

