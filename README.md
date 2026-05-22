# muzambinho-transparente

Portal de transparência não oficial para os gastos públicos da **Prefeitura de Muzambinho – MG**, exercício de **2026**.

## O que é

Um scraper que coleta dados do [PortalTP oficial](https://muzambinho-mg.portaltp.com.br/) (sistema Fiorilli) e os apresenta num site estático autocontido — sem precisar navegar pelo sistema da prefeitura, sem servidor para rodar.

**O portal embute o dataset completo de cada categoria** — nada é truncado para "top N". Todas as listas têm busca, ordenação e filtros que percorrem o dataset inteiro, com paginação client-side de 60 itens por vez.

Começa com uma **Visão geral** (4 cards visuais: balança fiscal, origem do dinheiro, pirâmide do orçamento, comissionados vs efetivos), seguida pelo **Radar de Gastos** (12 heurísticas de anomalia ordenadas por severidade).

Cobertura atual (exercício 2026 até hoje):

### De onde vem o dinheiro
- **2.544 receitas realizadas** totalizando R$ 34,76M arrecadados (de R$ 122M previstos)
- **7 convênios/transferências formais recebidos** (R$ 1,16M); 88% da arrecadação vem de transferências da União/Estado (FPM, FUNDEB, SUS, ICMS, IPVA)

### Para onde vai
- **2.324 empenhos** totalizando R$ 50,5M (empenhado líquido R$ 42,3M após anulações)
- **1.324 pagamentos efetivos** (R$ 11,2M — só 22% do empenhado virou saída de caixa)
- **384 credores/fornecedores** agregados (top: Folha de Pagamento R$ 12,3M = 24%)
- **57 diárias** (elemento contábil 33901400000 — fonte canônica, não o endpoint dedicado que retornava só 6)
- **10 subvenções** ao terceiro setor (R$ 126k)
- **81 processos de compra**: 5 licitações + 3 dispensas (R$ 7,79M!) + 30 contratos + 43 atas de RP

### Pessoas
- **825 servidores** cadastrados (749 ativos) com filtros por situação, vínculo e lotação
- **53 cargos comissionados** custando R$ 244k/mês (6% do quadro, 10% do custo)

### Achados-chave (Radar)
- ⚖️ Empenhou 22% a mais do que arrecadou (déficit de compromisso R$ 7,57M)
- 🏛️ 88% da receita vem de transferências externas
- ⚠️ 1 dispensa de R$ 7,79M sem licitação competitiva
- 🔄 16% dos empenhos foram anulados
- 💸 Só 22% dos empenhos viraram pagamento efetivo
- 🎩 Comissionados consomem 1.6× seu peso no quadro

## Estrutura

```
.
├── index.html                     # Portal de transparência (abrir no browser)
├── assets/
│   └── brasao.png                 # Brasão oficial (embutido como base64 no HTML)
├── scraping/
│   ├── _portaltp.py               # Helper compartilhado (Playwright + parsers)
│   │
│   ├── coleta_empenhos.py         # Empenhos individuais (despesas formais)
│   ├── coleta_pagamentos.py       # Pagamentos efetivos (3º estágio da despesa)
│   ├── coleta_diarias.py          # Diárias (via empenhos por elemento 33901400000)
│   ├── coleta_subvencoes.py       # Subvenções ao terceiro setor
│   ├── coleta_licitacoes.py       # Licitações + dispensas + contratos + atas RP
│   │
│   ├── coleta_receitas.py         # Receitas arrecadadas (de onde vem)
│   ├── coleta_transferencias.py   # Convênios/transferências recebidas
│   │
│   ├── coleta_servidores.py       # Cadastro de servidores + salário base
│   ├── coleta_comissionados.py    # Cargos de confiança (cruzado com servidores)
│   │
│   ├── agrega_credores.py         # Agrega empenhos por CNPJ → ranking
│   ├── gera_jsons_site.py         # CSVs → JSONs + insights + radar
│   ├── atualiza_index.py          # Gera index.html final a partir dos JSONs
│   │
│   ├── _inspect.py, _descobre_urls.py, _contar_endpoints.py
│   │                              # Diagnóstico de endpoints (não no pipeline)
│   └── _test_*.py                 # Validação de render/export
├── data/
│   ├── _raw/                      # Exports XML brutos do PortalTP (audit trail)
│   ├── empenhos_completo.csv      # Todos os 2324 empenhos do ano
│   ├── credores_completo.csv      # 384 credores agregados
│   ├── pagamentos_completo.csv    # 1324 pagamentos efetivos
│   ├── receitas_completo.csv      # 2544 receitas realizadas
│   ├── transferencias_completo.csv
│   ├── servidores_completo.csv    # 825 servidores
│   ├── comissionados_completo.csv # 53 cargos de confiança
│   ├── diarias_completo.csv
│   ├── subvencoes_completo.csv
│   ├── licitacoes_completo.csv, dispensas_completo.csv,
│   │   contratos_completo.csv, atas_completo.csv
│   ├── *_top50.csv / *_top20.csv  # Subsets antigos (artefato; portal usa _completo)
│   └── site/*.json                # JSONs completos + radar.json + insights.json
└── debug/                         # Screenshots e HTMLs de exploração
```

## Como usar

### Ver o portal

Abra `index.html` no browser. Não precisa de servidor.

### Atualizar os dados

```bash
pip install playwright beautifulsoup4 lxml
playwright install chromium

# Coletores (Playwright, ~30-60s cada). Empenhos é pré-requisito para diárias e credores.
python scraping/coleta_empenhos.py
python scraping/agrega_credores.py
python scraping/coleta_diarias.py       # depende de empenhos
python scraping/coleta_receitas.py
python scraping/coleta_transferencias.py
python scraping/coleta_pagamentos.py
python scraping/coleta_subvencoes.py
python scraping/coleta_servidores.py
python scraping/coleta_comissionados.py  # depende de servidores
python scraping/coleta_licitacoes.py     # licitações + dispensas + contratos + atas

# Pós-processamento (rápido, só stdlib)
python scraping/gera_jsons_site.py       # CSVs → JSONs + insights + radar
python scraping/atualiza_index.py        # gera o index.html final
```

Os CSVs são gerados em `data/`, JSONs em `data/site/`, e o `index.html` final na raiz.

## Fontes oficiais

- **[PortalTP Muzambinho](https://muzambinho-mg.portaltp.com.br/)** — sistema Fiorilli da Prefeitura (fonte primária)
- **[Site da Prefeitura · Transparência](https://www.muzambinho.mg.gov.br/transparencia)** — agregador oficial
- **[TransparênciaFácil](https://transparenciafacil.com.br/despesas/0184601)** — fonte secundária linkada pelo site oficial

## Notas técnicas

- O scraper usa Playwright (Chromium) porque o PortalTP é ASP.NET WebForms + DevExpress — ViewState/EventValidation impedem requests HTTP diretos.
- O portal **expõe export nativo CSV/XML/XLSX** dos grids; usamos o XML (estruturado) em vez de scrapear HTML.
- O XML do PortalTP tem tags com caracteres inválidos (`<CPF/CNPJ>`, `<Programa/Atividade/Ação>`, `<Categoria Econômica>`) e `&` cru em texto — saneamos antes de parsear (ver `scraping/_portaltp.py:ler_xml_grid`).
- CPFs de servidores e diaristas vêm mascarados pela LGPD (`***.123.456-**`); a Matrícula é a chave única.
- Sem dependência de pandas — só stdlib + Playwright + BeautifulSoup.

## Limitações conhecidas

- **Salários de servidores**: o PortalTP expõe apenas o **valor do nível salarial** (salário base de referência do cargo) — não a remuneração real em folha (sem horas extras, gratificações, descontos). O portal exibe a folha agregada como crédito do "FOLHA DE PAGAMENTO" no ranking de credores (R$ 12,3M/ano).
- **Anulações de empenhos**: 102 empenhos no ano têm valor negativo (correções/cancelamentos); são excluídos do top 50 mas contam no agregado por credor (Valor Líquido = Bruto − Anulações).
- **Período**: 01/01/2026 até a data da última coleta (veja o rodapé do `index.html`).

## Aviso

Este é um **projeto independente**, para fins informativos e de transparência cidadã. Não é gerido pela Prefeitura de Muzambinho. Todos os dados são públicos e extraídos do portal oficial. Se encontrar uma divergência, confira primeiro na fonte original e, se confirmada, abra uma _issue_.
