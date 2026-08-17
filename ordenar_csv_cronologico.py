# -*- coding: utf-8 -*-
import csv

csv_path = r"G:\Meu Drive\APP\2. Projetos e Aplicações\2.2 Aplicações e Códigos (GitHub)\YLuna85 LABs APPs\obituarium\data\2026\08\obituario_2026_08.csv"

registros = []
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    colunas = reader.fieldnames
    for r in reader:
        registros.append(r)

# Ordenar do mais recente para o mais antigo
def chave_data(r):
    d_pub = r.get("data_publicacao", "")
    d_col = r.get("data_coleta", "")
    d_fal = r.get("data_falecimento", "")
    return (d_pub or d_col or d_fal or "1970-01-01 00:00:00")

registros_ordenados = sorted(registros, key=chave_data, reverse=True)

with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for r in registros_ordenados:
        writer.writerow(r)

print(f"Base CSV reordenada cronologicamente (Mais recente -> Mais antigo). Total: {len(registros_ordenados)}")
