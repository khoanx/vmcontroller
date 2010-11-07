from boincvm.common import support, Exceptions, uuid, BaseWord, destinations, EntityDescriptor

import inspect
import sys

def getWords():
  currentModule = sys.modules[__name__]
  return dict(inspect.getmembers(currentModule, inspect.isclass))

class PING(BaseWord):
  def howToSay(self, dst):
    self.frame.headers['to'] = dst.id
    self.frame.headers['destination'] = CMD_REQ_DESTINATION
    self.frame.headers['ping-id'] = uuid.uuid1()

    return self.frame.pack()
  
class PONG(BaseWord):
  def listenAndAct(self, msg):
    self.subject.processPong(msg)


class CMD_RUN(BaseWord):
  def howToSay(self, to, cmdId, cmd, args=(), env={}, path=None, fileForStdin=''):

    headers = {}

    headers['destination'] = destinations.CMD_REQ_DESTINATION
    headers['to'] = to
    headers['cmd-id'] = cmdId

    #FIXME: this should go into the msg's body, serialized
    headers['cmd'] = cmd
    headers['args'] = args
    headers['env'] = env
    headers['path'] = path
    headers['fileForStdin'] = fileForStdin

    self.frame.headers = headers

    return self.frame.pack()

class CMD_RESULT(BaseWord):
  def listenAndAct(self, resultsMsg):
    #we receive the command execution results,
    #as sent by one of the vms (in serialized form)
    self.subject.processCmdResult(resultsMsg)


class HELLO(BaseWord):
  def listenAndAct(self, msg):
    headers = msg['headers']
    vmDescriptor = EntityDescriptor.deserialize(headers['descriptor'])
    self.subject.addVM(vmDescriptor)


class BYE(BaseWord):
  def listenAndAct(self, msg):
    headers = msg['headers']
    who = headers['id']
    self.subject.removeVM(who)

#because ain't ain't a word!
class AINT(BaseWord):
  def listenAndAct(self, requester, msg):
    logger.warn("Unknown message type received. Data = '%s'" % str(msg))
 
