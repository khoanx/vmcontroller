""" Instantiates the apropriate controller.

It follows the naming convention defined by appending 
the hypervisor name, as gotten from the provided configuration, 
with "Controller". Such a class must be exist and be accesible.

Note that if the controller class resides in a different package,
its name must include the package name as well.
"""
from boincvm.common import support, Exceptions

from twisted.internet import defer

import logging
import inject

logger = logging.getLogger( support.discoverCaller() )

CONTROLLERS_PATH = "controllers" #relative to this file

@inject.param('config')
def _createController(config):
  """ Creates the appropriate (hypervisor) controller based on the
      given configuration. 

      This is the place where to perform particular initialization tasks for 
      the particular hypervisor controller implementations.

      @param config: an instance of L{ConfigParser}
  """
  hv = config.get('Hypervisor', 'hypervisor')
  logger.debug("Hypervisor specified in config: '%s'" % hv)
  fqHvName = "%s.%s" % (CONTROLLERS_PATH, hv)
  
  try:
    hvPkg = __import__(fqHvName, globals=globals(), level=-1)
    hvMod = getattr(hvPkg, hv)
  except ImportError:
    msg = "Hypervisor '%s' is not supported" % hv
    logger.fatal(msg)
    raise Exceptions.ConfigError(msg)

  logger.info("Using %s as the HyperVisor" % hvMod.__name__)

  return hvMod 

_controller = None
def getController():
  global _controller
  if not _controller:
    _controller = _createController()

  return _controller

def start(vm):
  """start(vm)"""
  return defer.maybeDeferred( getController().start, vm )

def powerOff(vm):
  """powerOff(vm)"""
  return defer.maybeDeferred( getController().powerOff, vm )

def pause(vm): 
  """pause(vm)"""
  return defer.maybeDeferred( getController().pause, vm )

def unpause(vm):
  """unpause(vm)"""
  return defer.maybeDeferred( getController().unpause, vm )

def saveState(vm):
  """saveState(vm)"""
  return defer.maybeDeferred( getController().saveState, vm )

def getState(vm):
  """getState(vm)"""
  return defer.maybeDeferred( getController().getState, vm )

def saveSnapshot(vm, name, desc = ""):
  """saveSnapshot(vm, name, desc = "")"""
  return defer.maybeDeferred( getController().saveSnapshot, vm, name, desc )

def restoreSnapshot(vm):
  """restoreSnapshot(vm)"""
  return defer.maybeDeferred( getController().restoreSnapshot, vm )

def listAvailableVMs():
  """listAvailableVMs()"""
  return defer.maybeDeferred( getController().listAvailableVMs )

def listRunningVMs():
  """listRunningVMs()"""
  return defer.maybeDeferred( getController().listRunningVMs )

def getNamesToIdsMapping():
  """getNamesToIdsMapping"""
  return defer.maybeDeferred( getController().getNamesToIdsMapping )

def getIdsToNamesMapping(): 
  """getIdsToNamesMapping"""
  return defer.maybeDeferred( getController().getIdsToNamesMapping )

def getPerformanceData(vm):
  """getPerformanceData(vm)"""
  return defer.maybeDeferred( getController().getPerformanceData, vm)

def createVM(name, hddImagePath):
  """ """
  return defer.maybeDeferred( getController().createVM, name, hddImagePath ) 


