# cek.py — Pendeteksi TODO, Fungsi Panjang dan File dengan Pohon Error.

CLI kecil berbasis **tree-sitter** yang memeriksa file kode di dalam sebuah folder dan melaporkan:

1. komentar yang berisi `TODO` atau `FIXME`,
2. fungsi yang panjangnya lebih dari 30 baris, dan
3. file yang pohonnya mengandung error sintaks (node `ERROR` atau `MISSING`).

Bahasa yang didukung: **Python** (`.py`) dan **JavaScript** (`.js`, `.jsx`, `.mjs`, `.cjs`).

## Struktur folder

```
cek/
├── cek.py          # programnya
├── README.md
└── uji/            # file-file uji buatan sendiri
    ├── todo.py     # komentar TODO/FIXME (Python)
    ├── panjang.py  # fungsi panjang, tepat 30 baris, dan pendek (Python)
    ├── tepi.py     # kasus tepi: string, huruf kecil, method, fungsi bersarang (Python)
    ├── contoh.js   # semua kasus di atas untuk JavaScript
    ├── rusak.py    # sintaks Python rusak (tanda ':' pada def hilang)
    ├── rusak.js    # sintaks JavaScript rusak (kurung tidak ditutup)
    └── valid.py    # file benar, tidak boleh dilaporkan fitur 3
```

## Memasang dependensi

Butuh Python 3.10 atau lebih baru.

```bash
python -m pip install tree-sitter tree-sitter-python tree-sitter-javascript
```

## Cara menjalankan

```bash
python cek.py <folder>
```

Contoh, dari dalam folder `cek/`:

```bash
python cek.py uji
```

Jika perintah `python` tidak dikenali di Windows, ganti dengan `py`.

Folder `venv/`, `.venv/`, `.git/`, `node_modules/`, dan `__pycache__/` otomatis dilewati.
Setiap temuan dicetak dengan format `file:baris: keterangan`.

## Contoh output

Hasil `python cek.py uji`:

```
uji/contoh.js:1: // TODO: pindahkan ke modul util
uji/contoh.js:3: /* FIXME: blok komentar */
uji/contoh.js:6: fungsi 'panjangDeklarasi' terlalu panjang (36)
uji/contoh.js:43: fungsi 'panjangPanah' terlalu panjang (35)
uji/contoh.js:80: fungsi 'metodePanjang' terlalu panjang (33)
uji/panjang.py:1: fungsi 'fungsi_panjang' terlalu panjang (36)
uji/rusak.js:3: sintaks bermasalah (pohon mengandung ERROR/MISSING)
uji/rusak.py:3: sintaks bermasalah (pohon mengandung ERROR/MISSING)
uji/tepi.py:3: # FIXME: komentar di akhir baris
uji/tepi.py:6: fungsi 'metode_panjang' terlalu panjang (32)
uji/tepi.py:39: fungsi 'luar' terlalu panjang (34)
uji/tepi.py:40: fungsi 'dalam' terlalu panjang (32)
uji/todo.py:1: # TODO: rapikan modul ini
uji/todo.py:3: # FIXME: nama masih hardcode
```

Angka dalam kurung pada baris fungsi adalah jumlah baris fungsi tersebut. `valid.py` tidak muncul karena
file itu sehat: tidak ada TODO/FIXME, tidak ada fungsi panjang, dan pohonnya tidak mengandung error.
Program hanya mencetak jika ada temuan.

