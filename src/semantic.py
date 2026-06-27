"""
=============================================================
  BATAK COMPILER - SEMANTIC ANALYSIS
  Pemeriksaan tipe, scope, variabel tidak terdefinisi, dll
=============================================================
"""

from ast_nodes import *
from language_design import SymbolTable, BUILTIN_FUNCTIONS
from typing import List


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    """
    Melakukan analisis semantik pada AST:
    - Cek variabel dideklarasikan sebelum dipakai
    - Cek tipe data (type checking dasar)
    - Cek fungsi ada sebelum dipanggil
    - Cek return ada di fungsi
    - Cek break/continue hanya di dalam loop
    """

    def __init__(self):
        self.global_scope   = SymbolTable()
        self.current_scope  = self.global_scope
        self.functions      = {}         # { name: FuncDecl }
        self.in_loop        = 0          # counter loop nesting
        self.in_function    = False
        self.errors: List[str] = []

    def error(self, msg: str):
        self.errors.append(f"[SemanticError] {msg}")

    def warn(self, msg: str):
        print(f"  ⚠ [Warning] {msg}")

    def enter_scope(self):
        self.current_scope = SymbolTable(parent=self.current_scope)

    def exit_scope(self):
        self.current_scope = self.current_scope.parent

    # ─────────────────────────────────────────
    #  ENTRY POINT
    # ─────────────────────────────────────────
    def analyze(self, node: ASTNode):
        self.visit(node)
        return self.errors

    def visit(self, node: ASTNode):
        method = getattr(self, f"visit_{type(node).__name__}", self.generic_visit)
        return method(node)

    def generic_visit(self, node: ASTNode):
        pass

    # ─────────────────────────────────────────
    #  VISITORS
    # ─────────────────────────────────────────
    def visit_Program(self, node: Program):
        # Pass 1: daftarkan semua fungsi dulu
        for stmt in node.statements:
            if isinstance(stmt, FuncDecl):
                self.functions[stmt.name] = stmt
        # Pass 2: analisis semua statement
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDecl(self, node: VarDecl):
        if self.current_scope.exists(node.name) and node.name in self.current_scope.symbols:
            self.error(f"Variabel '{node.name}' sudah dideklarasikan di scope ini.")
            return
        inferred_type = node.dtype
        if node.init:
            init_type = self.visit(node.init)
            if init_type and not self._types_compatible(node.dtype, init_type):
                self.warn(f"Tipe '{init_type}' mungkin tidak cocok dengan deklarasi '{node.dtype}' untuk variabel '{node.name}'")
        self.current_scope.declare(node.name, inferred_type)

    def visit_Assign(self, node: Assign):
        if not self.current_scope.exists(node.name):
            self.error(f"Variabel '{node.name}' belum dideklarasikan.")
        val_type = self.visit(node.value)
        return val_type

    def visit_IfStmt(self, node: IfStmt):
        self.visit(node.condition)
        self.enter_scope()
        for stmt in node.then_body:
            self.visit(stmt)
        self.exit_scope()
        for cond, body in node.elif_clauses:
            self.visit(cond)
            self.enter_scope()
            for stmt in body:
                self.visit(stmt)
            self.exit_scope()
        if node.else_body:
            self.enter_scope()
            for stmt in node.else_body:
                self.visit(stmt)
            self.exit_scope()

    def visit_WhileStmt(self, node: WhileStmt):
        self.visit(node.condition)
        self.in_loop += 1
        self.enter_scope()
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()
        self.in_loop -= 1

    def visit_ForStmt(self, node: ForStmt):
        self.visit(node.iterable)
        self.in_loop += 1
        self.enter_scope()
        # variabel loop otomatis terdefinisi
        self.current_scope.declare(node.var, "angka")
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()
        self.in_loop -= 1

    def visit_FuncDecl(self, node: FuncDecl):
        self.enter_scope()
        prev_in_func = self.in_function
        self.in_function = True
        for param in node.params:
            self.current_scope.declare(param, "any")
        for stmt in node.body:
            self.visit(stmt)
        self.in_function = prev_in_func
        self.exit_scope()

    def visit_ReturnStmt(self, node: ReturnStmt):
        if not self.in_function:
            self.error("'mulak' (return) digunakan di luar fungsi.")
        if node.value:
            return self.visit(node.value)

    def visit_PrintStmt(self, node: PrintStmt):
        self.visit(node.value)

    def visit_BreakStmt(self, node: BreakStmt):
        if self.in_loop == 0:
            self.error("'tamat' (break) digunakan di luar loop.")

    def visit_ContinueStmt(self, node: ContinueStmt):
        if self.in_loop == 0:
            self.error("'lanjut' (continue) digunakan di luar loop.")

    def visit_BinOp(self, node: BinOp) -> str:
        left_type  = self.visit(node.left)
        right_type = self.visit(node.right)
        if node.op in ("+", "-", "*", "/", "%"):
            if left_type == "hata" or right_type == "hata":
                if node.op == "+":
                    return "hata"   # concatenation
                else:
                    self.error(f"Operator '{node.op}' tidak bisa digunakan pada string.")
            return "angka"
        if node.op in ("<", ">", "<=", ">=", "==", "!="):
            return "denggan"
        if node.op in ("dohot", "manang"):
            return "denggan"
        return "any"

    def visit_UnOp(self, node: UnOp) -> str:
        t = self.visit(node.operand)
        if node.op == "-":
            return "angka"
        if node.op == "ndang_be":
            return "denggan"
        return t

    def visit_Literal(self, node: Literal) -> str:
        type_map = {"int": "angka", "float": "angka", "str": "hata", "bool": "denggan"}
        return type_map.get(node.ltype, "any")

    def visit_Identifier(self, node: Identifier) -> str:
        if not self.current_scope.exists(node.name):
            self.error(f"Variabel '{node.name}' digunakan sebelum dideklarasikan.")
            return "any"
        info = self.current_scope.get(node.name)
        return info["type"]

    def visit_FuncCall(self, node: FuncCall) -> str:
        if node.name not in self.functions:
            self.error(f"Fungsi '{node.name}' dipanggil tapi tidak dideklarasikan.")
            return "any"
        func = self.functions[node.name]
        if len(node.args) != len(func.params):
            self.error(
                f"Fungsi '{node.name}' membutuhkan {len(func.params)} argumen, "
                f"tapi diberikan {len(node.args)}."
            )
        for arg in node.args:
            self.visit(arg)
        return "any"

    def visit_BuiltinCall(self, node: BuiltinCall) -> str:
        for arg in node.args:
            self.visit(arg)
        return_types = {
            "patuduhon": "any",
            "lehon":     "hata",
            "sian":      "angka",
            "gabehon":   "hata",
            "angkahon":  "angka",
            "dapothon":  "angka",
        }
        return return_types.get(node.name, "any")

    # ─────────────────────────────────────────
    def _types_compatible(self, declared: str, inferred: str) -> bool:
        if declared == "any" or inferred == "any":
            return True
        return declared == inferred

    def display_result(self):
        print("\n╔══════════════════════════════════════════════╗")
        print("║           HASIL SEMANTIC ANALYSIS            ║")
        print("╠══════════════════════════════════════════════╣")
        if not self.errors:
            print("  ✅ Tidak ada error semantik ditemukan!")
        else:
            for err in self.errors:
                print(f"  ❌ {err}")
        print(f"\n  Simbol di global scope:")
        for name, info in self.global_scope.symbols.items():
            print(f"    {name:<15} : {info['type']}")
        print("╚══════════════════════════════════════════════╝\n")


if __name__ == "__main__":
    from lexer   import Lexer
    from parser  import Parser

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

    analyzer = SemanticAnalyzer()
    errors   = analyzer.analyze(ast)
    analyzer.display_result()
