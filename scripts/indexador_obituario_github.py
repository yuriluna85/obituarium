#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
indexador_obituario_github.py - Varredura de materias/ e geração de páginas HTML individuais
Portal: Obituarium (Laboratório YLuna85 LABs)
Executa em ambiente local ou dentro do GitHub Actions.
"""

import sys
import os
import re
import csv
import json
import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

CAMINHO_BASE = Path(__file__).resolve().parent.parent
DIR_MATERIAS = CAMINHO_BASE / 'materias'
DIR_PAGINAS = CAMINHO_BASE / 'paginas'
DIR_DATA_HOMENAGENS = CAMINHO_BASE / 'data' / 'homenagens'
CSV_PRODUCAO_MENSAL = CAMINHO_BASE / 'data' / '2026' / '08' / 'obituario_2026_08.csv'
ARQUIVO_TEMPLATE = CAMINHO_BASE / 'templates' / 'homenagem_template.html'


def converter_markdown_para_html(md_texto: str) -> str:
    linhas = md_texto.split('\n')
    html_partes = []
    em_paragrafo = []

    def fechar_paragrafo():
        if em_paragrafo:
            txt = ' '.join(em_paragrafo).strip()
            if txt:
                txt = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', txt)
                txt = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', txt)
                txt = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', txt)
                html_partes.append(f'<p>{txt}</p>')
            em_paragrafo.clear()

    for l in linhas:
        l_strip = l.strip()
        if not l_strip:
            fechar_paragrafo()
            continue

        if l_strip.startswith('## '):
            fechar_paragrafo()
            sub = l_strip[3:].strip()
            html_partes.append(f'<h2>{sub}</h2>')
        elif l_strip.startswith('# '):
            fechar_paragrafo()
            continue
        elif l_strip.startswith('### Fonte Original') or l_strip.startswith('---'):
            fechar_paragrafo()
            break
        else:
            em_paragrafo.append(l_strip)

    fechar_paragrafo()
    return '\n'.join(html_partes)


def extrair_metadados_homenagem(caminho_md: Path) -> dict:
    conteudo = caminho_md.read_text(encoding='utf-8')
    metadados = {}
    corpo_md = conteudo

    if conteudo.startswith('---'):
        partes = conteudo.split('---', 2)
        if len(partes) >= 3:
            bloco_yaml = partes[1]
            corpo_md = partes[2].strip()
            for linha in bloco_yaml.strip().split('\n'):
                if ':' in linha:
                    chave, valor = linha.split(':', 1)
                    chave = chave.strip()
                    valor = valor.strip().strip('"').strip("'")
                    metadados[chave] = valor

    nome = metadados.get('nome_homenageado')
    if not nome:
        match_nome = re.search(r'^#\s+Homenagem(?:\s+Solene)?:\s+(.+)$', corpo_md, flags=re.MULTILINE)
        nome = match_nome.group(1).strip() if match_nome else caminho_md.stem.replace('-', ' ').title()

    resumo = metadados.get('resumo', '')
    if not resumo:
        match_bio = re.search(r'##\s+Síntese Biográfica e Trajetória\s*\n+([^\n#]+)', corpo_md, flags=re.IGNORECASE)
        if match_bio:
            resumo = match_bio.group(1).strip()
        else:
            match_p = re.search(r'\n\n([^#\n][^\n]+)', corpo_md)
            resumo = match_p.group(1).strip() if match_p else nome

    instituicao = metadados.get('instituicao_fonte', 'Fonte Oficial')
    tipo_nota = metadados.get('tipo_nota', 'Nota de Pesar')
    categoria = metadados.get('categoria_atuacao', 'Sociedade')
    uf = metadados.get('estado_uf', 'BR')
    municipio = metadados.get('municipio', 'Nacional')
    data_falecimento = metadados.get('data_falecimento', '2026-08-20')
    url_origem = metadados.get('url_origem', '')

    if not url_origem:
        match_url = re.search(r'\[https?://[^\]]+\]\((https?://[^\)]+)\)', corpo_md)
        if match_url:
            url_origem = match_url.group(1).strip()

    data_pub_iso = metadados.get('data_sintese') or datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    data_publicacao_formatada = data_pub_iso.replace('T', ' ')[:19]

    slug = caminho_md.stem

    return {
        'id': metadados.get('id', f"obit-{slug[:12]}").replace('obit-', ''),
        'slug': slug,
        'nome_homenageado': nome,
        'data_falecimento': data_falecimento,
        'data_publicacao': data_publicacao_formatada,
        'instituicao_fonte': instituicao,
        'tipo_nota': tipo_nota,
        'categoria_atuacao': categoria,
        'estado_uf': uf,
        'municipio': municipio,
        'resumo_homenagem': resumo,
        'texto_integral': corpo_md.replace('\n', ' ').strip()[:500],
        'url_origem': url_origem,
        'url_foto': metadados.get('url_foto', ''),
        'data_coleta': data_publicacao_formatada,
        'corpo_md': corpo_md
    }


def gerar_pagina_html_obituario(item: dict, template_str: str) -> Path:
    dt = datetime.datetime.now()
    dir_pagina = DIR_PAGINAS / dt.strftime('%Y') / dt.strftime('%m') / dt.strftime('%d')
    dir_pagina.mkdir(parents=True, exist_ok=True)
    arquivo_html = dir_pagina / f"{item['slug']}.html"

    corpo_html = converter_markdown_para_html(item['corpo_md'])
    caminho_raiz = '../../../../'

    conteudo = template_str \
        .replace('{{NOME}}', item['nome_homenageado']) \
        .replace('{{RESUMO}}', item['resumo_homenagem']) \
        .replace('{{TIPO_NOTA}}', item['tipo_nota']) \
        .replace('{{CATEGORIA}}', item['categoria_atuacao']) \
        .replace('{{INSTITUICAO}}', item['instituicao_fonte']) \
        .replace('{{ESTADO_UF}}', item['estado_uf']) \
        .replace('{{MUNICIPIO}}', item['municipio']) \
        .replace('{{DATA_FALECIMENTO}}', item['data_falecimento']) \
        .replace('{{DATA_PUBLICACAO}}', item['data_publicacao']) \
        .replace('{{URL_ORIGINAL}}', item['url_origem']) \
        .replace('{{CORPO_HTML}}', corpo_html) \
        .replace('{{CAMINHO_RAIZ}}', caminho_raiz)

    arquivo_html.write_text(conteudo, encoding='utf-8')
    return arquivo_html


def indexar_homenagens():
    if not DIR_MATERIAS.exists():
        print(f'[AVISO] Pasta de matérias não encontrada em: {DIR_MATERIAS}')
        return

    template_str = ''
    if ARQUIVO_TEMPLATE.exists():
        template_str = ARQUIVO_TEMPLATE.read_text(encoding='utf-8')
    else:
        print(f'[ERRO] Template não encontrado em: {ARQUIVO_TEMPLATE}')
        return

    arquivos_md = sorted(list(DIR_MATERIAS.glob('**/*.md')), reverse=True)
    print(f'[INDEXAÇÃO OBITUARIUM] Encontrados {len(arquivos_md)} arquivos Markdown em {DIR_MATERIAS}')

    homenagens_novas = []
    urls_processadas = set()

    for arq in arquivos_md:
        try:
            item = extrair_metadados_homenagem(arq)
            if item['url_origem'] and item['url_origem'] not in urls_processadas:
                caminho_html = gerar_pagina_html_obituario(item, template_str)
                rel_html = str(caminho_html.relative_to(CAMINHO_BASE)).replace('\\', '/')
                item['url_materia'] = rel_html

                homenagens_novas.append({k: v for k, v in item.items() if k not in ('corpo_md', 'slug')})
                urls_processadas.add(item['url_origem'])
                print(f'[PÁGINA GERADA OBITUARIUM] {rel_html}')

        except Exception as e:
            print(f'[ERRO] Falha ao indexar {arq}: {e}')

    linhas_existentes = []
    campos_csv = [
        'id', 'nome_homenageado', 'data_falecimento', 'data_publicacao',
        'instituicao_fonte', 'tipo_nota', 'categoria_atuacao', 'estado_uf',
        'municipio', 'resumo_homenagem', 'texto_integral', 'url_origem',
        'url_foto', 'data_coleta', 'url_materia'
    ]

    if CSV_PRODUCAO_MENSAL.exists():
        with open(CSV_PRODUCAO_MENSAL, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            for r in leitor:
                if r.get('url_origem') not in urls_processadas:
                    linhas_existentes.append(r)

    base_final = homenagens_novas + linhas_existentes

    CSV_PRODUCAO_MENSAL.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PRODUCAO_MENSAL, mode='w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=campos_csv)
        escritor.writeheader()
        escritor.writerows(base_final)

    print(f'[SUCESSO OBITUARIUM] {len(base_final)} registros salvos em {CSV_PRODUCAO_MENSAL} com páginas HTML')


if __name__ == '__main__':
    indexar_homenagens()
