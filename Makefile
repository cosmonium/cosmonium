PLATFORM=
TARGET_PLATFORM=
PYTHON=python3
SOURCE_TARGET=build
SOURCE_OPTIONS=
OS_SDK=
RELEASE=0
REQUIREMENTS=
PANDA3D_BASE_VERSION=1.11.0
CUSTOM_PANDA3D=1
ifeq ($(CUSTOM_PANDA3D),1)
    EXTRA_INDEX=""
    PANDA3D_VERSION=$(PANDA3D_BASE_VERSION).dev3368
    PANDA3D_VERSION_LONG=$(PANDA3D_VERSION)-gd9052bae76
else
    EXTRA_INDEX="--extra-index-url https://archive.panda3d.org/simple"
    PANDA3D_VERSION=$(PANDA3D_BASE_VERSION).dev3368
endif

BASE_VERSION=0.2.1.1
TAG_VERSION=0.3.0
COUNT=$(shell git rev-list --count v$(BASE_VERSION)..HEAD)

UI_LIST=default


ifneq ($(COUNT),)
  ifeq ($(COUNT),0)
    VERSION="$(TAG_VERSION)"
  else
    VERSION="$(TAG_VERSION).dev$(COUNT)"
  endif
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
            PLATFORM_BASE=linux
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
    PYTHON=C:/Panda3D-$(PANDA3D_BASE_VERSION)-x64/python/python.exe
    OS_SDK=8.1
    SOURCE_OPTIONS+=--windows-sdk $(OS_SDK)
endif

ifeq ($(PLATFORM),win32)
    PYTHON=C:/Panda3D-$(PANDA3D_BASE_VERSION)/python/python.exe
    OS_SDK=8.1
    SOURCE_OPTIONS+=--windows-sdk $(OS_SDK)
endif

ifneq ($(findstring manylinux2014,$(PLATFORM)),)
    SOURCE_TARGET=build-manylinux2014
endif

ifeq ($(PLATFORM),macosx_10_9_x86_64)
    OS_SDK=10.9
    SOURCE_OPTIONS+=--macosx-sdk $(OS_SDK)
    ifneq ($(RELEASE),1)
        SOURCE_OPTIONS+="--use-sdk-path"
    endif
endif

ifeq ($(PLATFORM),)
    $(error "Unknown platform !")
endif

ifeq ($(TARGET_PLATFORM),)
  TARGET_PLATFORM=$(PLATFORM)
endif

PYTHON_ABI=`$(PYTHON) tools/pyversion.py`


ifeq ($(CUSTOM_PANDA3D),1)
    PANDA3D_WHEEL=https://github.com/cosmonium/panda3d/releases/download/cosmonium-v$(PANDA3D_VERSION_LONG)/panda3d-$(PANDA3D_VERSION)+fp64-$(PYTHON_ABI)-$(TARGET_PLATFORM).whl
else
    PANDA3D_WHEEL="panda3d==$(PANDA3D_VERSION)"
endif

build: build-version build-source update-mo update-ui-mo update-data-mo

build-source:
	cd source && "$(MAKE)" $(SOURCE_TARGET) PYTHON="$(PYTHON)" OPTIONS="$(SOURCE_OPTIONS)"
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

update-ui-pot:
	for ui in $(UI_LIST); do cd config/ui/$$ui/po; "$(MAKE)" update-pot; cd ../../..; done

update-ui-po:
	for ui in $(UI_LIST); do cd config/ui/$$ui/po; "$(MAKE)" update-po; cd ../../..; done

update-ui-mo:
	for ui in $(UI_LIST); do cd config/ui/$$ui/po; "$(MAKE)" update-mo; cd ../../..; done

build-version:
ifneq ($(VERSION),)
	@echo 'Cosmonium version $(VERSION)'
	@echo 'version=$(VERSION)' > cosmonium/buildversion.py
else
	@rm -f cosmonium/buildversion.py
endif

clean:
	@cd source && "$(MAKE)" clean

BUILD_REQ:=

ifeq ($(REQUIREMENTS),)
    REQUIREMENTS=source/requirements-$(TARGET_PLATFORM).txt
    BUILD_REQ:=build-req
endif

build-req:
ifneq ($(EXTRA_INDEX),)
	@echo "$(EXTRA_INDEX)" > $(REQUIREMENTS)
else
	@echo > $(REQUIREMENTS)
endif

ifneq ($(PANDA3D_WHEEL),)
	@echo "$(PANDA3D_WHEEL)" >> $(REQUIREMENTS)
else
	@echo panda3d >> $(REQUIREMENTS)
endif
	@cat requirements.txt >> $(REQUIREMENTS)
	@cat $(REQUIREMENTS)

bapp: build-version $(BUILD_REQ)
	@echo "Building for $(TARGET_PLATFORM)"
	$(PYTHON) setup.py build_apps -p $(TARGET_PLATFORM) -r $(REQUIREMENTS)

bdist: build-version $(BUILD_REQ)
	@echo "Building for $(TARGET_PLATFORM)"
	$(PYTHON) setup.py bdist_apps -p $(TARGET_PLATFORM) -r $(REQUIREMENTS)

bclean:
	rm -rf build/

DIST_FILES=$(patsubst dist/%, %, $(wildcard dist/*.zip dist/*.tar.gz dist/*.exe dist/*.toto))
shasum:
	cd dist && for file in $(DIST_FILES); do shasum -a 512 $$file > $$file.sha512; done

.PHONY: build build-req build-source update-mo bapp bdist shasum
