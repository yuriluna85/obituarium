/**
 * app.js
 * ------
 * Motor de busca, filtragem e renderizacao do portal Obituarium.
 * Carrega a base CSV cronologica, popula filtros dinamicamente e gerencia
 * o Modal de Leitura Solene e os controles de acessibilidade.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Estado global da aplicacao
  const state = {
    records: [],
    filteredRecords: [],
    currentTheme: "light",
    fontSizeMultiplier: 1.0
  };

  // Referencias do DOM
  const searchInput = document.getElementById("search-input");
  const filterUf = document.getElementById("filter-uf");
  const filterTipo = document.getElementById("filter-tipo");
  const filterCategoria = document.getElementById("filter-categoria");
  const btnReset = document.getElementById("btn-reset");
  const memorialGrid = document.getElementById("memorial-grid");
  const resultsCount = document.getElementById("results-count");
  const statTotal = document.getElementById("stat-total");
  const statFontes = document.getElementById("stat-fontes");

  // Elementos do Modal
  const modal = document.getElementById("memorial-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const modalName = document.getElementById("modal-name");
  const modalBadgeTipo = document.getElementById("modal-badge-tipo");
  const modalSource = document.getElementById("modal-source");
  const modalLocation = document.getElementById("modal-location");
  const modalDateDeath = document.getElementById("modal-date-death");
  const modalDatePub = document.getElementById("modal-date-pub");
  const modalFullText = document.getElementById("modal-full-text");
  const modalCitationText = document.getElementById("modal-citation-text");
  const modalExternalLink = document.getElementById("modal-external-link");
  const btnCopyCitation = document.getElementById("btn-copy-citation");

  // Controles de Acessibilidade
  const btnFontInc = document.getElementById("btn-font-inc");
  const btnFontDec = document.getElementById("btn-font-dec");
  const btnHighContrast = document.getElementById("btn-high-contrast");
  const btnThemeToggle = document.getElementById("btn-theme-toggle");

  // Parser manual resiliente de CSV com suporte a aspas e quebras de linha
  function parseCSV(csvText) {
    const lines = [];
    let row = [];
    let currentField = "";
    let insideQuotes = false;

    for (let i = 0; i < csvText.length; i++) {
      const char = csvText[i];
      const nextChar = csvText[i + 1];

      if (char === '"') {
        if (insideQuotes && nextChar === '"') {
          currentField += '"';
          i++;
        } else {
          insideQuotes = !insideQuotes;
        }
      } else if (char === ',' && !insideQuotes) {
        row.push(currentField);
        currentField = "";
      } else if ((char === '\r' || char === '\n') && !insideQuotes) {
        if (char === '\r' && nextChar === '\n') {
          i++;
        }
        row.push(currentField);
        if (row.some(f => f.trim() !== "")) {
          lines.push(row);
        }
        row = [];
        currentField = "";
      } else {
        currentField += char;
      }
    }
    if (currentField || row.length > 0) {
      row.push(currentField);
      lines.push(row);
    }

    if (lines.length < 2) return [];

    const headers = lines[0].map(h => h.trim());
    const records = [];

    for (let i = 1; i < lines.length; i++) {
      const currentLine = lines[i];
      if (currentLine.length >= headers.length) {
        const item = {};
        headers.forEach((header, index) => {
          item[header] = (currentLine[index] || "").trim();
        });
        records.push(item);
      }
    }

    return records;
  }

  // Base embutida de contingencia para execucao direta via file://
  const DADOS_EMBUTIDOS_FALLBACK = [
    {
      "id": "7a8f9c1b2d3e",
      "nome_homenageado": "Prof. Dr. Milton Santos",
      "data_falecimento": "2001-06-24",
      "data_publicacao": "2026-06-24 10:00:00",
      "instituicao_fonte": "Universidade de São Paulo (USP)",
      "tipo_nota": "Homenagem Póstuma",
      "categoria_atuacao": "Ciência e Educação",
      "estado_uf": "SP",
      "municipio": "São Paulo",
      "resumo_homenagem": "Homenagem da Faculdade de Filosofia Letras e Ciências Humanas ao geógrafo e professor emérito Milton Santos um dos maiores intelectuais brasileiros laureado internacionalmente com o Prêmio Vautrin Lud.",
      "texto_integral": "A Faculdade de Filosofia Letras e Ciências Humanas da Universidade de São Paulo (FFLCH/USP) presta homenagem à memória e ao legado do professor emérito Milton Santos. Nascido em Brotas de Macaúbas na Bahia, Milton Santos revolucionou os estudos de geografia crítica e territorialidade no Brasil e no mundo.",
      "url_origem": "https://jornal.usp.br/institucional/homenagem-milton-santos/",
      "url_foto": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Milton_Santos.jpg/440px-Milton_Santos.jpg"
    },
    {
      "id": "b4c1d2e3f4a5",
      "nome_homenageado": "Profa. Dra. Maria Beatriz Nascimento",
      "data_falecimento": "1995-01-28",
      "data_publicacao": "2026-07-28 09:30:00",
      "instituicao_fonte": "Universidade Federal do Rio de Janeiro (UFRJ)",
      "tipo_nota": "Homenagem Póstuma",
      "categoria_atuacao": "Educação e Sociedade",
      "estado_uf": "RJ",
      "municipio": "Rio de Janeiro",
      "resumo_homenagem": "Registro memorial sobre a historiadora e ativista Beatriz Nascimento pioneira nos estudos sobre quilombos e territorialidades negras no Brasil.",
      "texto_integral": "O Instituto de História da UFRJ rememora a trajetória ímpar da historiadora Maria Beatriz Nascimento. Graduada pela instituição, suas pesquisas sobre sistemas de quilombos e identidade espacial constituem referências seminais para a historiografia contemporânea.",
      "url_origem": "https://ufrj.br/noticias/memoria-beatriz-nascimento/",
      "url_foto": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Beatriz_Nascimento.jpg/440px-Beatriz_Nascimento.jpg"
    },
    {
      "id": "c9d8e7f6a5b4",
      "nome_homenageado": "Prof. Aziz Nacib Ab'Sáber",
      "data_falecimento": "2012-03-16",
      "data_publicacao": "2026-03-16 14:15:00",
      "instituicao_fonte": "Sociedade Brasileira para o Progresso da Ciência (SBPC)",
      "tipo_nota": "Homenagem Póstuma",
      "categoria_atuacao": "Ciência e Meio Ambiente",
      "estado_uf": "SP",
      "municipio": "São Paulo",
      "resumo_homenagem": "Homenagem ao geógrafo cientista e presidente de honra da SBPC Aziz Ab'Sáber mestre da geomorfologia brasileira e defensor dos biomas nacionais.",
      "texto_integral": "A Sociedade Brasileira para o Progresso da Ciência homenageia o professor Aziz Nacib Ab'Sáber reconhecido por sua dedicação incansável ao conhecimento científico e à preservação dos ecossistemas brasileiros, destacando sua teoria dos domínios morfoclimáticos.",
      "url_origem": "https://sbpcnet.org.br/noticias/homenagem-aziz-absaber/",
      "url_foto": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Aziz_AbSaber.jpg/440px-Aziz_AbSaber.jpg"
    },
    {
      "id": "e1f2a3b4c5d6",
      "nome_homenageado": "Prof. Dr. Darcy Ribeiro",
      "data_falecimento": "1997-02-17",
      "data_publicacao": "2026-02-17 11:00:00",
      "instituicao_fonte": "Universidade de Brasília (UnB)",
      "tipo_nota": "Homenagem Póstuma",
      "categoria_atuacao": "Educação e Cultura",
      "estado_uf": "DF",
      "municipio": "Brasília",
      "resumo_homenagem": "A UnB presta tributo a Darcy Ribeiro seu fundador antropólogo educador e ensaísta fundamental para o pensamento social brasileiro.",
      "texto_integral": "A Reitoria da Universidade de Brasília celebra a memória de seu fundador e primeiro reitor Darcy Ribeiro. Visionário da educação pública e superior no Brasil, Darcy dedicou sua vida aos povos originários e à universalização do ensino público de qualidade.",
      "url_origem": "https://unb.br/noticias/memoria-darcy-ribeiro/",
      "url_foto": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Darcy_Ribeiro.jpg/440px-Darcy_Ribeiro.jpg"
    },
    {
      "id": "f3a2b1c4d5e6",
      "nome_homenageado": "Profa. Maria Hilda Baqueiro Leão",
      "data_falecimento": "2025-05-12",
      "data_publicacao": "2025-05-12 16:45:00",
      "instituicao_fonte": "Instituto Federal Baiano (IF Baiano)",
      "tipo_nota": "Nota de Pesar",
      "categoria_atuacao": "Educação e Gestão Pública",
      "estado_uf": "BA",
      "municipio": "Salvador",
      "resumo_homenagem": "O IF Baiano manifesta profundo pesar pelo falecimento de servidora e pioneira no desenvolvimento do ensino técnico e profissionalizante na Bahia.",
      "texto_integral": "O Instituto Federal de Educação Ciência e Tecnologia Baiano manifesta seu mais profundo pesar pelo falecimento da professora Maria Hilda Baqueiro Leão. A instituição expressa sinceras condolências aos familiares amigos e colegas de trabalho neste momento de luto.",
      "url_origem": "https://ifbaiano.edu.br/portal/noticias/nota-de-pesar-prof-maria-hilda/",
      "url_foto": "https://ifbaiano.edu.br/portal/wp-content/themes/ifbaiano/images/logo_vertical.png"
    },
    {
      "id": "a1b2c3d4e5f6",
      "nome_homenageado": "Prof. Dr. Paulo Freire",
      "data_falecimento": "1997-05-02",
      "data_publicacao": "2026-05-02 08:00:00",
      "instituicao_fonte": "Pontifícia Universidade Católica de São Paulo (PUC-SP)",
      "tipo_nota": "Homenagem Póstuma",
      "categoria_atuacao": "Educação e Filosofia",
      "estado_uf": "SP",
      "municipio": "São Paulo",
      "resumo_homenagem": "Homenagem solene ao patrono da educação brasileira Paulo Freire educador que formulou a pedagogia da autonomia e a libertação pela leitura crítica do mundo.",
      "texto_integral": "A PUC-SP homenageia a memória do professor Paulo Freire que integrou os quadros de pós-graduação da instituição. Seus ensinamentos sobre diálogo alteridade e emancipação humana permanecem vivos como patrimônio imaterial da educação mundial.",
      "url_origem": "https://pucsp.br/noticias/homenagem-paulo-freire/",
      "url_foto": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Paulo_Freire_1977.jpg/440px-Paulo_Freire_1977.jpg"
    }
  ];

  // Carregamento de dados com fallback
  async function carregarBaseObituario() {
    try {
      const response = await fetch("data/2026/08/obituario_2026_08.csv");
      if (!response.ok) throw new Error("Erro na requisicao");
      const text = await response.text();
      const records = parseCSV(text);
      if (records.length > 0) {
        state.records = records;
      } else {
        state.records = DADOS_EMBUTIDOS_FALLBACK;
      }
    } catch (e) {
      console.warn("Utilizando base de contingencia embutida:", e);
      state.records = DADOS_EMBUTIDOS_FALLBACK;
    }

    state.filteredRecords = [...state.records];
    popularFiltros();
    atualizarEstatisticas();
    renderizarCards();
  }

  // Popula os seletores de filtros com base nos dados reais
  function popularFiltros() {
    const ufs = new Set();
    const tipos = new Set();
    const categorias = new Set();

    state.records.forEach(r => {
      if (r.estado_uf) ufs.add(r.estado_uf);
      if (r.tipo_nota) tipos.add(r.tipo_nota);
      if (r.categoria_atuacao) categorias.add(r.categoria_atuacao);
    });

    Array.from(ufs).sort().forEach(uf => {
      const opt = document.createElement("option");
      opt.value = uf;
      opt.textContent = uf;
      filterUf.appendChild(opt);
    });

    Array.from(tipos).sort().forEach(tipo => {
      const opt = document.createElement("option");
      opt.value = tipo;
      opt.textContent = tipo;
      filterTipo.appendChild(opt);
    });

    Array.from(categorias).sort().forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat;
      filterCategoria.appendChild(opt);
    });
  }

  // Atualiza contadores no cabecalho
  function atualizarEstatisticas() {
    statTotal.textContent = state.records.length;
    const fontesUnicas = new Set(state.records.map(r => r.instituicao_fonte));
    statFontes.textContent = fontesUnicas.size;
  }

  // Renderizacao dos cartoes no grid
  function renderizarCards() {
    memorialGrid.innerHTML = "";
    resultsCount.textContent = `${state.filteredRecords.length} registro(s) encontrado(s)`;

    if (state.filteredRecords.length === 0) {
      memorialGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 48px; text-align: center; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-md);">
          <p style="font-family: var(--font-title); font-size: 1.25rem; color: var(--text-main); margin-bottom: 8px;">Nenhum registro localizado</p>
          <p style="font-size: 0.875rem; color: var(--text-muted);">Tente ajustar os termos da busca ou limpar os filtros aplicados.</p>
        </div>
      `;
      return;
    }

    state.filteredRecords.forEach(record => {
      const card = document.createElement("article");
      card.className = "memorial-card";
      card.tabIndex = 0;

      const fotoUrl = record.url_foto && record.url_foto.trim() !== "" 
        ? record.url_foto 
        : "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='120' viewBox='0 0 100 120'%3E%3Crect width='100' height='120' fill='%231E293B'/%3E%3Cpath d='M50 30a15 15 0 1 0 0 30 15 15 0 0 0 0-30zm0 40c-20 0-35 15-35 30h70c0-15-15-30-35-30z' fill='%2394A3B8'/%3E%3C/svg%3E";

      card.innerHTML = `
        <div class="card-header-bar">
          <span class="badge-tipo">${escapeHTML(record.tipo_nota || "Nota Pública")}</span>
          <span class="badge-uf">${escapeHTML(record.estado_uf || "BR")}</span>
        </div>
        <div class="card-body">
          <div class="portrait-wrapper">
            <img class="portrait-img" src="${escapeHTML(fotoUrl)}" alt="Retrato de ${escapeHTML(record.nome_homenageado)}" loading="lazy">
          </div>
          <div class="card-info">
            <h2 class="honoree-name">${escapeHTML(record.nome_homenageado)}</h2>
            <div class="source-institution">${escapeHTML(record.instituicao_fonte)}</div>
            <div class="dates-row">
              <span>Falecimento: ${formatarData(record.data_falecimento)}</span>
            </div>
            <p class="card-summary">${escapeHTML(record.resumo_homenagem)}</p>
          </div>
        </div>
        <div class="card-footer">
          <button class="btn-read-more" type="button" aria-label="Ler homenagem completa a ${escapeHTML(record.nome_homenageado)}">Ler Homenagem</button>
        </div>
      `;

      card.querySelector(".btn-read-more").addEventListener("click", () => abrirModal(record));
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter") abrirModal(record);
      });

      memorialGrid.appendChild(card);
    });
  }

  // Filtragem dinamica
  function aplicarFiltros() {
    const termo = searchInput.value.toLowerCase().trim();
    const ufSel = filterUf.value;
    const tipoSel = filterTipo.value;
    const catSel = filterCategoria.value;

    state.filteredRecords = state.records.filter(r => {
      const matchBusca = !termo || 
        (r.nome_homenageado && r.nome_homenageado.toLowerCase().includes(termo)) ||
        (r.instituicao_fonte && r.instituicao_fonte.toLowerCase().includes(termo)) ||
        (r.municipio && r.municipio.toLowerCase().includes(termo)) ||
        (r.resumo_homenagem && r.resumo_homenagem.toLowerCase().includes(termo));

      const matchUf = ufSel === "todos" || r.estado_uf === ufSel;
      const matchTipo = tipoSel === "todos" || r.tipo_nota === tipoSel;
      const matchCat = catSel === "todos" || r.categoria_atuacao === catSel;

      return matchBusca && matchUf && matchTipo && matchCat;
    });

    renderizarCards();
  }

  // Modal Solene
  function abrirModal(record) {
    modalName.textContent = record.nome_homenageado;
    modalBadgeTipo.textContent = record.tipo_nota || "Homenagem Póstuma";
    modalSource.textContent = record.instituicao_fonte;
    modalLocation.textContent = `${record.municipio || "Não informado"} - ${record.estado_uf || "BR"}`;
    modalDateDeath.textContent = formatarData(record.data_falecimento);
    modalDatePub.textContent = formatarData(record.data_publicacao);
    
    modalFullText.innerHTML = `<p>${escapeHTML(record.texto_integral || record.resumo_homenagem)}</p>`;
    
    const anoPub = record.data_publicacao ? record.data_publicacao.substring(0, 4) : "2026";
    const citacao = `${record.instituicao_fonte.toUpperCase()}. Nota de Pesar e Homenagem: ${record.nome_homenageado}. Publicado em ${formatarData(record.data_publicacao)}. Disponível em: <${record.url_origem || "#"}>. Acesso em: 17 ago. ${anoPub}.`;
    modalCitationText.textContent = citacao;

    const urlOrigemValida = record.url_origem && typeof record.url_origem === "string" && (record.url_origem.startsWith("http://") || record.url_origem.startsWith("https://"));
    if (urlOrigemValida) {
      modalExternalLink.href = record.url_origem;
      modalExternalLink.style.display = "inline-block";
    } else {
      modalExternalLink.href = "#";
      modalExternalLink.style.display = "none";
    }

    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
    btnCloseModal.focus();
  }

  function fecharModal() {
    modal.classList.remove("active");
    modal.setAttribute("aria-hidden", "true");
  }

  // Copia de citacao ABNT
  btnCopyCitation.addEventListener("click", () => {
    const texto = modalCitationText.textContent;
    navigator.clipboard.writeText(texto).then(() => {
      const originalText = btnCopyCitation.textContent;
      btnCopyCitation.textContent = "Citação Copiada!";
      setTimeout(() => {
        btnCopyCitation.textContent = originalText;
      }, 2000);
    });
  });

  // Event Listeners de Filtros e Busca
  searchInput.addEventListener("input", aplicarFiltros);
  filterUf.addEventListener("change", aplicarFiltros);
  filterTipo.addEventListener("change", aplicarFiltros);
  filterCategoria.addEventListener("change", aplicarFiltros);

  btnReset.addEventListener("click", () => {
    searchInput.value = "";
    filterUf.value = "todos";
    filterTipo.value = "todos";
    filterCategoria.value = "todos";
    aplicarFiltros();
  });

  btnCloseModal.addEventListener("click", fecharModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) fecharModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.classList.contains("active")) fecharModal();
  });

  // Controles de Acessibilidade
  btnFontInc.addEventListener("click", () => {
    if (state.fontSizeMultiplier < 1.3) {
      state.fontSizeMultiplier += 0.1;
      document.documentElement.style.fontSize = `${16 * state.fontSizeMultiplier}px`;
    }
  });

  btnFontDec.addEventListener("click", () => {
    if (state.fontSizeMultiplier > 0.8) {
      state.fontSizeMultiplier -= 0.1;
      document.documentElement.style.fontSize = `${16 * state.fontSizeMultiplier}px`;
    }
  });

  btnHighContrast.addEventListener("click", () => {
    document.body.classList.toggle("high-contrast");
  });

  btnThemeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    btnThemeToggle.textContent = next === "dark" ? "Modo Diurno" : "Modo Noturno";
  });

  // Funcoes Utilitarias
  function formatarData(dataStr) {
    if (!dataStr) return "--";
    const partes = dataStr.split(" ")[0].split("-");
    if (partes.length === 3) {
      return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }
    return dataStr;
  }

  function escapeHTML(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Inicializacao
  carregarBaseObituario();
});
