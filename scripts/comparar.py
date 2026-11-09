#!/usr/bin/env python3
import sys
from pathlib import Path

a, b = [dict(line.rstrip('\n').split('\t', 1) for line in Path(p).read_text().splitlines() if '\t' in line) for p in sys.argv[1:3]]
if a != b:
    diferencias = sorted(set(a) | set(b))
    ejemplos = [(k, a.get(k), b.get(k)) for k in diferencias if a.get(k) != b.get(k)]
    print('DIFERENCIAS:', ejemplos[:10], file=sys.stderr)
    sys.exit(1)
print(f'COINCIDENCIA_TOTAL: {len(a)} claves')
