import platform
import sys

version = platform.python_version_tuple()

base = "cp{}{}".format(version[0], version[1])

# abiflags is only available on Unix platforms
if hasattr(sys, 'abiflags'):
    abiflags = list(sys.abiflags) or ['']
else:
    abiflags = ['']

platform_tag = '-'.join([base] + [base + abi for abi in abiflags])

print(platform_tag)
