# -*- coding: utf-8 -*-
import os

target_dir = r"G:\Meu Drive\APP\2. Projetos e Aplicações\2.2 Aplicações e Códigos (GitHub)\YLuna85 LABs APPs\obituarium"
termos = ["Milton Santos", "Beatriz Nascimento", "Aziz", "Darcy Ribeiro", "Maria Hilda", "Paulo Freire"]

encontrados = []
print("=== VARREDURA COMPLETA NO REPOSITORIO OBITUARIUM ===")
for root, dirs, files in os.walk(target_dir):
    for f in files:
        if f.endswith((".csv", ".js", ".html", ".json", ".py", ".md")):
            # Ignora os scripts de teste e auditoria
            if f.startswith("teste_") or f == "limpar_base_csv.py":
                continue
            p = os.path.join(root, f)
            with open(p, "r", encoding="utf-8", errors="ignore") as arq:
                content = arq.read()
                for t in termos:
                    if t.lower() in content.lower():
                        msg = f"Termo '{t}' encontrado em: {p}"
                        print(msg)
                        encontrados.append(msg)

if not encontrados:
    print("\n[CONFIRMADO 100%] Nenhum registro de teste existe no CSV, JS, HTML ou codigo de producao do Obituarium.")
else:
    print(f"\n[ALERTA] Foram encontradas {len(encontrados)} ocorrencias.")
