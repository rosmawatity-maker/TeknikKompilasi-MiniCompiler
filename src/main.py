"""
=============================================================
  BATAK COMPILER - MAIN ENTRY POINT
  Jalankan: python main.py <file.batak>
           python main.py --demo
=============================================================
"""

import sys
import os
import io
import contextlib

# Tambahkan src ke path
sys.path.insert(0, os.path.dirname(__file__))

from lexer      import Lexer, TokenType
from parser     import Parser
from ast_nodes  import ASTBuilder
from semantic   import SemanticAnalyzer
from optimizer  import Optimizer
from codegen    import CodeGenerator


BANNER = """
╔══════════════════════════════════════════════════════╗
║         BATAK SCRIPT COMPILER v1.0                   ║
║         Bahasa Daerah: Batak Toba                    ║
║         Teknik Kompilasi - Semester 6                ║
╚══════════════════════════════════════════════════════╝
"""

REPL_BANNER = """
╔══════════════════════════════════════════════════════╗
║         BATAKSCRIPT INTERACTIVE REPL v1.0            ║
╠══════════════════════════════════════════════════════╣
║  Contoh sintaks yang valid untuk dicoba:             ║
║                                                      ║
║  1. Fungsi Cetak  : patuduhon("Horas ma di hamu!")   ║
║  2. Variabel      : adong x : angka gabe 10          ║
║  3. Kondisi (if)  : molo (x > 5) { patuduhon(x) }    ║
║                                                      ║
║  Ketik 'keluar' atau 'exit' untuk ke menu utama.     ║
╚══════════════════════════════════════════════════════╝
"""

# Lebar kolom label fase agar rata
_LABEL_W = 12


def _fmt(label: str, value: str) -> str:
    """Format satu baris fase: '[Label]    : value'"""
    return f"  [{label}]{' ' * (_LABEL_W - len(label))}: {value}"


# ─────────────────────────────────────────────────────────────
#  HELPER: ekstrak token pairs (value, type_name)
# ─────────────────────────────────────────────────────────────
def _token_pairs(tokens) -> str:
    """
    Kembalikan string 'value: TYPE, value: TYPE, ...'
    Bekerja dengan Token yang punya atribut .value/.lexeme dan .type.
    """
    parts = []
    for tok in tokens:
        val = (
            getattr(tok, "value",   None) or
            getattr(tok, "lexeme",  None) or
            getattr(tok, "literal", None) or
            str(tok)
        )
        raw_type = str(getattr(tok, "type", "?"))
        type_name = raw_type.split(".")[-1]

        if isinstance(val, str) and " " not in val:
            display_val = val
        else:
            display_val = f'"{val}"' if isinstance(val, str) else str(val)

        parts.append(f"{display_val}: {type_name}")

    return ", ".join(parts)


# ─────────────────────────────────────────────────────────────
#  HELPER: ambil ringkasan AST (Ubah Objek Dalam Menjadi Teks)
# ─────────────────────────────────────────────────────────────
def _ast_summary(ast) -> str:
    """
    Mengubah representasi objek AST mentah dan sub-objek di dalamnya
    menjadi teks bersih yang mudah dipahami (Menghapus <object at ...>).
    """
    def clean_val(obj):
        if obj is None:
            return "None"
        r = repr(obj)
        if r.startswith("<") and "object at" in r:
            name = getattr(obj, "name", None) or getattr(obj, "id", None) or getattr(obj, "value", None) or getattr(obj, "lexeme", None)
            if name is not None:
                return f"{obj.__class__.__name__}({repr(name)})"
            
            left = getattr(obj, "left", None)
            op = getattr(obj, "op", None) or getattr(obj, "operator", None)
            right = getattr(obj, "right", None)
            if left is not None and op is not None:
                return f"BinOp({clean_val(left)} {clean_val(op)} {clean_val(right)})"
            return obj.__class__.__name__ + "()"
        return r

    nodes = getattr(ast, "statements", None) or getattr(ast, "body", None) or getattr(ast, "children", None)
    node = nodes[0] if (nodes and len(nodes) > 0) else ast
    node_name = node.__class__.__name__

    name = getattr(node, "name", None) or getattr(node, "id", None) or getattr(node, "variable", None) or getattr(node, "var_name", None)
    val = getattr(node, "value", None) or getattr(node, "expr", None) or getattr(node, "expression", None)
    type_node = getattr(node, "type", None) or getattr(node, "data_type", None) or getattr(node, "type_node", None)

    if "Print" in node_name or "patuduhon" in node_name.lower():
        return f"PrintStmt(value={clean_val(val)})"
    
    if "VarDecl" in node_name or "Declaration" in node_name:
        return f"VarDecl(name={repr(name)}, type={repr(type_node or 'angka')}, value={clean_val(val or 10)})"

    if "If" in node_name or "molo" in node_name.lower():
        cond = getattr(node, "condition", None) or getattr(node, "cond", None) or getattr(node, "expr", None)
        return f"IfStmt(cond={clean_val(cond)})"

    return f"{node_name}()"


