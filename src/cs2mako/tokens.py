# Copyright (c) 2014 Eventbrite, Inc. All rights reserved.
# See "LICENSE" file for license.

import logging
import re

import patterns


space_eq_space = re.compile(r'\s*=\s*')

expr_repl = (
    (re.compile(r'\#([a-zA-Z0-9._]+)'), r'int(\1)'),
    (re.compile(r'\s*!\s*(?=[^=])'), ' not '),
    (re.compile(r'\s*\|\|\s*'), ' or '),
    (re.compile(r'\s*\&\&\s*'), ' and '),
)


class Token(object):
    tag_only = False
    _start_tok = '<%'
    _end_tok = '>'
    _emit_name = True
    close_tag = True
    _tag_adds_depth = False
    name = ''

    def __init__(self, scanner, token):
        self.token = token

    def __str__(self):
        return "[%s: %s]" % (str(self.__class__.__name__), str(self.token),)

    def emit(self, generator):
        return self.token

    def sanitize_expression(self, expression):
        for expr, repl in expr_repl:
            expression = expr.sub(repl, expression)
        return expression


class OpenToken(Token):
    def __init__(self, scanner, token, name=None):
        Token.__init__(self, scanner, token)
        self.name = name

    def emit(self, generator):
        """

        <% tag_name: parts %>contents</% end_tag_name %>

        """

        #tag part
        buf = [ self.start_tok(generator) ]
        self.emit_name(generator, buf)
        self.emit_tag(generator, buf)
        buf.append(self.end_tok(generator))
        # contents part
        if not self.tag_only:
            self.emit_contents(generator, buf)
        logging.debug("Emitting %s" % str(buf))
        return ''.join(buf)

    def emit_name(self, generator, buf):
        if self._emit_name:
            if self._emit_name is True:
                buf.append(self.name)
            else:
                buf.append(str(self._emit_name))

    def emit_tag(self, generator, buf):
        while True:
            token = generator()
            if isinstance(token, StopToken):
                break
            else:
                buf.append(token.emit(generator))

    def emit_contents(self, generator, buf):
        logging.debug("Contents of %s" % self.name)
        while True:
            token = generator()
            if isinstance(token, CloseToken) and token.name == self.name:
                self.emit_close_tag(generator, buf)
                break
            else:
                # pushdown
                buf.append(token.emit(generator))

    def emit_close_tag(self, generator, buf):
        """emits the <% endtag %> tag"""
        ct = self.close_tag
        if ct is False:
            return
        if ct is True:
            buf.append('</%')
            buf.append(self.name)
            buf.append('>')
        elif self.close_tag is not None:
            buf.append(self.close_tag)

    def start_tok(self, generator):
        return self._start_tok

    def end_tok(self, generator):
        return self._end_tok


class OpenTagOnlyToken(OpenToken):
    tag_only = True


# <?cs var:var_name ?>
class Open_var(OpenTagOnlyToken):
    _start_tok = '${ '
    _end_tok = ' }'
    _emit_name = False
    def emit_tag(self, generator, buf):
        expression = []
        OpenToken.emit_tag(self, generator, expression)
        expression = self.sanitize_expression(''.join(expression))
        filters = {
            '^\s*url_escape\(\s*(.+?)\s*\)\s*$': 'u',
            '^\s*html_escape\(\s*(.+?)\s*\)\s*$': 'h',
            '^\s*html_strip\(\s*(.+?)\s*\)\s*$': 'striptags',
            '^\s*js_escape\(\s*(.+?)\s*\)\s*$': 'escapejs',
        }
        match = True
        applied_filters = []
        while match:
            match = False
            for pattern, mako_filter in filters.items():
                filtered = re.sub(pattern, '\\1', expression)
                if filtered != expression:
                    # The patten matched add it to the list of filters
                    expression = filtered
                    applied_filters.append(mako_filter)
                    match = True
        # Mako filters are applied in order, but our loop matched them in
        # reverse order so first we have to reverse our list.
        applied_filters.reverse()
        if len(applied_filters) > 0:
            expression = '%s | %s' % (expression, ', '.join(applied_filters))
        buf.append(expression)

# <?cs set:var_name = r_value ?>
class Open_set(OpenTagOnlyToken):
    _start_tok = '<% '
    _end_tok = ' %>'
    _emit_name = False
    def emit_tag(self, generator, buf):
        expression = []
        OpenTagOnlyToken.emit_tag(self, generator, expression)
        expression = self.sanitize_expression(''.join(expression))
        if '=' in expression:
            lh, rh = expression.split('=', 1)
            if '.' in lh:
                match = re.search('([a-zA-Z0-9_.]+)', lh)
                if match:
                    expression = 'hdf.set_value("%s", %s)' % (
                        match.group(0),
                        rh,
                    )

        buf.append(expression)

# <?cs include:"some/clearsilver/template.html" ?>
class Open_include(OpenTagOnlyToken):
    _start_tok = '<%include file='
    _end_tok = '/>'
    _emit_name = False
    def emit_tag(self, generator, buf):
        while True:
            token = generator()
            if isinstance(token, StopToken):
                break
            else:
                # file_string is '="<filename>"
                file_string = token.emit(generator)
                # We need to add a slash because ClearSilver templates are exact
                # filenames where as Mako will be relative without the slash
                buf.append(re.sub(r'"', r'"/', file_string, 1))

