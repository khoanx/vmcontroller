from boincvm.common.BaseStompEngine import MsgInterpreter
from boincvm.common import EntityDescriptor, BaseWord

from twisted.trial import unittest

import inject
import stomper
import logging
import pdb

logging.basicConfig(level=logging.INFO, \
    format='%(message)s', )

class FakeSubject(object):
  #it only contains a fake descriptor
  def __init__(self, anId):
    self.descriptor = EntityDescriptor(anId)
    self.stuffDone = False

  def doStuff(self):
    self.stuffDone = True

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

injector = inject.Injector()
inject.register( injector )

subject = FakeSubject('FakeSubject')
injector.bind( 'subject', to=subject) #injected into BaseWord. It's either Host or VM in practice

words = dict( (('AWord', AWord),) )
injector.bind( 'words', to=words ) #gets injected into MsgInterpreter


class TestMsgInterpreter(unittest.TestCase):

  def setUp(self):
    self.msgInterpreter = MsgInterpreter()


  def test_interpret(self):
    # def interpret(self, msg):
    #will invoke .listenAndAct on the value of the "received" word
    msg = AWord().howToSay()
    self.assertFalse( subject.stuffDone )
    self.msgInterpreter.interpret( stomper.unpack_frame(msg) )
    self.assertTrue( subject.stuffDone )

  def test_interpretFails(self):
    msg = UnknownWord().howToSay()
    self.assertRaises(NameError, \
        lambda: self.msgInterpreter.interpret( stomper.unpack_frame(msg) ) )


