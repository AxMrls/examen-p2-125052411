#!/bin/sh
set -eu
DATA="/data/input/ventas_${MATRICULA}.csv"
OUT=/data/output/resultado
mkdir -p /evidencias
if [ ! -s "$DATA" ]; then
  echo "FALTA EL DATASET: $DATA. Ejecuta python3 scripts/generar_dataset.py 125052411 desde tu equipo y mueve el CSV a datos/." >&2
  exit 1
fi
hadoop version > /evidencias/hadoop_version.log 2>&1
# SSH local sin pedir password, como evidencia.
ssh -i /shared-ssh/id_ed25519 -o StrictHostKeyChecking=accept-new -o BatchMode=yes hadoop@localhost 'echo SSH_LOCAL_OK' > /evidencias/ssh_local.log 2>&1
rm -rf "$OUT"
cd /opt/proyecto/mapreduce
START=$(date +%s)
hadoop jar "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=1 \
  -files mapper.py,reducer.py \
  -input "$DATA" -output "$OUT" \
  -mapper 'python3 mapper.py' -reducer 'python3 reducer.py' \
  > /evidencias/mapreduce.log 2>&1
END=$(date +%s)
MR=$((END-START))
START=$(date +%s)
python3 /opt/proyecto/mapreduce/secuencial.py "$DATA" /data/output/secuencial.tsv
END=$(date +%s)
SEQ=$((END-START))
python3 /opt/proyecto/scripts/comparar.py "$OUT/part-00000" /data/output/secuencial.tsv
printf 'MapReduce: %s segundos\nSecuencial: %s segundos\n' "$MR" "$SEQ" | tee /evidencias/tiempos.log
python3 /opt/proyecto/scripts/cargar_resultados.py "$OUT/part-00000"
echo 'PIPELINE_COMPLETO' | tee /evidencias/estado.log
