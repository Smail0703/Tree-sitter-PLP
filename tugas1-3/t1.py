import tree_sitter_python as tspython
from tree_sitter import Language, Parser

parser = Parser(Language(tspython.language()))

print(25 * "=")
print("Kode 1")

kode = b"""def sapa(nama):
    return nama
"""
tree = parser.parse(kode)
print(tree.root_node)

for c in tree.root_node.children[0].children:
    print(c.type, "bernama" if c.is_named else "anonim")

print("\n")

params = tree.root_node.children[0].child_by_field_name("parameters")
for c in params.children:
    print(c.type, "bernama" if c.is_named else "anonim")

print(25 * "=")
print("Kode 2")

kode = b"""if x > 5:
    print("besar")
else:
    print("kecil")
"""

tree = parser.parse(kode)
print(tree.root_node)

for c in tree.root_node.children[0].children:
    print(c.type, "bernama" if c.is_named else "anonim")

print("\n")
if_node = tree.root_node.children[0]
else_node = if_node.child_by_field_name("alternative")

for c in else_node.children:
    print(c.type, "bernama" if c.is_named else "anonim")

print(25 * "=")
print("Kode 3")

kode = b"""class Kucing:
    def suara(self):
        return "meong"
"""

tree = parser.parse(kode)
print(tree.root_node)

kelas = tree.root_node.children[0]

print("-- child langsung class_definition --")
for c in kelas.children:
    print(c.type, "bernama" if c.is_named else "anonim")

print("-- isi body (block) --")
body = kelas.child_by_field_name("body")
for c in body.children:
    print(c.type, "bernama" if c.is_named else "anonim")

print("-- children vs named_children pada body --")
print(len(body.children), len(body.named_children))

print(25 * "=")
print("Kode 4 (sengaja rusak: tanda ':' dihapus)")

kode = b"""def sapa(nama)
    return nama
"""

tree = parser.parse(kode)
print(tree.root_node)
print("has_error:", tree.root_node.has_error)

print(25 * "=")
print("Kode 5 (sengaja rusak: tanda ')' dihapus)")

kode = b"""def sapa(nama:
    return nama
"""

tree = parser.parse(kode)
print(tree.root_node)
print("has_error:", tree.root_node.has_error)
