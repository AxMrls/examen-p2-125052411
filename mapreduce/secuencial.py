#!/usr/bin/env python3
"""Misma agregación sin Hadoop, en streaming desde disco."""
import csv
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation

entrada, salida = sys.argv[1:3]
totales = defaultdict(int)
with open(entrada, encoding='utf-8', newline='') as archivo:
    for campos in csv.reader(archivo):
        try:
            if len(campos) != 8 or campos[0].strip().lower() == 'id':
                continue
            _, fecha, tienda, cat, producto, cantidad, precio, pago = campos
            if not cat.strip() or not tienda.strip() or not producto.strip():
                continue
            mes = datetime.strptime(fecha.strip(), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m')
            unidades = int(cantidad)
            monto = Decimal(precio)
            if unidades <= 0 or monto < 0 or not monto.is_finite():
                continue
            centavos = unidades * int((monto * 100).to_integral_exact())
            totales[f'{cat.strip()}|{mes}'] += centavos
        except (ValueError, InvalidOperation, OverflowError, csv.Error):
            continue
with open(salida, 'w', encoding='utf-8') as archivo:
    for clave in sorted(totales):
        archivo.write(f'{clave}\t{Decimal(totales[clave]) / 100:.2f}\n')
print(f'Secuencial: {len(totales)} grupos')
