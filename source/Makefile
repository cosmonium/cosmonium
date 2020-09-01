PYTHON?=python3
ABI=3.7
OPTIONS=

build:
	$(PYTHON) ../tools/p3d_module_builder/build.py $(OPTIONS)

build-manylinux1:
	docker run --rm -v `pwd`/..:/cosmonium quay.io/pypa/manylinux1_x86_64 /cosmonium/source/build-manylinux1.sh

build-macos:
	/usr/local/opt/python@$(ABI)/bin/python3 ../tools/p3d_module_builder/build.py --use-sdk-path --python-libdir /usr/local/opt/python\@$(ABI)/Frameworks/Python.framework/Python  --python-incdir /usr/local/opt/python\@$(ABI)/Frameworks/Python.framework/Headers

build-macos-release:
	/usr/local/opt/python@$(ABI)/bin/python3 ../tools/p3d_module_builder/build.py --clean --python-libdir /usr/local/opt/python\@$(ABI)/Frameworks/Python.framework/Python  --python-incdir /usr/local/opt/python\@$(ABI)/Frameworks/Python.framework/Headers

build-win-release:
	$(PYTHON) ../tools/p3d_module_builder/build.py --clean --windows-sdk 7.1

clean:
	@rm -rf build/

.PHONY: build build-manylinux1 build-macos-37 clean
