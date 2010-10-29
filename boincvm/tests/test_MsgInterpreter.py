from boincvm.common.BaseStompEngine import MsgInterpreter
from boincvm.common import EntityDescriptor, BaseWord

from twisted.trial import unittest

import inject
import stomper
import logging
import pdb

logging.basicConfig(level=logging.INFO, \
    format='%(message)s', )

import config
config.configure()

class TestMsgInterpreter(unittest.TestCase):

  words = inject.attr('words')
  subject = inject.attr('subject')

  def setUp(self):
    self.msgInterpreter = MsgInterpreter()


  def test_interpret(self):
    # def interpret(self, msg):
    #will invoke .listenAndAct on the value of the "received" word
    msg = self.words['AWord']().howToSay()
    self.assertFalse( self.subject.stuffDone )
    self.msgInterpreter.interpret( stomper.unpack_frame(msg) )
    self.assertTrue( self.subject.stuffDone )

  def test_interpretFails(self):
    msg = config.UnknownWord().howToSay()
    self.assertRaises(NameError, \
        lambda: self.msgInterpreter.interpret( stomper.unpack_frame(msg) ) )


