# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re

url = 'https://news.google.com/rss/articles/CBMiuwFBVV95cUxNMXB3VlZKalZFdVBvaENjX0hTS042RXhndzEzMXYxd29qSkxPeEpjZHgwZVZfcWNYWFFCajdZUEhOS0ZkakFlSFYyanUxNkR4NFF6ZE9ZMW54VXVQZk5pZVFiZ3hJdFRRd2c4T2NLWlVOVUJzZlMwZXNTV1JKSFkyVW1uVWhKdFBrT2t3X0JyT1pia1dueFlGczBxWjNtYThoenRhSHBVeXNzaDJOV2tZeUs1VVZUc2JBUVdR?oc=5'

def resolver_url_google_news(google_url):
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        })
        resp = session.get(google_url, timeout=10)
        # Google News insere script de redirecionamento ou link no HTML
        # Procurar por link canônico no HTML retornado pelo Google
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Procurar links no corpo ou dados JS
        m = re.search(r'href="([^"]+)"', resp.text)
        links = re.findall(r'https?://[^\s"\'<>\\]+', resp.text)
        for l in links:
            if 'google.com' not in l and 'gstatic.com' not in l and 'w3.org' not in l:
                return l
    except Exception as e:
        print('Erro resolver:', e)
    return google_url

resolved = resolver_url_google_news(url)
print('Resolved URL:', resolved)
if resolved != url:
    r = requests.get(resolved, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    print('Destino Status:', r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    og = soup.find('meta', property='og:image')
    print('OG Image Destino:', og.get('content') if og else None)
