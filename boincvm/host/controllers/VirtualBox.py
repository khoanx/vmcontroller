""" Controller for the VirtualBox hypervisor.

"""
from boincvm.common import support, Exceptions

from twisted.internet import protocol, reactor, defer, threads

import logging
import os
import platform
import sys
import uuid
import pdb


WAITING_GRACE_MS = 3000  #FIXME: magic number of milliseconds

logger = logging.getLogger(__name__)


######## PUBLIC API ################

def start(vm):
  #what an ugly hack this is...
  if platform.system() != "Windows":
    def impl():
      session = _ctx['mgr'].getSessionObject(_ctx['vbox'])
      mach = _findMachineByNameOrId(vm)

      logger.info("Starting VM for machine %s" % mach.name)

      progress = _ctx['vbox'].openRemoteSession(session, mach.id, "vrdp", "")
      progress.waitForCompletion(WAITING_GRACE_MS) 
      completed = progress.completed
      if completed and (progress.resultCode == 0):
        logger.info("Startup of machine %s completed: %s" % (mach.name, str(completed)))
      else:
        _reportError(progress)
        return False

      session.close() 
      return True 

    d = threads.deferToThread(impl)
    
  else: 
    m = _findMachineByNameOrId(vm)
    mName = str(m.name)
    processProtocol = VBoxHeadlessProcessProtocol()
    pseudoCWD = os.path.dirname(sys.modules[__name__].__file__)
    vboxBinariesPath = None #TODO: use VBOX_INSTALL_PATH
    cmdWithPath = os.path.join(pseudoCWD, 'scripts', 'vboxstart.bat')
    cmdWithArgs = ("vboxstart.bat", vboxBinariesPath, mName)
    cmdPath = os.path.join(pseudoCWD, 'scripts')
    newProc = lambda: reactor.spawnProcess( processProtocol, cmdWithPath, args=cmdWithArgs, env=None, path=cmdPath )
    reactor.callWhenRunning(newProc)
    d = True #in order to have a unique return 

  try:
    _startCollectingPerfData(vm)
  except:
    pass #TODO: loggging
  
  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  return d


def powerOff(vm):
  def impl():
    return _execProgressCmd(vm, 'powerOff', None)

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread( impl )
  return d


def shutdown(vm):
  def impl():
    return _execProgressCmd(vm, 'shutdown', None)

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread( impl )
  return d


def pause(vm): 
  def impl():
    return _execProgressCmd(vm, 'pause', None)

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread( impl )
  return d

def unpause(vm): 
  def impl():
    return _execProgressCmd(vm, 'unpause', None)

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread( impl )
  return d


def saveState(vm):
  def impl():
    return _execProgressCmd(vm, 'saveState', None)

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread( impl )
  return d


def saveSnapshot( vm, name, desc):
  def impl():
    return _execProgressCmd(vm, 'saveSnapshot', (name, desc))

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread( impl )
  return d

def restoreSnapshot(vm):
  def impl():
    return _execProgressCmd(vm, 'restoreSnapshot', (name, desc))

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread( impl )
  return d

def getState( vm): 
  def impl():
    m = _ctx['vbox'].findMachine(vm)
    stateCode = m.state
    stateName = _getNameForMachineStateCode(stateCode)
    return stateName

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread(impl)
  
  return d

def listAvailableVMs():
  def impl():
    vbox = _ctx['vbox']
    ms = _getMachines()
    msNames = [ str(m.name) for m in ms ]
    return msNames
  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread(impl)
  return d

def listVMsWithState():
  def impl():
    vbox = _ctx['vbox']
    ms = _getMachines()
    msNamesAndStates = [ (str(m.name), _getNameForMachineStateCode(m.state)) \
        for m in ms ]
    return dict(msNamesAndStates)
  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread(impl)
  return d


def listRunningVMs():
  def impl():
    vbox = _ctx['vbox']
    ms = _getMachines()
    isRunning = lambda m: m.state ==  _ctx['ifaces'].MachineState_Running
    res = filter( isRunning, ms )
    res = [ str(m.name) for m in res ]
    return res
  
  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread(impl)
  return d

def getNamesToIdsMapping(): 
  macToName = _getMACToNameMapping()
  nameToMac = support.reverseDict(macToName)
  return nameToMac

def getIdsToNamesMapping(): 
  macToName = _getMACToNameMapping()
  return macToName


def getPerformanceData(vm):
  def impl():
    return _perf.query( ["*"], [vm] )
    
  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread(impl)
  return d
  

