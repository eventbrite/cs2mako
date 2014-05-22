# Copyright (c) 2014 Eventbrite, Inc. All rights reserved.
# See "LICENSE" file for license.

"""Classes to emulate Clearsilver's "hdf" data object, for use in Mako

Unit-tests are run by calling this file directly, not through Django:

    python hdf_emulator [perf]

"""

import logging
import weakref
import string

class NotSet(object):
    def __int__(self):
        return 0
    def __str__(self):
        return ''
    def __float__(self):
        return float(0)
    def __long__(self):
        return long(0)
NotSet = NotSet()

# future potential performance improvement:
# lookups like this:
#    a.b.c.d
# currently will look up in the hdf._map
#      a.b, a.b.c, a.b.c.d
# by way of __getattr__ in each node (starting from 'a')
# These lookups could return an object that proxies all
# actions (like __int__, __float__, __getitem__) and when
# and action occurs, does the dict lookup.
#
# timeit module (code below) shows that looking up
# 'a.b.c.d.e' is 4x slower than lookup of 'a'


class Hdf():
    def __init__(self):
        self._map = {}
        self._root_dict = {}

    def set_value(self, key, val):
        if not key and key == '':
            raise ValueError('key can not be blank')

        node = self._map.get(key)
        if node is None:
            node = self.create_node(key)
        node._val = val
        if isinstance(val, HdfNode):
            node._val = val._val
        # Explicity return an empty string because when this is rendered
        # in Mako the value will be converted to a string and show in the
        # template.
        return ''

    def get(self, key, default=NotSet):
        value = NullHdfNode(key, default)
        if key in self._map:
            logging.debug('Map has key %s' % key)
            value = self._map.get(key)

        return value

    def roots(self):
        """Get a copy of the dictionary of root nodes from this object."""
        return self._root_dict.copy()

    def get_value_dict(self):
        """Builds dict from all hdf nodes that have actual values."""
        value_dict = {}
        for name, node in self._map.items():
            if node._val != NotSet:
                value_dict[name] = node._val
        return value_dict

    def create_node(self, key):
        """Instatiate a node, and build its parent nodes if need"""

        # create_node('a.b.c')
        # if a.b.c.d doesn't exist:
        #     recursively build from a, a.b, a.b.c

        if self._map.has_key(key):
            return self._map[key]

        sub_keys = key.split('.')
        len_sub_keys = len(sub_keys)

        parent = None
        root_node = None
        for i in xrange(len_sub_keys):
            # i is the zero-count index of the current node

            # i=0: a
            # i=1: a.b
            # i=2: a.b.c
            partial_key = '.'.join(sub_keys[:i+1])

            node = self._map.get(partial_key)
            if node is None:
                node = HdfNode(hdf=self, key=partial_key)
                if parent is not None:
                    parent._children.append(node)
            parent = node
            if root_node is None:
                root_node = node

        self._root_dict[sub_keys[0]] = root_node
        return self._map[key]


class HdfNode(object):
    # __slots__ = ('_hdf', '_key', '_name', '_val', '_children', )
    def __init__(self, hdf, key, val=NotSet):
        self._hdf = weakref.ref(hdf)
        self._key = key

        # if: key = 'a.b.c.d'
        # then: name = 'd'
        # if: key = 'a'
        # then: name = 'a'
        self._name = key[key.rfind('.')+1:]
        hdf._map[ key ] = self

        self._val = val
        self._children = []

    def num_children(self):
        """Returns the number of child nodes that this node has."""
        return len(self._children)

    def _set_value(self, val):
        self._val = val

    def __getitem__(self, key):
        return self.__getattr__(key)
    def __getattr__(self, attr):
        try:
            return self._hdf()._map[ "%s.%s" % (self._key, attr) ]
        except KeyError:
            return NullHdfNode(("%s.%s" % (self._key, attr)))

    def find(self, arg):
        return string.find(str(self._val), arg)
    def __str__(self):
        return unicode(self._val)

    def __unicode__(self):
        return unicode(self._val)

    def __int__(self):
        val = 0
        try:
            val = int(float(self._val))
        except ValueError:
            pass
        return val
    def __long__(self):
        val = 0.0
        try:
            val = long(self._val)
        except ValueError:
            pass
        return val
    def __float__(self):
        val = 0.0
        try:
            val = float(self._val)
        except ValueError:
            pass
        return val
    def __oct__(self):
        try:
            return oct(self._val)
        except TypeError:
            return oct(int(self))
    def __hex__(self):
        try:
            return hex(self._val)
        except TypeError:
            return hex(int(self))
    def __iter__(self):
        return iter(self._children)
    def __eq__(self, other):
        if self._val is self:
            return self is other
        if self._val == NotSet and not bool(other):
            return True
        return unicode(self._val) == unicode(other)
    def __ne__(self, other):
        if self._val == NotSet:
            return not self.__eq__(other)
        return unicode(self._val) != unicode(other)
    def __lt__(self, other):
        if self._val == NotSet:
            return False
        else:
            return float(self) < other
    def __gt__(self, other):
        if self._val == NotSet:
            return False
        else:
            return float(self) > other
    def __le__(self, other):
        if self._val == NotSet:
            return True
        else:
            return float(self) <= other
    def __ge__(self, other):
        if self._val == NotSet:
            return True
        else:
            return float(self) >= other
    def __nonzero__(self):
        if self._val == NotSet:
            return self.num_children() > 0
        if self._val == '0':
            return False
        return bool(self._val)
    def __len__(self):
        if isinstance(self._val, basestring):
            return len(self._val)
        else:
            return self.num_children()
    def __add__(self, other):
        if isinstance(other, basestring):
            return u"%s%s" % (unicode(self), unicode(other))
        elif isinstance(other, int):
            return int(self) + other
    def __radd__(self, other):
        if isinstance(other, basestring):
            return u"%s%s" % (unicode(other), unicode(self))
        elif isinstance(other, int):
            return int(self) + other
    def __sub__(self, other):
        return int(self) - other
    def __rsub__(self, other):
        return other - int(self)

