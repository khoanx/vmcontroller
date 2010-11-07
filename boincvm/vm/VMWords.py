from boincvm.common import support, Exceptions
from boincvm.common import BaseWord
from boincvm.common import destinations

import CommandExecuter
import sys
import inspect 
import fnmatch

def getWords():
  currentModule = sys.modules[__name__]
  return dict(inspect.getmembers(currentModule, inspect.isclass))

class PING(BaseWord):
  def listenAndAct(self, msg):
    if fnmatch.fnmatch(self.subject.descriptor.id, headers['to']): 
      self.subject.pong(self)

class PONG(BaseWord):
  def howToSay(self, pingMsg):
    headers = {}
    headers['destination'] = destination.CMD_RES_DESTINATION
    headers['ping-id'] = pingMsg['headers']['ping-id'] 
    self.frame.headers = headers

    return self.frame.pack()


class CMD_RUN(BaseWord):
  def listenAndAct(self, msg):
    headers = msg['headers']
    #TODO: sanity checks for the headers
    #if the VM's id matches the given 'to' destination,
    #either trivially or "pattern"-ly
    if fnmatch.fnmatch(self.subject.descriptor.id, headers['to']): 
      paramsList = ('cmd', 'args', 'env', 'path', 'fileForStdin')
      params = {}
      for p in paramsList:
        params[p] = headers.get(p)

      cmdId = headers.get('cmd-id')

      cmdExecuter = CommandExecuter.CommandExecuter(cmdId, params)
      cmdExecuter.executeCommand(
          ).addCallback( cmdExecuter.getExecutionResults
          ).addErrback( cmdExecuter.errorHandler 
          ).addCallback( self.subject.dealWithExecutionResults
          )

class CMD_RESULT(BaseWord):
  def howToSay(self, results):
    #results is a dict with keys = ('cmd-id', 'out', 'err', 'finished', 'exitCodeOrSignal', 'resources' )

    self.frame.headers['destination'] = destinations.CMD_RES_DESTINATION
    self.frame.headers['cmd-id'] = results['cmd-id']

    results = support.serialize(results)

    self.frame.body = ' '.join( (self.frame.body, results) )

    return self.frame.pack()


class HELLO(BaseWord):
  def howToSay(self):
    self.frame.headers = {'destination': destinations.CONN_DESTINATION, 
        'descriptor': self.subject.descriptor.serialize() }
    return self.frame.pack()


class BYE(BaseWord):
  def howToSay(self):
    self.frame.headers = {'destination': destinations.CONN_DESTINATION, 
      'descriptor': self.subject.descriptor.serialize() }
    return self.frame.pack()

#because ain't ain't a word!
class AINT(BaseWord):
  def listenAndAct(self, requester, msg):
    logger.warn("Unknown message type received. Data = '%s'" % str(msg))
 
