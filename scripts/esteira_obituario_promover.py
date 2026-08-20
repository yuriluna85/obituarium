#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
esteira_obituario_promover.py - Promoção e publicação de homenagens solenes aprovadas
Portal: Obituarium (Laboratório YLuna85 LABs)
Migra da pré-curadoria para data/homenagens/AAAA/MM/DD/ e atualiza o CSV mensal.
"""

import sys
import os
import re
import csv
import json
import uuid
import argparse
import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

CAMINHO_BASE = Path(__file__).resolve().parent.parent
DIR_PRE_CURADORIA = CAMINHO_BASE / 'pre_curadoria'
DIR_HOMENAGENS_FINAL = CAMINHO_BASE / 'data' / 'homenagens'


def extrair_metadados_md(conteudo_md: str) -> tuple:
    metadados = {}
    corpo = conteudo_md
    if conteudo_md.startswith('---'):
        partes = conteudo_md.split('---', 2)
        if len(partes) >= 3:
            bloco_meta = partes[1]
            corpo = partes[2].strip()
            for linha in bloco_meta.splitlines():
                if ':' in linha:
                    chave, valor = linha.split(':', 1)
                    chave = chave.strip()
                    valor = valor.strip().strip('"').strip("'")
                    metadados[chave] = valor
    return metadados, corpo


def promover_homenagem_precuradoria(caminho_arquivo_str: str):
    caminho_origem = Path(caminho_arquivo_str)
    if not caminho_origem.is_absolute():
        caminho_origem = CAMINHO_BASE / caminho_origem

    if not caminho_origem.exists() or not caminho_origem.is_file():
        print(f'[ERRO] Arquivo de pré-curadoria não encontrado: {caminho_origem}')
        sys.exit(1)

    conteudo_md = caminho_origem.read_text(encoding='utf-8')
    metadados, corpo = extrair_metadados_md(conteudo_md)

    id_homenagem = metadados.get('id', f"obit-{uuid.uuid4().hex[:8]}")
    nome = metadados.get('nome_homenageado', caminho_origem.stem)
    instituicao = metadados.get('instituicao_fonte', 'Fonte Oficial')
    tipo_nota = metadados.get('tipo_nota', 'Nota de Pesar')
    categoria = metadados.get('categoria_atuacao', 'Sociedade')
    uf = metadados.get('estado_uf', 'BR')
    municipio = metadados.get('municipio', 'Nacional')
    data_falecimento = metadados.get('data_falecimento', '')
    url_origem = metadados.get('url_fonte_original', metadados.get('url_origem', ''))
    url_foto = metadados.get('url_foto', '')

    # Extrai o primeiro título em Markdown (# Homenagem: Nome)
    titulo_match = re.search(r'^#\s+(.+)$', corpo, flags=re.MULTILINE)
    titulo_final = titulo_match.group(1).strip() if titulo_match else f'Homenagem Solene: {nome}'
    corpo_limpo = re.sub(r'^#\s+.+\n*', '', corpo, flags=re.MULTILINE).strip()

    hoje = datetime.datetime.now()
    ano = hoje.strftime('%Y')
    mes = hoje.strftime('%m')
    dia = hoje.strftime('%d')
    slug = caminho_origem.stem

    # 1. Salva arquivo JSON individual temporal
    dir_destino_temporal = DIR_HOMENAGENS_FINAL / ano / mes / dia
    dir_destino_temporal.mkdir(parents=True, exist_ok=True)

    registro_json = {
        'id': id_homenagem,
        'slug': slug,
        'nome_homenageado': nome,
        'titulo': titulo_final,
        'instituicao_fonte': instituicao,
        'tipo_nota': tipo_nota,
        'categoria_atuacao': categoria,
        'estado_uf': uf,
        'municipio': municipio,
        'data_falecimento': data_falecimento,
        'data_publicacao': hoje.strftime('%Y-%m-%d %H:%M:%S'),
        'url_origem': url_origem,
        'url_foto': url_foto,
        'sintese_biografica': corpo_limpo,
        'status': 'publicada'
    }

    arquivo_json = dir_destino_temporal / f'{slug}.json'
    arquivo_json.write_text(json.dumps(registro_json, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[OK] Registro individual salvo em: {arquivo_json}')

    # 2. Atualiza a base CSV mensal do portal (data/AAAA/MM/obituario_AAAA_MM.csv)
    csv_mensal_dir = CAMINHO_BASE / 'data' / ano / mes
    csv_mensal_dir.mkdir(parents=True, exist_ok=True)
    arquivo_csv_mensal = csv_mensal_dir / f'obituario_{ano}_{mes}.csv'

    campos_csv_mensal = [
        'id', 'nome_homenageado', 'data_falecimento', 'data_publicacao',
        'instituicao_fonte', 'tipo_nota', 'categoria_atuacao', 'estado_uf',
        'municipio', 'resumo_homenagem', 'texto_integral', 'url_origem', 'url_foto', 'data_coleta'
    ]

    linhas_existentes = []
    if arquivo_csv_mensal.exists():
        with open(arquivo_csv_mensal, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            for r in leitor:
                if r.get('id') != id_homenagem and r.get('nome_homenageado') != nome:
                    linhas_existentes.append(r)

    nova_linha = {
        'id': id_homenagem.replace('obit-', ''),
        'nome_homenageado': nome,
        'data_falecimento': data_falecimento,
        'data_publicacao': hoje.strftime('%Y-%m-%d %H:%M:%S'),
        'instituicao_fonte': instituicao,
        'tipo_nota': tipo_nota,
        'categoria_atuacao': categoria,
        'estado_uf': uf,
        'municipio': municipio,
        'resumo_homenagem': corpo_limpo[:350].replace('\n', ' ') + '...',
        'texto_integral': corpo_limpo.replace('\n', ' '),
        'url_origem': url_origem,
        'url_foto': url_foto,
        'data_coleta': hoje.strftime('%Y-%m-%d %H:%M:%S')
    }

    linhas_existentes.insert(0, nova_linha)

    with open(arquivo_csv_mensal, mode='w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=campos_csv_mensal)
        escritor.writeheader()
        escritor.writerows(linhas_existentes)

    print(f'[OK] Base CSV de produção atualizada em: {arquivo_csv_mensal}')

    # 3. Move arquivo de pré-curadoria para histórico aprovados
    dir_historico = DIR_PRE_CURADORIA / 'historico_aprovados' / ano / mes
    dir_historico.mkdir(parents=True, exist_ok=True)
    destino_historico = dir_historico / caminho_origem.name
    caminho_origem.rename(destino_historico)
    print(f'[OK] Homenagem arquivada em: {destino_historico}')
    print(f'\n[SUCESSO] Homenagem solene promovida e pronta para o portal Obituarium!')


def listar_precuradoria():
    print('[INFO] Varrendo homenagens pendentes em pré-curadoria do Obituarium...')
    arquivos = list(DIR_PRE_CURADORIA.glob('**/*.md'))
    arquivos = [a for a in arquivos if 'historico_aprovados' not in str(a)]
    if not arquivos:
        print('[INFO] Nenhuma homenagem pendente em pré-curadoria.')
        return
    print(f'Total de homenagens pendentes: {len(arquivos)}')
    for idx, a in enumerate(arquivos, 1):
        rel = a.relative_to(CAMINHO_BASE)
        print(f'  [{idx}] {rel}')


def main():
    parser = argparse.ArgumentParser(description='Obituarium - Promover homenagem da pré-curadoria para publicação.')
    parser.add_argument('--arquivo', type=str, help='Caminho do arquivo .md em pré-curadoria')
    parser.add_argument('--listar', action='store_true', help='Lista homenagens pendentes em pré-curadoria')
    args = parser.parse_args()

    if args.listar:
        listar_precuradoria()
    elif args.arquivo:
        promover_homenagem_precuradoria(args.arquivo)
    else:
        listar_precuradoria()


if __name__ == '__main__':
    main()
