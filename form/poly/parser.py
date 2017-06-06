"""Routines for parsing text."""

import re

_NONE = 0
_SYMBOL = -1
_NUMBER = -2

_scanner = re.Scanner([
    (r'[a-zA-Z][0-9a-zA-Z]*', lambda self, token: _SYMBOL),
    (r'[1-9]*[0-9]', lambda self, token: _NUMBER),
    (r'\*\*', lambda self, token: '^'),
    (r'\+', lambda self, token: token),
    (r'\-', lambda self, token: token),
    (r'\*', lambda self, token: token),
    (r'\/', lambda self, token: token),
    (r'\^', lambda self, token: token),
    (r'\(', lambda self, token: token),
    (r'\)', lambda self, token: token),
    (r' +', None),  # skip spaces
])


class TokenList(object):
    """Tokens."""

    def __init__(self, tokens):
        """Construct a token list object."""
        self._tokens = tokens
        self.pos = 0

    def __len__(self):
        """Return the number of remaining tokens."""
        return len(self._tokens) - self.pos

    @property
    def next(self):
        """Return the next token type."""
        if len(self) <= 0:
            return _NONE
        return self._tokens[self.pos]

    def consume(self):
        """Consume the next token."""
        self.pos += 1

    def unconsume(self):
        """Unconsume the last token."""
        self.pos -= 1


def is_unsigned_integer(s):
    """Return True if the given string looks like an unsigned integer."""
    return re.match(r'^\s*[1-9]*[0-9]\s*$', s)


def is_signed_integer(s):
    """Return True if the given string looks like a signed integer."""
    return re.match(r'^[+\-\s]*[1-9]*[0-9]\s*$', s)


def is_symbol(s):
    """Return True if the given string looks like a symbol."""
    return re.match(r'^\s*[a-zA-Z][0-9a-zA-Z]*\s*$', s)


def is_lhs(s):
    """Return True if the given string looks like a LHS."""
    return re.match((
        r'^\s*'
        r'(?:'
        r'[a-zA-Z][0-9a-zA-Z]*'
        r'\s*'
        r'(?:'
        r'\^'
        r'\s*'
        r'[+-]*[1-9]*[0-9]'
        r'\s*'
        r')?'
        r')'
        r'(?:'
        r'[*/]'
        r'\s*'
        r'[a-zA-Z][0-9a-zA-Z]*'
        r'\s*'
        r'(?:'
        r'\^'
        r'\s*'
        r'[+-]*[1-9]*[0-9]'
        r'\s*'
        r')?'
        r')*'
        r'\s*$'
    ), s) or re.match((
        r'^\s*'
        r'1\s*'
        r'(?:'
        r'[*/]'
        r'\s*'
        r'[a-zA-Z][0-9a-zA-Z]*'
        r'\s*'
        r'(?:'
        r'\^'
        r'\s*'
        r'[+-]*[1-9]*[0-9]'
        r'\s*'
        r')?'
        r')*'
        r'\s*$'
    ), s)


def is_expression(s):
    """Return True if the given string looks like a valid FORM input."""
    tokens, reminder = _scanner.scan(s)
    if reminder:
        return False
    tokens = TokenList(tokens)
    if not _is_expression(tokens):
        return False
    if tokens:
        return False
    return True


def _is_expression(tokens):
    # expression = term, [ { ( "+" | "-" ), term } ];
    if not _is_term(tokens):
        return False
    while True:
        if tokens.next == '+' or tokens.next == '-':
            tokens.consume()
            if not _is_term(tokens):
                tokens.unconsume()
                break
            continue
        break
    return True


def _is_term(tokens):
    # term = [ { "+" | "-" } ], factor, [ { ("*" | "/" ), factor } ];
    oldpos = tokens.pos
    while True:
        if tokens.next == '+' or tokens.next == '-':
            tokens.consume()
        else:
            break
    if not _is_factor(tokens):
        tokens.pos = oldpos
        return False
    while True:
        if tokens.next == '*' or tokens.next == '/':
            tokens.consume()
            if not _is_factor(tokens):
                tokens.unconsume()
                break
            continue
        break
    return True


def _is_factor(tokens):
    # factor = ( SYMBOL | NUMBER | "(", expression, ")", [ "^", expression ] ;
    if tokens.next == _SYMBOL or tokens.next == _NUMBER:
        tokens.consume()
    elif tokens.next == '(':
        oldpos = tokens.pos
        tokens.consume()
        if not _is_expression(tokens) or tokens.next != ')':
            tokens.pos = oldpos
            return False
        tokens.consume()
    else:
        return False
    if tokens.next == '^':
        tokens.consume()
        if not _is_expression(tokens):
            tokens.unconsume()
    return True
