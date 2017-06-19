"""Routines for parsing text."""

from re import Scanner, match, split

from ..six import integer_types


_NONE = 0
_SYMBOL = -1
_NUMBER = -2

# Scanner for user input polynomials.
_scanner = Scanner([
    (r'[a-zA-Z][0-9a-zA-Z]*', lambda self, token: _SYMBOL),
    (r'[1-9][0-9]*|0', lambda self, token: _NUMBER),
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


def is_symbol(s):
    """Return True if the given string looks like a symbol."""
    return match(r'^\s*[a-zA-Z][0-9a-zA-Z]*\s*$', s) is not None


def is_bracketed_symbol(s):
    """Return True for a symbol with a squared bracket."""
    # XXX: no nesting
    return match(r'^\s*\[[^\[\]]+\]\s*$', s) is not None


def is_lhs(s):
    """Return True if the given string looks like a LHS."""
    return match((
        r'^\s*'
        # x^n
        r'(?:'
        r'[a-zA-Z][0-9a-zA-Z]*'
        r'\s*'
        r'(?:'
        r'\^'
        r'\s*'
        r'[+-]*[1-9][0-9]*'
        r'\s*'
        r')?'
        r')'
        # optional ('*' | '/') x^n
        r'(?:'
        r'[*/]'
        r'\s*'
        r'[a-zA-Z][0-9a-zA-Z]*'
        r'\s*'
        r'(?:'
        r'\^'
        r'\s*'
        r'[+-]*[1-9][0-9]*'
        r'\s*'
        r')?'
        r')*'

        r'\s*$'
    ), s) or match((
        r'^\s*'
        # 1
        r'1\s*'
        # optional ('*' | '/') x^n
        r'(?:'
        r'[*/]'
        r'\s*'
        r'[a-zA-Z][0-9a-zA-Z]*'
        r'\s*'
        r'(?:'
        r'\^'
        r'\s*'
        r'[+-]*[1-9][0-9]*'
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
    # term = factor, [ { ("*" | "/" ), factor } ];
    if not _is_factor(tokens):
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
    # factor = [ { "+" | "-" } ], power ;
    oldpos = tokens.pos
    while True:
        if tokens.next == '+' or tokens.next == '-':
            tokens.consume()
        else:
            break
    if not _is_power(tokens):
        tokens.pos = oldpos
        return False
    return True


def _is_power(tokens):
    # power = atom, [ "^", factor ] ;
    if not _is_atom(tokens):
        return False
    if tokens.next == '^':
        tokens.consume()
        if not _is_factor(tokens):
            tokens.unconsume()
    return True


def _is_atom(tokens):
    # atom = SYMBOL | NUMBER | "(", expression, ")"
    if tokens.next == _SYMBOL or tokens.next == _NUMBER:
        tokens.consume()
        return True
    if tokens.next == '(':
        oldpos = tokens.pos
        tokens.consume()
        if not _is_expression(tokens) or tokens.next != ')':
            tokens.pos = oldpos
            return False
        tokens.consume()
        return True
    return False


# Scanner for FORM output polynomials.
_term_scanner = Scanner([
    ((
        # optional '+' or '-'
        r'[+-]?'
        # n
        r'[1-9][0-9]*'
        # optional '/' n.
        r'(?:/[1-9][0-9]*)?'
        # optional x or x^n
        r'(?:'
        r'\*'
        r'(?:[a-zA-Z][0-9a-zA-Z]*|\[[^\[\]]+\])'
        r'(?:\^-?[1-9][0-9]*)?'
        r')*'
    ), lambda self, token: token),
    ((
        # optional '+' or '-'
        r'[+-]?'
        # x or x^n
        r'(?:[a-zA-Z][0-9a-zA-Z]*|\[[^\[\]]+\])'
        r'(?:\^-?[1-9][0-9]*)?'
        # optional x or x^n
        r'(?:'
        r'\*'
        r'(?:[a-zA-Z][0-9a-zA-Z]*|\[[^\[\]]+\])'
        r'(?:\^-?[1-9][0-9]*)?'
        r')*'
    ), lambda self, token: token),
])


def split_terms(s):
    """Split terms in the expanded form."""
    terms, reminder = _term_scanner.scan(s)
    assert(not reminder)
    return terms


def split_symbols(s, seq=False):
    """
    Split symbols.

    Examples
    --------
    >>> split_symbols('x,y,z')
    ['x', 'y', 'z']
    >>> split_symbols('a b c')
    ['a', 'b', 'c']

    >>> split_symbols('x')
    'x'
    >>> split_symbols('x,')
    ['x']
    >>> split_symbols('x,y')
    ['x', 'y']

    >>> split_symbols('x1,...,x5')
    ['x1', 'x2', 'x3', 'x4', 'x5']
    >>> split_symbols('x1...x5')
    ['x1', 'x2', 'x3', 'x4', 'x5']

    """
    # Insert spaces before and after '...', e.g., 'x1...x9' -> 'x1 ... x9'.
    s = s.replace('...', ' ... ')
    # Set seq=True for 'x,' -> ('x',)
    s = s.strip()
    if s.endswith(','):
        s = s[:-1].rstrip()
        seq = True
    # Check if empty.
    if not s:
        return [] if seq else None
    # Split by commas/spaces.
    a = split(r'\s*,\s*|\s+', s)
    a = expand_dots(a)
    if any(not is_symbol(x) for x in a):
        raise ValueError('symbols expected: {0}'.format(list(
            x for x in a if not is_symbol(x))))
    # Return str or list, by the properties of the input arguments.
    assert(len(a) >= 1)
    if len(a) == 1:
        return a if seq else a[0]
    return a


_triple_dots_scanner = Scanner([
    (r'[0-9]+', lambda self, token: int(token)),
    (r'[^0-9]+', lambda self, token: token),
])


def expand_dots(a):
    """Expand triple dot operators in the list ``a``.

    Examples
    --------
    >>> expand_dots(['x1', '...', 'x5'])
    ['x1', 'x2', 'x3', 'x4', 'x5']
    >>> expand_dots(['p9q7r3', '...', 'p11q5r3'])
    ['p9q7r3', 'p10q6r3', 'p11q5r3']

    """
    while True:
        try:
            i = a.index('...')
        except ValueError:
            break

        if i == 0:
            raise ValueError(
                'missing left operand for triple dot operator: {0}'.format(
                    ','.join(a[:2])))
        if i == len(a) - 1:
            raise ValueError(
                'missing right operand for triple dot operator: {0}'.format(
                    ','.join(a[-2:])))

        x, rx = _triple_dots_scanner.scan(a[i - 1])
        y, ry = _triple_dots_scanner.scan(a[i + 1])
        assert(not rx)
        assert(not ry)

        fmt = ''
        args = []

        if len(x) == len(y):
            for xj, yj in zip(x, y):
                if (bool(isinstance(xj, integer_types)) !=
                        bool(isinstance(yj, integer_types))):
                    fmt = None
                    break
                if xj == yj:
                    fmt += str(xj).replace('{', '{{').replace('}', '}}')
                    continue
                if not isinstance(xj, integer_types):
                    fmt = None
                    break
                if args and len(args[0]) != abs(xj - yj) + 1:
                    fmt = None
                    break
                fmt += '{{{0}}}'.format(len(args))
                if xj < yj:
                    args.append(range(xj, yj + 1))
                else:
                    args.append(range(xj, yj - 1, -1))

        if not fmt:
            raise ValueError('cannot expand triple dot operator: {0}'.format(
                ','.join(a[i - 1:i + 2])))

        a[i - 1:i + 2] = (
            (fmt.format(*aa) for aa in zip(*args)) if args else (fmt,)
        )
    return a
