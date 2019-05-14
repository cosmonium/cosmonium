from panda3d.core import PStatCollector
from functools import wraps

custom_collectors = {}

def pstat(func):
    collectorName = "%s:%s" % ('Engine', func.__name__)
    if not collectorName in custom_collectors.keys():
        custom_collectors[collectorName] = PStatCollector(collectorName)
    pstat = custom_collectors[collectorName]
    @wraps(func)
    def doPstat(*args, **kargs):
        pstat.start()
        returned = func(*args, **kargs)
        pstat.stop()
        return returned
    return doPstat

def levelpstat(name):
    collectorName = "%s:%s" % ('Engine', name)
    if not collectorName in custom_collectors.keys():
        custom_collectors[collectorName] = PStatCollector(collectorName)
    pstat = custom_collectors[collectorName]
    return pstat
