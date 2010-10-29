from boincvm.common import EntityDescriptor

from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet.protocol import Protocol

from StringIO import StringIO 
from ConfigParser import SafeConfigParser

import logging
import inject
import stomper


from boincvm.host import HostStompEngine
from boincvm.common import StompProtocolFactory, destinations

logging.basicConfig(level=logging.DEBUG, \
    format='%(message)s', )

import config
injector = config.configure()
injector.bind('stompEngine', to=HostStompEngine)

class TestHostStompEngine(unittest.TestCase):

  engine = inject.attr('stompEngine')

  def setUp(self): 
    self.stompProtocol = StompProtocolFactory().buildProtocol(('127.0.0.1',0))
    self.fakeTransport = proto_helpers.StringTransport()
    
  def tearDown(self):
    self.fakeTransport.clear()
    
  def test_connection(self):
    self.stompProtocol.makeConnection( self.fakeTransport )
    #ignore the connection request sent. We aren't testing that here
    self.fakeTransport.clear()

    #pretend we've received successful ack of our connection request.
    #check that the host engine subscribes to the topics upon connection
    connectedMsg = """CONNECTED
session:ID:snorky.local-49191-1185461799654-3:18"""
    self.stompProtocol.dataReceived(connectedMsg)

    msg1 = stomper.subscribe(destinations.CONN_DESTINATION)
    msg2 = stomper.subscribe(destinations.CMD_RES_DESTINATION)

    self.assertTrue( msg1 in self.fakeTransport.value() )
    self.assertTrue( msg2 in self.fakeTransport.value() )



