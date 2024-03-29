from __future__ import print_function
from boincvm.common import StompProtocolFactory, StompProtocol

from StringIO import StringIO 
from ConfigParser import SafeConfigParser

from twisted.test import proto_helpers
from twisted.trial import unittest
from twisted.internet import task, error

import stomper
import inject
import logging

logging.basicConfig(level=logging.DEBUG, format='%(message)s', )

import config
config.configure()

class TestStompProtocolFactory(unittest.TestCase):
  class _MyFakeConnector( proto_helpers._FakeConnector ):
    connectionAttempts = 0
    def connect(self):
      self.connectionAttempts += 1

  #God bless Python!
  proto_helpers._FakeConnector = _MyFakeConnector

  def setUp(self):
    self.factory = StompProtocolFactory()

  def _fakeConnect(self_):
    self_.connectionAttempts += 1

  def test_reconnection(self):
    clock = task.Clock()
    self.factory.clock = clock
    self.factory.maxRetries = 3

    fakeReactor = proto_helpers.MemoryReactor()
    self.assertEquals(0, len(fakeReactor.tcpClients))
    connector = fakeReactor.connectTCP('fakehost', 1234, self.factory)
    self.assertEquals(1, len(fakeReactor.tcpClients))

    for i in xrange( self.factory.maxRetries ):
      self.factory.clientConnectionFailed(connector, "Attempt %d" % i)
      self.assertEquals(1, len(clock.getDelayedCalls()))

      clock.advance( self.factory.delay )
      self.assertEquals(0, len(clock.getDelayedCalls()))
      self.assertEquals(i+1, connector.connectionAttempts)

    self.factory.clientConnectionFailed(connector, "Attempt %d" % i)
    self.assertEquals(0, len(clock.getDelayedCalls()))

    clock.advance( self.factory.delay )
    self.assertEquals(self.factory.retries-1, connector.connectionAttempts)


class TestStompProtocol(unittest.TestCase):

  def setUp(self):
    factory = StompProtocolFactory()

    self.protocol = factory.buildProtocol(('127.0.0.1',0)) #addr isn't used anyway: we are faking it
    self.fakeTransport = proto_helpers.StringTransport()

  def tearDown(self):
    self.fakeTransport.clear()

  def test_connectionMade(self):
    self.protocol.makeConnection( self.fakeTransport )
    #the protocol must have sent the request for login to 
    #the STOMP broker

    dataInTheWire = self.fakeTransport.value()
    expected = stomper.connect(config.USER, config.PASS)

    self.assertEquals(expected, dataInTheWire)

  def test_dataReceived(self):
    self.protocol.makeConnection( self.fakeTransport )
    self.fakeTransport.clear()

    fakeReceivedData = "do something!"
    self.protocol.dataReceived(fakeReceivedData)
    dataInTheWire = self.fakeTransport.value()
    expected = "aye aye sir"
    self.assertEquals( dataInTheWire, expected )

    self.fakeTransport.clear()
    self.protocol.dataReceived("foobar") #no reaction expected
    dataInTheWire = self.fakeTransport.value()
    expected = ''
    self.assertEquals( dataInTheWire, expected )

  def test_sendMsg(self):
    self.protocol.makeConnection( self.fakeTransport )
    self.fakeTransport.clear()
    self.protocol.sendMsg( 'foobar' )

    dataInTheWire = self.fakeTransport.value()
    expected = 'foobar'

    self.assertEquals(expected, dataInTheWire)


