#!/usr/bin/env python3
"""Emite categoria|AAAA-MM y valor exacto en centavos."""
import csv
import sys
from decimal import Decimal, InvalidOperation
from datetime import datetime

for linea in sys.stdin:
    try:
        campos = next(csv.reader([linea]))
        if len(campos) != 8 or campos[0].strip().lower() == 'id':
            continue
        _, fecha, tienda, categoria, producto, cantidad, precio, pago = campos
        if not categoria.strip() or not tienda.strip() or not producto.strip():
            continue
        mes = datetime.strptime(fecha.strip(), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m')
        unidades = int(cantidad)
        monto = Decimal(precio)
        if unidades <= 0 or monto < 0 or not monto.is_finite():
            continue
        centavos = unidades * int((monto * 100).to_integral_exact())
        print(f'{categoria.strip()}|{mes}\t{centavos}')
    except (ValueError, InvalidOperation, OverflowError, StopIteration, csv.Error):
        continue
