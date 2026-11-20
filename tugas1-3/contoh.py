import os
import sys as system
from pathlib import Path
from collections import defaultdict


def tambah(a, b):
    """Menjumlahkan dua angka."""
    return a + b


def kali(a, b, c):
    print("kali dipanggil")
    return a * b * c


def tanpa_parameter():
    print("tanpa parameter")


def bagi(a, b, c=1):
    if b == 0:
        return None
    hasil = a / b / c
    print(hasil)
    return hasil


def pangkat(a, b, c, d):
    return a ** b ** c ** d


print(tambah(1, 2))
print(os.getcwd())


class Kalkulator:
    """Docstring kelas, bukan docstring fungsi."""
    pass