# ─────────────────────────────────────────────────────────────
#  HELPER: ambil keterangan semantic (satu baris)
# ─────────────────────────────────────────────────────────────
def _semantic_summary(analyzer, errors, source_line: str) -> str:
    """
    Buat pesan semantic yang informatif berdasarkan errors list
    dan simbol baru yang sukses dideklarasikan.
    """
    if errors:
        return " | ".join(str(e) for e in errors)

    stripped = source_line.strip()
    if stripped.startswith("adong "):
        parts = stripped.split()
        var_name = parts[1] if len(parts) > 1 else "?"
        if ":" in var_name:
            var_name = var_name.split(":")[0]
        return f"OK (Variabel '{var_name}' berhasil dideklarasikan)"

    return "OK (Variabel & Tipe Data Valid)"


# ─────────────────────────────────────────────────────────────
#  HELPER: ambil ringkasan optimizer (satu baris)
# ─────────────────────────────────────────────────────────────
def _optimizer_summary(optimizer) -> str:
    changes = (
        getattr(optimizer, "changes",           None) or
        getattr(optimizer, "optimizations",     None) or
        getattr(optimizer, "optimization_count",None) or
        getattr(optimizer, "stats",             None)
    )
    if changes:
        if isinstance(changes, list):
            return "; ".join(str(c) for c in changes) if changes else "No optimization needed."
        if isinstance(changes, dict):
            items = [f"{k}: {v}" for k, v in changes.items() if v]
            return "; ".join(items) if items else "No optimization needed."
        if isinstance(changes, int):
            return f"{changes} optimization(s) applied." if changes > 0 else "No optimization needed."
        return str(changes)
    return "No optimization needed."


# ─────────────────────────────────────────────────────────────
#  HELPER: jalankan exec dan tangkap stdout
# ─────────────────────────────────────────────────────────────
def _exec_capture(code: str, global_env: dict) -> tuple[str, str | None]:
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, global_env)
        return buf.getvalue().rstrip("\n"), None
    except Exception as e:
        return "", str(e)


# ─────────────────────────────────────────────────────────────
#  FUNGSI UTAMA REPL: proses satu baris
# ─────────────────────────────────────────────────────────────
def _repl_compile_line(source_line: str, global_env: dict) -> None:
    """
    Kompilasi + eksekusi satu baris BatakScript tanpa pemotongan string.
    """

    # ── [Tokens] ────────────────────────────────────────
    lexer = Lexer(source_line)
    try:
        tokens = lexer.tokenize()
    except SyntaxError as e:
        print(_fmt("Tokens", f"ERROR - {e}"))
        return

    print(_fmt("Tokens", _token_pairs(tokens)))

    # ── [Parser] ────────────────────────────────────────
    parser = Parser(tokens)
    try:
        parse_tree = parser.parse()
    except SyntaxError as e:
        print(_fmt("Parser", f"ERROR - {e}"))
        return
    print(_fmt("Parser", "OK (Sintaks Valid)"))

    # ── [AST] ───────────────────────────────────────────
    builder = ASTBuilder()
    try:
        ast = builder.build(parse_tree)
    except Exception as e:
        print(_fmt("AST", f"ERROR - {e}"))
        return
    print(_fmt("AST", _ast_summary(ast)))

    # ── [Semantic] ──────────────────────────────────────
    analyzer = SemanticAnalyzer()
    _restore_symbol_table(analyzer, global_env)

    errors = analyzer.analyze(ast)
    sem_msg = _semantic_summary(analyzer, errors, source_line)
    print(_fmt("Semantic", sem_msg))

    if errors:
        return

    _save_symbol_table(analyzer, global_env)

    # ── [Optimizer] ─────────────────────────────────────
    optimizer = Optimizer()
    opt_ast   = optimizer.optimize(ast)
    print(_fmt("Optimizer", _optimizer_summary(optimizer)))

    # ── [Code Gen] ──────────────────────────────────────
    codegen = CodeGenerator()
    code    = codegen.generate(opt_ast)

    # Menampilkan kode Python asli yang utuh tanpa baris komentar compiler
    clean_lines = []
    for line in code.strip().splitlines():
        line_str = line.strip()
        if line_str.startswith("#"):
            continue
        if line_str:
            clean_lines.append(line_str)
            
    code_preview = " | ".join(clean_lines) if clean_lines else code.strip()
    print(_fmt("Code Gen", code_preview))

    # ── [Output] ────────────────────────────────────────
    captured, err = _exec_capture(code, global_env)
    if err:
        print(_fmt("Output", f"RUNTIME ERROR - {err}"))
    else:
        lines = captured.splitlines()
        if not lines:
            print(_fmt("Output", "(tidak ada output)"))
        else:
            print(_fmt("Output", lines[0]))
            for extra in lines[1:]:
                print(_fmt("",     extra))


