PLATFORM=
PYTHON=python3

ifeq ($(OS),Windows_NT)
    ifeq ($(PROCESSOR_ARCHITEW6432),AMD64)
        PLATFORM=win_amd64
    else
        ifeq ($(PROCESSOR_ARCHITECTURE),AMD64)
	        PLATFORM=win_amd64
        endif
        ifeq ($(PROCESSOR_ARCHITECTURE),x86)
	        PLATFORM=win32
        endif
    endif
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
        PLATFORM=manylinux1
	    UNAME_P := $(shell uname -p)
	    ifeq ($(UNAME_P),x86_64)
	        PLATFORM+=_x86_64
	    endif
	    ifneq ($(filter %86,$(UNAME_P)),)
	        PLATFORM+=_i686
	    endif
	    ifneq ($(filter arm%,$(UNAME_P)),)
	        PLATFORM+=_arm
	    endif
    endif
    ifeq ($(UNAME_S),Darwin)
        PLATFORM=macosx_10_9_x86_64
    endif
endif

build: build-source update-mo

build-source:
	@cd source && $(PYTHON) ../tools/p3d_module_builder/build.py
	@mv source/*.so lib/

update-mo:
	@cd po && make update-mo

bapp: build
	@echo "Building for $(PLATFORM)"
	$(PYTHON) setup.py build_apps -p $(PLATFORM)

bdist: build
	$(PYTHON) setup.py bdist_apps -p $(PLATFORM)

.PHONY: build build-source update-mo bapp bdist
