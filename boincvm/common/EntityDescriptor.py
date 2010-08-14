import support

class EntityDescriptor(object):
  """ Serializable representation of either a host or a VM.
      
      Use "simple" (numbers, strings) values. Sequences
      or maps may cause troubles with the datatypes 
      upon deserialization (but the underlaying functionality
      would still work: it's only the datatypes that might
      get mangled).
  """
  
  def __init__(self, id, **kw):
    self._dict = dict(**kw)
    self._dict['id'] = id

  def __contains__(self, key):
    return key in self._dict

  def serialize(self):
    return support.serialize(self._dict)
  
  def __getattr__(self, attr):
    if attr not in self._dict:
      raise AttributeError("'%s' not found in the descriptor" % attr)
    return self._dict[attr]

  def __setattr__(self, attr, value):
    object.__setattr__(self, attr, value)

  def __eq__(self, other):
    if type(self) != type(other):
      return False

    if len(self._dict) != len(other._dict):
      return False

    for k in self._dict.iterkeys():
      if self._dict[k] != other._dict.get(k):
        return False

    return True

  def __repr__(self):
    res = []
    d = dict(self._dict)
    id_ = d.pop('id')
    for k in sorted(d.iterkeys()):
      res.append( '%s: %s' % (k, self._dict[k]) )
    txt = ', '.join(res)
      
    return 'EntityDescriptor<id=%s>: {%s}' % (id_, txt)

  @staticmethod
  def deserialize(src):
    srcDict = support.deserialize(src)
    asciiDict = dict( [(str(k), v) for k,v in srcDict.iteritems()] )
    srcId = asciiDict.pop('id')
    descr = EntityDescriptor(srcId, **asciiDict)
    return descr

