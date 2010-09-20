from boincvm.common import support

import logging
import time 
import stomper 
import inject
import pdb

logger = logging.getLogger( support.discoverCaller() )

class BaseWord(object):
  """ Initializes the Frame object with the inheriting class' name """
  @inject.param('subject')
  def __init__(self, subject ):
    self.subject = subject

    self.frame = stomper.Frame()
    self.frame.body = self.name

    headers = {}
    headers['from'] = subject.descriptor.id
    headers['timestamp'] = str(time.time())
    self.frame.headers = headers

  @property
  def name(self):
    """ Get the word's name """
    return self.__class__.__name__

  
