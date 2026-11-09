#!/usr/bin/env python3
"""Agrega entradas ordenadas por clave sin cargar todo el dataset."""
import sys
from decimal import Decimal

clave_anterior = None
total = 0
for linea in sys.stdin:
    try:
        clave, centavos = linea.rstrip('\n').split('\t', 1)
        valor = int(centavos)
    except ValueError:
        continue
    if clave_anterior is not None and clave != clave_anterior:
        print(f'{clave_anterior}\t{Decimal(total) / 100:.2f}')
        total = 0
    clave_anterior = clave
    total += valor
if clave_anterior is not None:
    print(f'{clave_anterior}\t{Decimal(total) / 100:.2f}')
