PYTHON=python3
PYTHON_VERSION=3.7
OPTIONS=

build:
	$(PYTHON) ../tools/p3d_module_builder/build.py $(OPTIONS)

build-manylinux1:
	docker run --rm -v `pwd`/..:/cosmonium quay.io/pypa/manylinux1_x86_64 /cosmonium/source/build-manylinux1.sh

build-macos:
	/usr/local/opt/python@$(PYTHON_VERSION)/bin/python3 ../tools/p3d_module_builder/build.py --python-libdir /usr/local/opt/python\@$(PYTHON_VERSION)/Frameworks/Python.framework/Python  --python-incdir /usr/local/opt/python\@$(PYTHON_VERSION)/Frameworks/Python.framework/Headers $(OPTIONS)

clean:
	@rm -rf build/

.PHONY: build build-manylinux1 build-macos-37 clean
