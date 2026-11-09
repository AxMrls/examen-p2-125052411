# Examen Segundo Parcial — Pipeline de datos contenerizado

**Alumno:** Axel Isaac Sanchez Morales
**Matrícula:** `125052411`
**Materia:** Manejo Masivo de Datos (Big Data)
**Profesor:** Javier Moya
**Empresa:** DataMart

## Pregunta de negocio asignada

La matrícula **125052411** termina en **1**. Por lo tanto, debemos responder: **¿Cuál es el ingreso total (cantidad × precio_unitario) por categoría y por mes?**

La clave agregada es `categoria|AAAA-MM` y la medida es el ingreso total en unidades monetarias con dos decimales. Para evitar errores monetarios por coma flotante, se suman **centavos enteros** y se convierten a importe decimal solo al escribir la salida.

## Requisitos previos

- Docker Engine + Docker Compose (o Docker Desktop) operativo.
- Python 3 en el host, para el dataset original del examen.
- Espacio de disco para el CSV (~400 MB), imágenes Hadoop y datos de Docker.
- Conexión a Internet para descargar Debian, Hadoop y paquetes Python.

## Preparación inicial (una sola vez)

### 1. Generar el CSV propio (Paso 0)

Desde la raíz del proyecto:

```bash
python3 scripts/generar_dataset.py 125052411
```

En Windows, si `python3` no está disponible, usar `py -3 scripts/generar_dataset.py 125052411`.

Se genera `datos/ventas_125052411.csv` con **5,000,000 registros** y la misma semilla y algoritmo que el script del docente. El archivo está excluido de Git por `.gitignore` y se monta **solo lectura** en `/data/input` dentro de Hadoop.

### 2. Preparar variables de entorno

En Linux/macOS:

```bash
cp .env.example .env
```

En PowerShell:

```powershell
Copy-Item .env.example .env
```

Abre `.env` y establece una **contraseña única y no vacía** para `POSTGRES_PASSWORD`, por ejemplo una que hayas generado tú. No subas `.env` a Git. La plantilla `.env.example` se entrega sin contraseña.

### 3. Levantar absolutamente todos los servicios

```bash
docker compose up --build
```

Este comando construye Hadoop y API, inicia PostgreSQL, activa SSH, ejecuta Hadoop Streaming, ejecuta el procesamiento secuencial, compara las salidas e importa los grupos en PostgreSQL. **Nota:** el dataset y `.env` deben prepararse antes de este comando, como pide el Paso 0 del examen.

La API puede estar disponible antes de que termine Hadoop: revisa que `evidencias/estado.log` contenga `PIPELINE_COMPLETO` antes de evaluar los resultados.

En otra terminal:

```bash
docker compose ps
docker compose logs -f hadoop
```

## Estructura del proyecto

```text
examen-p2-125052411/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── datos/                         # CSV generado (ignorado por Git)
├── hadoop/
│   ├── Dockerfile
│   └── entrypoint.sh
├── mapreduce/
│   ├── mapper.py
│   ├── reducer.py
│   └── secuencial.py
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── scripts/
│   ├── generar_dataset.py
│   ├── ejecutar_pipeline.sh
│   ├── comparar.py
│   └── cargar_resultados.py
└── evidencias/                    # Logs, capturas, tiempos medidos
```

## A. Docker / Hadoop

El contenedor Hadoop usa `debian:bookworm-slim`, OpenJDK 17, Python 3, Hadoop 3.4.1 y SSH Server. `JAVA_HOME`, `HADOOP_HOME`, `HADOOP_CONF_DIR` y `PATH` están configurados en el Dockerfile. Hadoop funciona en **modo standalone** (sistema de archivos local, sin HDFS).

```bash
docker compose exec hadoop hadoop version
```

El archivo `docker-compose.yml` especifica exactamente **3 servicios**, una red propia `datamart_net`, datos de entrada montados solo lectura, volumen nombrado `postgres_data` para la base y archivo `.env` para las credenciales. `api` depende de `db`.

## B. SSH sin contraseña

Las llaves Ed25519 se **generan durante el primer arranque**, no se incluyen en Git ni en el Dockerfile. Se conservan en el volumen nombrado `ssh_keys`, compartido en solo lectura con la API. El usuario remoto es `hadoop`. La autenticación por contraseña está desactivada.

SSH local desde Hadoop:

```bash
docker compose exec -u hadoop hadoop ssh -i /shared-ssh/id_ed25519 -o StrictHostKeyChecking=accept-new -o BatchMode=yes hadoop@localhost 'whoami'
```

SSH desde el contenedor API hacia Hadoop (por nombre de servicio):

```bash
docker compose exec api ssh -o BatchMode=yes hadoop@hadoop whoami
```

Ambas conexiones deben devolver `hadoop` sin pedir contraseña. El cliente API tiene `IdentityFile /shared-ssh/id_ed25519` configurado en su imagen; la llave privada solo existe en el volumen Docker. Si el host SSH cambia sus llaves tras una recreación, recrea también API para limpiar `known_hosts`.

