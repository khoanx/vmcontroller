from boincvm.common import BaseStompEngine 
from boincvm.common import support, Exceptions 
from boincvm.common import destinations

#from twisted.internet import utils, defer, reactor
#from twisted.internet.task import LoopingCall
#from twisted.web import resource

import stomper
import logging
import time
import inject

@inject.appscope
class HostStompEngine(BaseStompEngine):
  
  logger = logging.getLogger(support.discoverCaller())

  #@inject.param('host', Host)
  def __init__(self, host):
    super( HostStompEngine, self ).__init__()


  def connected(self, msg):
    #once connected, subscribe
    self.msgSender.sendMsg( stomper.subscribe(destinations.CONN_DESTINATION)) 
    self.msgSender.sendMsg( stomper.subscribe(destinations.CMD_RES_DESTINATION))