def createVM(name, hddImagePath):
  vbox = _ctx['vbox']
  mgr = _ctx['mgr']
  def impl():
    ms = _getMachines()
    for m in ms:
      if m.name == name:
        raise ValueError("VM '%s' already exists" % name)
    guestType = vbox.getGuestOSType('Linux26') 
    newMachine = vbox.createMachine(name, guestType.id, "", "00000000-0000-0000-0000-000000000000", False)
    if not os.path.isfile( hddImagePath ):
      raise IOError("HDD image path doesn't point to a valid file: %s" % hddImagePath )
      
    try:
      newMachine.saveSettings()
      #register the machine with VB (ie, make it visible)
      vbox.registerMachine( newMachine )
      
      session = mgr.getSessionObject(vbox)
      vbox.openSession( session, newMachine.id )
      mutableM = session.machine
      _attachNICs( mutableM )
      _addSCSIStorageController( mutableM )
      _attachHDToMachine( mutableM, hddImagePath )
    except: 
      if session.state == _ctx['ifaces'].SessionState_Open :
        session.close()

      m = vbox.unregisterMachine(newMachine.id)
      m.deleteSettings()
      msg = "Rolled back creation of VM '%s'" % m.name
      logger.debug(msg)

      #the following two lines should go in a finally:,
      #but that's not supported by python 2.4
      if session.state == _ctx['ifaces'].SessionState_Open:
        session.close()

      raise

    #the following two lines should go in a finally:,
    #but that's not supported by python 2.4
    if session.state == _ctx['ifaces'].SessionState_Open:
      session.close()

    return (True, name)

  logger.debug("Controller method %s invoked" % support.discoverCaller() )
  d = threads.deferToThread( impl )
  return d

def destroyVM(vm):
  def impl():
    session = _getSessionForVM(vm)
    mach = session.machine
    id = mach.id
    name = mach.name

    atts = _ctx['vboxmgr'].getArray( mach, 'mediumAttachments' )
    mediums = []
    for a in atts:
      if a.medium:
        mach.detachDevice(a.controller, a.port, a.device)
        mediums.append( a.medium )
    mach.saveSettings()
    session.close()

    mach = _ctx['vbox'].unregisterMachine( id )
    if mach:
      mach.deleteSettings()

    for m in mediums:
      m.close()

    return (True, name)

  d = threads.deferToThread( impl )
  return d


######### internal methods follow #################

def _attachNICs(mutableM):
  vbox = _ctx['vbox']
  def _findHostOnlyInterface():
    host = vbox.host
    for iface in host.getNetworkInterfaces():
      if iface.interfaceType == _ctx['ifaces'].HostNetworkInterfaceType_HostOnly:
        return iface
    else:
      raise ValueError('No Host-Only interface found on the host')

  nic0 = mutableM.getNetworkAdapter(0) #NAT
  nic1 = mutableM.getNetworkAdapter(1) #host-only

  nic0.attachToNAT()
  nic0.enabled = True

  nic1.attachToHostOnlyInterface()
  hostOnlyIface = _findHostOnlyInterface()
  nic1.hostInterface = hostOnlyIface.name
  nic1.enabled = True

  mutableM.saveSettings()

def _addSCSIStorageController(mutableM):
  newController = mutableM.addStorageController('SCSI', _ctx['ifaces'].StorageBus_SCSI )
  newController.controllerType = _ctx['ifaces'].StorageControllerType_LsiLogic

  mutableM.saveSettings()

def _attachHDToMachine(mutableM, hddImagePath):
  vbox = _ctx['vbox']
  mgr = _ctx['mgr']

#function _assignRandomUUIDToHD not useful anymore:
#VBox fixed the bug the prevented assignation of uuid
#in the openHardDisk method
#  def _assignRandomUUIDToHD():
#    UUID_LINE_KEY = 'ddb.uuid.image' #XXX: always?
#    hdd = file(hddImagePath, 'r+b')
#    pos = 0
#    for l in hdd: #it should be around line 20
#      if l.startswith(UUID_LINE_KEY):
#        newUUIDLine = '%s="%s"' % (UUID_LINE_KEY, uuid.uuid4())
#        msg = "Using '%s' as the new UUID line for HDD image '%s'" % \
#            (newUUIDLine, hddImagePath)
#        logger.debug(msg)
#        hdd.seek(pos)
#        hdd.write(newUUIDLine)
#        hdd.close()
#        break
#      pos += len(l)
#    return
#
#  #_assignRandomUUIDToHD()

  newUUID = str(uuid.uuid4())
  hdd = vbox.openHardDisk(hddImagePath, _ctx['ifaces'].AccessMode_ReadWrite, True, newUUID, False, '')
  hddId = hdd.id
  mutableM.attachDevice('SCSI', 0, 0, _ctx['ifaces'].DeviceType_HardDisk, hddId ) 
  mutableM.saveSettings()


def _startCollectingPerfData(vm):
  _perf.setup(["*"], [vm], 10, 15) #FIXME: magic numbers: period, count

def _getMachines():
  return _ctx['vboxmgr'].getArray(_ctx['vbox'], 'machines')

def _findMachineByNameOrId(vm):
  vbox = _ctx['vbox']
  for m in _getMachines():
    if (m.name == vm) or (m.id == vm):
      res = m
      break
  else: #only reached if "break" never exec'd
    raise Exceptions.NoSuchVirtualMachine(str(vm))
  
  return res 

def _getSessionForVM(vm):
  vbox = _ctx['vbox']
  mgr = _ctx['mgr']
  session = mgr.getSessionObject(vbox)
  m = _findMachineByNameOrId(vm) 
  try:
    vbox.openExistingSession(session, m.id)
  except:
    vbox.openSession(session, m.id)
  return session 



