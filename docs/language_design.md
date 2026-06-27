# Desain Bahasa Batak Toba Script (BTS)

## 1. Nama Bahasa
**BTS (Batak Toba Script)** — Bahasa pemrograman berbasis kata-kata Batak Toba.

---

## 2. Keyword Bahasa Batak Toba

| Keyword BTS   | Setara (Python/C) | Keterangan                    |
|---------------|-------------------|-------------------------------|
| `toho`        | `if`              | Kondisi "jika"                |
| `ndada`       | `else`            | Kondisi "jika tidak"          |
| `tohokon`     | `elif`            | Kondisi "jika lagi"           |
| `sahat`       | `while`           | Perulangan "sampai"           |
| `ulang`       | `for`             | Perulangan "ulangi"           |
| `mulak`       | `return`          | Kembalikan nilai              |
| `pungka`      | `def`/`function`  | Definisi fungsi               |
| `boi`         | `true`            | Nilai benar                   |
| `ndaboi`      | `false`           | Nilai salah                   |
| `ndang`       | `not`             | Negasi                        |
| `dohot`       | `and`             | Konjungsi "dan"               |
| `manang`      | `or`              | Disjungsi "atau"              |
| `lehon`       | `let`/`var`       | Deklarasi variabel            |
| `arga`        | `const`           | Konstanta                     |
| `haporusan`   | `break`           | Hentikan loop                 |
| `lanjut`      | `continue`        | Lanjut iterasi berikutnya     |
| `mangalo`     | `class`           | Definisi kelas                |

---

## 3. Fungsi Bawaan (Built-in)

| Fungsi BTS        | Setara        | Keterangan                   |
|-------------------|---------------|------------------------------|
| `patuduhon(...)`  | `print(...)`  | Tampilkan output ke layar    |
| `tangko(...)`     | `input(...)`  | Ambil input dari pengguna    |
| `surat(...)`      | `str(...)`    | Konversi ke string           |
| `angka(...)`      | `int(...)`    | Konversi ke integer          |
| `desimal(...)`    | `float(...)`  | Konversi ke float            |
| `godang(...)`     | `len(...)`    | Panjang string/list          |
| `alap(...)`       | `range(...)`  | Generate range angka         |

---

## 4. Tipe Data

| Tipe BTS    | Setara     | Contoh               |
|-------------|------------|----------------------|
| `bilangan`  | `int`      | `5`, `-3`, `100`     |
| `desimal`   | `float`    | `3.14`, `-0.5`       |
| `surat`     | `string`   | `"horas"`, `'toba'`  |
| `bolean`    | `bool`     | `boi`, `ndaboi`      |
| `daftar`    | `list`     | `[1, 2, 3]`          |
| `tanpa`     | `null`     | `tanpa`              |

---

## 5. Operator

| Operator | Keterangan           |
|----------|----------------------|
| `+`      | Penjumlahan          |
| `-`      | Pengurangan          |
| `*`      | Perkalian            |
| `/`      | Pembagian            |
| `%`      | Modulo               |
| `==`     | Sama dengan          |
| `!=`     | Tidak sama dengan    |
| `<`      | Lebih kecil          |
| `>`      | Lebih besar          |
| `<=`     | Lebih kecil sama     |
| `>=`     | Lebih besar sama     |
| `=`      | Assignment           |

---

## 6. Grammar (BNF/EBNF)

```
program        ::= statement*

statement      ::= var_decl
                 | func_decl
                 | if_stmt
                 | while_stmt
                 | for_stmt
                 | return_stmt
                 | expr_stmt

var_decl       ::= ('lehon' | 'arga') IDENTIFIER '=' expression ';'

func_decl      ::= 'pungka' IDENTIFIER '(' params? ')' '{' statement* '}'
params         ::= IDENTIFIER (',' IDENTIFIER)*

if_stmt        ::= 'toho' '(' expression ')' '{' statement* '}'
                   ('tohokon' '(' expression ')' '{' statement* '}')*
                   ('ndada' '{' statement* '}')?

while_stmt     ::= 'sahat' '(' expression ')' '{' statement* '}'

for_stmt       ::= 'ulang' '(' IDENTIFIER 'ni' expression ')' '{' statement* '}'

return_stmt    ::= 'mulak' expression? ';'

expr_stmt      ::= expression ';'

expression     ::= assignment
assignment     ::= IDENTIFIER '=' expression | logic_or
logic_or       ::= logic_and ('manang' logic_and)*
logic_and      ::= equality ('dohot' equality)*
equality       ::= comparison (('==' | '!=') comparison)*
comparison     ::= addition (('<' | '>' | '<=' | '>=') addition)*
addition       ::= multiplication (('+' | '-') multiplication)*
multiplication ::= unary (('*' | '/' | '%') unary)*
unary          ::= ('ndang' | '-') unary | call
call           ::= primary ('(' arguments? ')')?
primary        ::= NUMBER | STRING | 'boi' | 'ndaboi' | 'tanpa'
                 | IDENTIFIER | '(' expression ')'

arguments      ::= expression (',' expression)*
```

---

## 7. Contoh Program BTS

```bts
// Horas! Program pertama dalam Bahasa Batak Toba Script

pungka hitung(a, b) {
    mulak a + b;
}

lehon nama = tangko("Aha goarmu? ");
patuduhon("Horas, " + nama + "!");

lehon angka1 = 10;
lehon angka2 = 20;
lehon hasil = hitung(angka1, angka2);
patuduhon("Hasilna: " + surat(hasil));

// Loop
ulang (i ni alap(1, 6)) {
    toho (i % 2 == 0) {
        patuduhon(surat(i) + " jempol");
    } ndada {
        patuduhon(surat(i) + " ganjil");
    }
}
```
