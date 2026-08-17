# Obituarium [Portal de Notas de Pesar e Memória Pública]

![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JS-ES6+-F7DF1E?logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![WCAG](https://img.shields.io/badge/WCAG_2.1-Nível_AAA-1AD37A)
![Status](https://img.shields.io/badge/Status-100%25_Funcional-00E676)

Aplicação web e sistema de mineração autônoma dedicada à catalogação, preservação histórica e indexação de notas de pesar, necrologias, decretos de luto oficial e homenagens póstumas emitidas por órgãos públicos, universidades e veículos de imprensa em todo o Brasil.

---

## 1. Visão Geral e Recursos

O **Obituarium** oferece um repositório centralizado, digno e solene para preservar a memória e o legado de servidores, cientistas, acadêmicos, artistas e cidadãos. A ferramenta opera em computadores, tablets e celulares sem dependência de bibliotecas pesadas.

### Matriz de Recursos e Funcionalidades

| Recurso | Operação Técnica | Resultado / Benefício |
| :--- | :--- | :--- |
| **Busca Instantânea** | Filtro dinâmico em tempo real por nome, cargo ou termo | Localização imediata de registros memoriais |
| **Filtros Multifacetados** | Seleção por Estado (UF), Tipo de Publicação e Área de Atuação | Segmentação precisa para pesquisa e consulta |
| **Bento Grid Solene** | Cartões biográficos com foto, dados institucionais e resumo | Visualização elegante inspirada no G1 e USP |
| **Modal Memorial View** | Exibição da íntegra da nota oficial com citação ABNT pronta | Acesso ao documento e referência para estudos |
| **Base CSV Cronológica** | Particionamento automático em `data/YYYY/MM/obituario_YYYY_MM.csv` | Transparência de dados e facilidade de auditoria |
| **Acessibilidade Universal** | Alto contraste, ajuste de fonte (A+/A-) e foco ARIA visível | Conformidade estrita WCAG 2.1 nível AAA |

---

## 2. Especificações Visuais e Design Tokens

A identidade visual do portal combina o rigor editorial e a clareza do G1 com a dignidade acadêmica do Portal da Universidade de São Paulo (USP):

| Elemento Visual | Token / Valor HSL | Razão de Contraste | Aplicação na Interface |
| :--- | :--- | :--- | :--- |
| **Bordô Nobre Memorial** | `hsl(340, 75%, 28%)` / `#7F1135` | 9.4:1 (Nível AAA) | Títulos institucionais, botões e acentos |
| **Azul Ardósia USP** | `hsl(215, 28%, 17%)` / `#1E293B` | 13.8:1 (Nível AAA) | Cabeçalhos e barras de navegação |
| **Fundo Mármore Diurno** | `hsl(40, 20%, 97%)` / `#F8F9FA` | Base de contraste | Superfície solene para leitura diurna |
| **Fundo Noturno Solene** | `hsl(220, 25%, 7%)` / `#0A0D14` | Base modo escuro | Experiência contemplativa noturna |

- **Acessibilidade Universal**: Suporte a atalhos de teclado, foco visível (`--focus-ring`), rótulos ARIA para leitores de tela e alternância instantânea para modo de alto contraste.
- **Blindagem Óptica**: Aplicação de sombras protetoras e contrastes elevados para garantir leitura confortável a usuários com baixa visão ou astigmatismo.

---

## 3. Guia de Instalação e Execução

### Pré-requisitos
- Python 3.10 ou superior (para execução do minerador).
- Navegador moderno (Chrome, Edge, Firefox ou Safari).

### Instalação de Dependências
```bash
python -m pip install -r requirements.txt
```

### Execução do Portal Web
Abra o arquivo `index.html` diretamente no navegador ou utilize o launcher:
```cmd
EXECUTAR_OBITUARIUM.bat
```

### Mineração Autônoma de Dados
```bash
# Mineração padrão e atualização do CSV do mês corrente
python auto_minerador_obituario.py

# Teste seguro sem gravação em disco
python auto_minerador_obituario.py --dry-run
```

---

## 4. Estrutura de Diretórios

```text
obituarium/
├── data/
│   └── 2026/
│       └── 08/
│           └── obituario_2026_08.csv   <-- Base particionada cronologicamente
├── .github/
│   └── workflows/
│       └── minerador_obituarium.yml    <-- Coleta periódica no GitHub Actions
├── index.html                          <-- Interface web semântica e acessível (SPA)
├── style.css                           <-- Design tokens HSL e Bento Grid
├── app.js                              <-- Motor de busca, filtros e modal
├── auto_minerador_obituario.py         <-- Engine de coleta e mineração global
├── validador_fontes.py                 <-- Validador de integridade e status HTTP 200
├── EXECUTAR_OBITUARIUM.bat             <-- Launcher Windows interativo
├── requirements.txt                    <-- Manifesto de bibliotecas Python
└── README.md                           <-- Documentação oficial e vitrine
```

---

## 5. Lógica de Negócio e Organização de Dados

1. **Particionamento Temporal**: Cada mês possui sua base isolada em `data/YYYY/MM/obituario_YYYY_MM.csv`.
2. **Deduplicação Semântica**: O identificador único `id` é gerado via hash MD5 de 12 caracteres calculado sobre o título e o nome do homenageado, evitando inserções repetidas.
3. **Resiliência Multi-Máquinas**: O minerador utiliza a classe adaptadora `FallbackFetcher`, executando de forma transparente com `scrapling`, `requests` ou `urllib.request` nativo.

---

## 6. Log de Atualizações (Changelog)

- **17/08/2026 (v1.1.0)**: **Expansão para Mineração Global e Validação Estrita de URLs**:
  - Integração do motor de busca aberta com Google News RSS Brasil (`pt-BR`) e feeds institucionais.
  - Implementação do módulo `validador_fontes.py` para garantia de status `HTTP 200` e checagem de marcadores semânticos de luto e homenagem.
  - Aperfeiçoamento do filtro de deduplicação semântica e descarte automático de notícias repetidas.
  - Homologação completa via `--dry-run` com 30 notícias capturadas, 1 repetição descartada e 29 inéditas validadas.
- **17/08/2026 (v1.0.0)**: **Lançamento Oficial do Portal Obituarium**:
  - Implementação da interface web responsiva inspirada no G1 e Portal da USP.
  - Criação da base de dados inicial em CSV particionada em `data/2026/08/obituario_2026_08.csv`.
  - Desenvolvimento do motor de busca instantânea e filtros multifacetados por Estado, Tipo e Área.
  - Implementação do Modal de Leitura Solene (*Memorial View*) com gerador de citação ABNT.
  - Inclusão do motor de coleta Python `auto_minerador_obituario.py` com suporte a `--dry-run`.
  - Configuração do workflow automatizado do GitHub Actions e do launcher Windows `EXECUTAR_OBITUARIUM.bat`.
  - Conformidade estrita com as diretrizes de acessibilidade WCAG 2.1 AAA e veto total a emojis.
