PYTHON=python3
OPTIONS=

build:
	$(PYTHON) ../tools/p3d_module_builder/build.py $(OPTIONS)

build-manylinux1:
	docker run --rm -v `pwd`/..:/cosmonium quay.io/pypa/manylinux1_x86_64 /cosmonium/source/build-manylinux1.sh

clean:
	@rm -rf build/

.PHONY: build build-manylinux1 clean
