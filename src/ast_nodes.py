"""
=============================================================
  BATAK COMPILER - AST (Abstract Syntax Tree)
  AST dibuat berdasarkan Parse Tree, membuang node-node
  yang tidak diperlukan untuk proses semantik & code gen
=============================================================
"""

from parser import Parser, ParseNode
from lexer  import Lexer
from typing import Any, List, Optional


# ─────────────────────────────────────────────
#  AST NODE CLASSES
# ─────────────────────────────────────────────
class ASTNode:
    """Base class untuk semua node AST."""
    def display(self, indent=0):
        raise NotImplementedError

    def _indent(self, n):
        return "  " * n


class Program(ASTNode):
    def __init__(self, statements: List):
        self.statements = statements

    def display(self, indent=0):
        print(self._indent(indent) + "Program")
        for stmt in self.statements:
            stmt.display(indent + 1)


class VarDecl(ASTNode):
    def __init__(self, name: str, dtype: str, init=None):
        self.name  = name
        self.dtype = dtype
        self.init  = init

    def display(self, indent=0):
        print(self._indent(indent) + f"VarDecl: {self.name} : {self.dtype}")
        if self.init:
            self.init.display(indent + 1)


class Assign(ASTNode):
    def __init__(self, name: str, value):
        self.name  = name
        self.value = value

    def display(self, indent=0):
        print(self._indent(indent) + f"Assign: {self.name} =")
        self.value.display(indent + 1)


class IfStmt(ASTNode):
    def __init__(self, condition, then_body, elif_clauses: List, else_body):
        self.condition     = condition
        self.then_body     = then_body
        self.elif_clauses  = elif_clauses  # list of (cond, body)
        self.else_body     = else_body

    def display(self, indent=0):
        print(self._indent(indent) + "If:")
        print(self._indent(indent+1) + "Condition:")
        self.condition.display(indent + 2)
        print(self._indent(indent+1) + "Then:")
        for stmt in self.then_body:
            stmt.display(indent + 2)
        for cond, body in self.elif_clauses:
            print(self._indent(indent+1) + "Elif:")
            cond.display(indent + 2)
            for stmt in body:
                stmt.display(indent + 2)
        if self.else_body:
            print(self._indent(indent+1) + "Else:")
            for stmt in self.else_body:
                stmt.display(indent + 2)


class WhileStmt(ASTNode):
    def __init__(self, condition, body: List):
        self.condition = condition
        self.body      = body

    def display(self, indent=0):
        print(self._indent(indent) + "While:")
        self.condition.display(indent + 1)
        for stmt in self.body:
            stmt.display(indent + 1)


class ForStmt(ASTNode):
    def __init__(self, var: str, iterable, body: List):
        self.var      = var
        self.iterable = iterable
        self.body     = body

    def display(self, indent=0):
        print(self._indent(indent) + f"For: {self.var} di")
        self.iterable.display(indent + 1)
        for stmt in self.body:
            stmt.display(indent + 1)


class FuncDecl(ASTNode):
    def __init__(self, name: str, params: List[str], body: List):
        self.name   = name
        self.params = params
        self.body   = body

    def display(self, indent=0):
        print(self._indent(indent) + f"FuncDecl: {self.name}({', '.join(self.params)})")
        for stmt in self.body:
            stmt.display(indent + 1)


class ReturnStmt(ASTNode):
    def __init__(self, value=None):
        self.value = value

    def display(self, indent=0):
        print(self._indent(indent) + "Return:")
        if self.value:
            self.value.display(indent + 1)


class PrintStmt(ASTNode):
    def __init__(self, value):
        self.value = value

    def display(self, indent=0):
        print(self._indent(indent) + "Print:")
        self.value.display(indent + 1)


class BreakStmt(ASTNode):
    def display(self, indent=0):
        print(self._indent(indent) + "Break")


class ContinueStmt(ASTNode):
    def display(self, indent=0):
        print(self._indent(indent) + "Continue")


# ─── Ekspresi ────────────────────────────────
class BinOp(ASTNode):
    def __init__(self, op: str, left, right):
        self.op    = op
        self.left  = left
        self.right = right

    def display(self, indent=0):
        print(self._indent(indent) + f"BinOp: {self.op}")
        self.left.display(indent + 1)
        self.right.display(indent + 1)


class UnOp(ASTNode):
    def __init__(self, op: str, operand):
        self.op      = op
        self.operand = operand

    def display(self, indent=0):
        print(self._indent(indent) + f"UnOp: {self.op}")
        self.operand.display(indent + 1)


class Literal(ASTNode):
    def __init__(self, value: Any, ltype: str):
        self.value = value
        self.ltype = ltype

    def display(self, indent=0):
        print(self._indent(indent) + f"Literal({self.ltype}): {self.value}")


