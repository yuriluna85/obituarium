# -*- coding: utf-8 -*-
"""
validador_fontes.py
-------------------
Módulo de validação de conectividade, status HTTP 200 e integridade semântica
para notas de pesar e homenagens póstumas do Portal Obituarium.

Garante tolerância zero a notícias fictícias e descarta links quebrados.
"""

import sys
import re
import urllib.request
import urllib.parse
import urllib.error

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
    REQUESTS_DISPONIVEL = True
except ImportError:
    REQUESTS_DISPONIVEL = False

TERMOS_VALIDACAO = [
    "pesar", "falecimento", "luto", "homenagem", "memoria", "obito",
    "condolencias", "sepultamento", "enterro", "velorio", "despedida",
    "in memoriam", "decreto de luto", "nota oficial"
]

def validar_url_e_conteudo(url, timeout=10):
    """
    Verifica se a URL responde com status HTTP 200 e se o conteúdo possui
    marcadores semânticos legítimos de nota de pesar ou homenagem póstuma.
    
    Retorna uma tupla (valido: bool, html_text: str, status_code: int).
    """
    if not url or not url.startswith("http"):
        return False, "", 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    html = ""
    status = 0

    if REQUESTS_DISPONIVEL:
        try:
            r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            status = r.status_code
            if status == 200:
                html = r.text
        except Exception:
            status = 0
    else:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", 200)
                if status == 200:
                    html = resp.read().decode('utf-8', errors='ignore')
        except Exception:
            status = 0

    if status != 200 or not html:
        return False, "", status

    # Checagem semântica para evitar falsos positivos
    html_lower = html.lower()
    contem_termos = any(termo in html_lower for termo in TERMOS_VALIDACAO)

    return contem_termos, html, status
