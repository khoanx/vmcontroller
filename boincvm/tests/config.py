from boincvm.common import StompProtocolFactory, StompProtocol, EntityDescriptor, BaseWord
from boincvm.host import HyperVisorController

from StringIO import StringIO 
from ConfigParser import SafeConfigParser

import inject

class FakeEngine(object):
  def react(self, data):
    if data == "do something!":
      return "aye aye sir"
    else:
      return None

class FakeSubject(object):
  #it only contains a fake descriptor
  def __init__(self, anId):
    self.descriptor = EntityDescriptor(anId)
    self.stuffDone = False

  def doStuff(self):
    self.stuffDone = True

USER = 'user'
PASS = 'pass'
def getConfig():
  cfg = \
"""
[Broker]
username=%s
password=%s

[Hypervisor]
hypervisor=VirtualBox
hypervisor_helpers_path=
""" % (USER, PASS)
  configFile = StringIO(cfg)
  config = SafeConfigParser()
  config.readfp(configFile)
  configFile.close()

  return config


class AWord(BaseWord.BaseWord):
  def howToSay(self):
    return self.frame.pack()

  def listenAndAct(self, msg):
    frm = msg['headers']['from']
    print "Acting upon subject '%s' to a request coming from '%s'" % \
        (self.subject.descriptor, frm)
    self.subject.doStuff()

class UnknownWord(BaseWord.BaseWord):
  def howToSay(self):
    return self.frame.pack()

def configure():
  injector = inject.Injector()
  inject.register(injector)

  injector.bind('config', to=getConfig)
  injector.bind('stompEngine', to=FakeEngine) 
  injector.bind('stompProtocol', to=StompProtocol) 
  injector.bind('subject', to=FakeSubject('FakeSubject')) #injected into BaseWord. It's either Host or VM in practice
  injector.bind('words', to=dict( (('AWord', AWord),) ) ) #gets injected into MsgInterpreter
  injector.bind('hvController', to=HyperVisorController)

  return injector