def _getMACToNameMapping():
  vbox = _ctx['vbox']
  def numsToColonNotation(nums):
    nums = str(nums)
    #gotta insert a : every two number, except for the last group.
    g = ( nums[i:i+2] for i in xrange(0, len(nums), 2) )
    return ':'.join(g)
  vbox = _ctx['vbox']
  ms = _getMachines()
  entriesGen = ( ( numsToColonNotation(m.getNetworkAdapter(1).MACAddress), str(m.name) ) 
      for m in _getMachines() ) 
  #entriesGen = ( ( m.getNetworkAdapter(1).MACAddress, str(m.name) ) for m in _getMachines() )

  mapping = dict(entriesGen)
  return mapping


def _initVRDPPorts():
  mgr = _ctx['mgr']
  vbox = _ctx['vbox']
  for i, m in enumerate(_getMachines()):
    if m.sessionState == _ctx['ifaces'].SessionState_Closed:

      session = mgr.getSessionObject(vbox)
      try: 
        vbox.openSession( session, m.id )
        mutableM = session.machine
        if mutableM.state == _ctx['ifaces'].MachineState_PoweredOff:
          vrdpServer = mutableM.VRDPServer
          vrdpServer.authType = _ctx['ifaces'].VRDPAuthType_Null
          vrdpPort = 3389 + i+1 
          vrdpServer.ports = str(vrdpPort)
          logger.debug("VRDP port set to %d for VM %s" % (vrdpPort, mutableM.name))
          mutableM.saveSettings()
        
      finally:
        if session.state == _ctx['ifaces'].SessionState_Open:
          session.close()
    else:
      logger.debug("Ignoring %s (Session state '%s')" % (m.name, m.sessionState))

def _reportError(progress):
    ei = progress.errorInfo
    if ei:
        logger.error("Error in %s: %s" %(ei.component, ei.text) )

def _getNameForMachineStateCode(c):
  d = _ctx['ifaces']._Values['MachineState']
  revD = [k for (k,v) in d.iteritems() if v == c]
  return revD[0]

def _execProgressCmd(vm,cmd,args):
    session = None
    try:
      session = _getSessionForVM(vm)
    except Exception,e:
      logger.error("Session to '%s' not open: %s" % (vm,str(e)))
      return

    if session.state != _ctx['ifaces'].SessionState_Open:
      logger.error("Session to '%s' in wrong state: %s" % (vm, session.state))
      session.close()
      return

    console=session.console
    mach=session.machine
    ops={'pause':           lambda: console.pause(),
         'unpause':         lambda: console.resume(),
         'powerOff':        lambda: console.powerDown(),
         'shutdown':        lambda: console.powerButton(),
         #'stats':          lambda: perfStats(ctx, mach),
         'saveState':       lambda: console.saveState(),
         'saveSnapshot':    lambda: console.takeSnapshot(args[0], args[1]) ,
         'restoreSnapshot': lambda: console.discardCurrentState(),
         #'plugcpu':     lambda: plugCpu(ctx, session.machine, session, args),
         #'unplugcpu':   lambda: unplugCpu(ctx, session.machine, session, args),
         }
    try:
      progress = ops[cmd]()
      if progress:
        progress.waitForCompletion(WAITING_GRACE_MS) 
        completed = progress.completed
        if not completed or (progress.resultCode != 0):
          _reportError(progress)
          return False

      logger.info("Execution of command '%s' on machine %s completed" % \
          (cmd, mach.name))

    except Exception, e:
      logger.error("Problem while running cmd '%s': %s" % (cmd, str(e)) )
      raise

    finally:
      session.close()

    return True


class _VBoxHeadlessProcessProtocol(protocol.ProcessProtocol):

  logger = logging.getLogger( support.discoverCaller() )

  def connectionMade(self):
    self.transport.closeStdin()
    self.logger.debug("VBoxHeadless process started!")

  def outReceived(self, data):
    self.logger.debug("VBoxHeadless stdout: %s" % data)
  def errReceived(self, data):
    self.logger.debug("VBoxHeadless stderr: %s" % data)

  def inConnectionLost(self):
    pass #we don't care about stdin. We do in fact close it ourselves

  def outConnectionLost(self):
    self.logger.info("VBoxHeadless closed its stdout")
  def errConnectionLost(self):
    self.logger.info("VBoxHeadless closed its stderr")

  def processExited(self, reason):
    #This is called when the child process has been reaped 
    pass
  def processEnded(self, reason):
    #This is called when all the file descriptors associated with the child
    #process have been closed and the process has been reaped
    self.logger.warn("Process ended (code: %s) " % reason.value.exitCode)



############ INITIALIZATION ######################

from vboxapi import VirtualBoxManager
_vboxmgr = VirtualBoxManager(None, None)
_ctx = { 
        'vboxmgr': _vboxmgr,
        'ifaces': _vboxmgr.constants,
        'vbox': _vboxmgr.vbox,
        'mgr': _vboxmgr.mgr
      }
_initVRDPPorts()

