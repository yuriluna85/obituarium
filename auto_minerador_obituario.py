# -*- coding: utf-8 -*-
"""
auto_minerador_obituario.py (v2.0)
----------------------------------
Motor autônomo de busca, raspagem profunda e curadoria solene de notas de pesar,
decretos de luto oficial e homenagens póstumas emitidas no Brasil.

Recursos:
1. Filtro Positivo Rigoroso: Apenas atos oficiais, notas de pesar e homenagens póstumas.
2. Filtro Negativo de Expurgo: Descarta acidentes na rodovia, crimes, novelas, shows e esportes.
3. Higienização Fina de Texto: html.unescape() e remoção de sufixos de agências.
4. Raspagem Profunda de Retratos (Scrapling Deep Photo Miner) com descarte de logos.
5. Deduplicação e Persistência Blindada em data/YYYY/MM/obituario_YYYY_MM.csv.
"""

import os
import sys
import csv
import json
import hashlib
import argparse
import re
import html
from datetime import datetime
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import urllib.error

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import do validador de fontes
try:
    from validador_fontes import validar_url_e_conteudo
except ImportError:
    def validar_url_e_conteudo(url, timeout=10):
        return True, "", 200

# Camada defensiva de scraping
try:
    import requests
    REQUESTS_DISPONIVEL = True
except ImportError:
    REQUESTS_DISPONIVEL = False

try:
    from bs4 import BeautifulSoup
    BS4_DISPONIVEL = True
except ImportError:
    BS4_DISPONIVEL = False

try:
    from scrapling import Fetcher
    SCRAPLING_DISPONIVEL = True
except ImportError:
    SCRAPLING_DISPONIVEL = False

    class FallbackResponse:
        def __init__(self, body_bytes, status_code=200):
            self.body = body_bytes
            self.status_code = status_code
            self.text = body_bytes.decode('utf-8', errors='ignore') if isinstance(body_bytes, bytes) else str(body_bytes)

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

