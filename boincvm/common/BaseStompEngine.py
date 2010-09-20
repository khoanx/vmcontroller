from boincvm.common import support
from boincvm.common import MsgInterpreter

import stomper
import logging
import inject

@inject.appscope
class BaseStompEngine(stomper.Engine):
  """
  G{classtree BaseStompEngine}
  """
  
  logger = logging.getLogger(support.discoverCaller())

  @inject.param('msgInterpreter', MsgInterpreter)
  def __init__(self, stompProtocol, msgInterpreter):
    super( BaseStompEngine, self ).__init__()
    self.stompProtocol = stompProtocol
    self._msgInterpreter = msgInterpreter

  def ack(self, msg):
    """Called when a MESSAGE message is received"""
    #msg is an unpacked frame
    headers = msg['headers']
  
    self._msgInterpreter.interpret(msg)

    if headers.get('ack') == 'client':
      res = stomper.Engine.ack(self, msg)
    else:
      res = stomper.NO_REPONSE_NEEDED

    return res

  def react(self, msg):
    """ Returns an iterable of responses """
    rxdFrame = stomper.unpack_frame(msg)
    cmd = rxdFrame['cmd']

    self.logger.info("Received a %s message." % cmd)
    self.logger.debug("Headers: %s ; Body: %s" % (rxdFrame['headers'], rxdFrame['body']))
    return stomper.Engine.react(self, msg)

