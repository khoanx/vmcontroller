class NoSuchVirtualMachine(Exception):
  def __init__(self, msg):
    self._msg = msg
  def __str__(self):
    return "No VM by the name/id %s found" % self._msg

class ConfigError(Exception):
  def __init__(self, msg):
    self._msg = msg

  def __str__(self):
    return "Configuration error: %s" % self._msg

class NotInitialized(Exception):
  def __init__(self, msg):
    self._msg = msg

  def __str__(self):
    return "Instance isn't fully initialized: %s" % self._msg

