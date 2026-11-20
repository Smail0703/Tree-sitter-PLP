import sys
from pathlib import Path
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

PY = Language(tspython.language())
parser = Parser(PY)

BATAS_BARIS = 30
FOLDER_DILEWATI = {"venv", ".venv", ".git", "node_modules", "__pycache__"}

Q_TODO = Query(PY, '((comment) @c (#match? @c "TODO|FIXME"))')
Q_FUNGSI = Query(PY, "(function_definition name: (identifier) @nama) @fungsi")


def cari_error_pertama(node):
    """Cari node ERROR / MISSING pertama (urutan dokumen) secara rekursif."""
    for child in node.children:
        if child.is_error or child.is_missing:
            return child
        if child.has_error:  # hanya turun ke cabang yang memang mengandung error
            hasil = cari_error_pertama(child)
            if hasil:
                return hasil
    return None


def cek_file(path):
    tree = parser.parse(path.read_bytes())

    # Fitur 1: komentar TODO/FIXME (sudah jadi)
    for node in QueryCursor(Q_TODO).captures(tree.root_node).get("c", []):
        print(f"{path}:{node.start_point[0] + 1}: {node.text.decode(errors='replace').strip()}")

    # Fitur 2: fungsi yang lebih dari 30 baris
    for _, cap in QueryCursor(Q_FUNGSI).matches(tree.root_node):
        fungsi = cap["fungsi"][0]
        nama = cap["nama"][0].text.decode(errors="replace")
        jumlah = fungsi.end_point[0] - fungsi.start_point[0] + 1
        if jumlah > BATAS_BARIS:
            print(f"{path}:{fungsi.start_point[0] + 1}: fungsi '{nama}' terlalu panjang ({jumlah} baris)")

    # Fitur 3: file yang pohonnya mengandung error



if len(sys.argv) < 2:
    sys.exit("Pemakaian: python cek.py <folder>")

for path in sorted(Path(sys.argv[1]).rglob("*.py")):
    if FOLDER_DILEWATI & set(path.parts):
        continue
    cek_file(path)