class Identifier(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def display(self, indent=0):
        print(self._indent(indent) + f"Identifier: {self.name}")


class FuncCall(ASTNode):
    def __init__(self, name: str, args: List):
        self.name = name
        self.args = args

    def display(self, indent=0):
        print(self._indent(indent) + f"FuncCall: {self.name}()")
        for arg in self.args:
            arg.display(indent + 1)


class BuiltinCall(ASTNode):
    def __init__(self, name: str, args: List):
        self.name = name
        self.args = args

    def display(self, indent=0):
        print(self._indent(indent) + f"BuiltinCall: {self.name}()")
        for arg in self.args:
            arg.display(indent + 1)


# ─────────────────────────────────────────────
#  AST BUILDER  (ParseNode → ASTNode)
# ─────────────────────────────────────────────
class ASTBuilder:
    def build(self, parse_node: ParseNode) -> ASTNode:
        method = getattr(self, f"build_{parse_node.node_type}", self.generic_build)
        return method(parse_node)

    def generic_build(self, node: ParseNode):
        raise ValueError(f"[ASTBuilder] Node tidak dikenal: {node.node_type}")

    def build_PROGRAM(self, node: ParseNode) -> Program:
        stmts = [self.build(c) for c in node.children]
        return Program(stmts)

    def build_VAR_DECL(self, node: ParseNode) -> VarDecl:
        name  = node.children[0].value
        dtype = node.children[1].value
        init  = self.build(node.children[2].children[0]) if len(node.children) > 2 else None
        return VarDecl(name, dtype, init)

    def build_ASSIGN(self, node: ParseNode) -> Assign:
        name  = node.children[0].value
        value = self.build(node.children[1])
        return Assign(name, value)

    def build_IF(self, node: ParseNode) -> IfStmt:
        cond      = self.build(node.children[0].children[0])
        then_body = [self.build(c) for c in node.children[1].children]
        elif_clauses = []
        else_body    = None

        for child in node.children[2:]:
            if child.node_type == "ELIF":
                ec   = self.build(child.children[0].children[0])
                eb   = [self.build(c) for c in child.children[1:]]
                elif_clauses.append((ec, eb))
            elif child.node_type == "ELSE":
                else_body = [self.build(c) for c in child.children]

        return IfStmt(cond, then_body, elif_clauses, else_body)

    def build_WHILE(self, node: ParseNode) -> WhileStmt:
        cond = self.build(node.children[0].children[0])
        body = [self.build(c) for c in node.children[1].children]
        return WhileStmt(cond, body)

    def build_FOR(self, node: ParseNode) -> ForStmt:
        var      = node.children[0].value
        iterable = self.build(node.children[1].children[0])
        body     = [self.build(c) for c in node.children[2].children]
        return ForStmt(var, iterable, body)

    def build_FUNC_DECL(self, node: ParseNode) -> FuncDecl:
        name   = node.children[0].value
        params = [p.value for p in node.children[1].children]
        body   = [self.build(c) for c in node.children[2].children]
        return FuncDecl(name, params, body)

    def build_RETURN(self, node: ParseNode) -> ReturnStmt:
        val = self.build(node.children[0]) if node.children else None
        return ReturnStmt(val)

    def build_PRINT(self, node: ParseNode) -> PrintStmt:
        return PrintStmt(self.build(node.children[0]))

    def build_BREAK(self, node: ParseNode) -> BreakStmt:
        return BreakStmt()

    def build_CONTINUE(self, node: ParseNode) -> ContinueStmt:
        return ContinueStmt()

    def build_EXPR_STMT(self, node: ParseNode):
        return self.build(node.children[0])

    def build_BINOP(self, node: ParseNode) -> BinOp:
        return BinOp(node.value, self.build(node.children[0]), self.build(node.children[1]))

    def build_UNOP(self, node: ParseNode) -> UnOp:
        return UnOp(node.value, self.build(node.children[0]))

    def build_INT_LITERAL(self, node: ParseNode) -> Literal:
        return Literal(node.value, "int")

    def build_FLOAT_LITERAL(self, node: ParseNode) -> Literal:
        return Literal(node.value, "float")

    def build_STR_LITERAL(self, node: ParseNode) -> Literal:
        return Literal(node.value, "str")

    def build_BOOL_LITERAL(self, node: ParseNode) -> Literal:
        return Literal(node.value, "bool")

    def build_IDENTIFIER(self, node: ParseNode) -> Identifier:
        return Identifier(node.value)

    def build_FUNC_CALL(self, node: ParseNode) -> FuncCall:
        args = [self.build(c) for c in node.children]
        return FuncCall(node.value, args)

    def build_BUILTIN_CALL(self, node: ParseNode) -> BuiltinCall:
        args = [self.build(c) for c in node.children]
        return BuiltinCall(node.value, args)


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
    lexer   = Lexer(sample)
    tokens  = lexer.tokenize()
    parser  = Parser(tokens)
    ptree   = parser.parse()

    builder = ASTBuilder()
    ast     = builder.build(ptree)

    print("=== ABSTRACT SYNTAX TREE (AST) ===\n")
    ast.display()
