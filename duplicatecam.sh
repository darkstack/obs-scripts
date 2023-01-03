#!/bin/bash
VIDEO=`ls -1 /dev/video3`
if [ -e /dev/video3 ]; then
    echo "found V4L2"
else
    echo "not found V4L2"
    sudo modprobe v4l2loopback exclusive_caps=1 video_nr=3,4
fi 
echo "Duplicate with ffmpeg"
ffmpeg -i /dev/video0 -f v4l2 /dev/video3 -f v4l2 /dev/video4 
