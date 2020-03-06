FROM ubuntu:18.04
RUN apt-get update -y
RUN apt-get install -y python3.6 build-essential python3-pip libxml2-dev zlib1g-dev strace ninja-build
RUN apt-get install -y git
RUN pip3 install meson
RUN git clone https://github.com/grisha85/umake.git /umake && pip3 install -e /umake
RUN pip3 install pyinstrument ipdb ipython
