from twisted.trial import unittest

from boincvm.common import EntityDescriptor 

class TestEntityDescriptor(unittest.TestCase):

  def setUp(self):
    self.descriptor1 = EntityDescriptor(id=123, name='test1', foo=1, bar=2)
    self.descriptor2 = EntityDescriptor(456, foo=3)
    self.descriptor3 = EntityDescriptor(0)
 

  def test_contains(self):
    self.assertTrue( 'foo' in self.descriptor1 )
    self.assertTrue( 'id' in self.descriptor1 )
    self.assertTrue( 'name' in self.descriptor1 )

    self.assertTrue( 'id' in self.descriptor2 )


  def test_serialization(self):
    serialized = self.descriptor1.serialize()
    deserialized = EntityDescriptor.deserialize(serialized)
    self.assertEquals(self.descriptor1, deserialized)

  def test_setattr(self):
    self.descriptor1.foobar = 3
    self.assertEquals(3, self.descriptor1.foobar)

    #overwriting
    self.descriptor1.foo = 11
    self.assertEquals(11, self.descriptor1.foo)

  def test_getattr(self):
 
    self.assertRaises(AttributeError, lambda: self.descriptor1.nonexistent) 
    self.assertEquals(123, self.descriptor1.id)
    self.assertEquals('test1', self.descriptor1.name)
    self.assertEquals(1, self.descriptor1.foo)
    self.assertEquals(2, self.descriptor1.bar)

    self.assertRaises(AttributeError, lambda: self.descriptor2.bar)
    self.assertEquals(3, self.descriptor2.foo)
    self.assertEquals(456, self.descriptor2.id)

  def test_repr(self):
    self.assertEquals("""EntityDescriptor<id=123>: {bar: 2, foo: 1, name: test1}""" , repr(self.descriptor1))
    




