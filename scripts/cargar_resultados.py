#!/usr/bin/env python3
"""Importa Hadoop Streaming a PostgreSQL, con UPSERT idempotente."""
import os
import sys
from decimal import Decimal
import psycopg2

archivo = sys.argv[1]
conexion = psycopg2.connect(
    host=os.environ.get('POSTGRES_HOST', 'db'),
    dbname=os.environ['POSTGRES_DB'],
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD'],
)
with conexion:
    with conexion.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS resultados (
            categoria TEXT NOT NULL,
            mes CHAR(7) NOT NULL,
            ingreso_total NUMERIC(18,2) NOT NULL,
            PRIMARY KEY (categoria, mes)
        )""")
        contador = 0
        with open(archivo, encoding='utf-8') as f:
            for linea in f:
                clave, ingreso = linea.strip().split('\t')
                categoria, mes = clave.rsplit('|', 1)
                cur.execute("""INSERT INTO resultados (categoria, mes, ingreso_total)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (categoria, mes) DO UPDATE SET ingreso_total=EXCLUDED.ingreso_total""",
                    (categoria, mes, Decimal(ingreso)))
                contador += 1
print(f'CARGADOS: {contador} registros agregados')
conexion.close()
