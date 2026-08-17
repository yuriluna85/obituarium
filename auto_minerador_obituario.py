# -*- coding: utf-8 -*-
"""
auto_minerador_obituario.py
----------------------------
Motor autônomo de busca, raspagem e indexação de notas de pesar públicas,
decretos de luto oficial e homenagens póstumas emitidas no Brasil.

Gera bases de dados particionadas em data/YYYY/MM/obituario_YYYY_MM.csv.
Possui camada de resiliência multi-máquinas (FallbackFetcher).
"""

import os
import sys
import csv
import json
import hashlib
import argparse
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import urllib.error

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Camada defensiva de scraping
try:
    import requests
    REQUESTS_DISPONIVEL = True
except ImportError:
    REQUESTS_DISPONIVEL = False

try:
    from scrapling import Fetcher
    SCRAPLING_DISPONIVEL = True
except ImportError:
    SCRAPLING_DISPONIVEL = False

    class FallbackResponse:
        def __init__(self, body_bytes, status_code=200):
            self.body = body_bytes
            self.status_code = status_code

    class Fetcher:
        def __init__(self):
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
            }

        def get(self, url, timeout=15):
            if REQUESTS_DISPONIVEL:
                try:
                    r = requests.get(url, headers=self.headers, timeout=timeout)
                    return FallbackResponse(r.content, r.status_code)
                except Exception:
                    pass
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return FallbackResponse(resp.read(), getattr(resp, "status", 200))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) if os.path.basename(SCRIPT_DIR) == "minerador" else SCRIPT_DIR
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

CSV_COLUNAS = [
    "id", "nome_homenageado", "data_falecimento", "data_publicacao",
    "instituicao_fonte", "tipo_nota", "categoria_atuacao", "estado_uf",
    "municipio", "resumo_homenagem", "texto_integral", "url_origem",
    "url_foto", "data_coleta"
]

def obter_caminho_csv_mes_corrente(data_ref=None):
    """Retorna o caminho particionado data/YYYY/MM/obituario_YYYY_MM.csv."""
    agora = data_ref or datetime.now()
    ano_str = agora.strftime("%Y")
    mes_str = agora.strftime("%m")
    pasta_mes = os.path.join(DATA_DIR, ano_str, mes_str)
    os.makedirs(pasta_mes, exist_ok=True)
    nome_arquivo = f"obituario_{ano_str}_{mes_str}.csv"
    return os.path.join(pasta_mes, nome_arquivo)

def extrair_hash(texto):
    """Gera um hash curto para deduplicação semântica rápida."""
    return hashlib.md5(texto.strip().lower().encode('utf-8')).hexdigest()[:12]

def carregar_dados_existentes(caminho_csv):
    """Carrega dados existentes do CSV para evitar duplicidades."""
    registros = []
    if os.path.exists(caminho_csv):
        try:
            with open(caminho_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    registros.append(row)
        except Exception:
            return []
    return registros

def salvar_dados_csv(caminho_csv, registros):
    """Salva a lista completa de registros no arquivo CSV particionado."""
    with open(caminho_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUNAS)
        writer.writeheader()
        for r in registros:
            writer.writerow(r)

def limpar_html(texto):
    """Higieniza tags HTML e normaliza espaçamentos."""
    if not texto:
        return ""
    texto = re.sub(r'<[^>]+>', '', texto)
    return ' '.join(texto.split())

def minerar_fontes_institucionais():
    """
    Executa a mineração de feeds institucionais e portais públicos de notícias de pesar.
    """
    print("Minerando fontes institucionais e portais de noticias (USP, IFs, UFRJ, G1)...")
    novos = []
    fetcher = Fetcher()

    fontes_rss = [
        {
            "nome": "Jornal da USP",
            "url": "https://jornal.usp.br/feed/",
            "uf": "SP",
            "municipio": "São Paulo",
            "filtro": ["pesar", "falecimento", "luto", "homenagem", "memoria", "obito"]
        },
        {
            "nome": "IF Baiano Notícias",
            "url": "https://ifbaiano.edu.br/portal/feed/",
            "uf": "BA",
            "municipio": "Salvador",
            "filtro": ["pesar", "falecimento", "luto"]
        }
    ]

    for f in fontes_rss:
        try:
            page = fetcher.get(f["url"], timeout=12)
            root = ET.fromstring(page.body)
            for item in root.findall(".//item")[:15]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""

                clean_desc = limpar_html(desc)
                clean_title = limpar_html(title)

                texto_comb = (clean_title + " " + clean_desc).lower()
                if any(termo in texto_comb for termo in f["filtro"]):
                    tipo = "Luto Oficial" if "luto" in texto_comb else ("Nota de Pesar" if "pesar" in texto_comb else "Homenagem Póstuma")
                    cat = "Educação e Ciência" if any(k in f["nome"].lower() for k in ["usp", "if", "uf", "universidade"]) else "Sociedade"

                    novos.append({
                        "id": extrair_hash(clean_title),
                        "nome_homenageado": clean_title.replace("Nota de pesar:", "").replace("Nota de Pesar -", "").strip(),
                        "data_falecimento": datetime.now().strftime("%Y-%m-%d"),
                        "data_publicacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "instituicao_fonte": f["nome"],
                        "tipo_nota": tipo,
                        "categoria_atuacao": cat,
                        "estado_uf": f["uf"],
                        "municipio": f["municipio"],
                        "resumo_homenagem": clean_desc[:240].strip() + ("..." if len(clean_desc) > 240 else ""),
                        "texto_integral": clean_desc,
                        "url_origem": link,
                        "url_foto": "",
                        "data_coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        except Exception as e:
            print(f"  [Aviso na fonte {f['nome']}]: {e}")

    return novos

def executar_mineracao_obituario(dry_run=False):
    """Executa a coleta e consolida no CSV do mês corrente."""
    print("=" * 65)
    print("OBITUARIUM - MOTOR DE MINERACAO E INDEXACAO DE NOTAS DE PESAR")
    print("=" * 65)

    caminho_csv = obter_caminho_csv_mes_corrente()
    existentes = carregar_dados_existentes(caminho_csv)
    ids_existentes = {r["id"] for r in existentes}

    coletas = minerar_fontes_institucionais()
    ineditos = [c for c in coletas if c["id"] not in ids_existentes]

    print(f"\nTotal minerado nas fontes ativas: {len(coletas)} registros.")
    print(f"Novas notas de pesar ineditas: {len(ineditos)}")
    print(f"Registros ja consolidados no mes: {len(existentes)}")

    if not dry_run and ineditos:
        consolidado = ineditos + existentes
        salvar_dados_csv(caminho_csv, consolidado)
        print(f"Base CSV atualizada com sucesso em: {caminho_csv}")
    elif dry_run:
        print("Modo --dry-run ativo: nenhum arquivo foi gravado no disco.")

    print("=" * 65)
    return ineditos or existentes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minerador e Indexador de Notas de Pesar para o Obituarium.")
    parser.add_argument("--dry-run", action="store_true", help="Executa a busca sem persistir no CSV")
    args = parser.parse_args()

    executar_mineracao_obituario(dry_run=args.dry_run)
