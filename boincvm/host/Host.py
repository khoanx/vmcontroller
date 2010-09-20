""" Represents the host, along with its supported operations. 

This module isn't meant to be used directly, but rather through the exposed
XMLRPC facade.
"""

from boincvm.common import support, Exceptions
import HyperVisorController


from twisted.internet import defer

import logging
import inject
import pdb 

#@inject.appscope
#class Host(object):
#  logger = logging.getLogger( support.discoverCaller() )
#
#  cmdRegistry = CommandRegistry()
#  vmRegistry = VMRegistry()
#  fileTxs = FileTxs()
#  xmlrpcServer = HostXMLRPCService()
#    
#  def requestCommandExecution(self, toVmName, cmd, args=(), env={}, path=None, fileForStdin=''):
#    if not self._vmRegistry.isValid(to):
#      msg = "Invalid VM Id: '%s'" % to 
#      self.logger.error(msg)
#      raise ValueError(msg)
#
#    return cmdReqsSent.requestCommandExecution(
#
#  def requestCmdExecution(self, to, cmdId, cmd, args=(), env={}, path=None, fileForStdin=''):
#
#  def processCommandExecutionResults():
#
#
#  def addVM():
#
#  def removeVM():
#
#
#  def copyFileToVM():
#
#  def copyFileFromVM():
#
#
#
#  def getDescriptor():
#
#
#
#@inject.appscope
#class CommandRegistry(object):
#  """ 
#  For all command-execution related. 
#
#  Keeps track of requests made, served and retired
#  """
#  logger = logging.getLogger(support.discoverCaller())
#
#  def __init__(self):
#    self._cmdReqsSent = {} #cmdId: dict with keys (timestamp, to, cmd, args, env, path)
#    self._cmdReqsRetired = {} #finished cmdReqsSent
#    self._cmdReqsRcvd = {}
#
#  #XXX: too many args. Create a "request" object encapsulating it
#  def requestCmdExecution(self, toVmId, cmdId, cmd, args=(), env={}, path=None, fileForStdin=''):
#    toSend = words.CMD_RUN(self).
#             howToSay(self, toVmId, cmdId, cmd, args, env, 
#                 path, fileForStdin )
#
#    #XXX: move to Host. The CommandRegistry only deals with the creation of the message
#    engine.sendStompMessage( toSend )
#
#    #XXX: code repetition. see comment at method's head
#    requestKeys = ('timestamp', 'to', 'cmd', 'args', 'env', 'path', 'fileForStdin')
#    requestValues = (time.time(), to, cmd, args, env, path, fileForStdin )
#    self._cmdReqsSent[cmdId] = dict( zip( requestKeys, requestValues) )
#    self.logger.info("Requested execution of command '%s' with cmd-id '%s'" % (cmd, cmdId))
#
#  def processCmdResult(self, resultsMsg):
#    serializedResults = resultsMsg['body'].split(None, 1)[1]
#    #serializeded data: dict with keys (cmd-id, out, err, finished?, code/signal, resources)
#    results = support.deserialize(serializedResults)
#    self.logger.debug("Deserialized results: %s" % results)
#    cmdId = results.pop('cmd-id')
#    #this comes from a word.CMD_RESULT.listenAndAct
#    #note down for which cmd we are getting the result back
#    assert cmdId in self._cmdReqsSent
#    self._cmdReqsRcvd[cmdId] = results
#    self._cmdReqsRetired[cmdId] = self._cmdReqsSent.pop(cmdId)
#    self.logger.info("Received command results for cmd-id '%s'", cmdId )
#
#  def popCmdResults(self, cmdId):
#    # for invalid cmdIds, returning None could
#    # result in problems with xml-rpc. Thus we
#    # resource to an empty string, which likewise
#    # fails a boolean test
#    return self._cmdReqsRcvd.pop(cmdId, "") 
#
#
#  def listFinishedCmds(self):
#    return self._cmdReqsRcvd.keys()
#
#  def getCmdDetails(self, cmdId):
#    details = self._cmdReqsSent.get(cmdId)
#    if not details:
#      details = self._cmdReqsRetired.get(cmdId)
#    return support.serialize(details)




