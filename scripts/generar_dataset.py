#!/usr/bin/env python3
"""Generador del profesor, misma semilla, output directo a datos/."""
import sys, random, csv
from pathlib import Path
from datetime import datetime, timedelta

matricula = sys.argv[1].strip() if len(sys.argv) == 2 else input('Ingresa tu matricula (9 digitos): ').strip()
while not (matricula.isdigit() and len(matricula) == 9):
    matricula = input('Matricula invalida. Debe tener exactamente 9 digitos: ').strip()
random.seed(matricula)
print(f'Generando dataset para {matricula}...')
N = 5_000_000
tiendas = [f'T{str(i).zfill(3)}' for i in range(1, random.randint(15, 40))]
categorias = ['Electronica', 'Abarrotes', 'Ropa', 'Hogar', 'Juguetes', 'Farmacia', 'Deportes', 'Papeleria', 'Mascotas', 'Bebidas']
productos = {c: [f'{c[:3].upper()}-{j:04d}' for j in range(1, random.randint(30, 80))] for c in categorias}
pagos = ['Efectivo', 'Tarjeta', 'Transferencia', 'Vales']
inicio = datetime(2025, 1, 1)
Path('datos').mkdir(exist_ok=True)
with open(f'datos/ventas_{matricula}.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['id','fecha_hora','tienda','categoria','producto','cantidad','precio_unitario','metodo_pago'])
    for i in range(1, N+1):
        cat = random.choice(categorias)
        fecha = inicio + timedelta(seconds=random.randint(0, 365*24*3600))
        w.writerow([i, fecha.strftime('%Y-%m-%d %H:%M:%S'), random.choice(tiendas), cat,
                    random.choice(productos[cat]), random.randint(1,12),
                    round(random.uniform(5,2500),2), random.choice(pagos)])
print('Listo: datos/ventas_'+matricula+'.csv')