(Di Windows pemisah path tercetak `\`, bukan `/`.)

## Cara kerja

### 1. Fitur 1: komentar TODO/FIXME

Query yang dipakai:

```scheme
((comment) @c (#match? @c "TODO|FIXME"))
```

- `(comment)` cocok dengan node bertipe `comment`. Tipe ini ada di grammar Python (`# ...`) maupun JavaScript
  (`// ...` dan `/* ... */`), jadi satu query dipakai untuk kedua bahasa.
- `@c` menangkap node komentar yang cocok.
- `(#match? @c "TODO|FIXME")` adalah predikat: node hanya lolos jika teksnya cocok dengan regex `TODO|FIXME`.
  Regex ini dicari di bagian mana pun teks komentar, tidak harus di awal. Pembandingannya peka huruf besar-kecil.
- Kurung terluar mengelompokkan pola dan predikatnya menjadi satu pola query.

`QueryCursor(query).captures(tree.root_node)` mengembalikan dictionary `{nama_capture: [node, ...]}`.
Kode memakai `.get("c", [])` supaya file tanpa komentar yang cocok tidak menyebabkan `KeyError`.

Posisi node di tree-sitter berbentuk `(baris, kolom)` dan **mulai dari 0**, sehingga nomor baris yang dicetak
selalu `start_point[0] + 1` agar sama dengan nomor baris di editor.

**Kenapa tidak cukup dengan regex pada teks mentah:** regex akan ikut menangkap `TODO` yang berada di dalam
string, misalnya `"# TODO ini bukan komentar"`. Tree-sitter sudah tahu bagian mana yang `comment` dan mana yang
`string`, sehingga hanya komentar asli yang dilaporkan.

### 2. Fitur 2: fungsi lebih dari 30 baris

Query untuk Python:

```scheme
(function_definition name: (identifier) @nama) @fungsi
```

- `@fungsi` (di luar kurung) menangkap **seluruh** node `function_definition`, dari `def` sampai akhir body.
- `@nama` menangkap nama fungsinya lewat field `name:`.

Karena yang dibutuhkan adalah pasangan nama dan node fungsi dari fungsi yang sama, dipakai
`QueryCursor(query).matches(root)`, bukan `captures`. `matches` mengembalikan daftar `(indeks_pola, capture)`,
dan `capture` adalah dictionary `{"fungsi": [node], "nama": [node]}`, jadi nama dan fungsi yang diambil
dijamin berasal dari satu kecocokan.

Panjang fungsi dihitung dari posisi node:

```python
jumlah = fungsi.end_point[0] - fungsi.start_point[0] + 1
```

- `end_point[0]` adalah baris terakhir (mulai dari 0), `start_point[0]` baris pertama.
- Selisih ditambah 1 karena kedua ujung ikut dihitung (fungsi di baris 1 sampai 3 panjangnya 3 baris, bukan 2).
- Node berakhir di token terakhir body, sehingga baris kosong setelah fungsi tidak ikut terhitung.
  Baris kosong dan komentar di dalam body ikut terhitung.
- Syaratnya `jumlah > 30` (lebih dari), jadi fungsi tepat 30 baris tidak dilaporkan.

**Semua fungsi dihitung.** Method di dalam kelas dan fungsi bersarang ikut diperiksa karena query mencocokkan
setiap `function_definition` di mana pun posisinya. Fungsi yang membungkus fungsi lain dilaporkan dengan panjang
seluruh isinya, sehingga baris milik fungsi dalam terhitung di dua fungsi.

### 3. Fitur 3: file yang pohonnya mengandung error

Tree-sitter tidak menolak kode yang salah. Parser-nya dirancang untuk editor, yang hampir selalu menampilkan
kode yang sedang setengah ditulis, jadi tetap menghasilkan pohon dan menandai bagian yang tidak cocok dengan
tata bahasa:

- node `ERROR` membungkus potongan kode yang tidak bisa dicocokkan dengan aturan grammar,
- node `MISSING` adalah token yang disisipkan parser sendiri karena dianggap hilang (misalnya `)` atau `:`).

**Mendeteksi error di seluruh file:** `tree.root_node.has_error` bernilai `True` jika ada node `ERROR` atau
`MISSING` di mana pun dalam pohon. Nilai ini hanya menjawab "ada atau tidak", belum menunjukkan letaknya.

**Mencari letak error:** fungsi rekursif `baris_error(node)` menelusuri pohon dari akar.

```python
def baris_error(node):
    """Baris node ERROR/MISSING pertama (urut posisi di file)."""
    if node.is_error or node.is_missing:
        return node.start_point[0] + 1
    for child in node.children:
        if child.has_error or child.is_error or child.is_missing:
            hasil = baris_error(child)
            if hasil:
                return hasil
    return None
```

- Jika node itu sendiri `ERROR` atau `MISSING`, nomor barisnya langsung dikembalikan.
- Jika tidak, hanya child yang mengandung error yang ditelusuri, sehingga cabang yang sehat dilewati.
- Child ditelusuri dari kiri ke kanan, jadi yang ditemukan adalah error **pertama menurut posisi di file**.
- Nomor baris diambil dari `start_point[0] + 1`, karena posisi di tree-sitter mulai dari 0 sedangkan nomor
  baris di editor mulai dari 1.

Pemanggilannya di dalam `cek_file`:

```python
if tree.root_node.has_error:
    print(f"{path}:{baris_error(tree.root_node)}: sintaks bermasalah (pohon mengandung ERROR/MISSING)")
```

Bentuk keluarannya:

```
uji/rusak.py:3: sintaks bermasalah (pohon mengandung ERROR/MISSING)
```

Baris yang dilaporkan adalah tempat parser pertama kali tidak bisa melanjutkan, dan bisa berbeda dari tempat
kesalahan sebenarnya (misalnya kurung yang lupa ditutup baru terasa beberapa baris kemudian). Fitur ini
berlaku untuk Python dan JavaScript tanpa kode tambahan, karena `has_error`, `is_error`, dan `is_missing`
tersedia pada node dari grammar mana pun.

### 4. Dukungan JavaScript

Cukup mengganti grammar (`tree-sitter-javascript`) dan query fungsi, karena nama node-nya berbeda dari Python:

```scheme
(function_declaration name: (identifier) @nama) @fungsi
(method_definition name: (property_identifier) @nama) @fungsi
(variable_declarator name: (identifier) @nama value: (arrow_function) @fungsi)
(variable_declarator name: (identifier) @nama value: (function_expression) @fungsi)
```

| Pola | Bentuk kode yang ditangkap |
| --- | --- |
| `function_declaration` | `function nama() { ... }` |
| `method_definition` | method di dalam `class` |
| `variable_declarator` + `arrow_function` | `const nama = () => { ... }` |
| `variable_declarator` + `function_expression` | `const nama = function () { ... }` |

Pada dua pola terakhir yang ditangkap sebagai `@fungsi` adalah node fungsinya (`arrow_function` atau
`function_expression`), bukan seluruh deklarasi `const`, karena nama fungsi tersimpan di variabelnya.
Query komentar untuk fitur 1 dan cara menghitung baris untuk fitur 2 sama persis dengan Python.

**Batasan JavaScript:** fungsi anonim yang tidak diberi nama lewat variabel (misalnya callback
`arr.map(x => ...)` atau properti objek `{ aksi: () => ... }`) tidak dilaporkan, karena tidak ada nama
untuk ditampilkan.

### 5. Penanganan masalah umum

- **`UnicodeDecodeError` saat mencetak:** teks node didekode dengan `decode(errors="replace")`, sehingga
  karakter yang tidak bisa dibaca diganti tanda pengganti dan program tidak berhenti.
- **Program lambat di repo besar:** folder `venv`, `.git`, `node_modules`, dan sejenisnya dilewati sebelum
  `cek_file` dipanggil.

## Pengujian

Semua pengujian memakai file buatan sendiri di folder `uji/`. Hasil yang diharapkan ditentukan lebih dulu dengan
menghitung manual (nomor baris di editor atau `grep -n`), lalu dibandingkan dengan output program.

### Fitur 1: komentar TODO/FIXME

| # | Kasus yang diuji | File | Yang diharapkan | Hasil |
| --- | --- | --- | --- | --- |
| 1 | Komentar `# TODO` di awal file | `todo.py` baris 1 | Dilaporkan | Sesuai |
| 2 | Komentar `# FIXME` di dalam fungsi | `todo.py` baris 3 | Dilaporkan | Sesuai |
| 3 | Komentar biasa tanpa TODO/FIXME | `todo.py` baris 7 | Tidak dilaporkan | Sesuai |
| 4 | Komentar di akhir baris kode (`x = 1  # FIXME: ...`) | `tepi.py` baris 3 | Dilaporkan | Sesuai |
| 5 | `TODO` di dalam string, bukan komentar | `tepi.py` baris 1 | Tidak dilaporkan | Sesuai |
| 6 | `todo` huruf kecil | `tepi.py` baris 2 | Tidak dilaporkan (regex peka huruf besar-kecil) | Sesuai |
| 7 | Komentar `//` JavaScript | `contoh.js` baris 1 | Dilaporkan | Sesuai |
| 8 | Komentar blok `/* ... */` JavaScript | `contoh.js` baris 3 | Dilaporkan | Sesuai |
| 9 | `TODO` di dalam string JavaScript | `contoh.js` baris 2 | Tidak dilaporkan | Sesuai |
| 10 | `todo` huruf kecil di JavaScript | `contoh.js` baris 4 | Tidak dilaporkan | Sesuai |

Jumlah temuan fitur 1 cocok dengan hitungan manual: 2 di `todo.py`, 1 di `tepi.py`, 2 di `contoh.js`.

### Fitur 2: fungsi lebih dari 30 baris

| # | Kasus yang diuji | File | Panjang (manual) | Yang diharapkan | Hasil |
| --- | --- | --- | --- | --- | --- |
| 1 | Fungsi panjang | `panjang.py` `fungsi_panjang` (baris 1 sampai 36) | 36 | Dilaporkan | Sesuai |
| 2 | Fungsi tepat di batas | `panjang.py` `fungsi_pas_30` | 30 | Tidak dilaporkan (syarat `> 30`) | Sesuai |
| 3 | Fungsi pendek | `panjang.py` `fungsi_pendek` | 2 | Tidak dilaporkan | Sesuai |
| 4 | Method di dalam kelas | `tepi.py` `metode_panjang` (baris 6 sampai 37) | 32 | Dilaporkan | Sesuai |
| 5 | Fungsi pembungkus | `tepi.py` `luar` (baris 39 sampai 72) | 34 | Dilaporkan | Sesuai |
| 6 | Fungsi bersarang | `tepi.py` `dalam` (baris 40 sampai 71) | 32 | Dilaporkan | Sesuai |
| 7 | `function` deklarasi (JS) | `contoh.js` `panjangDeklarasi` (baris 6 sampai 41) | 36 | Dilaporkan | Sesuai |
| 8 | Arrow function dalam `const` (JS) | `contoh.js` `panjangPanah` (baris 43 sampai 77) | 35 | Dilaporkan | Sesuai |
| 9 | Method kelas (JS) | `contoh.js` `metodePanjang` (baris 80 sampai 112) | 33 | Dilaporkan | Sesuai |
| 10 | Fungsi tepat di batas (JS) | `contoh.js` `pas30` (baris 115 sampai 144) | 30 | Tidak dilaporkan | Sesuai |
| 11 | Fungsi pendek (JS) | `contoh.js` `pendek` | 1 | Tidak dilaporkan | Sesuai |

Kasus 5 dan 6 menunjukkan bahwa fungsi pembungkus dan fungsi bersarang dilaporkan terpisah, sehingga baris
milik `dalam` terhitung dua kali (di `luar` dan di `dalam`). Ini sesuai dengan aturan "semua fungsi dihitung".

### Fitur 3: file yang pohonnya mengandung error

| # | Kasus yang diuji | File | Yang diharapkan | Hasil |
| --- | --- | --- | --- | --- |
| 1 | Tanda `:` pada `def` hilang (Python) | `rusak.py` baris 3 | Dilaporkan di baris 3 | Sesuai |
| 2 | Kurung tidak ditutup pada `function f( {` (JavaScript) | `rusak.js` baris 3 | Dilaporkan di baris 3 | Sesuai |
| 3 | File yang sintaksnya benar | `valid.py` | Tidak dilaporkan | Sesuai |