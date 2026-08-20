#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
esteira_obituario_coletor.py - Coleta e estruturação de homenagens solenes reais
Portal: Obituarium (Laboratório YLuna85 LABs)
Opera estritamente com fontes e comunicados oficiais reais.
"""

import sys
import os
import csv
import uuid
import argparse
import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

CAMINHO_BASE = Path(__file__).resolve().parent.parent
ARQUIVO_CSV_MINERACAO = CAMINHO_BASE / 'data' / 'mineracao_obituario_bruta.csv'
CSV_REAL_EXISTENTE = CAMINHO_BASE / 'data' / '2026' / '08' / 'obituario_2026_08.csv'

CAMPOS_CSV = [
    'id_homenagem',
    'data_coleta',
    'url_origem',
    'instituicao_fonte',
    'nome_homenageado',
    'tipo_nota',
    'categoria_atuacao',
    'estado_uf',
    'municipio',
    'data_falecimento',
    'texto_integral_bruto',
    'url_foto',
    'status_processamento'
]


def inicializar_csv_mineracao():
    ARQUIVO_CSV_MINERACAO.parent.mkdir(parents=True, exist_ok=True)
    if not ARQUIVO_CSV_MINERACAO.exists():
        with open(ARQUIVO_CSV_MINERACAO, mode='w', encoding='utf-8', newline='') as f:
            escritor = csv.DictWriter(f, fieldnames=CAMPOS_CSV, delimiter=';')
            escritor.writeheader()


def carregar_registros_reais_existentes(limite: int = 5):
    """Importa registros reais e legítimos do banco oficial do Obituarium para a esteira."""
    inicializar_csv_mineracao()
    if not CSV_REAL_EXISTENTE.exists():
        print(f'[AVISO] Base oficial existente não encontrada em: {CSV_REAL_EXISTENTE}')
        return

    # Mapeia URLs já inseridas na esteira
    urls_existentes = set()
    with open(ARQUIVO_CSV_MINERACAO, mode='r', encoding='utf-8') as f:
        leitor = csv.DictReader(f, delimiter=';')
        for r in leitor:
            if r.get('url_origem'):
                urls_existentes.add(r.get('url_origem'))

    novos = 0
    with open(CSV_REAL_EXISTENTE, mode='r', encoding='utf-8') as f:
        leitor_real = csv.DictReader(f)
        for r in leitor_real:
            url = r.get('url_origem', '').strip()
            if not url or url in urls_existentes:
                continue

            id_homenagem = f"obit-{r.get('id', uuid.uuid4().hex[:8])}"
            data_coleta = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

            registro = {
                'id_homenagem': id_homenagem,
                'data_coleta': data_coleta,
                'url_origem': url,
                'instituicao_fonte': r.get('instituicao_fonte', 'Fonte Oficial').strip(),
                'nome_homenageado': r.get('nome_homenageado', '').strip(),
                'tipo_nota': r.get('tipo_nota', 'Nota de Pesar').strip(),
                'categoria_atuacao': r.get('categoria_atuacao', 'Sociedade').strip(),
                'estado_uf': r.get('estado_uf', 'BR').strip(),
                'municipio': r.get('municipio', 'Nacional').strip(),
                'data_falecimento': r.get('data_falecimento', '').strip(),
                'texto_integral_bruto': (r.get('texto_integral') or r.get('resumo_homenagem', '')).strip().replace('\r\n', ' ').replace('\n', ' '),
                'url_foto': r.get('url_foto', '').strip(),
                'status_processamento': 'pendente_sintese'
            }

            with open(ARQUIVO_CSV_MINERACAO, mode='a', encoding='utf-8', newline='') as f_out:
                escritor = csv.DictWriter(f_out, fieldnames=CAMPOS_CSV, delimiter=';')
                escritor.writerow(registro)

            urls_existentes.add(url)
            novos += 1
            print(f"[OK] Homenagem real registrada: {registro['nome_homenageado']} ({registro['instituicao_fonte']})")
            if limite > 0 and novos >= limite:
                break

    print(f'[INFO] Total de registros reais importados para esteira: {novos}')


def main():
    parser = argparse.ArgumentParser(description='Obituarium - Importar homenagens reais para esteira.')
    parser.add_argument('--limite', type=int, default=5, help='Quantidade de registros a importar (0 para todos)')
    parser.add_argument('--todos', action='store_true', help='Importa todos os registros disponíveis')
    args = parser.parse_args()

    limite_final = 0 if args.todos else args.limite
    carregar_registros_reais_existentes(limite=limite_final)


if __name__ == '__main__':
    main()
