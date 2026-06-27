"""
=============================================================
  BATAK COMPILER - DESAIN BAHASA
  Bahasa: BatakScript (berbasis Bahasa Batak Toba)
=============================================================

TABEL SIMBOL / GRAMMAR / KEYWORD / FUNGSI BAWAAN
"""

# ─────────────────────────────────────────────
#  KEYWORD (Kata kunci Bahasa Batak Toba)
# ─────────────────────────────────────────────
KEYWORDS = {
    # Deklarasi variabel
    "adong":    "VAR",          # "ada" → deklarasi variabel
    # Tipe data
    "angka":    "TYPE_INT",     # tipe integer
    "hata":     "TYPE_STRING",  # tipe string
    "denggan":  "TYPE_BOOL",    # tipe boolean (denggan = baik/true)
    "jahat":    "TYPE_BOOL",    # nilai false
    # Kondisi
    "molo":     "IF",           # "kalau" → if
    "ndang":    "ELSE",         # "tidak" → else
    "nunga":    "ELIF",         # "sudah" → elif
    # Perulangan
    "sahat":    "WHILE",        # "sampai" → while
    "hali":     "FOR",          # "kali/putaran" → for
    "di":       "IN",           # "di" → in
    # Fungsi
    "karejo":   "FUNC",         # "kerja" → function
    "mulak":    "RETURN",       # "kembali" → return
    # Logika
    "dohot":    "AND",          # "dan" → and
    "manang":   "OR",           # "atau" → or
    "ndang_be": "NOT",          # "tidak lagi" → not
    # Nilai boolean
    "ture":     "TRUE",         # "benar" → true
    "sala":     "FALSE",        # "salah" → false
    # Lain-lain
    "gabe":     "ASSIGN_FUNC",  # "menjadi" → =
    "tamat":    "BREAK",        # "selesai" → break
    "lanjut":   "CONTINUE",     # lanjut → continue
}

# ─────────────────────────────────────────────
#  FUNGSI BAWAAN (Built-in Functions)
# ─────────────────────────────────────────────
BUILTIN_FUNCTIONS = {
    "patuduhon":  "PRINT",      # "tunjukkan" → print
    "lehon":      "INPUT",      # "beri" → input
    "pature":     "OUTPUT",     # "perbaiki/hasilkan" → output/return value
    "sian":       "LEN",        # "dari" → len()
    "gabehon":    "STR",        # "jadikan string" → str()
    "angkahon":   "INT",        # "jadikan angka" → int()
    "dapothon":   "RANGE",      # "mendatangi" → range()
    "torhon":     "PRINT_LINE", # "cetak baris" → println
}

# ─────────────────────────────────────────────
#  TABEL SIMBOL (Symbol Table - runtime)
# ─────────────────────────────────────────────
class SymbolTable:
    """
    Tabel simbol untuk menyimpan variabel, fungsi, dan tipe data.
    Mendukung scope (global & lokal).
    """
    def __init__(self, parent=None):
        self.symbols = {}       # { name: {"type": ..., "value": ...} }
        self.parent  = parent   # scope induk (untuk nested function)

    def declare(self, name: str, dtype: str, value=None):
        if name in self.symbols:
            raise Exception(f"[SymbolTable] Variabel '{name}' sudah dideklarasikan di scope ini.")
        self.symbols[name] = {"type": dtype, "value": value}

    def set(self, name: str, value):
        if name in self.symbols:
            self.symbols[name]["value"] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise Exception(f"[SymbolTable] Variabel '{name}' belum dideklarasikan.")

    def get(self, name: str):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise Exception(f"[SymbolTable] Variabel '{name}' tidak ditemukan.")

    def exists(self, name: str) -> bool:
        if name in self.symbols:
            return True
        if self.parent:
            return self.parent.exists(name)
        return False

    def display(self):
        print("\n╔══════════════════════════════╗")
        print("║       TABEL SIMBOL           ║")
        print("╠══════════════════════════════╣")
        print(f"  {'Nama':<15} {'Tipe':<10} {'Nilai'}")
        print("  " + "-"*40)
        for name, info in self.symbols.items():
            print(f"  {name:<15} {info['type']:<10} {info['value']}")
        print("╚══════════════════════════════╝\n")


# ─────────────────────────────────────────────
#  GRAMMAR BNF (Backus-Naur Form)
# ─────────────────────────────────────────────
GRAMMAR_BNF = """
=== GRAMMAR BATAKSCRIPT (BNF) ===

<program>       ::= <statement>*

<statement>     ::= <var_decl>
                  | <assign>
                  | <if_stmt>
                  | <while_stmt>
                  | <for_stmt>
                  | <func_decl>
                  | <return_stmt>
                  | <print_stmt>
                  | <expr_stmt>

<var_decl>      ::= 'adong' IDENTIFIER ':' <type> ('gabe' <expr>)?

<type>          ::= 'angka' | 'hata' | 'denggan'

<assign>        ::= IDENTIFIER 'gabe' <expr>

<if_stmt>       ::= 'molo' '(' <expr> ')' '{' <statement>* '}'
                    ('nunga' '(' <expr> ')' '{' <statement>* '}')*
                    ('ndang' '{' <statement>* '}')?

<while_stmt>    ::= 'sahat' '(' <expr> ')' '{' <statement>* '}'

<for_stmt>      ::= 'hali' IDENTIFIER 'di' <expr> '{' <statement>* '}'

<func_decl>     ::= 'karejo' IDENTIFIER '(' <params>? ')' '{' <statement>* '}'

<params>        ::= IDENTIFIER (',' IDENTIFIER)*

<return_stmt>   ::= 'mulak' <expr>

<print_stmt>    ::= 'patuduhon' '(' <expr> ')'

<expr>          ::= <or_expr>
<or_expr>       ::= <and_expr> ('manang' <and_expr>)*
<and_expr>      ::= <not_expr> ('dohot' <not_expr>)*
<not_expr>      ::= 'ndang_be' <not_expr> | <compare>
<compare>       ::= <add_expr> (('<'|'>'|'<='|'>='|'=='|'!=') <add_expr>)*
<add_expr>      ::= <mul_expr> (('+'|'-') <mul_expr>)*
<mul_expr>      ::= <unary>   (('*'|'/') <unary>)*
<unary>         ::= '-' <primary> | <primary>
<primary>       ::= INTEGER | FLOAT | STRING | BOOLEAN | IDENTIFIER
                  | IDENTIFIER '(' <args>? ')'
                  | '(' <expr> ')'

<args>          ::= <expr> (',' <expr>)*
"""

if __name__ == "__main__":
    print("=== DESAIN BAHASA BATAKSCRIPT ===")
    print(f"\nJumlah Keyword   : {len(KEYWORDS)}")
    print(f"Fungsi Bawaan    : {len(BUILTIN_FUNCTIONS)}")
    print("\n--- KEYWORDS ---")
    for k, v in KEYWORDS.items():
        print(f"  {k:<12} → {v}")
    print("\n--- FUNGSI BAWAAN ---")
    for k, v in BUILTIN_FUNCTIONS.items():
        print(f"  {k:<12} → {v}")
    print(GRAMMAR_BNF)
    sym = SymbolTable()
    sym.declare("bilangan", "angka", 10)
    sym.declare("nama", "hata", "Batak")
    sym.display()
