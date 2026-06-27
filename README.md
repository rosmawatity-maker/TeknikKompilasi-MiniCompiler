# BatakScript: Mini Compiler

Proyek *mini compiler* ini dirancang untuk menerjemahkan kode sumber berbasis bahasa Batak Toba menjadi kode Python yang valid dan siap dieksekusi. Proyek ini dikembangkan sebagai pemenuhan tugas besar untuk mata kuliah **Teknik Kompilasi**.

---

## Identitas Pengembang

- **Nama:** Rosmawati Pasaribu
- **NIM:** 231011402174

---

## Fitur Utama

- **Lexical Analysis (Lexer):** Memecah kode sumber menjadi daftar token logis yang dikenali sistem.
- **Syntactic Analysis (Parser):** Memeriksa struktur kode berdasarkan aturan tata bahasa (*grammar*) dan menyusunnya ke dalam *Abstract Syntax Tree* (AST).
- **Semantic Analysis:** Melakukan validasi logika program, termasuk pemeriksaan tipe data (*type checking*) dan manajemen ruang lingkup variabel (*scope management*).
- **Code Optimization:** Mengoptimalkan performa kode hasil translasi menggunakan teknik *Constant Folding*.
- **Code Generation:** Mentranslasikan AST secara akurat menjadi kode Python murni.

---

## Struktur Proyek

```text
batak_compiler/
│
├── docs/
│   └── language_design.md    # Dokumentasi desain bahasa & spesifikasi sintaks
│
├── examples/
│   ├── hello_batak.batak     # Contoh program dasar mencetak teks
│   ├── faktorial.batak       # Contoh implementasi fungsi rekursif
│   └── interaktif.batak      # Contoh program menerima input dari pengguna
│
└── src/
    ├── main.py               # Titik masuk utama (Entry Point) program
    ├── language_design.py    # Definisi kata kunci (keywords) bahasa Batak Toba
    ├── lexer.py              # Komponen Lexical Analyzer
    ├── ast_nodes.py          # Definisi node untuk struktur pohon AST
    ├── parser.py             # Komponen Syntactic Analyzer
    ├── semantic.py           # Komponen Semantic Analyzer & Type Checker
    ├── optimizer.py          # Komponen pengoptimal kode (Constant Folding)
    └── codegen.py            # Komponen Code Generator (BatakScript to Python)