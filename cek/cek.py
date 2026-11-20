import sys
from pathlib import Path
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser, Query, QueryCursor

BATAS_BARIS = 30
FOLDER_DILEWATI = {"venv", ".venv", ".git", "node_modules", "__pycache__"}

# Query komentar sama untuk kedua bahasa: node "comment" ada di grammar Python maupun JavaScript.
POLA_TODO = '((comment) @c (#match? @c "TODO|FIXME"))'

# Query fungsi berbeda per bahasa karena nama node di grammar-nya berbeda.
POLA_FUNGSI_PY = "(function_definition name: (identifier) @nama) @fungsi"
POLA_FUNGSI_JS = """
(function_declaration name: (identifier) @nama) @fungsi
(method_definition name: (property_identifier) @nama) @fungsi
(variable_declarator name: (identifier) @nama value: (arrow_function) @fungsi)
(variable_declarator name: (identifier) @nama value: (function_expression) @fungsi)
"""


def siapkan_bahasa(modul, pola_fungsi):
    bahasa = Language(modul.language())
    return {
        "parser": Parser(bahasa),
        "q_todo": Query(bahasa, POLA_TODO),
        "q_fungsi": Query(bahasa, pola_fungsi),
    }


PY = siapkan_bahasa(tspython, POLA_FUNGSI_PY)
JS = siapkan_bahasa(tsjs, POLA_FUNGSI_JS)

# ekstensi file -> bahasa yang dipakai untuk mem-parse-nya
BAHASA = {".py": PY, ".js": JS, ".jsx": JS, ".mjs": JS, ".cjs": JS}

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

def cek_file(path, bahasa):
    tree = bahasa["parser"].parse(path.read_bytes())

    # Fitur 1: komentar TODO/FIXME
    for node in QueryCursor(bahasa["q_todo"]).captures(tree.root_node).get("c", []):
        print(f"{path}:{node.start_point[0] + 1}: {node.text.decode(errors='replace').strip()}")

    # Fitur 2: fungsi yang lebih dari 30 baris
    for _, cap in QueryCursor(bahasa["q_fungsi"]).matches(tree.root_node):
        fungsi = cap["fungsi"][0]
        nama = cap["nama"][0].text.decode(errors="replace")
        jumlah = fungsi.end_point[0] - fungsi.start_point[0] + 1
        if jumlah > BATAS_BARIS:
            print(f"{path}:{fungsi.start_point[0] + 1}: fungsi '{nama}' terlalu panjang ({jumlah})") 

    # Fitur 3: file yang pohonnya mengandung error
    if tree.root_node.has_error:
        print(f"{path}:{baris_error(tree.root_node)}: sintaks bermasalah (pohon mengandung ERROR/MISSING)")

if len(sys.argv) < 2:
    sys.exit("Pemakaian: python cek.py <folder>")

for path in sorted(Path(sys.argv[1]).rglob("*")):
    if path.suffix not in BAHASA or not path.is_file():
        continue
    if FOLDER_DILEWATI & set(path.parts):
        continue
    cek_file(path, BAHASA[path.suffix])
