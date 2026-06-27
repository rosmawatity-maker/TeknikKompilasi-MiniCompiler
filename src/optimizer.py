"""
=============================================================
  BATAK COMPILER - CODE OPTIMIZER
  Optimasi AST sebelum code generation:
  - Constant Folding  (ekspresi konstan dihitung compile-time)
  - Constant Propagation (nilai konstan disebarkan)
  - Dead Code Elimination (kode tidak terjangkau dihapus)
  - Algebraic Simplification (0+x=x, 1*x=x, dll)
=============================================================
"""

from ast_nodes import *
from typing import Any, Optional


class Optimizer:
    def __init__(self):
        self.constants = {}   # { var_name: value }  untuk const propagation
        self.stats     = {"folded": 0, "propagated": 0, "dead_eliminated": 0, "simplified": 0}

    def optimize(self, node: ASTNode) -> ASTNode:
        method = getattr(self, f"opt_{type(node).__name__}", self.generic_opt)
        return method(node)

    def generic_opt(self, node: ASTNode) -> ASTNode:
        return node

    # ─────────────────────────────────────────
    def opt_Program(self, node: Program) -> Program:
        new_stmts = []
        for stmt in node.statements:
            opt = self.optimize(stmt)
            if opt is not None:
                new_stmts.append(opt)
        return Program(new_stmts)

    def opt_VarDecl(self, node: VarDecl) -> VarDecl:
        if node.init:
            opt_init = self.optimize(node.init)
            # Jika inisialisasi adalah literal konstan, simpan untuk propagation
            if isinstance(opt_init, Literal):
                self.constants[node.name] = opt_init.value
            return VarDecl(node.name, node.dtype, opt_init)
        return node

    def opt_Assign(self, node: Assign) -> Assign:
        opt_val = self.optimize(node.value)
        if isinstance(opt_val, Literal):
            self.constants[node.name] = opt_val.value
        else:
            # Nilai berubah jadi bukan konstan lagi
            self.constants.pop(node.name, None)
        return Assign(node.name, opt_val)

    def opt_IfStmt(self, node: IfStmt):
        opt_cond = self.optimize(node.condition)

        # Dead code elimination: kondisi selalu True/False
        if isinstance(opt_cond, Literal) and node.dtype if hasattr(node, 'dtype') else False:
            pass

        if isinstance(opt_cond, Literal):
            if opt_cond.value is True:
                # Ambil hanya then_body
                self.stats["dead_eliminated"] += 1
                return Program([self.optimize(s) for s in node.then_body])
            elif opt_cond.value is False:
                self.stats["dead_eliminated"] += 1
                if node.else_body:
                    return Program([self.optimize(s) for s in node.else_body])
                return None

        then_body    = [self.optimize(s) for s in node.then_body]
        elif_clauses = [(self.optimize(c), [self.optimize(s) for s in b])
                        for c, b in node.elif_clauses]
        else_body    = [self.optimize(s) for s in node.else_body] if node.else_body else None
        return IfStmt(opt_cond, then_body, elif_clauses, else_body)

    def opt_WhileStmt(self, node: WhileStmt):
        opt_cond = self.optimize(node.condition)
        if isinstance(opt_cond, Literal) and opt_cond.value is False:
            self.stats["dead_eliminated"] += 1
            return None    # loop tidak pernah jalan
        # Di dalam loop, variabel bisa berubah - jangan propagasi dari luar
        saved = dict(self.constants)
        self.constants = {}
        body = [self.optimize(s) for s in node.body]
        self.constants = saved
        return WhileStmt(opt_cond, body)

    def opt_ForStmt(self, node: ForStmt) -> ForStmt:
        return ForStmt(node.var, self.optimize(node.iterable),
                       [self.optimize(s) for s in node.body])

    def opt_FuncDecl(self, node: FuncDecl) -> FuncDecl:
        # Buat scope bersih untuk fungsi - tidak ada propagasi konstan dari luar
        saved = dict(self.constants)
        self.constants = {}   # scope bersih
        body = [self.optimize(s) for s in node.body]
        self.constants = saved
        return FuncDecl(node.name, node.params, body)

    def opt_ReturnStmt(self, node: ReturnStmt) -> ReturnStmt:
        val = self.optimize(node.value) if node.value else None
        return ReturnStmt(val)

    def opt_PrintStmt(self, node: PrintStmt) -> PrintStmt:
        return PrintStmt(self.optimize(node.value))

    def opt_BreakStmt(self, node):    return node
    def opt_ContinueStmt(self, node): return node

    # ─────────────────────────────────────────
    #  EKSPRESI
    # ─────────────────────────────────────────
    def opt_BinOp(self, node: BinOp) -> ASTNode:
        left  = self.optimize(node.left)
        right = self.optimize(node.right)

        # ── Constant Folding ──────────────────
        if isinstance(left, Literal) and isinstance(right, Literal):
            result = self._fold(node.op, left.value, right.value)
            if result is not None:
                self.stats["folded"] += 1
                ltype = "bool" if isinstance(result, bool) else \
                        "float" if isinstance(result, float) else \
                        "str"   if isinstance(result, str)  else "int"
                return Literal(result, ltype)

        # ── Algebraic Simplification ──────────
        # x + 0 = x,  0 + x = x
        if node.op == "+":
            if isinstance(right, Literal) and right.value == 0:
                self.stats["simplified"] += 1; return left
            if isinstance(left, Literal) and left.value == 0:
                self.stats["simplified"] += 1; return right

        # x - 0 = x
        if node.op == "-" and isinstance(right, Literal) and right.value == 0:
            self.stats["simplified"] += 1; return left

        # x * 1 = x,  1 * x = x
        if node.op == "*":
            if isinstance(right, Literal) and right.value == 1:
                self.stats["simplified"] += 1; return left
            if isinstance(left, Literal) and left.value == 1:
                self.stats["simplified"] += 1; return right
            # x * 0 = 0
            if isinstance(right, Literal) and right.value == 0:
                self.stats["simplified"] += 1; return Literal(0, "int")
            if isinstance(left, Literal) and left.value == 0:
                self.stats["simplified"] += 1; return Literal(0, "int")

        # x / 1 = x
        if node.op == "/" and isinstance(right, Literal) and right.value == 1:
            self.stats["simplified"] += 1; return left

        return BinOp(node.op, left, right)

    def opt_UnOp(self, node: UnOp) -> ASTNode:
        operand = self.optimize(node.operand)
        if isinstance(operand, Literal):
            if node.op == "-" and isinstance(operand.value, (int, float)):
                self.stats["folded"] += 1
                return Literal(-operand.value, operand.ltype)
            if node.op == "ndang_be" and isinstance(operand.value, bool):
                self.stats["folded"] += 1
                return Literal(not operand.value, "bool")
        return UnOp(node.op, operand)

    def opt_Identifier(self, node: Identifier) -> ASTNode:
        # Constant Propagation
        if node.name in self.constants:
            val = self.constants[node.name]
            self.stats["propagated"] += 1
            ltype = "bool"  if isinstance(val, bool) else \
                    "float" if isinstance(val, float) else \
                    "str"   if isinstance(val, str)   else "int"
            return Literal(val, ltype)
        return node

    def opt_Literal(self, node: Literal) -> Literal:
        return node

    def opt_FuncCall(self, node: FuncCall) -> FuncCall:
        return FuncCall(node.name, [self.optimize(a) for a in node.args])

    def opt_BuiltinCall(self, node: BuiltinCall) -> BuiltinCall:
        return BuiltinCall(node.name, [self.optimize(a) for a in node.args])

    # ─────────────────────────────────────────
    def _fold(self, op: str, l: Any, r: Any) -> Optional[Any]:
        try:
            if op == "+":  return l + r
            if op == "-":  return l - r
            if op == "*":  return l * r
            if op == "/" and r != 0: return l / r
            if op == "%" and r != 0: return l % r
            if op == "**": return l ** r
            if op == "<":  return l < r
            if op == ">":  return l > r
            if op == "<=": return l <= r
            if op == ">=": return l >= r
            if op == "==": return l == r
            if op == "!=": return l != r
        except Exception:
            pass
        return None

    def display_stats(self):
        print("\n╔═════════════════════════════════════════╗")
        print("║         HASIL OPTIMASI KODE             ║")
        print("╠═════════════════════════════════════════╣")
        print(f"  Constant Folding      : {self.stats['folded']} optimasi")
        print(f"  Constant Propagation  : {self.stats['propagated']} optimasi")
        print(f"  Dead Code Eliminated  : {self.stats['dead_eliminated']} blok")
        print(f"  Algebraic Simplif.    : {self.stats['simplified']} optimasi")
        total = sum(self.stats.values())
        print(f"  ─────────────────────────────────────")
        print(f"  Total Optimasi        : {total}")
        print("╚═════════════════════════════════════════╝\n")


if __name__ == "__main__":
    from lexer    import Lexer
    from parser   import Parser
    from semantic import SemanticAnalyzer

    sample = """
adong a : angka gabe 10
adong b : angka gabe 20
adong c : angka gabe a + b
adong d : angka gabe c * 0
adong e : angka gabe 5 + 3 * 2

molo (ture) {
    patuduhon("Selalu dijalankan")
}

molo (sala) {
    patuduhon("Tidak pernah jalan - dead code")
}
"""
    lexer   = Lexer(sample)
    tokens  = lexer.tokenize()
    parser  = Parser(tokens)
    ptree   = parser.parse()
    builder = ASTBuilder()
    ast     = builder.build(ptree)

    optimizer = Optimizer()
    opt_ast   = optimizer.optimize(ast)
    optimizer.display_stats()
    print("=== AST SETELAH OPTIMASI ===")
    opt_ast.display()
