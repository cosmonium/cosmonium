PLATFORM=
PYTHON_VERSION=3
PYTHON=python$(PYTHON_VERSION)
SOURCE_TARGET=build
SOURCE_OPTIONS=
OS_SDK=
RELEASE=0
REQUIREMENTS=
PANDA3D_VERSION=1.10.7.dev30

ifeq ($(RELEASE),1)
    PYTHON_VERSION=3.7
	SOURCE_OPTIONS=--clean
endif

ifeq ($(PLATFORM),)
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
        UNAME_S = $(shell uname -s)
        ifeq ($(UNAME_S),Linux)
            PLATFORM_BASE=manylinux1
            UNAME_P = $(shell uname -p)
            ifeq ($(UNAME_P),x86_64)
               PLATFORM=$(PLATFORM_BASE)_x86_64
           endif
           ifneq ($(filter %86,$(UNAME_P)),)
               PLATFORM=$(PLATFORM_BASE)_i686
           endif
           ifneq ($(filter arm%,$(UNAME_P)),)
               PLATFORM=$(PLATFORM_BASE)_arm
           endif
        endif
        ifeq ($(UNAME_S),Darwin)
            PLATFORM=macosx_10_9_x86_64
        endif
    endif
endif

ifeq ($(PLATFORM),win_amd64)
    PYTHON=C:/Panda3D-1.10.7-x64/python/python.exe
    OS_SDK=7.1
    SOURCE_OPTIONS+=--windows-sdk $(OS_SDK)
    SOURCE_OPTIONS+=--cmake 'C:\Program Files\CMake\bin\cmake.exe'
endif

ifeq ($(PLATFORM),win32)
    PYTHON=C:/Panda3D-1.10.7/python/python.exe
    OS_SDK=7.1
    SOURCE_OPTIONS+=--windows-sdk $(OS_SDK)
    SOURCE_OPTIONS+=--cmake 'C:\Program Files\CMake\bin\cmake.exe'
endif

ifneq ($(findstring manylinux,$(PLATFORM)),)
    ifeq ($(RELEASE),1)
        SOURCE_TARGET=build-manylinux1
    endif
endif

ifeq ($(PLATFORM),macosx_10_9_x86_64)
    OS_SDK=10.9
    PYTHON_VERSION=3.7
    SOURCE_OPTIONS+=--macosx-sdk $(OS_SDK)
    ifneq ($(RELEASE),1)
        SOURCE_OPTIONS+="--use-sdk-path"
    endif
endif

ifeq ($(PLATFORM),)
    $(error "Unknown platform !")
endif

PANDA3D_WHEEL=https://github.com/cosmonium/panda3d/releases/download/cosmonium-v$(PANDA3D_VERSION)/panda3d-$(PANDA3D_VERSION)+fp64+opt-cp37-cp37m-$(PLATFORM).whl

build: build-source update-mo update-data-mo

build-source:
	cd source && "$(MAKE)" $(SOURCE_TARGET) PYTHON="$(PYTHON)" PYTHON_VERSION=${PYTHON_VERSION} OPTIONS="$(SOURCE_OPTIONS)"
ifeq ($(OS),Windows_NT)
	@mv -f source/*.pyd lib/
else
	@mv -f source/*.so lib/
endif

update-pot:
	@cd po && "$(MAKE)" update-pot

update-po:
	@cd po && "$(MAKE)" update-po

update-mo:
	@cd po && "$(MAKE)" update-mo

update-data-pot:
	@cd data/po && "$(MAKE)" update-pot

update-data-po:
	@cd data/po && "$(MAKE)" update-po

update-data-mo:
	@cd data/po && "$(MAKE)" update-mo

clean:
	@cd source && "$(MAKE)" clean

ifeq ($(RELEASE),1)
BUILD_REQ:=

ifeq ($(REQUIREMENTS),)
    REQUIREMENTS=source/requirements-$(PLATFORM).txt
    BUILD_REQ:=build-req
endif

build-req:
	@echo "$(PANDA3D_WHEEL)" > $(REQUIREMENTS)
	@cat requirements.txt >> $(REQUIREMENTS)
	@cat $(REQUIREMENTS)

bapp: build $(BUILD_REQ)
	@echo "Building for $(PLATFORM)"
	$(PYTHON) setup.py build_apps -p $(PLATFORM) -r $(REQUIREMENTS)

bdist: build $(BUILD_REQ)
	$(PYTHON) setup.py bdist_apps -p $(PLATFORM) -r $(REQUIREMENTS)
else
bapp:
	@echo "bapp can only be invoked in RELEASE mode"
bdist:
	@echo "bdist can only be invoked in RELEASE mode"
endif

.PHONY: build build-req build-source update-mo bapp bdist
