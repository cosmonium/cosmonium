PYTHON?=python3

build:
	$(PYTHON) ../tools/p3d_module_builder/build.py

build-manylinux1:
	docker run --rm -v `pwd`/..:/cosmonium quay.io/pypa/manylinux1_x86_64 /cosmonium/source/build-manylinux1.sh

.PHONY: build build-manylinux1