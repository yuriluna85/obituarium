# -*- coding: utf-8 -*-
import base64
import re
import requests
from bs4 import BeautifulSoup

url = 'https://news.google.com/rss/articles/CBMiuwFBVV95cUxNMXB3VlZKalZFdVBvaENjX0hTS042RXhndzEzMXYxd29qSkxPeEpjZHgwZVZfcWNYWFFCajdZUEhOS0ZkakFlSFYyanUxNkR4NFF6ZE9ZMW54VXVQZk5pZVFiZ3hJdFRRd2c4T2NLWlVOVUJzZlMwZXNTV1JKSFkyVW1uVWhKdFBrT2t3X0JyT1pia1dueFlGczBxWjNtYThoenRhSHBVeXNzaDJOV2tZeUs1VVZUc2JBUVdR?oc=5'

def decodificar_google_news_url(google_url):
    try:
        m = re.search(r'/articles/([A-Za-z0-9_\-]+)', google_url)
        if m:
            b64 = m.group(1)
            padded = b64 + '=' * (-len(b64) % 4)
            raw = base64.urlsafe_b64decode(padded.encode('ascii'))
            urls = re.findall(b'https?://[^\\x00-\\x1f\\x7f-\\xff\\s"\'<>]+', raw)
            for u in urls:
                url_str = u.decode('utf-8', errors='ignore')
                if 'google.com' not in url_str:
                    return url_str
    except Exception as e:
        print('Erro decode:', e)
    return None

decoded = decodificar_google_news_url(url)
print('URL Decodificada:', decoded)
if decoded:
    r = requests.get(decoded, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=10)
    print('Status destino:', r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    og = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})
    print('og:image destino:', og.get('content') if og else None)