# ─────────────────────────────────────────────────────────────
#  HELPER: paksa simpan & restore memori tabel simbol (DEEP COPY)
# ─────────────────────────────────────────────────────────────
_SYM_KEY = "__repl_symbol_table__"
_FN_KEY  = "__repl_function_table__"


def _save_symbol_table(analyzer: SemanticAnalyzer, env: dict) -> None:
    for attr in ("symbol_table", "symbols", "scope", "variables", "current_scope"):
        if hasattr(analyzer, attr):
            target = getattr(analyzer, attr)
            if hasattr(target, "symbols") and isinstance(target.symbols, dict):
                env[_SYM_KEY] = dict(target.symbols)
            elif isinstance(target, dict):
                env[_SYM_KEY] = dict(target)
            else:
                env[_SYM_KEY] = target
            break

    fn = (
        getattr(analyzer, "function_table", None) or
        getattr(analyzer, "functions",      None)
    )
    if fn is not None:
        env[_FN_KEY] = dict(fn) if isinstance(fn, dict) else fn


def _restore_symbol_table(analyzer: SemanticAnalyzer, env: dict) -> None:
    saved_sym = env.get(_SYM_KEY)
    if saved_sym is not None:
        for attr in ("symbol_table", "symbols", "scope", "variables", "current_scope"):
            if hasattr(analyzer, attr):
                target = getattr(analyzer, attr)
                if hasattr(target, "symbols") and isinstance(target.symbols, dict):
                    target.symbols.update(saved_sym)
                elif isinstance(target, dict):
                    target.update(saved_sym)
                else:
                    if hasattr(target, "define") and isinstance(saved_sym, dict):
                        for k, v in saved_sym.items():
                            try: target.define(k, v)
                            except: pass
                    else:
                        setattr(analyzer, attr, saved_sym)
                break

    saved_fn = env.get(_FN_KEY)
    if saved_fn is not None:
        for attr in ("function_table", "functions"):
            if hasattr(analyzer, attr):
                try:
                    target = getattr(analyzer, attr)
                    if isinstance(target, dict):
                        target.update(saved_fn)
                    else:
                        setattr(analyzer, attr, saved_fn)
                except Exception:
                    pass
                break


# ─────────────────────────────────────────────────────────────
#  REPL LOOP
# ─────────────────────────────────────────────────────────────
def jalankan_repl():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(REPL_BANNER)

    global_env:  dict = {}

    while True:
        try:
            baris = input("BatakScript >>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [↩] Kembali ke menu utama...\n")
            break

        if not baris:
            continue

        if baris.lower() in ("keluar", "exit"):
            print("  [↩] Kembali ke menu utama...\n")
            break

        _repl_compile_line(baris, global_env)
        print()


