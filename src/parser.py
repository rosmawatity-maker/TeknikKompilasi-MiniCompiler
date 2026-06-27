"""
=============================================================
  BATAK COMPILER - PARSER
  Mengecek urutan token dan menghasilkan Parse Tree
=============================================================
"""

from lexer import Lexer, Token, TokenType
from language_design import KEYWORDS, BUILTIN_FUNCTIONS
from typing import List, Optional, Any


class ParseNode:
    def __init__(self, node_type: str, value: Any = None, children: List = None):
        self.node_type = node_type
        self.value     = value
        self.children  = children or []

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):
        return f"ParseNode({self.node_type}, {self.value})"

    def display(self, indent=0, prefix=""):
        connector = "├── " if prefix == "├" else "└── " if prefix == "└" else ""
        val_str   = f" [{self.value}]" if self.value is not None else ""
        print("    " * indent + connector + f"{self.node_type}{val_str}")
        for i, child in enumerate(self.children):
            is_last = (i == len(self.children) - 1)
            child.display(indent + 1, "└" if is_last else "├")


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos    = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek_next(self) -> Token:
        idx = self.pos + 1
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, ttype: str, value: str = None) -> Token:
        tok = self.current()
        if tok.type != ttype:
            raise SyntaxError(
                f"[Parser] Diharapkan tipe '{ttype}' tapi dapat '{tok.type}' "
                f"('{tok.value}') di baris {tok.line}:{tok.column}"
            )
        if value and tok.value != value:
            raise SyntaxError(
                f"[Parser] Diharapkan '{value}' tapi dapat '{tok.value}' "
                f"di baris {tok.line}:{tok.column}"
            )
        return self.advance()

    def match(self, ttype: str, value: str = None) -> bool:
        tok = self.current()
        if tok.type != ttype:
            return False
        if value and tok.value != value:
            return False
        return True

    def parse(self) -> ParseNode:
        root = ParseNode("PROGRAM")
        while not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                root.add_child(stmt)
        return root

    def parse_statement(self) -> Optional[ParseNode]:
        tok = self.current()
        if tok.type == TokenType.EOF:
            return None
        if tok.type == TokenType.KEYWORD and tok.value == "adong":
            return self.parse_var_decl()
        if tok.type == TokenType.KEYWORD and tok.value == "molo":
            return self.parse_if()
        if tok.type == TokenType.KEYWORD and tok.value == "sahat":
            return self.parse_while()
        if tok.type == TokenType.KEYWORD and tok.value == "hali":
            return self.parse_for()
        if tok.type == TokenType.KEYWORD and tok.value == "karejo":
            return self.parse_func_decl()
        if tok.type == TokenType.KEYWORD and tok.value == "mulak":
            return self.parse_return()
        if tok.type == TokenType.KEYWORD and tok.value == "patuduhon":
            return self.parse_print()
        if tok.type == TokenType.KEYWORD and tok.value == "tamat":
            self.advance()
            return ParseNode("BREAK")
        if tok.type == TokenType.KEYWORD and tok.value == "lanjut":
            self.advance()
            return ParseNode("CONTINUE")
        if tok.type == TokenType.IDENTIFIER:
            if self.peek_next().value == "gabe":
                return self.parse_assign()
            return self.parse_expr_stmt()
        if tok.type == TokenType.PUNCTUATION and tok.value == ";":
            self.advance()
            return None
        if tok.type == TokenType.PUNCTUATION and tok.value == "}":
            return None
        return self.parse_expr_stmt()

    def parse_var_decl(self) -> ParseNode:
        node = ParseNode("VAR_DECL")
        self.expect(TokenType.KEYWORD, "adong")
        name = self.expect(TokenType.IDENTIFIER)
        node.add_child(ParseNode("NAME", name.value))
        self.expect(TokenType.PUNCTUATION, ":")
        dtype = self.expect(TokenType.KEYWORD)
        node.add_child(ParseNode("TYPE", dtype.value))
        if self.match(TokenType.KEYWORD, "gabe"):
            self.advance()
            node.add_child(ParseNode("INIT", children=[self.parse_expr()]))
        return node

    def parse_assign(self) -> ParseNode:
        name = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.KEYWORD, "gabe")
        expr = self.parse_expr()
        node = ParseNode("ASSIGN")
        node.add_child(ParseNode("NAME", name.value))
        node.add_child(expr)
        return node

    def parse_if(self) -> ParseNode:
        node = ParseNode("IF")
        self.expect(TokenType.KEYWORD, "molo")
        self.expect(TokenType.PUNCTUATION, "(")
        cond = self.parse_expr()
        self.expect(TokenType.PUNCTUATION, ")")
        node.add_child(ParseNode("CONDITION", children=[cond]))
        self.expect(TokenType.PUNCTUATION, "{")
        then_block = ParseNode("THEN")
        while not self.match(TokenType.PUNCTUATION, "}") and not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                then_block.add_child(stmt)
        self.expect(TokenType.PUNCTUATION, "}")
        node.add_child(then_block)
        while self.match(TokenType.KEYWORD, "nunga"):
            self.advance()
            self.expect(TokenType.PUNCTUATION, "(")
            elif_cond = self.parse_expr()
            self.expect(TokenType.PUNCTUATION, ")")
            elif_block = ParseNode("ELIF")
            elif_block.add_child(ParseNode("CONDITION", children=[elif_cond]))
            self.expect(TokenType.PUNCTUATION, "{")
            while not self.match(TokenType.PUNCTUATION, "}") and not self.match(TokenType.EOF):
                stmt = self.parse_statement()
                if stmt:
                    elif_block.add_child(stmt)
            self.expect(TokenType.PUNCTUATION, "}")
            node.add_child(elif_block)
        if self.match(TokenType.KEYWORD, "ndang"):
            self.advance()
            if self.match(TokenType.PUNCTUATION, "{"):
                self.expect(TokenType.PUNCTUATION, "{")
                else_block = ParseNode("ELSE")
                while not self.match(TokenType.PUNCTUATION, "}") and not self.match(TokenType.EOF):
                    stmt = self.parse_statement()
                    if stmt:
                        else_block.add_child(stmt)
                self.expect(TokenType.PUNCTUATION, "}")
                node.add_child(else_block)
        return node

    def parse_while(self) -> ParseNode:
        node = ParseNode("WHILE")
        self.expect(TokenType.KEYWORD, "sahat")
        self.expect(TokenType.PUNCTUATION, "(")
        cond = self.parse_expr()
        self.expect(TokenType.PUNCTUATION, ")")
        node.add_child(ParseNode("CONDITION", children=[cond]))
        self.expect(TokenType.PUNCTUATION, "{")
        body = ParseNode("BODY")
        while not self.match(TokenType.PUNCTUATION, "}") and not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                body.add_child(stmt)
        self.expect(TokenType.PUNCTUATION, "}")
        node.add_child(body)
        return node

    def parse_for(self) -> ParseNode:
        node = ParseNode("FOR")
        self.expect(TokenType.KEYWORD, "hali")
        var = self.expect(TokenType.IDENTIFIER)
        node.add_child(ParseNode("VAR", var.value))
        self.expect(TokenType.KEYWORD, "di")
        iterable = self.parse_expr()
        node.add_child(ParseNode("ITERABLE", children=[iterable]))
        self.expect(TokenType.PUNCTUATION, "{")
        body = ParseNode("BODY")
        while not self.match(TokenType.PUNCTUATION, "}") and not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                body.add_child(stmt)
        self.expect(TokenType.PUNCTUATION, "}")
        node.add_child(body)
        return node

    def parse_func_decl(self) -> ParseNode:
        node = ParseNode("FUNC_DECL")
        self.expect(TokenType.KEYWORD, "karejo")
        name = self.expect(TokenType.IDENTIFIER)
        node.add_child(ParseNode("NAME", name.value))
        self.expect(TokenType.PUNCTUATION, "(")
        params = ParseNode("PARAMS")
        while not self.match(TokenType.PUNCTUATION, ")") and not self.match(TokenType.EOF):
            param = self.expect(TokenType.IDENTIFIER)
            params.add_child(ParseNode("PARAM", param.value))
            if self.match(TokenType.PUNCTUATION, ","):
                self.advance()
        self.expect(TokenType.PUNCTUATION, ")")
        node.add_child(params)
        self.expect(TokenType.PUNCTUATION, "{")
        body = ParseNode("BODY")
        while not self.match(TokenType.PUNCTUATION, "}") and not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                body.add_child(stmt)
        self.expect(TokenType.PUNCTUATION, "}")
        node.add_child(body)
        return node

    def parse_return(self) -> ParseNode:
        self.expect(TokenType.KEYWORD, "mulak")
        node = ParseNode("RETURN")
        if not self.match(TokenType.PUNCTUATION, "}") and not self.match(TokenType.EOF):
            node.add_child(self.parse_expr())
        return node

    def parse_print(self) -> ParseNode:
        self.expect(TokenType.KEYWORD, "patuduhon")
        self.expect(TokenType.PUNCTUATION, "(")
        node = ParseNode("PRINT")
        node.add_child(self.parse_expr())
        self.expect(TokenType.PUNCTUATION, ")")
        return node

    def parse_expr_stmt(self) -> ParseNode:
        expr = self.parse_expr()
        return ParseNode("EXPR_STMT", children=[expr])

    def parse_expr(self) -> ParseNode:
        return self.parse_or()

    def parse_or(self) -> ParseNode:
        left = self.parse_and()
        while self.match(TokenType.KEYWORD, "manang"):
            op = self.advance()
            right = self.parse_and()
            node = ParseNode("BINOP", op.value)
            node.add_child(left); node.add_child(right)
            left = node
        return left

    def parse_and(self) -> ParseNode:
        left = self.parse_not()
        while self.match(TokenType.KEYWORD, "dohot"):
            op = self.advance()
            right = self.parse_not()
            node = ParseNode("BINOP", op.value)
            node.add_child(left); node.add_child(right)
            left = node
        return left

    def parse_not(self) -> ParseNode:
        if self.match(TokenType.KEYWORD, "ndang_be"):
            self.advance()
            node = ParseNode("UNOP", "ndang_be")
            node.add_child(self.parse_not())
            return node
        return self.parse_compare()

    def parse_compare(self) -> ParseNode:
        left = self.parse_add()
        cmp_ops = ["<", ">", "<=", ">=", "==", "!="]
        while self.match(TokenType.OPERATOR) and self.current().value in cmp_ops:
            op = self.advance()
            right = self.parse_add()
            node = ParseNode("BINOP", op.value)
            node.add_child(left); node.add_child(right)
            left = node
        return left

    def parse_add(self) -> ParseNode:
        left = self.parse_mul()
        while self.match(TokenType.OPERATOR) and self.current().value in ("+", "-"):
            op = self.advance()
            right = self.parse_mul()
            node = ParseNode("BINOP", op.value)
            node.add_child(left); node.add_child(right)
            left = node
        return left

    def parse_mul(self) -> ParseNode:
        left = self.parse_unary()
        while self.match(TokenType.OPERATOR) and self.current().value in ("*", "/", "%"):
            op = self.advance()
            right = self.parse_unary()
            node = ParseNode("BINOP", op.value)
            node.add_child(left); node.add_child(right)
            left = node
        return left

    def parse_unary(self) -> ParseNode:
        if self.match(TokenType.OPERATOR, "-"):
            op = self.advance()
            node = ParseNode("UNOP", "-")
            node.add_child(self.parse_primary())
            return node
        return self.parse_primary()

    def parse_primary(self) -> ParseNode:
        tok = self.current()
        if tok.type == TokenType.INTEGER:
            self.advance()
            return ParseNode("INT_LITERAL", int(tok.value))
        if tok.type == TokenType.FLOAT:
            self.advance()
            return ParseNode("FLOAT_LITERAL", float(tok.value))
        if tok.type == TokenType.STRING:
            self.advance()
            return ParseNode("STR_LITERAL", tok.value)
        if tok.type == TokenType.KEYWORD and tok.value in ("ture", "sala"):
            self.advance()
            return ParseNode("BOOL_LITERAL", tok.value == "ture")
        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            if self.match(TokenType.PUNCTUATION, "("):
                self.advance()
                node = ParseNode("FUNC_CALL", tok.value)
                while not self.match(TokenType.PUNCTUATION, ")") and not self.match(TokenType.EOF):
                    node.add_child(self.parse_expr())
                    if self.match(TokenType.PUNCTUATION, ","):
                        self.advance()
                self.expect(TokenType.PUNCTUATION, ")")
                return node
            return ParseNode("IDENTIFIER", tok.value)
        if tok.type == TokenType.KEYWORD and tok.value in BUILTIN_FUNCTIONS:
            self.advance()
            if self.match(TokenType.PUNCTUATION, "("):
                self.advance()
                node = ParseNode("BUILTIN_CALL", tok.value)
                while not self.match(TokenType.PUNCTUATION, ")") and not self.match(TokenType.EOF):
                    node.add_child(self.parse_expr())
                    if self.match(TokenType.PUNCTUATION, ","):
                        self.advance()
                self.expect(TokenType.PUNCTUATION, ")")
                return node
        if tok.type == TokenType.PUNCTUATION and tok.value == "(":
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.PUNCTUATION, ")")
            return expr
        raise SyntaxError(
            f"[Parser] Token tak terduga '{tok.value}' ({tok.type}) "
            f"di baris {tok.line}:{tok.column}"
        )


if __name__ == "__main__":
    sample = """
adong nama : hata gabe "Batak Toba"
adong umur : angka gabe 25

karejo horas(x) {
    molo (x > 0) {
        patuduhon("Horas! ")
    } ndang {
        patuduhon("Ndang horas")
    }
    mulak x * 2
}

sahat (umur < 30) {
    umur gabe umur + 1
}
"""
    lexer  = Lexer(sample)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    tree   = parser.parse()
    print("=== PARSE TREE ===")
    tree.display()
