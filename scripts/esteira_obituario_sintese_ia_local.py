#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
esteira_obituario_sintese_ia_local.py - Síntese solene por IA Local (Ollama) para Obituarium
Portal: Obituarium (Laboratório YLuna85 LABs)
Zero custo de tokens de API.
"""

import sys
import os
import csv
import re
import json
import time
import uuid
import datetime
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

CAMINHO_BASE = Path(__file__).resolve().parent.parent
ARQUIVO_CSV_MINERACAO = CAMINHO_BASE / 'data' / 'mineracao_obituario_bruta.csv'
DIR_PRE_CURADORIA = CAMINHO_BASE / 'pre_curadoria'
OLLAMA_BIN = Path(r'C:\Users\yuri.almeida\AppData\Local\Programs\Ollama\ollama.exe')
OLLAMA_URL = 'http://127.0.0.1:11434'
MODELO_PADRAO = 'llama3.2:3b'

SYSTEM_PROMPT_MEMORIALISTA = (
    'Você é o redator memorialista oficial do Obituarium, portal solene e ético dedicado à preservação da memória e do legado histórico de cidadãos e servidores públicos. '
    'Sua função é elaborar uma síntese biográfica e solene com base no comunicado oficial de falecimento fornecido. '
    'Regras Mandatórias Rígidas: '
    '1. Não invente nomes, datas, parentescos ou dados não presentes no texto original. '
    '2. Proibição absoluta de emojis. '
    '3. Proibição absoluta de travessões intercalares; utilize vírgulas ou períodos gramaticais autônomos. '
    '4. Expurgo de adjetivos sensacionalistas ou dramáticos de IA (como partida trágica, destino fatal, impacto crucial). '
    '5. Estrutura de saída: Título da Homenagem (# Homenagem: [Nome]), Seção "## Síntese Biográfica e Trajetória" e Seção "## Legado e Condolências".'
)


def sanitizar_texto_anti_ia(texto: str) -> str:
    """Higieniza o texto gerado removendo travessões intercalares e termos sensacionalistas."""
    limpo = texto.replace(' — ', ', ').replace('—', ', ').replace(' – ', ', ')
    substituicoes = {
        r'\bcrucial\b': 'fundamental',
        r'\bintrincado\b': 'complexo',
        r'\bdivisor de águas\b': 'marco referencial',
        r'\bshowcase\b': 'demonstração',
        r'\bpotencial\b': 'relevância'
    }
    for padrao, sub in substituicoes.items():
        limpo = re.sub(padrao, sub, limpo, flags=re.IGNORECASE)
    return limpo.strip()


def garantir_servidor_ollama():
    """Verifica se o servidor Ollama está ativo. Caso contrário, inicia em background."""
    try:
        req = urllib.request.urlopen(f'{OLLAMA_URL}/api/tags', timeout=2)
        if req.status == 200:
            return None
    except Exception:
        pass

    print('[INFO] Iniciando serviço local do Ollama...')
    try:
        proc = subprocess.Popen([str(OLLAMA_BIN), 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        return proc
    except Exception as e:
        print(f'[AVISO] Erro ao iniciar Ollama automaticamente: {e}')
        return None


def chamar_ia_local(prompt_usuario: str, modelo: str = MODELO_PADRAO) -> str:
    """Executa inferência local no Ollama sem custo de tokens."""
    payload = {
        'model': modelo,
        'prompt': f'{SYSTEM_PROMPT_MEMORIALISTA}\n\nNota Oficial:\n{prompt_usuario}',
        'stream': False,
        'options': {
            'temperature': 0.2,
            'top_p': 0.9
        }
    }
    dados = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'{OLLAMA_URL}/api/generate',
        data=dados,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resposta:
            corpo = json.loads(resposta.read().decode('utf-8'))
            return corpo.get('response', '')
    except Exception as e:
        print(f'[AVISO] Inferência Ollama ({e}). Utilizando sintetizador solene determinístico.')
        return ''


def gerar_slug(nome: str) -> str:
    slug = nome.lower().strip()
    slug = re.sub(r'[àáâãäå]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')[:50]


def processar_esteira_obituario_sintese():
    if not ARQUIVO_CSV_MINERACAO.exists():
        print(f'[ERRO] CSV de mineração não encontrado em: {ARQUIVO_CSV_MINERACAO}')
        return

    proc_ollama = garantir_servidor_ollama()
    linhas = []
    processados = 0

    with open(ARQUIVO_CSV_MINERACAO, mode='r', encoding='utf-8') as f:
        leitor = csv.DictReader(f, delimiter=';')
        campos = leitor.fieldnames
        for r in leitor:
            linhas.append(r)

    hoje = datetime.datetime.now()
    ano_str = hoje.strftime('%Y')
    mes_str = hoje.strftime('%m')
    dia_str = hoje.strftime('%d')
    data_formatada_extenso = hoje.strftime('%d/%m/%Y às %H:%M:%S')
    dir_destino = DIR_PRE_CURADORIA / ano_str / mes_str / dia_str
    dir_destino.mkdir(parents=True, exist_ok=True)

    for linha in linhas:
        if linha.get('status_processamento') == 'pendente_sintese':
            id_homenagem = linha.get('id_homenagem')
            nome = linha.get('nome_homenageado')
            instituicao = linha.get('instituicao_fonte')
            tipo_nota = linha.get('tipo_nota', 'Nota de Pesar')
            categoria = linha.get('categoria_atuacao', 'Sociedade')
            uf = linha.get('estado_uf', 'BR')
            municipio = linha.get('municipio', 'Nacional')
            data_falecimento = linha.get('data_falecimento', '')
            texto_bruto = linha.get('texto_integral_bruto', '')
            url_origem = linha.get('url_origem', '')
            url_foto = linha.get('url_foto', '')

            print(f'\n[PROCESSANDO HOMENAGEM] {nome} | {instituicao}...')

            prompt_usuario = (
                f'Homenageado: {nome}\n'
                f'Instituição Emissora: {instituicao}\n'
                f'Tipo de Nota: {tipo_nota}\n'
                f'Área de Atuação: {categoria}\n'
                f'Localidade: {municipio} - {uf}\n'
                f'Data de Falecimento: {data_falecimento}\n'
                f'Texto Literal da Nota Oficial: {texto_bruto}'
            )

            resposta_ia = chamar_ia_local(prompt_usuario)

            if not resposta_ia:
                resposta_ia = (
                    f'# Homenagem Solene: {nome}\n\n'
                    f'## Síntese Biográfica e Trajetória\n'
                    f'A instituição {instituicao} emitiu comunicado oficial de {tipo_nota.lower()} em reverência à memória de {nome}, destacando suas contribuições no âmbito de {categoria}.\n\n'
                    f'## Legado e Condolências\n'
                    f'{texto_bruto}\n\n'
                    f'O portal Obituarium manifesta sua solidariedade aos familiares, amigos e pares institucionais, preservando este registro como testemunho de sua trajetória.'
                )

            texto_higienizado = sanitizar_texto_anti_ia(resposta_ia)
            slug = gerar_slug(nome)
            data_sintese_iso = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            arquivo_md_nome = f'{ano_str}-{mes_str}-{dia_str}_{slug}.md'
            caminho_md = dir_destino / arquivo_md_nome

            # Bloco de Transparência e Fonte Original no Rodapé
            bloco_rodape = (
                f'\n\n---\n\n'
                f'### Fonte Original e Transparência Memorial\n'
                f'* **Instituição Emissora**: {instituicao}\n'
                f'* **Acesso à Nota Oficial na Íntegra**: [{url_origem}]({url_origem})\n'
                f'* **Data de Coleta e Registro**: {data_formatada_extenso}\n'
            )

            conteudo_final_md = (
                f'---\n'
                f'id: "{id_homenagem}"\n'
                f'status_curadoria: "pendente"\n'
                f'data_sintese: "{data_sintese_iso}"\n'
                f'nome_homenageado: "{nome}"\n'
                f'tipo_nota: "{tipo_nota}"\n'
                f'categoria_atuacao: "{categoria}"\n'
                f'instituicao_fonte: "{instituicao}"\n'
                f'estado_uf: "{uf}"\n'
                f'municipio: "{municipio}"\n'
                f'data_falecimento: "{data_falecimento}"\n'
                f'url_origem: "{url_origem}"\n'
                f'url_foto: "{url_foto}"\n'
                f'persona_aplicada: "Memorialista Obituarium"\n'
                f'---\n\n'
                f'{texto_higienizado}'
                f'{bloco_rodape}'
            )

            caminho_md.write_text(conteudo_final_md, encoding='utf-8')
            linha['status_processamento'] = 'sintetizado'
            processados += 1
            print(f'[CONCLUÍDO] Homenagem salva em pré-curadoria: {caminho_md}')

    with open(ARQUIVO_CSV_MINERACAO, mode='w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=campos, delimiter=';')
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f'\n[FINALIZADO] Total de homenagens sintetizadas e prontas para revisão: {processados}')

    if proc_ollama:
        try:
            proc_ollama.terminate()
        except Exception:
            pass


if __name__ == '__main__':
    processar_esteira_obituario_sintese()
