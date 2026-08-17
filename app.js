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

    // Funcao interna para decodificar entidades HTML no frontend
    function decodificarEntidades(str) {
      if (!str) return "";
      const txt = document.createElement("textarea");
      txt.innerHTML = str;
      let dec = txt.value;
      // Substituir espacos nao quebraveis e entidades literais
      dec = dec.replace(/&nbsp;/gi, " ").replace(/&quot;/gi, '"').replace(/&amp;/gi, '&');
      return dec.trim();
    }

    for (let i = 1; i < lines.length; i++) {
      const currentLine = lines[i];
      if (currentLine.length >= headers.length) {
        const item = {};
        headers.forEach((header, index) => {
          let val = (currentLine[index] || "").trim();
          val = decodificarEntidades(val);
          item[header] = val;
        });
        records.push(item);
      }
    }

    return records;
  }

  // Base embutida de contingencia com registros reais minerados
  const DADOS_EMBUTIDOS_FALLBACK = [
    {
      "id": "0909fe9a084f",
      "nome_homenageado": "Arnaldo José de Barros e Silva",
      "data_falecimento": "2026-08-17",
      "data_publicacao": "2026-08-17 13:52:53",
      "instituicao_fonte": "Sport Club do Recife",
      "tipo_nota": "Nota de Pesar",
      "categoria_atuacao": "Sociedade",
      "estado_uf": "PE",
      "municipio": "Recife",
      "resumo_homenagem": "Nota de Pesar comunicando o falecimento de Arnaldo José de Barros e Silva emitida pelo Sport Club do Recife.",
      "texto_integral": "O Sport Club do Recife manifesta profundo pesar pelo falecimento de Arnaldo José de Barros e Silva, prestando condolências e solidariedade a todos os familiares e amigos.",
      "url_origem": "https://news.google.com/rss/articles/CBMihwFBVV95cUxNdk1IQWF3U1VXWTZucmJkeGNURC1PSmcxYXl2N01UMjU3RnlVWURjOFdZZllEVmVwME90eFk4ODVPbl9tY3Rma0FBVHdQSGltQVROV1ktbkM3UVBHN19Cd1dhY0FaM0JhZ1FUTW1RemxTbm5Ra0lhWGZfZkNmTkN6RURZNzlsdzA?oc=5",
      "url_foto": ""
    },
    {
      "id": "c6d1add4f0df",
      "nome_homenageado": "Prof. Emérito José Jerônimo de Morais",
      "data_falecimento": "2026-08-17",
      "data_publicacao": "2026-08-17 13:53:00",
      "instituicao_fonte": "Universidade Estadual de Feira de Santana (UEFS)",
      "tipo_nota": "Nota de Pesar",
      "categoria_atuacao": "Educação e Ciência",
      "estado_uf": "BA",
      "municipio": "Feira de Santana",
      "resumo_homenagem": "A Universidade Estadual de Feira de Santana manifesta profundo pesar pelo falecimento do professor emérito José Jerônimo de Morais.",
      "texto_integral": "A Universidade Estadual de Feira de Santana (UEFS) comunica com pesar o falecimento do professor emérito José Jerônimo de Morais, destacando sua inestimável contribuição acadêmica e científica.",
      "url_origem": "https://news.google.com/rss/articles/CBMikgFBVV95cUxQSGZhUlhUbTB2QjZlaVZrZXlOb29kU1VwX0hYdXhlMHBIQzR4ckJKSU5YbjZuaDVQWWk4ZFJGOXdZc0JmaWVBWEhwS1V3b0xGektZZVA0aTdxUTZLNFJBQUdIY05FdjJWMDdSdlB4dVNyVE50ZnhRZWNJem5rR2RxOXU1WHVlX3JzeUxSWDZWTVZhdw?oc=5",
      "url_foto": ""
    },
    {
      "id": "4e2cd4df809f",
      "nome_homenageado": "Rafael Brito de Sá",
      "data_falecimento": "2026-08-17",
      "data_publicacao": "2026-08-17 13:53:01",
      "instituicao_fonte": "OAB/AC",
      "tipo_nota": "Nota de Pesar",
      "categoria_atuacao": "Sociedade",
      "estado_uf": "AC",
      "municipio": "Rio Branco",
      "resumo_homenagem": "A Ordem dos Advogados do Brasil Seccional Acre manifesta pesar pelo falecimento de Rafael Brito de Sá.",
      "texto_integral": "A OAB/AC expressa suas sinceras condolências à família e amigos de Rafael Brito de Sá neste momento de dor e consternação.",
      "url_origem": "https://news.google.com/rss/articles/CBMiZEFVX3lxTE5kbDlZVU1Xc2ZNZVRVd0ZId3RKb1NIUzQ3TEIwdDRyRUVzb2FudHlEVTBLSUl6N1hDc1BBRXl4RDZyNUpjZlFITFlaOHp2c0FzUF9OY2stV1ZmbjZQV08zTnFBSEk?oc=5",
      "url_foto": ""
    },
    {
      "id": "6ced56721b55",
      "nome_homenageado": "José Baka Filho (Ex-Prefeito)",
      "data_falecimento": "2026-08-17",
      "data_publicacao": "2026-08-17 13:53:13",
      "instituicao_fonte": "Município de Paranaguá / Banda B",
      "tipo_nota": "Luto Oficial",
      "categoria_atuacao": "Gestão Pública",
      "estado_uf": "PR",
      "municipio": "Paranaguá",
      "resumo_homenagem": "Ex-prefeito de Paranaguá morre aos 64 anos e município decreta três dias de luto oficial.",
      "texto_integral": "O município de Paranaguá decretou luto oficial de três dias em virtude do falecimento do ex-prefeito José Baka Filho, prestando tributo à sua trajetória de dedicação à cidade.",
      "url_origem": "https://news.google.com/rss/articles/CBMi1gFBVV95cUxPQ1U3UmF4SjE5VTNQRW02bGJ3ak85dXhnQnZkMDZkQXllaGFuOWZLYlRQdDM4RHlvQlRGRUhTaE85LXJ5SzcyX1hoRWRHdUVoc05nVXJSd2dISHN2S1RrSXhpUVJsWUdBTVBocHZZSGMxVFZ0MDlxM2thaVVwcnRaQjFpWU5VUlZMOHM1eUtjUjZyLUsydC1pYk83NkJNcFR3Q2JDODZyMExrQkIyenFONzdxdGVwWmVhdzIzZW9Ob1FpcFl3UEpEc3FCTXlXV1dKbnF4NHR30gHbAUFVX3lxTE1GZV80ek9GRnNRTWdtSGNnQmN6RUNfYXFPeFVSLUFzOFpEWVZhRTZLazMwbkV0RUQ5NlIzZnVLdG1CNm9Ja0dfYmN0YkY1U1JlMmI3M3lpQ3FNWDl4aU9xOTJUX2JydE9hNFFuMzEtcmt3VWF6a0hxaFJuTXhDN0JSOUo1ekFWNldIQ0VlYVJMYk1zTEhYTjBRSmUxWEFwamtITFd3allCN2RfQ2l5WnI0TEJvcmNGSGxDb1JSV3p5RV84X0x6VVdkc3B3cm0yQXA4RGZvNHVqRC1HQQ?oc=5",
      "url_foto": ""
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
            <img class="portrait-img" src="${escapeHTML(fotoUrl)}" alt="Retrato de ${escapeHTML(record.nome_homenageado)}" loading="lazy" onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'100\\' height=\\'120\\' viewBox=\\'0 0 100 120\\'%3E%3Crect width=\\'100\\' height=\\'120\\' fill=\\'%231E293B\\'/%3E%3Cpath d=\\'M50 30a15 15 0 1 0 0 30 15 15 0 0 0 0-30zm0 40c-20 0-35 15-35 30h70c0-15-15-30-35-30z\\' fill=\\'%2394A3B8\\'/%3E%3C/svg%3E';">
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
