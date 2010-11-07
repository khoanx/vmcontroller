from boincvm.common import support, Exceptions

from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.internet import reactor

import stomper
import inject
import logging
import pdb 


#@inject.appscope
class StompProtocol(Protocol):
  
  #transport available at self.transport, as set by BaseProtocol.makeConnection
  #factory available at self.factory, as set by Factory.buildProtocol

  logger = logging.getLogger( support.discoverCaller() )

  stompEngine = inject.attr('stompEngine')
  config = inject.attr('config')

  def __init__(self):
    self._username = self.config.get('Broker', 'username')
    self._password = self.config.get('Broker', 'password')

  def sendMsg(self, msg):
    self.logger.debug("Sending msg '%s'" % msg)
    self.transport.write(msg)

  def connectionMade(self):
    """
    Called when a connection is made. 
    Protocol initialization happens here
    """
    self.logger.info("Connection with the broker made")
    stompConnectMsg = stomper.connect(self._username, self._password)
    self.sendMsg(stompConnectMsg)

    try:
      self.factory.resetDelay()
    except:
      pass

  def connectionLost(self, reason):
    """Called when the connection is shut down"""
    self.logger.info("Connection with the broker lost")

  def dataReceived(self, data):
    """Called whenever data is received"""
    reactions = self.stompEngine.react(data)
    if reactions:
      for reaction in filter(None,reactions):
        self.sendMsg(reaction)
 

class StompProtocolFactory(ReconnectingClientFactory):
  """ Responsible for creating an instance of L{StompProtocol} """

  logger = logging.getLogger( support.discoverCaller() )

  __stompProtocol = inject.attr('stompProtocol')
  initialDelay = delay = 5.0
  factor = 1.0
  jitter = 0.0

  def __init__(self):
    #retry every 5 seconds, with no back-off
    self.protocol = lambda: self.__stompProtocol #sigh... self.protocol must be callable

  def clientConnectionLost(self, connector, reason):
    self.logger.info("Connection with the broker lost: %s" % reason)
    ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

  def clientConnectionFailed(self, connector, reason):
    self.logger.error("Connection with the broker failed: %s" % reason )
    ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)



