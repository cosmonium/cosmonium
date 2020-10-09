PLATFORM:=
PLATFORM_ARCH:=
PYTHON=python3
SOURCE_TARGET:=build
SOURCE_OPTIONS=
RELEASE=0
REQUIREMENTS=

ifeq ($(RELEASE),1)
    PYTHON=python3.7
endif

ifeq ($(OS),Windows_NT)
    PLATFORM:=win
    PYTHON=C:/thirdparty/win-python3.7-x64/python.exe
    ifeq ($(RELEASE),1)
        SOURCE_TARGET:=build-win-release
    endif
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
        SOURCE_TARGET:=build-macos
        PLATFORM_ARCH:=macosx_10_9_x86_64
    endif
endif

build: build-source update-mo

build-source:
	cd source && "$(MAKE)" $(SOURCE_TARGET) PYTHON=$(PYTHON) OPTIONS=$(SOURCE_OPTIONS)
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
