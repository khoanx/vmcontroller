from boincvm_common.stomp.protocol import destinations, BaseWord
from boincvm_common import support, EntityDescriptor

import logging
import stomper 

logger = logging.getLogger('words')

class PING(BaseWord):
  def howToSay(self, to, timestamp):
    self._frame.cmd = 'SEND'
    headers = {}
    headers['destination'] = destinations.CMD_REQ_DESTINATION
    headers['to'] = to
    headers['timestamp'] = timestamp
    self._frame.headers = headers
    return self._frame.pack()
  
  def listenAndAct(self, msg):
    self._requester.pong(msg)

class PONG(BaseWord):
  def howToSay(self, pingMsg):
    self._frame.cmd = 'SEND'
    headers = {}
    headers['destination'] = destinations.CMD_RES_DESTINATION
    headers['from'] = self._requester.id
    headers['timestamp'] = pingMsg['headers']['timestamp'] 
    self._frame.headers = headers

    return self._frame.pack()

  def listenAndAct(self, msg):
    self._requester.processPong(msg)


###############################################


class CMD_RUN(BaseWord):
  def howToSay(self, to, cmdId, cmd, args=(), env={}, path=None, fileForStdin=''):
    self._frame.cmd = 'SEND'
    headers = {}

    headers['destination'] = destinations.CMD_REQ_DESTINATION
    headers['to'] = to #vm's id
    headers['cmd-id'] = cmdId

    #FIXME: this should go into the msg's body, serialized
    headers['cmd'] = cmd
    headers['args'] = args
    headers['env'] = env
    headers['path'] = path

    headers['fileForStdin'] = fileForStdin

    self._frame.headers = headers

    return self._frame.pack()

  def listenAndAct(self, msg):
    #host doesn't execute commands
    pass

class CMD_RESULT(BaseWord):
  def howToSay(self, results):
	  #host doesn't execute commands
    pass

  def listenAndAct(self, resultsMsg):
    #we receive the command execution results,
    #as sent by one of the vms (in serialized form)
    self._requester.processCmdResult(resultsMsg)

###########################################################



class HELLO(BaseWord):
  def howToSay(self):
    hostDescr = self._requester.descriptor.serialize()

    self._frame.cmd = 'SEND'
    self._frame.headers = {'destination': destinations.CONN_DESTINATION, 'entity': entityDescr}

    #XXX: the entity description goes in the body!

    return self._frame.pack()

  def listenAndAct(self, msg):
    headers = msg['headers']
    vmDescr = EntityDescriptor.load(headers['entity']) 
    host.addVM(vmDescr)


class BYE(BaseWord):
  def howToSay(self, vm):
    self._frame.cmd = 'SEND'
    self._frame.headers = {'destination': destinations.CONN_DESTINATION, 'id': vm.id, 'ip': vm.ip}
    #XXX: the entity description goes in the body!
    return self._frame.pack()

  def listenAndAct(self, host, msg):
    headers = msg['headers']
    who = headers['id']
    host.removeVM(who)

class STILL_ALIVE(BaseWord):
  def howToSay(self, vm):
    #host doesn't say this word
    pass

  def listenAndAct(self, host, msg):
    headers = msg['headers']
    vmId = headers['id']
    vmIp = headers['ip']
    host.keepVMForNow(vmId, vmIp)
    #XXX: we only need the id


###########################################

#because ain't ain't a word!
class AINT(BaseWord):
  def listenAndAct(self, requester, msg):
    logger.warn("Unknown message type received. Data = '%s'" % str(msg))
    