## C. MapReduce y comparativa de rendimiento

El `mapper.py` procesa cada línea con `csv.reader`, descarta el encabezado y las filas mal formadas, extrae `AAAA-MM` y emite `categoria|mes<TAB>centavos`. Hadoop ordena por clave antes de enviar datos al `reducer.py`, que suma los centavos y produce `categoria|mes<TAB>ingreso`.

La ejecución es automática en `scripts/ejecutar_pipeline.sh`. Para ver la salida:

```bash
docker compose exec hadoop sh -c 'head /data/output/resultado/part-00000'
```

El proceso ejecuta también `secuencial.py` sobre el mismo dataset, compara todos los pares clave/valor con `comparar.py` y falla si existe alguna diferencia. Los tiempos se miden con el reloj de la propia ejecución y se guardan en `evidencias/tiempos.log`. Revisa también `evidencias/mapreduce.log`.

### Tiempos reales y resultado de comparación

**Mediciones realizadas el 9 de noviembre de 2026 en Windows 11 / Docker Desktop, con el dataset de la matrícula 125052411.**

| Método | Tiempo real (segundos) |
|---|---:|
| Hadoop MapReduce (standalone) | **61 s** |
| Python secuencial | **55 s** |

**Coincidencia comprobada:** `COINCIDENCIA_TOTAL: 120 claves`. Se cargaron `120 registros agregados` en PostgreSQL y el registro de prueba `PruebaExamen` persistió tras `docker compose down` y `docker compose up -d`.

**Interpretación:** Con un único archivo de unos 400 MB y Hadoop en modo standalone, un script Python secuencial puede ser más rápido porque evita el costo de inicialización del job, ejecución de procesos, serialización y ordenamiento que introduce Hadoop Streaming. Hadoop destaca cuando los datos son considerablemente mayores, se procesan en paralelo a través de múltiples nodos o se necesitan capacidades de escalabilidad y tolerancia a fallos. En esta ejecución, Python secuencial fue **6 s más rápido** (aproximadamente 9,8 % menos tiempo que los 61 s de MapReduce).

## D. Integración con PostgreSQL y API

`cargar_resultados.py` lee el archivo `part-00000` y realiza UPSERT sobre la tabla `resultados (categoria, mes, ingreso_total)`, con llave primaria compuesta `(categoria, mes)`. El proceso es repetible sin duplicar grupos.

API con Swagger UI: <http://localhost:8000/docs> (si usas `API_PORT=8000`).

```bash
curl http://localhost:8000/salud
curl http://localhost:8000/resultados
curl http://localhost:8000/resultados/Electronica
curl 'http://localhost:8000/resultados/Electronica?mes=2025-01'
```

POST de prueba desde Linux/macOS:

```bash
curl -X POST http://localhost:8000/resultados \
  -H 'Content-Type: application/json' \
  -d '{"categoria":"Prueba","mes":"2025-01","ingreso_total":123.45}'
```

En Windows se recomienda usar `http://localhost:8000/docs` → **POST /resultados** → **Try it out** para evitar diferencias de escape en PowerShell.

### Persistencia

```bash
docker compose down
docker compose up --build
curl http://localhost:8000/resultados
```

`postgres_data` se conserva, por lo que las filas siguen presentes. **Observación:** al volver a arrancar, el pipeline también vuelve a calcular e importar los valores originales; el registro `Prueba` sirve para demostrar que la fila insertada por POST persiste si no se borra. Si haces `docker compose down -v`, se eliminan `postgres_data`, `hadoop_output` y `ssh_keys`; al levantar otra vez, el pipeline regenera el cálculo y repuebla automáticamente la tabla.

## E. Teoría (3–5 líneas por respuesta)

**1. Modos Hadoop y HDFS.** Standalone ejecuta el procesamiento en un solo equipo y usa archivos locales, sin HDFS. Pseudo-distribuido ejecuta los demonios Hadoop como procesos separados en una sola máquina y puede usar HDFS. Totalmente distribuido ejecuta los demonios en varios nodos y emplea HDFS para almacenamiento distribuido. En este examen se utiliza standalone.

**2. ¿Por qué montar el dataset como volumen?** El dataset es grande y copiarlo con `COPY` aumentaría el tamaño de la imagen y el tiempo de construcción. El montaje permite cambiar o regenerar el archivo sin reconstruir Hadoop. Además, el montaje `:ro` impide que el contenedor modifique el original y facilita no subir CSV a Git.

**3. ¿Qué pasa al hacer `down` y `down -v`?** `docker compose down` elimina contenedores y redes del proyecto, pero conserva los volúmenes nombrados; PostgreSQL mantiene sus datos. `docker compose down -v` elimina también los volúmenes nombrados declarados en Compose, destruyendo los datos persistidos del proyecto. Si el pipeline se vuelve a ejecutar puede recalcularlos desde el CSV.