# Blacklist de termos que NÃO são homenagens póstumas (notícias de acidentes, crimes, exposições ou entretenimento)
TERMOS_BLACKLIST = [
    "acidente", "colisão", "capotamento", "atropelamento", "na br", "rodovia", "br-",
    "assassinato", "homicídio", "tiroteio", "executado", "preso", "baleado", "chacina",
    "novela", "show", "carnaval", "festival", "futebol", "jogos dos", "campeonato", "enredo",
    "xadrez", "cordel", "samba de mesa", "cinema", "parques de", "programação", "cobrança indevida",
    "reclame aqui", "terremoto", "um minuto de silêncio", "exposição em homenagem", "torcedor",
    "resgates de", "fase final", "terá um minuto"
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

def limpar_html_e_entidades(texto):
    """Decodifica entidades HTML (&nbsp;, &quot;) e remove tags."""
    if not texto:
        return ""
    texto_decodificado = html.unescape(texto)
    sem_tags = re.sub(r'<[^>]+>', ' ', texto_decodificado)
    # Remove espaços e quebras redundantes
    limpo = ' '.join(sem_tags.split())
    return limpo.strip()

def normalizar_nome_homenageado(titulo):
    """
    Extrai com precisão cirúrgica o nome da pessoa homenageada a partir do título da nota.
    Exemplo: 'Nota de Pesar: Adélia dos Santos Oliveira - News Rondônia' -> 'Adélia dos Santos Oliveira'
    """
    if not titulo:
        return ""
    limpo = limpar_html_e_entidades(titulo)
    
    # 1. Remove prefixos de atos solenes e prefeituras
    limpo = re.sub(r'^(nota de pesar|luto oficial|comunicado de falecimento e missa|comunicado de falecimento|comunicado|pesar|homenagem póstuma|homenagem|in memoriam|luto na|luto)[:\s\-\–—]+', '', limpo, flags=re.IGNORECASE)
    limpo = re.sub(r'^(prefeitura de [^\-\–—\|]+ decreta luto oficial pelo falecimento de|prefeitura decreta luto pelo falecimento de|governador decreta luto oficial pela morte de|paranaguá decreta luto de três dias pela morte do ex-prefeito|paranaguá decreta luto de três dias pela morte de)\s+', '', limpo, flags=re.IGNORECASE)
    
    # 2. Remove sufixos de veículos e portais após traço, barra ou hífen
    limpo = re.sub(r'(\s*[\-\–—\|]\s*.*)$', '', limpo)
    
    # 3. Limpeza de pronomes de tratamento e expressões institucionais
    limpo = re.sub(r'^(pelo falecimento de|pelo falecimento da|pela morte de|pelo passamento de|do ilmo sr\.?|da ilma sra\.?|do exmo des\.?|exmo des\.?|ilmo dr\.?|ilma dra\.?|ilmo sr\.?|ilma sra\.?|residente jurídica|do professor|da professora|do servidor|da servidora|professor emérito|prof\. emérito|prof\.|profa\.)\s+', '', limpo, flags=re.IGNORECASE)
    
    return limpo.strip()

def eh_homenagem_postuma_valida(titulo, texto=""):
    """
    Valida se a matéria é genuinamente uma homenagem póstuma ou nota de pesar,
    descartando crimes, acidentes e falsos positivos de eventos.
    """
    comb = (titulo + " " + texto).lower()
    
    # Checagem de Blacklist
    if any(termo in comb for termo in TERMOS_BLACKLIST):
        return False
    
    # Checagem de Marcadores Solenes Positivos Obrigatórios
    marcadores_positivos = [
        "nota de pesar", "luto oficial", "decretou luto", "decreta luto",
        "homenagem póstuma", "in memoriam", "comunicado de falecimento",
        "comunica com pesar", "profundo pesar", "pesar institucional",
        "condolências", "sessão solene em memória"
    ]
    
    return any(m in comb for m in marcadores_positivos)

def extrair_hash_registro(nome, instituicao=""):
    """Gera um hash curto para deduplicação semântica rápida."""
    base = f"{normalizar_nome_homenageado(nome).lower()}|{instituicao.lower()}"
    return hashlib.md5(base.encode('utf-8')).hexdigest()[:12]

def carregar_dados_existentes(caminho_csv):
    """Carrega dados existentes do CSV de forma blindada contra colunas excedentes."""
    registros = []
    if os.path.exists(caminho_csv):
        try:
            with open(caminho_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    limpo = {col: str(row.get(col, "") or "").strip() for col in CSV_COLUNAS}
                    if limpo.get("id") and limpo.get("nome_homenageado"):
                        registros.append(limpo)
        except Exception:
            return []
    return registros

def salvar_dados_csv(caminho_csv, registros):
    """Salva a lista completa de registros no arquivo CSV ordenados do mais recente para o mais antigo."""
    def chave_data(r):
        d_pub = r.get("data_publicacao", "")
        d_col = r.get("data_coleta", "")
        d_fal = r.get("data_falecimento", "")
        return (d_pub or d_col or d_fal or "1970-01-01 00:00:00")

    registros_ordenados = sorted(registros, key=chave_data, reverse=True)

    with open(caminho_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=CSV_COLUNAS, 
            extrasaction='ignore', 
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        for r in registros_ordenados:
            item_sanitizado = {
                col: str(r.get(col, "") or "").replace("\r", " ").replace("\n", " ").strip()
                for col in CSV_COLUNAS
            }
            writer.writerow(item_sanitizado)

def extrair_retrato_e_artigo_profundo(url):
    """
    Scrapling Deep Photo Miner: acessa a página original para raspar o retrato
    do homenageado (og:image / article img) e o corpo de texto integral.
    """
    foto = ""
    texto_expandido = ""
    fetcher = Fetcher()
    
    # Palavras e domínios de logos/placeholders para descarte absoluto
    blacklist_foto = [
        "logo", "icon", "placeholder", "default", "avatar", "googleusercontent", 
        "gstatic", "banner", "share", "fallback", "favicon", "google_news"
    ]
    
    try:
        resp = fetcher.get(url, timeout=8)
        html_raw = resp.body.decode('utf-8', errors='ignore') if isinstance(resp.body, bytes) else str(resp.body)
        
        if BS4_DISPONIVEL:
            soup = BeautifulSoup(html_raw, "html.parser")
            
            # 1. Metatag OpenGraph
            og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if og_img and og_img.get("content"):
                candidata = og_img["content"].strip()
                if candidata.startswith("http") and not any(b in candidata.lower() for b in blacklist_foto):
                    foto = candidata
            
            # 2. Primeira imagem do artigo se OpenGraph for genérico
            if not foto:
                art_img = soup.select_one("article img, .noticia img, .materia img, .content img, figure img")
                if art_img and art_img.get("src"):
                    candidata = art_img["src"].strip()
                    if candidata.startswith("http") and not any(b in candidata.lower() for b in blacklist_foto):
                        foto = candidata
            
            # 3. Corpo textual da nota
            artigo = soup.find("article") or soup.find("div", class_=re.compile(r'(content|materia|noticia|post|entry)', re.I))
            if artigo:
                texto_expandido = limpar_html_e_entidades(artigo.get_text())
        else:
            m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html_raw, re.I)
            if m:
                candidata = m.group(1).strip()
                if candidata.startswith("http") and not any(b in candidata.lower() for b in blacklist_foto):
                    foto = candidata
    except Exception:
        pass
    
    return foto, texto_expandido

def minerar_google_news_global():
    """
    Busca no Google News RSS brasileiro por atos solenes, luto oficial e notas de pesar legítimas.
    """
    print("  [1/3] Minerando Google News RSS Brasil com Filtros Solenes...")
    novos = []
    fetcher = Fetcher()

    queries = [
        '"nota de pesar" site:.br',
        '"luto oficial" site:.br',
        '"decretou luto oficial" site:.br',
        '"homenagem póstuma" site:.br',
        '"comunicado de falecimento" site:.br'
    ]

    for q in queries:
        try:
            url_encoded = urllib.parse.quote(q)
            rss_url = f"https://news.google.com/rss/search?q={url_encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
            resp = fetcher.get(rss_url, timeout=12)
            root = ET.fromstring(resp.body)
            for item in root.findall(".//item")[:12]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                source_elem = item.find("source")
                fonte = source_elem.text if source_elem is not None else "Imprensa Nacional"

                clean_title = limpar_html_e_entidades(title)
                clean_desc = limpar_html_e_entidades(desc)

                # Aplicação rigorosa dos filtros solenes
                if not eh_homenagem_postuma_valida(clean_title, clean_desc):
                    continue

                nome_homenageado = normalizar_nome_homenageado(clean_title)
                if len(nome_homenageado) < 4:
                    continue

                # Raspagem profunda de retrato e artigo
                foto, texto_exp = extrair_retrato_e_artigo_profundo(link)
                texto_final = texto_exp if texto_exp else clean_desc

                tipo = "Luto Oficial" if "luto" in clean_title.lower() else ("Homenagem Póstuma" if "homenagem" in clean_title.lower() else "Nota de Pesar")
                
                cat = "Educação e Ciência" if any(k in clean_title.lower() for k in ["prof", "doutor", "reitor", "universidade", "pesquisador", "docente"]) else \
                      ("Gestão Pública" if any(k in clean_title.lower() for k in ["prefeito", "governador", "vereador", "servidor", "tribunal", "oab"]) else "Sociedade")

                novos.append({
                    "id": extrair_hash_registro(nome_homenageado, fonte),
                    "nome_homenageado": nome_homenageado,
                    "data_falecimento": datetime.now().strftime("%Y-%m-%d"),
                    "data_publicacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "instituicao_fonte": fonte,
                    "tipo_nota": tipo,
                    "categoria_atuacao": cat,
                    "estado_uf": "BR",
                    "municipio": "Nacional",
                    "resumo_homenagem": clean_desc[:240].strip() + ("..." if len(clean_desc) > 240 else ""),
                    "texto_integral": texto_final,
                    "url_origem": link,
                    "url_foto": foto,
                    "data_coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            print(f"    [Aviso Google News]: {e}")

    return novos

def minerar_fontes_institucionais_academicas():
    """
    Varre portais e feeds RSS institucionais de universidades e centros federais.
    """
    print("  [2/3] Minerando Rede Universitária e Centros Federais...")
    novos = []
    fetcher = Fetcher()

    fontes = [
        {
            "nome": "Jornal da USP",
            "url": "https://jornal.usp.br/feed/",
            "uf": "SP",
            "municipio": "São Paulo",
            "filtro": ["pesar", "falecimento", "luto", "homenagem", "memoria", "obito"]
        }
    ]

    for f in fontes:
        try:
            page = fetcher.get(f["url"], timeout=12)
            root = ET.fromstring(page.body)
            for item in root.findall(".//item")[:10]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""

                clean_desc = limpar_html_e_entidades(desc)
                clean_title = limpar_html_e_entidades(title)
                texto_comb = (clean_title + " " + clean_desc).lower()

                if any(termo in texto_comb for termo in f["filtro"]) and eh_homenagem_postuma_valida(clean_title, clean_desc):
                    nome_homenageado = normalizar_nome_homenageado(clean_title)
                    tipo = "Luto Oficial" if "luto" in texto_comb else ("Nota de Pesar" if "pesar" in texto_comb else "Homenagem Póstuma")
                    foto, texto_exp = extrair_retrato_e_artigo_profundo(link)

                    novos.append({
                        "id": extrair_hash_registro(nome_homenageado, f["nome"]),
                        "nome_homenageado": nome_homenageado,
                        "data_falecimento": datetime.now().strftime("%Y-%m-%d"),
                        "data_publicacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "instituicao_fonte": f["nome"],
                        "tipo_nota": tipo,
                        "categoria_atuacao": "Educação e Ciência",
                        "estado_uf": f["uf"],
                        "municipio": f["municipio"],
                        "resumo_homenagem": clean_desc[:240].strip() + ("..." if len(clean_desc) > 240 else ""),
                        "texto_integral": texto_exp if texto_exp else clean_desc,
                        "url_origem": link,
                        "url_foto": foto,
                        "data_coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        except Exception as e:
            print(f"    [Aviso Institucional {f['nome']}]: {e}")

    return novos

def executar_mineracao_obituario(dry_run=False):
    """
    Executa a mineração solene v2.0, filtra rigorosamente homenagens póstumas,
    raspa retratos profundos e atualiza a base CSV cronológica.
    """
    print("=" * 75)
    print("OBITUARIUM v2.0 - PORTAL DE HOMENAGENS POSTUMAS E ATOS SOLENES (BRASIL)")
    print("=" * 75)

    caminho_csv = obter_caminho_csv_mes_corrente()
    existentes = carregar_dados_existentes(caminho_csv)
    
    # Purificação da base existente e re-normalização de nomes
    existentes_validos = []
    for r in existentes:
        if eh_homenagem_postuma_valida(r["nome_homenageado"], r["resumo_homenagem"]):
            nome_norm = normalizar_nome_homenageado(r["nome_homenageado"])
            if len(nome_norm) >= 5 and not nome_norm.lower().startswith("e missa"):
                r["nome_homenageado"] = nome_norm
                existentes_validos.append(r)
    
    ids_existentes = {r["id"] for r in existentes_validos}
    nomes_existentes = {normalizar_nome_homenageado(r["nome_homenageado"]).lower() for r in existentes_validos}

    # 1. Coleta solene
    coleta_google = minerar_google_news_global()
    coleta_academica = minerar_fontes_institucionais_academicas()
    total_bruto = coleta_google + coleta_academica

    print(f"\nTotal bruto capturado: {len(total_bruto)}")

    # 2. Deduplicação e Descarte de Repetidas
    print("  [3/3] Aplicando deduplicação e validação de retratos...")
    ineditos = []
    duplicados_descartados = 0

    for item in total_bruto:
        nome_norm = normalizar_nome_homenageado(item["nome_homenageado"]).lower()
        if item["id"] in ids_existentes or nome_norm in nomes_existentes:
            duplicados_descartados += 1
            continue
        
        ids_existentes.add(item["id"])
        nomes_existentes.add(nome_norm)
        ineditos.append(item)

    print(f"Notícias repetidas descartadas: {duplicados_descartados}")
    print(f"Novas homenagens póstumas solenes e inéditas: {len(ineditos)}")
    print(f"Total de registros válidos no acervo mensal: {len(existentes_validos) + len(ineditos)}")

    # 3. Gravação e Persistência
    if not dry_run:
        consolidado = ineditos + existentes_validos
        salvar_dados_csv(caminho_csv, consolidado)
        print(f"\n[OK] Base CSV atualizada com sucesso em: {caminho_csv}")
    elif dry_run:
        print("\n[INFO] Modo --dry-run ativo: nenhum registro foi persistido no disco.")

    print("=" * 75)
    return ineditos or existentes_validos

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minerador Solene de Homenagens Póstumas do Obituarium v2.0.")
    parser.add_argument("--dry-run", action="store_true", help="Executa a busca sem persistir no CSV")
    args = parser.parse_args()

    executar_mineracao_obituario(dry_run=args.dry_run)
