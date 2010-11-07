#!/bin/env python

from boincvm.common import support, Exceptions
from boincvm.common import StompProtocolFactory, StompProtocol

from boincvm.vm import VMStompEngine, VMWords

from twisted.internet import reactor, protocol
from twisted.application import internet, service

from ConfigParser import SafeConfigParser
import os
import tempfile
import logging
import inject

logging.basicConfig(level=logging.DEBUG, \
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', 
    )

def start(config):
  """Start twisted event loop and the fun should begin..."""
  host = config.get('Broker', 'host') 
  port = int(config.get('Broker', 'port'))
  username = config.get('Broker', 'username')
  password = config.get('Broker', 'password')

  
  stompProtocolFactory = StompProtocolFactory()
  
  #spawnChirpServerProcess(config)

  #reactor.connectTCP(host, port, stompProtocolFactory)
  #reactor.run()
  return internet.TCPClient(host, port, stompProtocolFactory)



class ChirpServerProcessProtocol(protocol.ProcessProtocol):

  logger = logging.getLogger( support.discoverCaller() )

  def __init__(self, aclFileName):
    self._aclFileName = aclFileName

  def connectionMade(self):
    self.transport.closeStdin()
    self.logger.debug("Process started!")

  def outReceived(self, data):
    self.logger.debug("Chirp Server stdout: %s" % data)
  def errReceived(self, data):
    self.logger.debug("Chirp Server stderr: %s" % data)

  def inConnectionLost(self):
    pass #we don't care about stdin. We do in fact close it ourselves

  def outConnectionLost(self):
    self.logger.info("Chirp Server closed its stdout")
  def errConnectionLost(self):
    self.logger.info("Chirp Server closed its stderr")

  def processExited(self, reason):
    #This is called when the child process has been reaped 
    os.remove(self._aclFileName)
  def processEnded(self, reason):
    #This is called when all the file descriptors associated with the child
    #process have been closed and the process has been reaped
    self.logger.warn("Process ended (code: %s) " % reason.value.exitCode)


def createChirpACLFile(dirToServe):
  f = file( os.path.join(dirToServe, '.__acl'), 'w' )
  f.write('address:* rwl\n')
  f.close()
  return f.name

def spawnChirpServerProcess(config):
  """ Launches the webservices server.

      The server's path is given by the configuration 
      directive 'hypervisor_helpers_path' under the 'Host' section
    
      The callback method 'controllerInitializer' will be called
      once the server has been started. 
      
  """
  dirToServe = os.path.expanduser(config.get('VM', 'dir_to_serve'))
  aclFileName = createChirpACLFile(dirToServe)
  csCmd = 'chirp_server -E -U5s -u - -r %s' % (dirToServe, )
  cmdWithArgs = csCmd.split()
  cmd = cmdWithArgs[0]
  cmdWithPath = cmd
  processProtocol = ChirpServerProcessProtocol(aclFileName)
  newProc = lambda: reactor.spawnProcess( processProtocol, cmdWithPath, args=cmdWithArgs, env=None )
  reactor.callWhenRunning(newProc) 

#if __name__ == '__main__':
#  from sys import argv
#  if len(argv) < 2:
#    print "Usage: %s <config-file>" % argv[0]
#    exit(-1)
#  else:
#    configFile = argv[1]
#
#    config = SafeConfigParser()
#    config.read(configFile)

application = service.Application("boinc-vm-controller")



configFile = '/etc/boinc-vm-controller/VMConfig.cfg' #FIXME: HARDCODED
if not os.path.isfile(configFile):
  configFile = os.path.basename(configFile) 

config = SafeConfigParser()
config.read(configFile)

injector = inject.Injector()
inject.register(injector)

injector.bind('config', to=config )
injector.bind('words', to=VMWords.getWords, scope=inject.appscope)
injector.bind('stompProtocol', to=StompProtocol, scope=inject.appscope) 
injector.bind('stompEngine', to=VMStompEngine, scope=inject.appscope) 
injector.bind('subject', to=VMStompEngine, scope=inject.appscope) 


service = start(config)
service.setServiceParent(application)

