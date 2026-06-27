"""
=============================================================
  BATAK COMPILER - CODE GENERATOR
  Menghasilkan Python code dari AST BatakScript
=============================================================
"""

from ast_nodes import *
from language_design import BUILTIN_FUNCTIONS
from typing import List


class CodeGenerator:
    def __init__(self):
        self.output  : List[str] = []
        self.indent  : int       = 0
        self.func_names = set()

    def emit(self, line: str = ""):
        self.output.append("    " * self.indent + line)

    def generate(self, node: ASTNode) -> str:
        method = getattr(self, f"gen_{type(node).__name__}", self.generic_gen)
        return method(node)

    def generic_gen(self, node: ASTNode) -> str:
        return ""

    # ─────────────────────────────────────────
    #  TOP LEVEL
    # ─────────────────────────────────────────
    def gen_Program(self, node: Program) -> str:
        self.emit("# ============================================")
        self.emit("# Kode dihasilkan oleh BatakScript Compiler")
        self.emit("# Bahasa: Batak Toba → Python")
        self.emit("# ============================================")
        self.emit()
        # Kumpulkan semua fungsi dulu
        for stmt in node.statements:
            if isinstance(stmt, FuncDecl):
                self.func_names.add(stmt.name)
        # Generate semua
        for stmt in node.statements:
            self.generate(stmt)
        return "\n".join(self.output)

    # ─────────────────────────────────────────
    #  STATEMENT
    # ─────────────────────────────────────────
    def gen_VarDecl(self, node: VarDecl):
        if node.init:
            val = self.expr(node.init)
            self.emit(f"{node.name} = {val}")
        else:
            defaults = {"angka": "0", "hata": '""', "denggan": "False"}
            self.emit(f"{node.name} = {defaults.get(node.dtype, 'None')}")

    def gen_Assign(self, node: Assign):
        val = self.expr(node.value)
        self.emit(f"{node.name} = {val}")

    def gen_IfStmt(self, node: IfStmt):
        cond = self.expr(node.condition)
        self.emit(f"if {cond}:")
        self.indent += 1
        for stmt in node.then_body:
            self.generate(stmt)
        if not node.then_body:
            self.emit("pass")
        self.indent -= 1
        for cond_e, body in node.elif_clauses:
            self.emit(f"elif {self.expr(cond_e)}:")
            self.indent += 1
            for stmt in body:
                self.generate(stmt)
            if not body:
                self.emit("pass")
            self.indent -= 1
        if node.else_body:
            self.emit("else:")
            self.indent += 1
            for stmt in node.else_body:
                self.generate(stmt)
            if not node.else_body:
                self.emit("pass")
            self.indent -= 1

    def gen_WhileStmt(self, node: WhileStmt):
        cond = self.expr(node.condition)
        self.emit(f"while {cond}:")
        self.indent += 1
        for stmt in node.body:
            self.generate(stmt)
        if not node.body:
            self.emit("pass")
        self.indent -= 1

    def gen_ForStmt(self, node: ForStmt):
        iterable = self.expr(node.iterable)
        self.emit(f"for {node.var} in {iterable}:")
        self.indent += 1
        for stmt in node.body:
            self.generate(stmt)
        if not node.body:
            self.emit("pass")
        self.indent -= 1

    def gen_FuncDecl(self, node: FuncDecl):
        params = ", ".join(node.params)
        self.emit()
        self.emit(f"def {node.name}({params}):")
        self.indent += 1
        for stmt in node.body:
            self.generate(stmt)
        if not node.body:
            self.emit("pass")
        self.indent -= 1
        self.emit()

    def gen_ReturnStmt(self, node: ReturnStmt):
        if node.value:
            self.emit(f"return {self.expr(node.value)}")
        else:
            self.emit("return")

    def gen_PrintStmt(self, node: PrintStmt):
        val = self.expr(node.value)
        self.emit(f"print({val})")

    def gen_BreakStmt(self, node):
        self.emit("break")

    def gen_ContinueStmt(self, node):
        self.emit("continue")

    # Handle Program node dari dead code elimination
    def gen_Program_inline(self, node):
        for stmt in node.statements:
            self.generate(stmt)

    # ─────────────────────────────────────────
    #  EKSPRESI
    # ─────────────────────────────────────────
    def expr(self, node: ASTNode) -> str:
        method = getattr(self, f"expr_{type(node).__name__}", None)
        if method:
            return method(node)
        # Fallback: coba generate sebagai statement
        return ""

    def expr_Literal(self, node: Literal) -> str:
        if node.ltype == "str":
            return repr(node.value)
        if node.ltype == "bool":
            return "True" if node.value else "False"
        return str(node.value)

    def expr_Identifier(self, node: Identifier) -> str:
        return node.name

    def expr_BinOp(self, node: BinOp) -> str:
        op_map = {"dohot": "and", "manang": "or"}
        op = op_map.get(node.op, node.op)
        left  = self.expr(node.left)
        right = self.expr(node.right)
        return f"({left} {op} {right})"

    def expr_UnOp(self, node: UnOp) -> str:
        op_map = {"ndang_be": "not "}
        op = op_map.get(node.op, node.op)
        return f"({op}{self.expr(node.operand)})"

    def expr_FuncCall(self, node: FuncCall) -> str:
        args = ", ".join(self.expr(a) for a in node.args)
        return f"{node.name}({args})"

    def expr_BuiltinCall(self, node: BuiltinCall) -> str:
        args = ", ".join(self.expr(a) for a in node.args)
        builtin_map = {
            "patuduhon": "print",
            "lehon":     "input",
            "pature":    "print",
            "sian":      "len",
            "gabehon":   "str",
            "angkahon":  "int",
            "dapothon":  "range",
            "torhon":    "print",
        }
        py_name = builtin_map.get(node.name, node.name)
        return f"{py_name}({args})"

    def display(self, code: str):
        print("\n╔══════════════════════════════════════════════╗")
        print("║          KODE PYTHON YANG DIHASILKAN         ║")
        print("╠══════════════════════════════════════════════╣")
        for i, line in enumerate(code.split("\n"), 1):
            print(f"  {i:>3} │ {line}")
        print("╚══════════════════════════════════════════════╝\n")


if __name__ == "__main__":
    from lexer      import Lexer
    from parser     import Parser
    from optimizer  import Optimizer

    sample = """
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

patuduhon(horas(5))
"""
    lexer    = Lexer(sample)
    tokens   = lexer.tokenize()
    parser   = Parser(tokens)
    ptree    = parser.parse()
    builder  = ASTBuilder()
    ast      = builder.build(ptree)
    optimizer = Optimizer()
    opt_ast  = optimizer.optimize(ast)

    codegen  = CodeGenerator()
    code     = codegen.generate(opt_ast)
    codegen.display(code)

    print("=== MENJALANKAN KODE ===")
    exec(code)
