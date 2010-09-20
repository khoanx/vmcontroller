from boincvm.common import support

import logging
import inject

@inject.appscope
class MsgInterpreter(object):

  logger = logging.getLogger(support.discoverCaller())

  @inject.param('words')
  def __init__(self, words):
    """ 
    @param words a list of "words" (ie, commands represented as classes)
    
    """
    self._words = dict( ( (w.__name__, w) for w in words ) )

  def interpret(self, msg):
    #msg is an unpacked STOMP frame
    firstWord = msg['body'].split(None,1)[0] #only interested in the 1st word

    self.logger.debug("Trying to interpret %s" % (firstWord, ) )
    try:
      word = self._words[firstWord]()
    except KeyError:
      raise NameError("Word '%s' unknown" % firstWord)

    word.listenAndAct(msg)

