try:
    from . import buildversion
    version_str = buildversion.version
except ImportError:
    version_str = "0.3.0"

version_major = int(version_str.split('.')[0])
version_minor = int(version_str.split('.')[1])
version_revision = int(version_str.split('.')[2])

version = (version_major, version_minor, version_revision)
