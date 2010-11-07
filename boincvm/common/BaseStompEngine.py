from boincvm.common import support

import stomper
import logging
import inject



#@inject.appscope
class MsgInterpreter(object):

  logger = logging.getLogger(support.discoverCaller())

  @inject.param('words')
  def __init__(self, words):
    """ 
    @param words a list of "words" (ie, commands represented as classes)
    
    """
    self._words = words

  def interpret(self, msg):
    #msg is an unpacked STOMP frame
    firstWord = msg['body'].split(None,1)[0] #only interested in the 1st word

    self.logger.debug("Trying to interpret %s" % (firstWord, ) )
    try:
      word = self._words[firstWord]()
    except KeyError:
      raise NameError("Word '%s' unknown" % firstWord)

    word.listenAndAct(msg)


class BaseStompEngine(stomper.Engine):
  """
  G{classtree BaseStompEngine}
  """
  
  logger = logging.getLogger(support.discoverCaller())

  @inject.param('msgInterpreter', MsgInterpreter, scope=inject.appscope)
  def __init__(self, msgInterpreter):
    super( BaseStompEngine, self ).__init__()
    self._msgInterpreter = msgInterpreter

  def ack(self, msg):
    """Called when a MESSAGE message is received"""
    #msg is an unpacked frame
    self._msgInterpreter.interpret(msg)
    return stomper.NO_REPONSE_NEEDED

  def react(self, msg):
    """ Returns an iterable of responses """
    rxdFrame = stomper.unpack_frame(msg)
    cmd = rxdFrame['cmd']

    self.logger.info("Received a %s message." % cmd)
    self.logger.debug("Headers: %s ; Body: %s" % (rxdFrame['headers'], rxdFrame['body']))
    try:
      res = list(stomper.Engine.react(self, msg))
    except Exception, e:
      self.logger.error(str(e))
      res = stomper.NO_REPONSE_NEEDED
    return res

