PYTHON=python3
OPTIONS=

build:
	$(PYTHON) ../tools/p3d_module_builder/build.py $(OPTIONS)

build-manylinux2014:
	docker run -v `pwd`/..:/cosmonium quay.io/pypa/manylinux2014_x86_64 /cosmonium/source/build-manylinux2014.sh

clean:
	@rm -rf build/

.PHONY: build build-manylinux2014 clean
