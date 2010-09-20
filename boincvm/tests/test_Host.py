from twisted.trial import unittest

import sys
from StringIO import StringIO 
from ConfigParser import SafeConfigParser
import logging
import inject

from boincvm.host import Host, HyperVisorController
from boincvm.common import EntityDescriptor, Exceptions

logging.basicConfig(level=logging.DEBUG, \
    format='%(message)s', )

def getConfig():
  cfg = \
"""
[Hypervisor]
hypervisor=VirtualBox
hypervisor_helpers_path=
"""
  configFile = StringIO(cfg)
  config = SafeConfigParser()
  config.readfp(configFile)
  configFile.close()

  return config

injector = inject.Injector()
inject.register(injector)

injector.bind('config', to=getConfig)
injector.bind('hvController', to=HyperVisorController)

class TestVMRegistry(unittest.TestCase):

  def setUp(self):
    self.vmRegistry = Host.VMRegistry()

    self.names = ("testVM1", "testVM2")
    self.ids = ("DE:AD:BE:EF:00:01", "DE:AD:BE:EF:00:02")
    self.extras = ({"extraData": "extra extra!"}, {"extraData": "extra extra! (bis)"})
    
    self.descriptors = map( lambda i, d: EntityDescriptor(i,**d), self.ids, self.extras)
 
    for d in self.descriptors:
      self.vmRegistry.addVM( d )
   
  def test_addVM(self):
    nonExistantVM = EntityDescriptor("00:00:00:00:00:00") 
    self.assertRaises(Exceptions.NoSuchVirtualMachine, self.vmRegistry.addVM, nonExistantVM) 

  def test_removeVM(self):
    self.assertTrue( self.vmRegistry.isValid( self.ids[0] ) )
    self.vmRegistry.removeVM( self.ids[0] )
    self.assertFalse( self.vmRegistry.isValid( self.ids[0] ) )

  def test_isValid(self):
    for id in self.ids:
      self.assertTrue( self.vmRegistry.isValid( id ) ) 

    self.assertFalse( self.vmRegistry.isValid('wrongId') ) 

  def test_getitem(self): 
    for (name, id) in zip(self.names, self.ids):
      self.assertIsInstance( self.vmRegistry[id], EntityDescriptor )
      self.assertEquals( id, self.vmRegistry[id].id )
      self.assertEquals( name, self.vmRegistry[id].name )

  def test_getRegisteredVMs(self):
    regdVMs = self.vmRegistry.getRegisteredVMs()
    for id in self.ids:
      self.assertIn(id, regdVMs) 

class TestCommandRegistry(unittest.TestCase):

  def setUp(self):
    pass
    



