PYTHON?=python3

build:
	$(PYTHON) ../tools/p3d_module_builder/build.py

build-manylinux1:
	docker run --rm -v `pwd`/..:/cosmonium quay.io/pypa/manylinux1_x86_64 /cosmonium/source/build-manylinux1.sh

build-macos-37:
	/usr/local/opt/python@3.7/bin/python3 ../tools/p3d_module_builder/build.py --clean --python-libdir /usr/local/opt/python\@3.7/Frameworks/Python.framework/Python  --python-incdir /usr/local/opt/python\@3.7/Frameworks/Python.framework/Headers

.PHONY: build build-manylinux1 build-macos-37
