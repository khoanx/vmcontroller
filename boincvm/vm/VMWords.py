from boincvm.common import support, Exceptions
from boincvm.common import BaseWord

import CommandExecuter

class PING(BaseWord):
  def listenAndAct(self, msg):
    if fnmatch.fnmatch(self.src.descriptor.id, headers['to']): 
      self._vm.pong(self)

class PONG(BaseWord):
  def howToSay(self, vm, pingMsg):
    headers = {}
    headers['destination'] = CMD_RES_DESTINATION
    headers['ping-id'] = pingMsg['headers']['ping-id'] 
    self._frame.headers = headers

    return self._frame.pack()


class CMD_RUN(BaseWord):
  def listenAndAct(self, vm, msg):
    headers = msg['headers']
    #TODO: sanity checks for the headers
    #if the VM's id matches the given 'to' destination,
    #either trivially or "pattern"-ly
    if fnmatch.fnmatch(vm.id, headers['to']): 
      paramsList = ('cmd', 'args', 'env', 'path', 'fileForStdin')
      params = {}
      for p in paramsList:
        params[p] = headers.get(p)

      cmdId = headers.get('cmd-id')

      cmdExecuter = CommandExecuter.CommandExecuter(cmdId, params)
      cmdExecuter.executeCommand(
          ).addCallback( cmdExecuter.getExecutionResults
          ).addErrback( cmdExecuter.errorHandler 
          ).addCallback( vm.dealWithExecutionResults
          )

class CMD_RESULT(BaseWord):
  def howToSay(self, vm, results):
    #results is a dict with keys = ('cmd-id', 'out', 'err', 'finished', 'exitCodeOrSignal', 'resources' )

    self._frame.headers['destination'] = CMD_RES_DESTINATION
    self._frame.headers['cmd-id'] = results['cmd-id']

    results = support.serialize(results)

    self._frame.body = ' '.join( (self._frame.body, results) )

    return self._frame.pack()


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
  def howToSay(self, vm):
    self._frame.headers = {'destination': CONN_DESTINATION, 'id': vm.id, 'ip': vm.ip}
    return self._frame.pack()

class STILL_ALIVE(BaseWord):
  def howToSay(self, vm):
    self._frame.headers = {'destination': CONN_DESTINATION, 'id': vm.id, 'ip': vm.ip }
    return self._frame.pack()


#because ain't ain't a word!
class AINT(BaseWord):
  def listenAndAct(self, requester, msg):
    logger.warn("Unknown message type received. Data = '%s'" % str(msg))
 
