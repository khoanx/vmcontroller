from twisted.trial import unittest
from twisted.test import proto_helpers

import sys
from StringIO import StringIO 
from ConfigParser import SafeConfigParser
import logging
import inject
import stomper
import uuid

from boincvm.host import Host, HostWords
from boincvm.common import EntityDescriptor, Exceptions, destinations

logging.basicConfig(level=logging.DEBUG, \
    format='%(message)s', )

import config
injector = config.configure()
injector.bind('words', to=HostWords.getWords )

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
  def test_getNameForId(self):
    for i in xrange(len(self.ids)):
      name = self.vmRegistry.getNameForId( self.ids[i] )
      self.assertEquals( self.names[i], name )

  def test_getIdForName(self):
    for i in xrange(len(self.names)):
      id_ = self.vmRegistry.getIdForName( self.names[i] )
      self.assertEquals( self.ids[i], id_)

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


class TestHost(unittest.TestCase):
  def setUp(self):
    self.host = Host.Host()

  def test_requestCommandExecution(self):
    pass


class TestCommandRegistry(unittest.TestCase):

  stompProtocol = inject.attr('stompProtocol')

  def setUp(self):
    self.cmdRegistry = Host.CommandRegistry()

    self.names = ("testVM1", "testVM2")
    self.ids = ("DE:AD:BE:EF:00:01", "DE:AD:BE:EF:00:02")
    
    self.descriptors = map( lambda i: EntityDescriptor(i), self.ids)
 
    for d in self.descriptors:
      self.cmdRegistry.vmRegistry.addVM( d )

    self.fakeTransport = proto_helpers.StringTransport()

  def tearDown(self):
    self.fakeTransport.clear()

  def test_sendCmdRequest(self):
    self.stompProtocol.makeConnection( self.fakeTransport )
    self.fakeTransport.clear() #discard connection frames

    for vmName, vmId in zip(self.names, self.ids):
      self.cmdRegistry.sendCmdRequest(vmName, 'fooCmd')
      
      rxdFrame = stomper.unpack_frame( self.fakeTransport.value() )

      self.assertEquals('SEND', rxdFrame['cmd'])
      self.assertEquals('CMD_RUN', rxdFrame['body'])

      headers = rxdFrame['headers']

      self.assertEquals('fooCmd', headers['cmd'])

      rxdCmdId = uuid.UUID( headers['cmd-id'] )
      self.assertTrue( isinstance(rxdCmdId, uuid.UUID ) )

      self.assertEquals( headers['destination'], destinations.CMD_REQ_DESTINATION )

      self.assertEquals( headers['to'], vmId )
      self.fakeTransport.clear() #discard connection frames


      ###########

      self.assertIn(headers['cmd-id'], self.cmdRegistry._cmdReqsSent)

#  def test_processCmdResult(self): 

    #depends on the implementation of VMWords

#    self.cmdRegistry.sendCmdRequest(self.names[0], 'fooCmd')
#    rxdFrame = stomper.unpack_frame(self.cmdRegistry.msgSender.data)
#    cmdId = rxdFrame['headers']['cmd-id']
#    self.assertIn(cmdId, self.cmdRegistry._cmdReqsSent)
#    reqSent = self.cmdRegistry._cmdReqsSent[cmdId]
#
#    self.cmdRegistry.processCmdResult(rxdFrame)
#
#    self.assertIn(cmdId, self._cmdReqsRcvd)
#    self.assertEquals(reqSent, self._cmdReqsRcvd[cmdId])
#    self.assertEquals(reqSent, self._cmdReqsRetired[cmdId])


