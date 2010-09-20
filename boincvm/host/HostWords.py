from boincvm.common import support, Exceptions, uuid
from boincvm.common import BaseWord

class PING(BaseWord):
  def howToSay(self, dst):
    self._frame.headers['to'] = dst.id
    self._frame.headers['destination'] = CMD_REQ_DESTINATION
    self._frame.headers['ping-id'] = uuid.uuid1()

    return self._frame.pack()
  
class PONG(BaseWord):
  def listenAndAct(self, msg):
    self.subject.processPong(msg)


class CMD_RUN(BaseWord):
  def howToSay(self, host, to, cmdId, cmd, args=(), env={}, path=None, fileForStdin=''):
    headers = {}

    headers['destination'] = CMD_REQ_DESTINATION
    headers['to'] = to
    headers['cmd-id'] = cmdId

    #FIXME: this should go into the msg's body, serialized
    headers['cmd'] = cmd
    headers['args'] = args
    headers['env'] = env
    headers['path'] = path
    headers['fileForStdin'] = fileForStdin

    self._frame.headers = headers

    return self._frame.pack()

class CMD_RESULT(BaseWord):
  def listenAndAct(self, host, resultsMsg):
    #we receive the command execution results,
    #as sent by one of the vms (in serialized form)
    host.processCmdResult(resultsMsg)


class HELLO(BaseWord):
  def howToSay(self, vm):
    self._frame.headers = {'destination': CONN_DESTINATION, 'id': vm.id, 'ip': vm.ip}
    return self._frame.pack()

  def listenAndAct(self, host, msg):
    headers = msg['headers']
    vmId = headers['id']
    vmIp = headers['ip']
    host.addVM(vmId, vmIp)


class BYE(BaseWord):
  def listenAndAct(self, host, msg):
    headers = msg['headers']
    who = headers['id']
    host.removeVM(who)

class STILL_ALIVE(BaseWord):
  def listenAndAct(self, host, msg):
    headers = msg['headers']
    vmId = headers['id']
    vmIp = headers['ip']
    host.keepVMForNow(vmId, vmIp)


#because ain't ain't a word!
class AINT(BaseWord):
  def listenAndAct(self, requester, msg):
    logger.warn("Unknown message type received. Data = '%s'" % str(msg))
 
