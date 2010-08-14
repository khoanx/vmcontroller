from boincvm.host.controllers import VirtualBox

from twisted.trial import unittest
from twisted.internet import reactor, defer

import sys
import os
import tempfile
import logging
import shutil
import time
import pdb 

logging.basicConfig(level=logging.INFO, \
    format='%(message)s', )

VBOX_FOLDER = os.getenv('VBOX_USER_HOME')
print "Using %s as the VBOX_USER_HOME" % VBOX_FOLDER

class TestVirtualBoxController(unittest.TestCase):
  timeout=10.0
  def _createVMs(self):
    # create VMs
    self.IMAGE1_LOCATION = 'testVMImages/image1/cernvm-1.6.0-x86.vmdk'
    self.IMAGE2_LOCATION = 'testVMImages/image2/cernvm-1.6.0-x86.vmdk'

    imagePath1 = os.path.join(sys.path[0], 
        self.IMAGE1_LOCATION)
    imagePath2 = os.path.join(sys.path[0], 
        self.IMAGE2_LOCATION)

    self.assertTrue(os.path.isfile(imagePath1))
    self.assertTrue(os.path.isfile(imagePath2))

    d1 = VirtualBox.createVM("image1", imagePath1)
    d2 = VirtualBox.createVM("image2", imagePath2)
    
    dl = defer.DeferredList([d1,d2])
    return dl

  
  @defer.inlineCallbacks
  def _powerEverythingOff(self): 
    try:
      yield VirtualBox.powerOff('image1')
      yield VirtualBox.powerOff('image2')
    except:
      pass

  def _destroyVMs(self): 
    d1 = VirtualBox.destroyVM('image1')
    d2 = VirtualBox.destroyVM('image2')

    dl = defer.DeferredList([d1, d2])
    return dl


  def setUp(self):
    return self._createVMs() 

  def tearDown(self):
    return self._destroyVMs()

 
  def test_createVM(self):
    _toStdMACSyntax = lambda s: \
      ':'.join([ s[i:i+2]  for i in range(0,len(s),2) ])

    for machineName in ('image1', 'image2'):
      m = VirtualBox._findMachineByNameOrId(machineName)

      nic0 = m.getNetworkAdapter(0)
      nic0attachmentType = nic0.attachmentType
      self.assertEquals(VirtualBox._ctx['ifaces'].NetworkAttachmentType_NAT, nic0attachmentType)

      nic1 = m.getNetworkAdapter(1)
      self.assertEquals(VirtualBox.getNamesToIdsMapping().get(machineName), \
          _toStdMACSyntax(nic1.MACAddress))

      nic1attachmentType = nic1.attachmentType
      self.assertEquals(VirtualBox._ctx['ifaces'].NetworkAttachmentType_HostOnly, nic1attachmentType)

      hd = m.getMediumAttachment('SCSI', 0,0).medium
      if machineName == 'image1':
        self.assertSubstring(self.IMAGE1_LOCATION, hd.location)
      elif machineName == 'image2':
        self.assertSubstring(self.IMAGE2_LOCATION, hd.location)

  def test_listAvailableVMs(self):
    def _checkResults(results):
      self.assertIn( 'image1', results) 
      self.assertIn( 'image2', results) 

    d = VirtualBox.listAvailableVMs()
    d.addCallback( _checkResults )
    return d


  def test_listRunningVMs_1(self): 
    @defer.inlineCallbacks
    def _checkNoneRunning():
      running = yield VirtualBox.listRunningVMs()
      self.assertEquals(0, len(running) )

    @defer.inlineCallbacks
    def _checkOneRunning(isRunning):
      self.assertTrue( isRunning )
      running = yield VirtualBox.listRunningVMs()
      self.assertEquals(1, len(running) )
      self.assertEquals('image1', running[0] ) 

      powerOffRes = yield VirtualBox.powerOff('image1')
      self.assertTrue(powerOffRes)
      _checkNoneRunning()

    dStart = VirtualBox.start('image1')
    dStart.addCallback( _checkOneRunning )

    return dStart

  def test_listRunningVMs_2(self):
    @defer.inlineCallbacks
    def _checkNoneRunning():
      running = yield VirtualBox.listRunningVMs()
      self.assertEquals(0, len(running) )
    
    @defer.inlineCallbacks
    def _checkBothRunning(areRunning):
      self.assertTrue( areRunning[0] )
      self.assertTrue( areRunning[1] )

      running = yield VirtualBox.listRunningVMs()
      self.assertEquals(2, len(running) )
      self.assertIn('image1', running ) 
      self.assertIn('image2', running ) 

      time.sleep(3)

      powerOffRes1 = yield VirtualBox.powerOff('image1')
      powerOffRes2 = yield VirtualBox.powerOff('image2')
      self.assertTrue(powerOffRes1)
      self.assertTrue(powerOffRes2)
      _checkNoneRunning()

    _checkNoneRunning()

    dBoth = defer.DeferredList( [VirtualBox.start(m) for m in ('image1', 'image2')] )
    dBoth.addCallback( _checkBothRunning )
    
    return dBoth


  def test_getState(self):
    @defer.inlineCallbacks
    def impl(startRes):
      self.assertTrue(startRes)

      state1 = yield VirtualBox.getState('image1')
      state2 = yield VirtualBox.getState('image2') 
      self.assertEquals('Running', state1 )
      self.assertEquals('PoweredOff', state2 )

      time.sleep(3)

      powerOffRes1 = yield VirtualBox.powerOff('image1')
      self.assertTrue(powerOffRes1)

    d = VirtualBox.start('image1')
    d.addCallback(impl)
    return d

  def test_pause(self):
    @defer.inlineCallbacks
    def impl(startRes):
      self.assertTrue(startRes)
 
      image1State = yield VirtualBox.getState('image1')
      self.assertEquals('Running', image1State)

      pauseRes = yield VirtualBox.pause('image1')
      self.assertTrue(pauseRes)

      image1State = yield VirtualBox.getState('image1')
      self.assertEquals('Paused', image1State)
  
      unpauseRes = yield VirtualBox.unpause('image1')
      self.assertTrue(unpauseRes)

      image1State = yield VirtualBox.getState('image1')
      self.assertEquals('Running', image1State)

      time.sleep(3)

      powerOffRes1 = yield VirtualBox.powerOff('image1')
      self.assertTrue(powerOffRes1)
   

    d = VirtualBox.start('image1')
    d.addCallback(impl)
    return d

  def test_listVMsWithState(self):
    @defer.inlineCallbacks
    def impl(namesAndStates):
      self.assertEquals('PoweredOff', namesAndStates.get('image1'))
      self.assertEquals('PoweredOff', namesAndStates.get('image2'))

      startRes = yield VirtualBox.start('image1')
      self.assertTrue(startRes)

      namesAndStates = yield VirtualBox.listVMsWithState()
      self.assertEquals('Running', namesAndStates.get('image1'))
      self.assertEquals('PoweredOff', namesAndStates.get('image2'))
      
      time.sleep(3)
 
      powerOffRes1 = yield VirtualBox.powerOff('image1')
      self.assertTrue(powerOffRes1)

    d = VirtualBox.listVMsWithState()
    d.addCallback(impl)
    return d


  def test_start(self):
    @defer.inlineCallbacks
    def impl(res):
      self.assertTrue(res)

      time.sleep(3)
      powerOffRes = yield VirtualBox.powerOff('image1')
      self.assertTrue(powerOffRes)

    d = VirtualBox.start('image1')
    d.addCallback(impl)
    return d



