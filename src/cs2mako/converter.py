# Copyright (c) 2014 Eventbrite, Inc. All rights reserved.
# See "LICENSE" file for license.

"""This is a tokenizer and LR(1) parser for clearsilver that outputs Mako."""
import logging
import re

import patterns
import tokens


def open_token(scanner, token):
    """This is a factory for OpenToken objects"""
    match = patterns.open_r.search(token)
    name = match.group(1)
    logging.debug("Opening token %s" % name)
    if not match:
        raise ValueError("token (%s) not okay." % (token,))
    Class = getattr(tokens, "Open_" + name, tokens.OpenToken)
    return Class(scanner, token, name=name)

scanner = re.Scanner(
    [
        (patterns.open_r_str, open_token),
        (r'\<\?cs\s*\#', tokens.Open_comment),
        (r'\<\?cs\s*else\s*', tokens.Open_else),
        (patterns.close_r_str, tokens.CloseToken),
        (r'\s*\?\>', tokens.StopToken),
        (r'.', tokens.Char),
    ],
    flags=re.MULTILINE,
)

class Converter(object):
    def __init__(self, input_string):
        self.input_string = input_string

    def tokenize(self):
        """takes input string and yields the token list

        Usage:
            def parse(self):
                ...
                for token in converter.tokenize(input_file):
                    PDA on token
                ...

        Uses a few generators to get around the fact that re.Scanner
        doesn't seem to support multiline, and non-match tokens need
        to be tokenized into a generic single-character token.

        """
        def tokenize(s):
            first_line = True
            for line in s.split("\n"):
                logging.debug("Current Line:%s" % line)
                if first_line is not True:
                    yield tokens.Char(None, "\n")
                else:
                    first_line = False
                scanned_tokens = scanner.scan(line)[0]
                for token in scanned_tokens:
                    yield token

        last_char = None

        for token in tokenize(self.input_string):
            if isinstance(token, tokens.Char):
                if last_char is None:
                    last_char = []
                last_char.append(token.token)
            else:
                if last_char is not None:
                    yield tokens.Char(None, ''.join(last_char))
                    last_char = None
                yield token
        if last_char is not None:
            yield tokens.Char(None, ''.join(last_char))
        # LR(1) peek make last token get stuck as pending after StopIteration
        yield tokens.Char(None, '')

    def convert(self):
        """Streaming parser and code generator, retuns list of strings"""
        gen = self.tokenize()

        class counter(object):
            def __init__(self):
                self.count = 0
            def inc(self):
                self.count += 1
                return self.count
        counter = counter()

        def generator():
            counter.inc()
            generator.count = counter.count
            logging.debug("Emitting: %s" % generator.peek)
            try:
                return generator.peek
            finally:
                generator.peek = gen.next()
        # pre-fill these tracker variables
        generator.count = counter.count
        generator.peek = gen.next()
        generator.nest_depth = -1

        buf = []
        try:
            while True:
                next = generator()
                buf.append(
                    next.emit(generator)
                )
        except StopIteration:
            pass

        return self.post_process(buf)

    def post_process(self, buf):
        """Post process the converted template to perform some additional
        tweaks
        """
        converted = "".join(buf)
        pat = re.compile(r"^[ \t]*\\\r?\n", re.MULTILINE)
        processed = re.sub(pat, '', converted, 0)
        return processed
