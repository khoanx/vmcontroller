from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet.protocol import Protocol

import logging
import inject
import stomper


from boincvm.host import HostStompEngine
from boincvm.common import StompProtocolFactory, StompProtocol, destinations
from boincvm.common.StompProtocol import MsgSender

logging.basicConfig(level=logging.DEBUG, \
    format='%(message)s', )

injector = inject.Injector()
inject.register(injector)

injector.bind('words', to=())


class FakeStompProtocol(Protocol):
  
  msgSender = inject.attr('msgSender', MsgSender)
  
  def __init__(self):
    self.data = None

  def dataReceived(self, data):
    self.data = data

  def connectionMade(self):
    self.msgSender.senderFunc = self.transport.write
 
class TestHostStompEngine(unittest.TestCase):

  def setUp(self): 
    self.fakeProtocol = FakeStompProtocol()
    self.fakeTransport = proto_helpers.StringTransport()
    
    self.fakeProtocol.makeConnection( self.fakeTransport )
    
    self.engine = HostStompEngine(self.fakeProtocol)



  def test_connection(self):
    #check that the engine subscribes to the topics upon connection
    self.engine.connected(None)

    msg1 = stomper.subscribe(destinations.CONN_DESTINATION)
    msg2 = stomper.subscribe(destinations.CMD_RES_DESTINATION)

    self.assertTrue( msg1 in self.fakeTransport.value() )
    self.assertTrue( msg2 in self.fakeTransport.value() )





