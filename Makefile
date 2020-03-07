.PHONY: prepare umake ninja

define build-dpdk
	docker run --rm -it --privileged -w/dpdk \
		--env UMAKE_CONFIG_MINIO_URL=${UMAKE_CONFIG_MINIO_URL} \
		--env UMAKE_CONFIG_MINIO_ACCESS_KEY=${UMAKE_CONFIG_MINIO_ACCESS_KEY} \
		--env UMAKE_CONFIG_MINIO_SECRET_KEY=${UMAKE_CONFIG_MINIO_SECRET_KEY} -v`pwd`:/dpdk dpdk-builder bash -c "$(1)"
endef


prepare:
	docker build -t dpdk-builder - < Dockerfile
	docker run --rm -it -w/dpdk -v`pwd`:/dpdk dpdk-builder meson build && python3.6 parse_ninja.py

umake:
	# --privileged - for some reason strace needs --privileged mode
	$(call build-dpdk, time umake)

umake-local:
	sudo rm -rf .umake/db.pickle
	$(call build-dpdk, time umake)

umake-remote:
	sudo rm -rf .umake/
	$(call build-dpdk, time umake)

ninja: 
	$(call build-dpdk, cd build && time ninja)

enter:
	$(call build-dpdk, bash)
