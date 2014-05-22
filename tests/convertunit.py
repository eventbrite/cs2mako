# Copyright (c) 2014 Eventbrite, Inc. All rights reserved.
# See "LICENSE" file for license.

import os
import sys
import unittest

sys.path[0] = os.path.join(sys.path[0],'..', 'src')
from cs2mako.addintl import add_intl
from cs2mako.converter import Converter

class TestClearSilverConverter(unittest.TestCase):
    def setUp(self):
        pass

    def test_comment(self):
        # Make sure that comment tags are properly converted
        clear_silver="""<html>
        <body>
            <div> <?cs # Start test div ?>
            </div>
        </body>
        </html>
        """
        mako="""<html>
        <body>
            <div> <%doc> Start test div</%doc>
            </div>
        </body>
        </html>
        """
        converter = Converter(clear_silver)
        result_buf = converter.convert()
        self.assertEqual(''.join(result_buf), mako)

    def test_include(self):
        # Make sure that include tags are properly converted
        clear_silver='<?cs include:"testfile.html"?>'
        mako='<%include file="/testfile.html"/>'
        converter = Converter(clear_silver)
        result_buf = converter.convert()
        self.assertEqual(''.join(result_buf), mako)

    def test_inline_if(self):
        clear_silver='<?cs if test==1 ?>SELECTED<?cs /if?>'
        mako='% if test==1:\nSELECTED\\\n% endif\n'
        converter = Converter(clear_silver)
        result_buf = converter.convert()
        self.assertEqual(''.join(result_buf), mako)

    def test_if_else(self):
        clear_silver='<?cs if test==1 ?>SELECTED<?cs else ?>NOPE<?cs /if?>'
        mako='% if test==1:\nSELECTED\\\n% else:\nNOPE\\\n% endif\n'
        converter = Converter(clear_silver)
        result_buf = converter.convert()
        self.assertEqual(''.join(result_buf), mako)

    def test_nested_if_else(self):
        clear_silver="""
<?cs if test==1 ?>
  SELECTED
<?cs else ?>
  <?cs if foo==2 ?>
    NOPE
  <?cs elif bar==1 ?>
    Maybe
  <?cs else ?>
    Oh yeah
  <?cs /if ?>
<?cs /if?>
"""
        mako="""
% if test==1:

  SELECTED
% else:

  % if foo==2:

    NOPE
  % elif bar==1:

    Maybe
  % else:

    Oh yeah
  % endif

% endif

"""
        converter = Converter(clear_silver)
        result_buf = converter.convert()
        self.assertEqual(''.join(result_buf), mako)

    def test_set(self):
        clear_silver='<?cs set:test = 1 ?>'
        mako='<% test = 1 %>'
        converter = Converter(clear_silver)
        result_buf = converter.convert()
        self.assertEqual(''.join(result_buf), mako)

    def test_clearsilver_functions(self):
        clear_silver='<?cs var:url_escape(test) ?>'
        mako='${ test | u }'
        converter = Converter(clear_silver)
        result = converter.convert()
        self.assertEqual(result, mako)

    def test_multiple_functions(self):
        clear_silver='<?cs var: html_escape( url_escape(test)) ?>'
        mako='${ test | u, h }'
        converter = Converter(clear_silver)
        result = converter.convert()
        self.assertEqual(result, mako)
        clear_silver='<?cs var: js_escape( html_strip(test)) ?>'
        mako='${ test | striptags, escapejs }'
        converter = Converter(clear_silver)
        result = converter.convert()
        self.assertEqual(result, mako)

    def test_no_functions(self):
        clear_silver='<?cs var:test ?>'
        mako='${ test }'
        converter = Converter(clear_silver)
        result = converter.convert()
        self.assertEqual(result, mako)

    def test_def(self):
        clear_silver='<?cs def:test(var1) ?>\n<h1>Hello</h1>\n<?cs /def ?>'
        mako='<%def name="test(var1)">\n<h1>Hello</h1>\n</%def>'
        converter = Converter(clear_silver)
        result = converter.convert()
        self.assertEqual(result, mako)

    def test_name(self):
        clear_silver='<?cs name:cs_var ?>'
        mako='${name(cs_var)}'
        converter = Converter(clear_silver)
        result = converter.convert()
        self.assertEqual(result, mako)

    def test_call(self):
        clear_silver='<?cs call:macro(var1, var2) ?>'
        mako='${macro(var1, var2)}'
        converter = Converter(clear_silver)
        result = converter.convert()
        self.assertEqual(result, mako)

class TestGettextIntl(unittest.TestCase):
    def test_add_simple(self):
        self.assertEqual(add_intl("this is a\nlame test"),
                '${ _("this is a") }\n${ _("lame test") }')

    def test_add_html(self):
        html = "<html>this is a test</html>"
        self.assertEqual(add_intl(html),
                '<html>${ _("this is a test") }</html>')

    def test_input(self):
        html = '<html><input name="test" value="hello"/></html>'
        res = '<html><input name="test" value="${ _("hello") }"/></html>'
        self.assertEqual(add_intl(html), res)

    def test_input_no_slash(self):
        html = '<html><input name="test" value="hello"></html>'
        res = '<html><input name="test" value="${ _("hello") }"></html>'
        self.assertEqual(add_intl(html), res)

    def test_buf(self):
        html = "<html><input type='text' value='inital value' "\
            + "<% if some_style %> style='color: green;' <% endif %> "\
            + "id='something' onblur='doStuff();' /></html>"
        res = "<html><input type='text' value='${ _(\"inital value\") }' "\
            + "<% if some_style %> style='color: green;' <% endif %> "\
            + "id='something' onblur='doStuff();' /></html>"
        self.assertEqual(add_intl(html), res)

    def test_mako(self):
        html = "% if blah\nThis is a test value\n% endif"
        res = "% if blah\n${ _(\"This is a test value\") }\n% endif"
        self.assertEqual(add_intl(html), res)

    def test_js(self):
        html = "<script>blah blah\ntest value\n\t</script>"
        res = "<script>blah blah\ntest value\n\t</script>"
        self.assertEqual(add_intl(html), res)

    def test_if_tag(self):
        html = '<div id="test" class="\"\n% if mg.signup:' \
            + '\n"container_signup\"\n%endif">'
        res = html
        self.assertEqual(add_intl(html), res)

if __name__ == '__main__':
    unittest.main()
#    test = TestGettextIntl('test_add_html')
#    unittest.TextTestRunner().run(test)