@inject.appscope
class VMRegistry(object):
  """
  Keeps track of the registered virtual machines.
  """
  logger = logging.getLogger(support.discoverCaller())

  #PING/PONG
  #HELLO/BYE
  #STILL_ALIVE

  @inject.param('hvController')
  def __init__(self, hvController):
    self._vms = {}
    self._hvController = hvController
    self._idsToNames = self._getIdsToNamesMapping()

  def addVM(self, vmDescriptor):
    """
    @param vmDescriptor an instance of L{EntityDescriptor}
    """
    name = self._getNameForId( vmDescriptor.id )
    vmDescriptor.name = name
    self._vms[vmDescriptor.id] = vmDescriptor
    self.logger.info("VM '%s' has joined the party" % self._vms[vmDescriptor.id].name )

  def removeVM(self, vmId): 
    """ Removes a VM from the party """
    vmDescriptor = self._vms.pop(vmId)
    self.logger.info("VM '%s' has left the party" % vmDescriptor.name )

  def isValid(self, vmId):
    return vmId in self._vms

  def __getitem__(self, vmId):
    return self._vms[vmId]

  def getRegisteredVMs(self):
    """ Returns a list of the registered VMs """
    return self._vms.keys()
  
  def _getNameForId(self, vmId):
    name = self._idsToNames.get(vmId)
    if not name:
      self.logger.error("Unable to match VM ID '%s' to any registered VM (is \
          the VM controller really running from within a VM?)", str(vmId))
      raise Exceptions.NoSuchVirtualMachine(str(vmId))
    else:
      return name

  def _getIdsToNamesMapping(self):
    def holder(): pass
    holder.res = None

    @defer.inlineCallbacks
    def _initializeIdsToNamesMapping():
      idsToNamesMap = yield self._hvController.getIdsToNamesMapping()
      self.logger.debug("Ids -> Names table initialized: %s" % idsToNamesMap)
      holder.res = idsToNamesMap
    
    _initializeIdsToNamesMapping()
    return holder.res


#@inject.appscope
#class FileTxs(object):
#  """ 
#  Handles the file transmission (to and from).
#  """
#  logger = logging.getLogger(support.discoverCaller())
#  vmRegistry = inject.attr('VMRegistry', VMRegistry)
#  def __init__(self):
#
#  def cpFileToVM(self, vmId, pathToLocalFileName, pathToRemoteFileName = None ):
#    """
#    @param pathToRemoteFileName where to store the file, relative to the root of the server.
#    If None, the basename of the source will be stored in the / of the server.
#    """
#    #this returns a deferred whose callbacks take care of returning the result
#    if not self.vmRegistry.isValid(vmId):
#      msg = "Invalid VM Id: '%s'" % vmId 
#      self.logger.error(msg)
#      dres = defer.fail(msg)
#    else:
#      vmIp = self.vmRegistry[vmId].ip 
#      if not pathToRemoteFileName:
#        pathToRemoteFileName = basename(pathToLocalFileName)
#      #chirp_put [options] <local-file> <hostname[:port]> <remote-file>
#      args = ('-t 10', pathToLocalFileName, vmIp, pathToRemoteFileName) #FIXME: magic numbers
#      chirp_cmd = join( self._chirpPath, 'chirp_put')
#      dres = utils.getProcessOutputAndValue(chirp_cmd, args)
#
#    return dres
#    
#
#  def cpFileFromVM(self, vmId, pathToRemoteFileName, pathToLocalFileName = None):
#    #this returns a deferred whose callbacks take care of returning the result
#    if not self.vmRegistry.isValid(vmId):
#      msg = "Invalid VM Id: '%s'" % vmId 
#      self.logger.error(msg)
#      dres = defer.fail(msg)
#    else:
#      vmIp = self._vms[vmId].ip
#      if not pathToLocalFileName:
#        pathToLocalFileName = pathToRemoteFileName
#      #chirp_get [options] <hostname[:port]> <remote-file> <local-file>
#      args = ('-t 10', vmIp, pathToRemoteFileName, pathToLocalFileName)  #FIXME: magic numbers
#      chirp_cmd = join( self._chirpPath, 'chirp_get')
#      dres = utils.getProcessOutputAndValue(chirp_cmd, args)
#    return dres

