.PHONY: prepare umake ninja

prepare:
	docker build -t dpdk-builder - < Dockerfile
	docker run --rm -it -w/dpdk -v`pwd`:/dpdk dpdk-builder meson build && python3.6 parse_ninja.py

umake:
	# --privileged - for some reason strace needs --privileged mode
	docker run --rm -it --privileged -w/dpdk -v/home/dn/umake:/umake -v`pwd`:/dpdk dpdk-builder bash -c 'time umake --no-remote-cache'
ninja: 
	docker run --rm -it -w/dpdk/build -v`pwd`:/dpdk dpdk-builder bash -c 'time ninja'

