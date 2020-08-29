PLATFORM:=
PLATFORM_ARCH:=
PYTHON=python3
SOURCE_TARGET:=build
RELEASE=0
REQUIREMENTS=

ifeq ($(RELEASE),1)
    PYTHON=python3.7
endif

ifeq ($(OS),Windows_NT)
    PLATFORM:=win
    ifeq ($(PROCESSOR_ARCHITEW6432),AMD64)
        PLATFORM_ARCH:=win_amd64
    else
        ifeq ($(PROCESSOR_ARCHITECTURE),AMD64)
	        PLATFORM_ARCH:=win_amd64
        endif
        ifeq ($(PROCESSOR_ARCHITECTURE),x86)
	        PLATFORM_ARCH:=win32
        endif
    endif
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
        PLATFORM:=manylinux1
        ifeq ($(RELEASE),1)
            SOURCE_TARGET:=build-manylinux1
        endif
	    UNAME_P := $(shell uname -p)
	    ifeq ($(UNAME_P),x86_64)
	        PLATFORM_ARCH:=$(PLATFORM)_x86_64
	    endif
	    ifneq ($(filter %86,$(UNAME_P)),)
	        PLATFORM_ARCH:=$(PLATFORM)_i686
	    endif
	    ifneq ($(filter arm%,$(UNAME_P)),)
	        PLATFORM_ARCH:=$(PLATFORM)_arm
	    endif
    endif
    ifeq ($(UNAME_S),Darwin)
        PLATFORM:=macosx
        ifeq ($(RELEASE),1)
            SOURCE_TARGET:=build-macos-37
            PYTHON=/usr/local/opt/python@3.7/bin/python3
        endif
        PLATFORM_ARCH:=macosx_10_9_x86_64
    endif
endif

clean:
	@cd source && $(MAKE) clean

build: build-source update-mo

build-source:
	@cd source && $(MAKE) $(SOURCE_TARGET) PYTHON=$(PYTHON)
	@mv -f source/*.so lib/

update-mo:
	@cd po && make update-mo

ifeq ($(RELEASE),1)
REQUIREMENTS=source/requirements-$(PLATFORM_ARCH).txt

bapp: build
	@echo "Building for $(PLATFORM)"
	$(PYTHON) setup.py build_apps -p $(PLATFORM_ARCH) -r $(REQUIREMENTS)

bdist: build
	$(PYTHON) setup.py bdist_apps -p $(PLATFORM_ARCH) -r $(REQUIREMENTS)
else
bapp:
	@echo "bapp can only be invoked in RELEASE mode"
bdist:
	@echo "bdist can only be invoked in RELEASE mode"
endif

.PHONY: build build-source update-mo bapp bdist
