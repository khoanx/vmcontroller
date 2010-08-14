from boincvm.common import support

from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.internet import reactor

import stomper
import logging

class StompProtocol(Protocol):
  
  #transport available at self.transport, as set by BaseProtocol.makeConnection
  #factory available at self.factory, as set by Factory.buildProtocol

  logger = logging.getLogger( support.discoverCaller() )

  def __init__(self, username, password, stompEngineCtor):
    self._username = username
    self._password = password

    self._stompEngine = stompEngineCtor(self)

  def connectionMade(self):
    """
    Called when a connection is made. 
    Protocol initialization happens here
    """
    self.logger.info("Connection with the broker made")
    stompConnectMsg = stomper.connect(self._username, self._password)
    self.sendStompMessage(stompConnectMsg)

  def connectionLost(self, reason):
    """Called when the connection is shut down"""
    self.logger.info("Connection with the broker lost")

  def dataReceived(self, data):
    """Called whenever data is received"""
    reaction = self._stompEngine.react(data)
    if reaction:
      self.sendStompMessage(reaction)
 
  def sendStompMessage(self, msg):
    self.transport.write(msg)


class StompProtocolFactory(ReconnectingClientFactory):
  """ Responsible for creating an instance of L{StompProtocol} """

  logger = logging.getLogger( support.discoverCaller() )

  def __init__(self, username, password, stompEngineCtor):

    #retry every 5 seconds, with no back-off
    self.delay = 5.0 
    self.factor = 1.0
    self.jitter = 0.0

    self.protocol = lambda: StompProtocol(username, password, stompEngineCtor)

  def buildProtocol(self, addr):
    p = ReconnectingClientFactory.buildProtocol(self, addr)

    def augmentedConnectionMade():
      p.originalConnMade()
      self.resetDelay()
    
    p.originalConnMade = p.connectionMade
    p.connectionMade = augmentedConnectionMade
    return p

  def clientConnectionLost(self, connector, reason):
    self.logger.info("Connection with the broker lost: %s" % reason)
    ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

  def clientConnectionFailed(self, connector, reason):
    self.logger.error("Connection with the broker failed: %s" % reason )
    ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)