class NullHdfNode(HdfNode):
    def __init__(self, key, default_value=NotSet):
        self._key = key
        self._val = default_value
        self._children = []

    def __getattr__(self, attr):
        return NullHdfNode(("%s.%s" % (self._key, attr)))

    def __getitem__(self, attr):
        return NullHdfNode(("%s.%s" % (self._key, attr)))

    def __call__(self, *args):
        # Take args, convert the values to strings and join with commas
        arg_string = reduce(lambda x, y: "%s, %s" % (str(x), str(y)), args)
        return "%s(%s)" % (self._val, arg_string)

if __name__ == "__main__":
    import unittest

    class TestHdfEmulator(unittest.TestCase):
        def setUp(self):
            self.hdf = Hdf()

        def test_01(self):
            self.assertTrue(isinstance(self.hdf, Hdf))

        def test_02(self):
            key = 'a'
            value = "value-is-this"

            self.hdf.set_value(key, value)
            _map = self.hdf._map

            self.assertTrue(isinstance(_map, dict))
            self.assertTrue(_map.has_key(key))
            self.assertTrue(isinstance(_map[key], HdfNode))
            self.assertEquals(_map[key]._val, value)
            self.assertEquals(_map[key]._key, key)
            self.assertEquals(_map[key]._name, key)

        def test_03(self):
            key = 'a.b.c.d'
            half = 'a.b'
            value = "this-is-val"

            self.hdf.set_value(key, value)
            _map = self.hdf._map

            self.assertTrue(isinstance(_map, dict))
            self.assertTrue(_map.has_key(key))
            self.assertTrue(isinstance(_map[key], HdfNode))

            self.assertEquals(_map[key]._val, value)
            self.assertEquals(_map[half]._val, NotSet)
            self.assertEquals(_map['a']._children[0]._key, 'a.b')

        def test_04(self):
            key = 'mg.a.b.c.d'
            value = "my-happy-time"

            self.hdf.set_value(key, value)
            mg = self.hdf.get('mg')

            self.assertEquals(mg.a.b.c.d._val, value)
            self.assertEquals(mg.a.b.c.d._key, key)
            self.assertEquals(mg.a.b.c.d._name, 'd')
            self.assertEquals(str(mg.a.b.c.d), str(value))
            self.assertEquals(unicode(mg.a.b.c.d), unicode(value))

        def test_05(self):
            key = 'mg.qdata.x%(i)s'
            value = "value-%(val)s-was"
            values = ('foo','bar','zam','bong')
            for i in range(len(values)):
                val = values[i]
                self.hdf.set_value(key % locals(), value % locals())

            mg = self.hdf.get('mg')
            self.assertEqual(str(mg.qdata.x2), 'value-zam-was')

        def test_10_numeric_types(self):
            key = 'mg.qdata.num'
            value = 2
            self.hdf.set_value(key, value)
            mg = self.hdf.get('mg')
            for fn in (int, float, long, oct, hex):
                self.assertEqual(fn(mg.qdata.num), fn(2))
        def test_11_numeric_types(self):
            key = 'mg.qdata.num'
            value = '2'
            self.hdf.set_value(key, value)
            mg = self.hdf.get('mg')
            for fn in (
                        int, float, long,
                        oct, hex
                       ):
                self.assertEqual(fn(mg.qdata.num), fn(2))

        def test_26_value(self):
            """list of values on increasing length, checks value

                values:
                    value-x-was
                    value-xx-was
                    value-xxx-was
                    ... etc.

            """
            key = 'mg.qdata.%(i)s'
            value = "value-%(val)s-was"
            for i in range(100):
                val = 'x' * i
                self.hdf.set_value(key % locals(), value % locals())

            mg = self.hdf.get('mg')
            self.assertEqual(str(mg.qdata['64']), 'value-' + 'x'*64 + '-was')

        def test_26_iter(self):
            """list of values on incr length: tests iteration in same order

                values:
                    value-x-was
                    value-xx-was
                    value-xxx-was
                    ... etc.

            """
            key = 'mg.qdata.%(i)s'
            value = "value-%(val)s-was"
            for i in range(100):
                val = 'x' * i
                self.hdf.set_value(key % locals(), value % locals())

            mg = self.hdf.get('mg')
            previous = ''
            for n in map(str, mg.qdata):
                self.assertTrue(len(n) > len(previous))
                # python 2.7: self.assertGreater(len(n), len(previous))
                previous = n

    def perf_test():
        import timeit
        setup = """from __main__ import Hdf
hdf = Hdf()
hdf.set_value('%(key)s', 'a')
mg = hdf.get('mg')
        """
        statement = """x = str(%(key)s)"""
        for key in ('mg.a', 'mg.a.b.c.d.e'):
            t = timeit.Timer(statement % locals(), setup % locals())
            print "%s: %.2f usec/pass" % (
                key,
                1000000 * t.timeit(number=100000)/100000
            )
    import sys
    if len(sys.argv) > 1:
        perf_test()
    else:
        unittest.main()
