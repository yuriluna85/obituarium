# -*- coding: utf-8 -*-
import requests
import json
import re

url = 'https://news.google.com/rss/articles/CBMiuwFBVV95cUxNMXB3VlZKalZFdVBvaENjX0hTS042RXhndzEzMXYxd29qSkxPeEpjZHgwZVZfcWNYWFFCajdZUEhOS0ZkakFlSFYyanUxNkR4NFF6ZE9ZMW54VXVQZk5pZVFiZ3hJdFRRd2c4T2NLWlVOVUJzZlMwZXNTV1JKSFkyVW1uVWhKdFBrT2t3X0JyT1pia1dueFlGczBxWjNtYThoenRhSHBVeXNzaDJOV2tZeUs1VVZUc2JBUVdR?oc=5'

def decodificar_google_news_artigo(google_url):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    })
    r = session.get(google_url, timeout=10)
    
    # 1. Procurar nas tags data-n-a-id ou c-wiz
    # O Google insere um payload JS com [..., ["https://site-destino.com.br/..."]]
    urls_encontradas = re.findall(r'"(https?://(?!www\.google|news\.google|lh3\.google|accounts\.google|play\.google|fonts\.gstatic)[^"\'\s\\]+)"', r.text)
    for u in urls_encontradas:
        if not u.endswith(('.js', '.css', '.png', '.jpg', '.svg', '.woff2', '.ico')):
            return u
    return None

real_url = decodificar_google_news_artigo(url)
print('URL Real Encontrada:', real_url)
if real_url:
    r_art = requests.get(real_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r_art.text, 'html.parser')
    og = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})
    print('OG Real da Noticia:', og.get('content') if og else None)
