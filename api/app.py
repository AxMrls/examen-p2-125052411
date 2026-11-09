"""API de resultados por categoría y mes. Documentación: /docs"""
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


def conectar():
    return psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', 'db'),
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        cursor_factory=RealDictCursor,
    )


@asynccontextmanager
async def lifespan(app):
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS resultados (
                categoria TEXT NOT NULL,
                mes CHAR(7) NOT NULL,
                ingreso_total NUMERIC(18,2) NOT NULL,
                PRIMARY KEY(categoria, mes))""")
    yield


app = FastAPI(title='DataMart — 125052411', lifespan=lifespan)

class Resultado(BaseModel):
    categoria: str = Field(min_length=1)
    mes: str = Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    ingreso_total: Decimal = Field(ge=0)


def consulta(sql, parametros=()):
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, parametros)
            return cur.fetchall()


@app.get('/salud')
def salud():
    return {'estado': 'ok', 'matricula': '125052411'}


@app.get('/resultados')
def resultados():
    return consulta('SELECT categoria, mes, ingreso_total FROM resultados ORDER BY categoria, mes')


@app.get('/resultados/{clave}')
def resultados_categoria(clave: str, mes: Optional[str] = Query(None)):
    if mes:
        filas = consulta('SELECT categoria, mes, ingreso_total FROM resultados WHERE categoria=%s AND mes=%s ORDER BY mes', (clave, mes))
    else:
        filas = consulta('SELECT categoria, mes, ingreso_total FROM resultados WHERE categoria=%s ORDER BY mes', (clave,))
    if not filas:
        raise HTTPException(status_code=404, detail='Sin resultados para ese filtro')
    return filas


@app.post('/resultados', status_code=201)
def crear_o_actualizar(resultado: Resultado):
    with conectar() as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO resultados (categoria, mes, ingreso_total)
                VALUES (%s, %s, %s)
                ON CONFLICT (categoria, mes) DO UPDATE
                SET ingreso_total=EXCLUDED.ingreso_total RETURNING categoria, mes, ingreso_total""",
                (resultado.categoria, resultado.mes, resultado.ingreso_total))
            return cur.fetchone()
