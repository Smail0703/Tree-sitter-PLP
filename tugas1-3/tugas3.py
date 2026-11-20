"""Tugas 3 - menjalankan semua query dan membandingkan dengan hitungan manual."""
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

PY = Language(tspython.language())
parser = Parser(PY)
tree = parser.parse(open("contoh.py", "rb").read())
root = tree.root_node

def query(file):
    return Query(PY, open(file).read())

print("== 1. Nama fungsi + jumlah parameter (matches) ==")
hasil = {}
for _, cap in QueryCursor(query("fungsi.scm")).matches(root):
    nama = cap["nama"][0].text.decode()
    jumlah = cap["params"][0].named_child_count
    hasil[nama] = jumlah
    print(f"  {nama}: {jumlah} parameter")
manual = {"tambah": 2, "kali": 3, "tanpa_parameter": 0, "bagi": 3, "pangkat": 4}
print("  cocok dengan hitungan manual:", hasil == manual)

print("== 2. Pemanggilan print(...) ==")
caps = QueryCursor(query("print.scm")).captures(root)
for n in sorted(caps["fn"], key=lambda n: n.start_byte):
    print(f"  baris {n.start_point[0] + 1}")
print("  jumlah:", len(caps["fn"]), "| manual: 5 | cocok:", len(caps["fn"]) == 5)

print("== 3. Import (nama modul) ==")
caps = QueryCursor(query("impor.scm")).captures(root)
urut = sorted(caps["modul"], key=lambda n: n.start_byte)  # captures dikelompokkan per pola, urutkan per posisi
moduls = [n.text.decode() for n in urut]
for n in urut:
    print(f"  baris {n.start_point[0] + 1}: {n.text.decode()}")
print("  cocok dengan manual ['os','sys','pathlib','collections']:",
      moduls == ["os", "sys", "pathlib", "collections"])

print("== 4. [Pengayaan] Docstring fungsi ==")
caps = QueryCursor(query("docstring.scm")).captures(root)
for n in caps["doc"]:
    print(f"  baris {n.start_point[0] + 1}: {n.text.decode()}")
print("  jumlah:", len(caps["doc"]), "| manual: 1 (hanya tambah; docstring kelas bukan fungsi)")
