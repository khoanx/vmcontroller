#!/bin/env python

from boincvm.common import StompProtocolFactory, StompProtocol
from boincvm.host import HostStompEngine, HostXMLRPCService, HostWords, Host, HyperVisorController

from twisted.internet import reactor
import coilmq.start

import logging
import multiprocessing
import time 
import inject
from ConfigParser import SafeConfigParser
import pdb

logging.basicConfig(level=logging.DEBUG, \
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', )

logger = logging.getLogger(__name__)

def startSTOMPBroker(config, serverUpEvent, tries=-1, delay=1, backoff=1.5):
  """

  @param tries number of times to retry starting the broker. < 0 means infinitely many.
  @param delay number of seconds to wait after the first failed attempt
  @param backoff factor by which the delay will be incremented after a failure.
  """
  #stomp broker
  mtries = tries
  mdelay = delay
  coilserver = None
  from coilmq.config import config as coilconfig
  if config.has_section('coilmq'):
    for k,v in config.items('coilmq'):
      coilconfig.set('coilmq', k, v)
      logger.debug("Set %s to %s for coilmq config." % (k,v))
  while True:
    try:
      coilserver = coilmq.start.server_from_config(coilconfig)
      logger.info("Stomp server listening on %s:%s" % \
          coilserver.server_address)
      serverUpEvent.set()
      coilserver.serve_forever()
    except IOError as ex:
      logger.error("Exception while starting coilmq broker: '%s'", ex)
      if mtries != 0: 
        logger.debug("Retrying coilmq startup in %.1f seconds...", mdelay)
        time.sleep(mdelay)
        mdelay *= backoff
        mtries -= 1
      else:
        logger.debug("Ran out of trials (tried %d times) for coilmq startup. Giving up.", tries)
        break
    finally:
      if coilserver: coilserver.server_close()


@inject.param('config')
def start(config, brokerTimeout = 60.0):
  """
  Start twisted event loop and the fun should begin...

  @param brokerTimeout how long to wait for a broker 
  
  @return a negative number upon failure. Otherwise, it never returns.
  """
  
  manager = multiprocessing.Manager()
  serverUpEvent = manager.Event()
  broker = multiprocessing.Process(target=startSTOMPBroker, args=(config,serverUpEvent))
  broker.daemon = True
  broker.name = 'STOMP-Broker'
  broker.start()

  serverUpEvent.wait(brokerTimeout)
  if not serverUpEvent.is_set():
    logger.fatal("Broker not available after %.1f seconds. Giving up", brokerTimeout)
    return -1


  stompProtocolFactory = StompProtocolFactory()
 
  xmlrpcService = HostXMLRPCService()
  xmlrpcService.makeEngineAccesible()

  host = config.get('Broker', 'host') 
  port = int(config.get('Broker', 'port'))
  reactor.connectTCP(host, port, stompProtocolFactory)
  reactor.run()


if __name__ == '__main__':
  from sys import argv, exit
  if len(argv) < 2:
    print "Usage: %s <config-file>" % argv[0]
    exit(-1)
  else:
    configFile = argv[1]

    config = SafeConfigParser()
    config.read(configFile)


    injector = inject.Injector()
    inject.register(injector)

    injector.bind('config', to=config)
    injector.bind('words', to=HostWords.getWords)
    injector.bind('stompEngine', to=HostStompEngine, scope=inject.appscope) 
    injector.bind('stompProtocol', to=StompProtocol, scope=inject.appscope) 
    injector.bind('subject', to=Host) 
    injector.bind('hvController', to=HyperVisorController)
    
    
    

    exit(start())