# ─────────────────────────────────────────────────────────────
#  COMPILE & RUN (untuk mode demo / file)
# ─────────────────────────────────────────────────────────────
def compile_and_run(source_code: str, verbose: bool = True, run: bool = True):
    if verbose:
        print(BANNER)

    print("━" * 55)
    print(" FASE 1: LEXICAL ANALYSIS (Lexer)")
    print("━" * 55)
    lexer  = Lexer(source_code)
    try:
        tokens = lexer.tokenize()
    except SyntaxError as e:
        print(f"  [ERROR] Lexer: {e}")
        return
    if verbose:
        lexer.display_tokens()
    else:
        print(f"  [OK] {len(tokens)-1} token berhasil dibuat.")

    print("━" * 55)
    print(" FASE 2: SYNTAX ANALYSIS (Parser -> Parse Tree)")
    print("━" * 55)
    parser = Parser(tokens)
    try:
        parse_tree = parser.parse()
    except SyntaxError as e:
        print(f"  [ERROR] Parse: {e}")
        return
    if verbose:
        print()
        parse_tree.display()
    else:
        print("  [OK] Parse Tree berhasil dibuat.")

    print("━" * 55)
    print(" FASE 3: AST CONSTRUCTION")
    print("━" * 55)
    builder = ASTBuilder()
    try:
        ast = builder.build(parse_tree)
    except Exception as e:
        print(f"  [ERROR] AST: {e}")
        return
    if verbose:
        print()
        ast.display()
    else:
        print("  [OK] AST berhasil dibangun.")

    print("━" * 55)
    print(" FASE 4: SEMANTIC ANALYSIS")
    print("━" * 55)
    analyzer = SemanticAnalyzer()
    errors   = analyzer.analyze(ast)
    analyzer.display_result()
    if errors:
        print("  [ERROR] Kompilasi dihentikan karena error semantik.")
        return

    print("━" * 55)
    print(" FASE 5: CODE OPTIMIZATION")
    print("━" * 55)
    optimizer = Optimizer()
    opt_ast   = optimizer.optimize(ast)
    optimizer.display_stats()

    print("━" * 55)
    print(" FASE 6: CODE GENERATION (-> Python)")
    print("━" * 55)
    codegen = CodeGenerator()
    code    = codegen.generate(opt_ast)
    codegen.display(code)

    out_dir  = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "output.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"  [Saved] Kode disimpan ke: {out_path}")

    if run:
        print("━" * 55)
        print(" FASE 7: EKSEKUSI")
        print("━" * 55)
        try:
            exec(code, {})
        except Exception as e:
            print(f"  [ERROR] Runtime: {e}")

    print("\n" + "━" * 55)
    print("  [OK] Kompilasi selesai!")
    print("━" * 55)


# ─────────────────────────────────────────────
#  DEMO SOURCE
# ─────────────────────────────────────────────
DEMO_SOURCE = """
// ============================================
// Program Demo BatakScript
// Menghitung faktorial dengan bahasa Batak Toba
// ============================================

adong salam : hata gabe "Horas ma di hamu!"
adong angkanta : angka gabe 10

karejo faktorial(n) {
    molo (n <= 1) {
        mulak 1
    } ndang {
        mulak n * faktorial(n - 1)
    }
}

karejo fizzbatak(max) {
    adong i : angka gabe 1
    sahat (i <= max) {
        molo (i % 15 == 0) {
            patuduhon("HorasBoru")
        } nunga (i % 3 == 0) {
            patuduhon("Horas")
        } nunga (i % 5 == 0) {
            patuduhon("Boru")
        } ndang {
            patuduhon(i)
        }
        i gabe i + 1
    }
}

patuduhon(salam)
patuduhon("Faktorial 5 = ")
patuduhon(faktorial(5))
patuduhon("Faktorial 7 = ")
patuduhon(faktorial(7))
patuduhon("--- FizzBatak 1 sampai 15 ---")
fizzbatak(15)
"""


# ─────────────────────────────────────────────
#  MENU & ENTRY POINT
# ─────────────────────────────────────────────
def pilih_menu():
    print(BANNER)
    print("  Pilih mode:")
    print("  [1] Demo otomatis (tanpa input)")
    print("  [2] Interactive REPL (ketik kode langsung)")
    print("  [3] Kompilasi file .batak sendiri")
    print()
    pilihan = input("  Masukkan pilihan (1/2/3): ").strip()
    return pilihan


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            compile_and_run(DEMO_SOURCE)
        elif sys.argv[1] == "--repl":
            jalankan_repl()
        else:
            filepath = sys.argv[1]
            if not os.path.exists(filepath):
                print(f"File tidak ditemukan: {filepath}")
                sys.exit(1)
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            compile_and_run(source)
    else:
        while True:
            pilihan = pilih_menu()
            if pilihan == "1":
                compile_and_run(DEMO_SOURCE)
                break
            elif pilihan == "2":
                jalankan_repl()
                continue
            elif pilihan == "3":
                filepath = input("  Masukkan path file .batak: ").strip()
                if not os.path.exists(filepath):
                    print(f"File tidak ditemukan: {filepath}")
                    sys.exit(1)
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
                compile_and_run(source)
                break
            else:
                print("  [!] Pilihan tidak valid, coba lagi.\n")