CEFPython3 shared library references libpythonX.Y.so.1.0 by mistake on Linux.
By design libpythonX.Y.so.1.0 is not shipped with Panda3D as it is already
included in the Panda3D shared libraries. To avoid an error due to a missing
library we add empty libraries with the required name.

See https://github.com/panda3d/panda3d/issues/839