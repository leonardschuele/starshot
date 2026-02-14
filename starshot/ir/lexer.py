"""Tokenizer for S-expression Starshot IR."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    LPAREN = auto()
    RPAREN = auto()
    STRING = auto()
    INT = auto()
    FLOAT = auto()
    IDENT = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


class LexError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"Lex error at {line}:{col}: {msg}")
        self.line = line
        self.col = col


def tokenize(source: str) -> list[Token]:
    """Tokenize an S-expression source string into a list of tokens."""
    tokens: list[Token] = []
    i = 0
    line = 1
    col = 1

    while i < len(source):
        ch = source[i]

        # Skip whitespace
        if ch in ' \t\r':
            i += 1
            col += 1
            continue

        if ch == '\n':
            i += 1
            line += 1
            col = 1
            continue

        # Skip comments (;; to end of line)
        if ch == ';':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue

        # Parentheses
        if ch == '(':
            tokens.append(Token(TokenType.LPAREN, '(', line, col))
            i += 1
            col += 1
            continue

        if ch == ')':
            tokens.append(Token(TokenType.RPAREN, ')', line, col))
            i += 1
            col += 1
            continue

        # String literals
        if ch == '"':
            start_col = col
            i += 1
            col += 1
            buf = []
            while i < len(source) and source[i] != '"':
                if source[i] == '\\' and i + 1 < len(source):
                    i += 1
                    col += 1
                    esc = source[i]
                    if esc == 'n':
                        buf.append('\n')
                    elif esc == 't':
                        buf.append('\t')
                    elif esc == '"':
                        buf.append('"')
                    elif esc == '\\':
                        buf.append('\\')
                    else:
                        buf.append(esc)
                elif source[i] == '\n':
                    buf.append('\n')
                    line += 1
                    col = 0
                else:
                    buf.append(source[i])
                i += 1
                col += 1
            if i >= len(source):
                raise LexError("Unterminated string literal", line, start_col)
            i += 1  # skip closing quote
            col += 1
            tokens.append(Token(TokenType.STRING, ''.join(buf), line, start_col))
            continue

        # Numbers and identifiers
        if _is_atom_char(ch):
            start_col = col
            start = i
            while i < len(source) and _is_atom_char(source[i]):
                i += 1
                col += 1
            word = source[start:i]
            tokens.append(_classify_atom(word, line, start_col))
            continue

        raise LexError(f"Unexpected character: {ch!r}", line, col)

    tokens.append(Token(TokenType.EOF, '', line, col))
    return tokens


def _is_atom_char(ch: str) -> bool:
    return ch not in '() \t\n\r;"' and ch.isprintable()


def _classify_atom(word: str, line: int, col: int) -> Token:
    # Try integer
    if _is_int(word):
        return Token(TokenType.INT, word, line, col)
    # Try float
    if _is_float(word):
        return Token(TokenType.FLOAT, word, line, col)
    # Otherwise it's an identifier (includes operators like +, -, >=, etc.)
    return Token(TokenType.IDENT, word, line, col)


def _is_int(s: str) -> bool:
    if s.startswith('-'):
        return len(s) > 1 and s[1:].isdigit()
    return s.isdigit()


def _is_float(s: str) -> bool:
    t = s
    if t.startswith('-'):
        t = t[1:]
    if '.' not in t:
        return False
    parts = t.split('.')
    if len(parts) != 2:
        return False
    return parts[0].isdigit() and parts[1].isdigit()