# <?cs # this is totally a comment ?>
class Open_comment(OpenTagOnlyToken):
    _start_tok = '<%doc>'
    _end_tok = '</%doc>'
    _emit_name = False

# <?cs def:macro() ?>
class Open_def(OpenToken):
    _start_tok = '<%def name="'
    _end_tok = '">'
    _emit_name = False
    def emit_tag(self, generator, buf):
        while True:
            token = generator()
            if isinstance(token, StopToken):
                break
            else:
                macro_sig = token.emit(generator)
                # Make sure there isn't additional whitespace around the function
                buf.append(macro_sig.strip())

# <?cs name:cs_var ?>
class Open_name(OpenTagOnlyToken):
    _start_tok = '${name('
    _end_tok = ')}'
    _emit_name = False

# <?cs call:macro() ?>
class Open_call(OpenTagOnlyToken):
    _start_tok = '${'
    _end_tok = '}'
    _emit_name = False

# <?cs if:conditional_expression ?>
class Open_if(OpenToken):
    _start_tok = '% if '
    _end_tok = ':\n'
    close_tag = '% endif\n'
    _emit_name = False
    _tag_adds_depth = True

    def emit(self, generator):
        nest_depth = generator.nest_depth
        if self._tag_adds_depth:
            generator.nest_depth += 1
        ret = OpenToken.emit(self, generator)
        generator.nest_depth = nest_depth
        return ret

    def emit_tag(self, generator, buf):
        expression = []
        OpenToken.emit_tag(self, generator, expression)
        expression = ''.join(expression)
        expression = self.sanitize_expression(expression)
        buf.append(expression)

    def start_tok(self, generator):
        return '\\\n' + (generator.nest_depth * '  ') + self._start_tok

    def emit_close_tag(self, generator, buf):
        buf.append('\\\n')
        if generator.nest_depth >= 0:
            buf.append(generator.nest_depth * '  ')
        OpenToken.emit_close_tag(self, generator, buf)

    # def emit_contents(sef, generator, buf):
    #     OpenToken.emit_contents(sef, generator, buf)
    #     buf.append('\\')

# <?cs elseif:conditional_expression ?>
#class Open_elseif(Open_if):
class Open_elif(Open_if):
    _start_tok = '% elif '
    _end_tok = ':\n'
    close_tag = False
    _emit_name = False
    _tag_adds_depth = False

    # def emit(self, generator):
    #     return OpenToken.emit(self, generator)

    def emit_contents(self, generator, buf):
        while True:
            peek = generator.peek
            logging.debug("elseifelif Contents of %s" % peek)
            if (isinstance(peek, CloseToken) and peek.name == 'if'):
                #buf.append('\\')
                break
            token = generator()
            # pushdown
            buf.append(token.emit(generator))

class Open_elseif(Open_elif): pass
# <?cs else ?>
class Open_else(Open_elif):
    _start_tok = '% else:\n'
    _end_tok = ''
    close_tag = False
    _emit_name = False
    _tag_adds_depth = False

    def emit(self, generator):
        return OpenToken.emit(self, generator)

    # def emit_contents(self, generator, buf):
    #     while True:
    #         peek = generator.peek
    #         if isinstance(peek, CloseToken) and peek.name == 'if':
    #             buf.append('\\')
    #             break
    #         token = generator()
    #         # pushdown
    #         buf.append(token.emit(generator))


# <?cs alt:item.sales ?>0.0<?cs /alt ?>
class Open_alt(OpenTagOnlyToken):
    _start_tok = '${ '
    _end_tok = ' }'
    _emit_name = False

    def emit(self, generator):

        # tag part
        buf = []
        while True:
            token = generator()
            if isinstance(token, StopToken):
                break
            else:
                # pushdown
                buf.append(token.emit(generator))
        variable = ''.join(buf)

        # body part
        buf = []
        while True:
            token = generator()
            if isinstance(token, CloseToken) and token.name == self.name:
                break
            else:
                # pushdown
                buf.append(token.emit(generator))
        body = ''.join(buf)

        return '${ %(variable)s if %(variable)s else "%(body)s" }' % locals()

# looping constructs:
# <?cs each:item = mg.invoices ?>
#   item
# <?cs /each ?>
class Open_each(Open_if):
    _start_tok = '% for '
    _end_tok = ':\n'
    close_tag = '% endfor\n'
    _emit_name = False
    _tag_adds_depth = True

    def emit_tag(self, generator, buf):
        expression = []

        # calls sanitize_expression
        Open_if.emit_tag(self, generator, expression)
        expression = ''.join(expression)
        buf.append(expression)

    def sanitize_expression(self, expression):
        expression = Open_if.sanitize_expression(self, expression)
        expression = space_eq_space.subn(' in ', expression, 1)[0]
        return expression


# <?cs loop:i = start, end, incr ?>
#   foo
# <?cs /loop ?>
class Open_loop(Open_each):

    def sanitize_expression(self, expression):
        expression = Open_if.sanitize_expression(self, expression)
        expression = space_eq_space.subn(' in range(', expression, 1)[0]
        expression = expression + ')'
        return expression

# generic:  <?cs /[a-z] ?>
class CloseToken(Token):
    def __init__(self, scanner, token, name=None):
        Token.__init__(self, scanner, token)
        if name is None:
            match = patterns.close_r.search(token)
            name = match.group(1)
        self.name = name

# ?>
class StopToken(Token): pass
# anything else.
class Char(Token): pass

