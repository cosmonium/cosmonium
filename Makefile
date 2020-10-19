PLATFORM=
PLATFORM_ARCH=
PYTHON_VERSION=3
PYTHON=python$(PYTHON_VERSION)
SOURCE_TARGET=build
SOURCE_OPTIONS=
OS_SDK=
RELEASE=0
REQUIREMENTS=
PANDA3D_VERSION=1.10.7.dev13

ifeq ($(RELEASE),1)
    PYTHON_VERSION=3.7
	SOURCE_OPTIONS=--clean
endif

ifeq ($(OS),Windows_NT)
    PLATFORM=win
    PYTHON=C:/Panda3D-1.10.7-x64/python/python.exe
    OS_SDK=7.1
    SOURCE_OPTIONS+=--windows-sdk $(OS_SDK)
    SOURCE_OPTIONS+=--cmake 'C:\Program Files\CMake\bin\cmake.exe'
    ifeq ($(PROCESSOR_ARCHITEW6432),AMD64)
        PLATFORM_ARCH=win_amd64
    else
        ifeq ($(PROCESSOR_ARCHITECTURE),AMD64)
            PLATFORM_ARCH=win_amd64
        endif
        ifeq ($(PROCESSOR_ARCHITECTURE),x86)
            PLATFORM_ARCH=win32
        endif
    endif
else
    UNAME_S = $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
        PLATFORM=manylinux1
        ifeq ($(RELEASE),1)
            SOURCE_TARGET=build-manylinux1
        endif
        UNAME_P = $(shell uname -p)
        ifeq ($(UNAME_P),x86_64)
           PLATFORM_ARCH=$(PLATFORM)_x86_64
       endif
       ifneq ($(filter %86,$(UNAME_P)),)
           PLATFORM_ARCH=$(PLATFORM)_i686
       endif
       ifneq ($(filter arm%,$(UNAME_P)),)
           PLATFORM_ARCH=$(PLATFORM)_arm
       endif
    endif
    ifeq ($(UNAME_S),Darwin)
        PLATFORM=macosx
        OS_SDK=10.9
        PYTHON_VERSION=3.7
        SOURCE_TARGET=build-macos
        SOURCE_OPTIONS+=--macosx-sdk $(OS_SDK)
        PLATFORM_ARCH=macosx_10_9_x86_64
        ifneq ($(RELEASE),1)
            SOURCE_OPTIONS+="--use-sdk-path"
        endif
    endif
endif

ifeq ($(PLATFORM),)
    $(error "Unknown platform !")
endif

PANDA3D_WHEEL=https://github.com/cosmonium/panda3d/releases/download/cosmonium-v$(PANDA3D_VERSION)/panda3d-$(PANDA3D_VERSION)+fp64+opt-cp37-cp37m-$(PLATFORM_ARCH).whl

build: build-source update-mo

build-source:
	cd source && "$(MAKE)" $(SOURCE_TARGET) PYTHON="$(PYTHON)" PYTHON_VERSION=${PYTHON_VERSION} OPTIONS="$(SOURCE_OPTIONS)"
ifeq ($(OS),Windows_NT)
	@mv -f source/*.pyd lib/
else
	@mv -f source/*.so lib/
endif

update-mo:
	@cd po && "$(MAKE)" update-mo

clean:
	@cd source && "$(MAKE)" clean

ifeq ($(RELEASE),1)
BUILD_REQ:=

ifeq ($(REQUIREMENTS),)
    REQUIREMENTS=source/requirements-$(PLATFORM_ARCH).txt
    BUILD_REQ:=build-req
endif

build-req:
	@echo "$(PANDA3D_WHEEL)" > $(REQUIREMENTS)
	@cat requirements.txt >> $(REQUIREMENTS)
	@cat $(REQUIREMENTS)

bapp: build $(BUILD_REQ)
	@echo "Building for $(PLATFORM)"
	$(PYTHON) setup.py build_apps -p $(PLATFORM_ARCH) -r $(REQUIREMENTS)

bdist: build $(BUILD_REQ)
	$(PYTHON) setup.py bdist_apps -p $(PLATFORM_ARCH) -r $(REQUIREMENTS)
else
bapp:
	@echo "bapp can only be invoked in RELEASE mode"
bdist:
	@echo "bdist can only be invoked in RELEASE mode"
endif

.PHONY: build build-req build-source update-mo bapp bdist
