archery-scorer
==========
Uses open-cv to detect and score an archery scorecard.
Flask is used to host a basic website for a demo. 


Basic Setup
-------------
The base scorecard image is in base_images.
Boxes should be shaded darker so that they can properly be detected. 

Download required packages with pip install -r reqeuirements.txt
If you get the error "ImportError: libGL.so.1: cannot open shared object file: No such file or directory"
Try unistalling opencv-python and install opencv-python-headless
