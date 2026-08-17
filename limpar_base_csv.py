# -*- coding: utf-8 -*-
import csv
import html
import re

csv_path = r"G:\Meu Drive\APP\2. Projetos e Aplicações\2.2 Aplicações e Códigos (GitHub)\YLuna85 LABs APPs\obituarium\data\2026\08\obituario_2026_08.csv"

registros_limpos = []
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    colunas = reader.fieldnames
    for r in reader:
        # Se for registro de teste antigo, ignora
        if any(nome in r.get("nome_homenageado", "") for nome in ["Milton Santos", "Beatriz Nascimento", "Aziz", "Darcy Ribeiro", "Maria Hilda", "Paulo Freire"]):
            continue
        
        # Limpar &nbsp; e entidades HTML de todos os campos
        for k in r:
            if r[k]:
                val = html.unescape(r[k])
                val = val.replace("&nbsp;", " ").replace("&quot;", '"').replace("&amp;", "&")
                val = " ".join(val.split())
                # Se for URL de foto com googleusercontent ou gstatic, limpa para usar avatar
                if k == "url_foto" and any(b in val.lower() for b in ["googleusercontent", "gstatic", "google_news", "logo"]):
                    val = ""
                r[k] = val
        registros_limpos.append(r)

with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for r in registros_limpos:
        writer.writerow(r)

print(f"CSV purificado com sucesso. Total de registros reais: {len(registros_limpos)}")