**4. ¿Por qué MapReduce no siempre es más rápido?** Hadoop agrega tiempo de arranque, planificación, serialización y ordenamiento. Para 400 MB en un solo equipo, esos costos pueden superar los beneficios de paralelismo y Python simple puede ganar. MapReduce conviene con volúmenes enormes, varios nodos y trabajos repetitivos que aprovechan la distribución, especialmente si hay requerimientos de resiliencia.

**5. CMD / ENTRYPOINT y COPY / ADD.** `CMD` ofrece un comando o argumentos por defecto que pueden reemplazarse al ejecutar el contenedor. `ENTRYPOINT` define el ejecutable principal y los argumentos de ejecución suelen añadirse a él. `COPY` copia archivos del contexto de construcción a la imagen; `ADD` añade funciones como extraer ciertos archivos comprimidos locales y obtener archivos desde URL. Para copias normales, es preferible `COPY`.

## F. Preparación para defensa oral

**Cambiar puerto público de API:** editar `API_PORT=8080` en `.env`; ejecutar `docker compose up -d --force-recreate api`; acceder a `http://localhost:8080/docs`. El puerto dentro del contenedor sigue siendo `8000`.

**Cambiar agregación:** en `mapper.py`, clave actual = `categoria|mes`, valor = `cantidad * precio en centavos`; para filtrar por mes, comprobar la fecha antes de `print`. Para calcular promedio por grupo, emitir `ingreso_centavos<TAB>1` y agregar sumas y contadores en `reducer.py`. Adaptar también `secuencial.py`, `comparar.py` y la tabla/API para mantener coherencia.

**Borrar volumen y recargar:** `docker compose down -v` seguido de `docker compose up --build`. Esta acción elimina datos persistidos del proyecto. El CSV en `datos/` no se borra porque es un bind mount del host.

**Diagnóstico:** `docker compose ps`, `docker compose logs hadoop`, `docker compose logs api`, `docker compose logs db`, `docker compose exec hadoop hadoop version` y comprobar `evidencias/`.

## Evidencias y comprobaciones del examen

1. `hadoop version` (captura / `evidencias/hadoop_version.log`).
2. SSH local y SSH API → Hadoop sin contraseña (`evidencias/ssh_local.log` + captura del segundo comando).
3. Job MapReduce y `part-00000` (captura de terminal y `evidencias/mapreduce.log`).
4. Tiempos reales de ambos métodos y coincidencia (`evidencias/tiempos.log`).
5. Respuesta de `GET /resultados`, filtro por categoría y POST en Swagger.
6. `docker compose down` + posterior consulta que pruebe persistencia.

## Publicación GitHub

Desde la raíz del proyecto:

```bash
git init
git add .
git status
git commit -m "Examen P2 DataMart: Docker Hadoop MapReduce API"
# Crear repositorio vacío en GitHub y establecer su URL como origin.
git branch -M main
git remote add origin URL_DE_TU_REPOSITORIO
git push -u origin main
```

Revisar **antes de publicar**: `git status` y `git ls-files` no deben contener `*.csv` ni `.env`, ni claves privadas. El ZIP de la entrega tampoco contiene CSV generado ni contraseñas.

## Estado de verificación al 9 de noviembre de 2026

En el equipo del estudiante se verificaron: compilación de imágenes Docker, tres contenedores operativos, `Hadoop 3.4.1`, procesamiento del dataset propio, `COINCIDENCIA_TOTAL: 120 claves`, tiempos de 61 s y 55 s, importación de 120 agregados, respuesta de `GET /resultados` y del filtro `GET /resultados/Ropa` (HTTP 200), escritura `POST /resultados` (HTTP 201), y persistencia de `PruebaExamen` tras recreación de contenedores. La configuración SSH local fue corregida y verificada; la conexión SSH desde API fue comprobada correctamente después de reconstruir los contenedores. No se afirma que ya se haya probado un despliegue en otra computadora.

### Capturas recomendadas

- `docker compose ps` con los tres servicios.
- `docker compose exec hadoop hadoop version` mostrando 3.4.1.
- `docker compose exec -u hadoop hadoop ssh -o BatchMode=yes localhost whoami` mostrando `hadoop`.
- `docker compose exec api ssh -o BatchMode=yes hadoop@hadoop whoami` mostrando `hadoop`.
- Consola o archivo `evidencias/tiempos.log` con 61 s / 55 s y `COINCIDENCIA_TOTAL: 120 claves`.
- Swagger con `GET /resultados` y `POST /resultados` (201).
- Salida de `GET /resultados/PruebaExamen` tras `down` y `up -d`.

### Antes del primer push

Desde Windows CMD: `git status --short`, `git check-ignore .env datos/ventas_125052411.csv`, `git ls-files`. Nunca agregar `.env`, CSV, llaves privadas ni `docker-compose.respaldo.yml` al repositorio. Revisa también los archivos de evidencia para que no contengan credenciales.
