try:
    from . import buildversion
    version = buildversion.version
except ImportError:
    version = "v0.2.x"
