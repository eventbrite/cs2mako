# Copyright (c) 2014 Eventbrite, Inc. All rights reserved.
# See "LICENSE" file for license.

import sys
from StringIO import StringIO

from mako.runtime import Context
from mako.template import Template

class TestValue():
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    def __call__(self, *args):
        # Take args, convert the values to strings and join with commas
        arg_string = reduce(lambda x, y: "%s, %s" % (str(x), str(y)), args)
        return TestValue("%s(%s)" % (self.name, arg_string))

    def __nonzero__(self):
        return 1

    def __getattr__(self, attr_name):
        return TestValue("%s.%s" % (self.name, attr_name))

class TestContext(Context):
    def get(self, key, default=None):
        return TestValue("*****%s" % key)


def test_render():
    if len(sys.argv) < 2:
        print "Missing filename"
        sys.exit(2)

    template = Template(filename=sys.argv[1])
    buf = StringIO()
    ctx = TestContext(buf)
    template.render_context(ctx)
    print buf.getvalue()

    sys.exit(0)


if __name__ == "__main__":
    test_render()
