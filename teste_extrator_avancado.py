# -*- coding: utf-8 -*-
import requests
import re
from bs4 import BeautifulSoup

url = 'https://news.google.com/rss/articles/CBMiuwFBVV95cUxNMXB3VlZKalZFdVBvaENjX0hTS042RXhndzEzMXYxd29qSkxPeEpjZHgwZVZfcWNYWFFCajdZUEhOS0ZkakFlSFYyanUxNkR4NFF6ZE9ZMW54VXVQZk5pZVFiZ3hJdFRRd2c4T2NLWlVOVUJzZlMwZXNTV1JKSFkyVW1uVWhKdFBrT2t3X0JyT1pia1dueFlGczBxWjNtYThoenRhSHBVeXNzaDJOV2tZeUs1VVZUc2JBUVdR?oc=5'

def extrair_destino_google(google_url):
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    })
    r = s.get(google_url, timeout=10)
    # No HTML do Google News existe um elemento <c-wiz> com data-n-a-id ou tags <a jsname>
    soup = BeautifulSoup(r.text, 'html.parser')
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if href.startswith('./articles/'):
            continue
        if href.startswith('http') and not any(g in href for g in ['google.com', 'gstatic.com', 'googleusercontent.com']):
            return href
    
    # Busca por regex em blocos JS de AF_initDataCallback
    m = re.findall(r'"(https?://(?!www\.google|news\.google|lh3\.google|accounts\.google|play\.google|fonts\.gstatic|fonts\.googleapis)[^"\s\\]+)"', r.text)
    for cand in m:
        if cand.endswith('.html') or cand.endswith('.php') or '/noticia' in cand or '/nota' in cand or '/portal' in cand or '.gov.br' in cand or '.jus.br' in cand or '.leg.br' in cand:
            return cand
    if m:
        return m[0]
    return None

dst = extrair_destino_google(url)
print('Destino Real do Artigo:', dst)
if dst:
    r_art = requests.get(dst, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    soup = BeautifulSoup(r_art.text, 'html.parser')
    og = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})
    print('Foto Real (og:image):', og.get('content') if og else None)
