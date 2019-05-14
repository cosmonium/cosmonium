from __future__ import print_function
from __future__ import absolute_import

#Import and load before any other packages
from .parsers.configparser import configParser
configParser.load()
configParser.save()
