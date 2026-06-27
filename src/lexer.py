"""
=============================================================
  BATAK COMPILER - LEXER
  Menghasilkan 7 jenis token dari source code BatakScript
=============================================================

TOKEN TYPES:
  1. KEYWORD    - kata kunci bahasa (molo, adong, dll)
  2. IDENTIFIER - nama variabel/fungsi
  3. INTEGER    - bilangan bulat
  4. FLOAT      - bilangan desimal
  5. STRING     - teks dalam tanda kutip
  6. OPERATOR   - +, -, *, /, ==, !=, <, >, dll
  7. PUNCTUATION- (, ), {, }, :, ,, ;
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from language_design import KEYWORDS, BUILTIN_FUNCTIONS

# ─────────────────────────────────────────────
#  TOKEN CLASS
# ─────────────────────────────────────────────
@dataclass
class Token:
    type:    str
    value:   str
    line:    int
    column:  int

    def __repr__(self):
        return f"Token({self.type:<14} | '{self.value}' | baris {self.line}:{self.column})"


# ─────────────────────────────────────────────
#  TOKEN TYPES (7 jenis)
# ─────────────────────────────────────────────
class TokenType:
    KEYWORD     = "KEYWORD"
    IDENTIFIER  = "IDENTIFIER"
    INTEGER     = "INTEGER"
    FLOAT       = "FLOAT"
    STRING      = "STRING"
    OPERATOR    = "OPERATOR"
    PUNCTUATION = "PUNCTUATION"
    EOF         = "EOF"


# ─────────────────────────────────────────────
#  LEXER CLASS
# ─────────────────────────────────────────────
class Lexer:
    def __init__(self, source_code: str):
        self.source  = source_code
        self.pos     = 0
        self.line    = 1
        self.column  = 1
        self.tokens: List[Token] = []

    def error(self, char):
        raise SyntaxError(
            f"[Lexer] Karakter tidak dikenal '{char}' "
            f"di baris {self.line}, kolom {self.column}"
        )

    def peek(self, offset=0) -> Optional[str]:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos    += 1
        self.column += 1
        if ch == '\n':
            self.line  += 1
            self.column = 1
        return ch

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch in ' \t\r\n':
                self.advance()
            elif ch == '/' and self.peek(1) == '/':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.advance()
            elif ch == '/' and self.peek(1) == '*':
                self.advance(); self.advance()
                while self.pos < len(self.source):
                    if self.source[self.pos] == '*' and self.peek(1) == '/':
                        self.advance(); self.advance()
                        break
                    self.advance()
            else:
                break

    def read_number(self) -> Token:
        start_col = self.column
        num_str   = ""
        is_float  = False

        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            ch = self.source[self.pos]
            if ch == '.':
                if is_float:
                    break
                is_float = True
            num_str += self.advance()

        ttype = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(ttype, num_str, self.line, start_col)

    def read_string(self) -> Token:
        start_col = self.column
        quote     = self.advance()
        result    = ""

        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == '\\':
                self.advance()
                esc = self.advance()
                escape_map = {'n': '\n', 't': '\t', '\\': '\\', '"': '"', "'": "'"}
                result += escape_map.get(esc, esc)
            elif ch == quote:
                self.advance()
                break
            else:
                result += self.advance()
        else:
            raise SyntaxError(f"[Lexer] String tidak ditutup di baris {self.line}")

        return Token(TokenType.STRING, result, self.line, start_col)

    def read_identifier_or_keyword(self) -> Token:
        start_col = self.column
        word      = ""

        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            word += self.advance()

        if word in KEYWORDS or word in BUILTIN_FUNCTIONS:
            return Token(TokenType.KEYWORD, word, self.line, start_col)
        return Token(TokenType.IDENTIFIER, word, self.line, start_col)

    def read_operator(self) -> Optional[Token]:
        start_col = self.column
        two_char_ops = ["==", "!=", "<=", ">=", "**"]
        two = self.source[self.pos:self.pos+2]
        if two in two_char_ops:
            self.advance(); self.advance()
            return Token(TokenType.OPERATOR, two, self.line, start_col)
        ch = self.source[self.pos]
        if ch in "+-*/%<>=!":
            self.advance()
            return Token(TokenType.OPERATOR, ch, self.line, start_col)
        return None

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace_and_comments()

            if self.pos >= len(self.source):
                break

            ch = self.source[self.pos]

            if ch in ('"', "'"):
                self.tokens.append(self.read_string())
            elif ch.isdigit():
                self.tokens.append(self.read_number())
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier_or_keyword())
            elif ch in "+-*/%<>=!":
                tok = self.read_operator()
                if tok:
                    self.tokens.append(tok)
                else:
                    self.error(ch)
            elif ch in "(){}[]:,;":
                self.tokens.append(Token(TokenType.PUNCTUATION, ch, self.line, self.column))
                self.advance()
            else:
                self.error(ch)

        self.tokens.append(Token(TokenType.EOF, "EOF", self.line, self.column))
        return self.tokens

    def display_tokens(self):
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║                   HASIL LEXER / TOKEN                   ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"  {'No':<4} {'Tipe':<14} {'Nilai':<20} {'Baris:Kolom'}")
        print("  " + "─"*55)
        for i, tok in enumerate(self.tokens, 1):
            if tok.type == TokenType.EOF:
                break
            print(f"  {i:<4} {tok.type:<14} {repr(tok.value):<20} {tok.line}:{tok.column}")
        print(f"\n  Total token: {len(self.tokens) - 1}")
        print("╚══════════════════════════════════════════════════════════╝\n")


if __name__ == "__main__":
    sample = """
// Program pertama dalam BatakScript
adong nama : hata gabe "Batak Toba"
adong umur : angka gabe 25

karejo horas(x) {
    molo (x > 0) {
        patuduhon("Horas! " + nama)
    } ndang {
        patuduhon("Ndang horas")
    }
    mulak x * 2
}

sahat (umur < 30) {
    umur gabe umur + 1
}
"""
    print("=== SOURCE CODE ===")
    print(sample)
    lexer  = Lexer(sample)
    tokens = lexer.tokenize()
    lexer.display_tokens()

    from collections import Counter
    counts = Counter(t.type for t in tokens if t.type != TokenType.EOF)
    print("--- Ringkasan Tipe Token ---")
    for ttype, cnt in counts.most_common():
        print(f"  {ttype:<14} : {cnt} token")
