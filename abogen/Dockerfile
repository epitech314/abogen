# Special thanks to @geo38 from Reddit, who provided this Dockerfile:
# https://www.reddit.com/r/selfhosted/comments/1k8x1yo/comment/mpe0bz8/

# Use a docker base image that runs a window manager that can be viewed
# outside the image with a web browser or VNC client.
# https://github.com/jlesage/docker-baseimage-gui
FROM jlesage/baseimage-gui:debian-12-v4

# Load stuff needed by abogen
RUN apt-get update \
 && apt-get install -y \
        python3 \
        python3-venv \
        python3-pip \
        python3-pyqt6 \
        espeak-ng \
        libxcb-cursor0 \
        libgl1 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# The base image will run /startapp.sh on launch.
#
# The base image runs that script as user 'app' uid=1000. That user
# does not exist in the base image but is created at run time.
#
# We need to install abogen in python venv (requirement of newer python3).
#
# The python venv has to be writable by the 'app' user as abogen dynamically
# installs python packages, so create the venv as that user
#
# We intend to share the /shared directory with the host using a bind volume
# in order to access any source files and the created files.

RUN echo '#!/bin/bash\nsource /app/venv/bin/activate\nexec abogen' > /startapp.sh \
  && chmod 555 /startapp.sh \
  && mkdir /app /shared \
  && chown 1000:1000 /app /shared \
  && chmod 755 /app /shared
USER 1000:1000
RUN python3 -m venv /app/venv
RUN /bin/bash -c "source /app/venv/bin/activate && pip install abogen"
# Change back to user ROOT as the startup scripts inside base image needs it
USER root
