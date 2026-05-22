# muzambinho-transparente

Portal de transparência não oficial para os gastos públicos da **Prefeitura de Muzambinho – MG**, exercício de **2026**.

## O que é

Um scraper que coleta dados do [PortalTP oficial](https://muzambinho-mg.portaltp.com.br/) (sistema Fiorilli) e os apresenta num site estático autocontido — sem precisar navegar pelo sistema da prefeitura, sem servidor para rodar.

**O portal embute o dataset completo de cada categoria** — nada é truncado para "top N". Todas as listas têm busca, ordenação e filtros que percorrem o dataset inteiro, com paginação client-side de 60 itens por vez.

A primeira seção é um **Radar de Gastos** com cards de anomalias detectadas automaticamente (concentração de credores, dispensas de alto valor, anulações excessivas, etc.).

Cobertura atual:

- **2.324 empenhos** totalizando R$ 50,5 milhões no ano (todos navegáveis)
- **384 credores/fornecedores** agregados (top: Folha de Pagamento R$ 12,3M = 24% do orçamento)
- **825 servidores** cadastrados (749 ativos) com filtros por situação, vínculo e lotação
- **57 diárias** classificadas como elemento contábil 33901400000 (extraídas dos empenhos — o endpoint dedicado retornava só 6)
- **81 processos de compra**: 5 licitações + 3 dispensas (R$ 7,79M!) + 30 contratos + 43 atas de RP
- **8 achados no Radar de Gastos**, ordenados por severidade

## Estrutura

```
.
├── index.html                     # Portal de transparência (abrir no browser)
├── scraping/
│   ├── _portaltp.py               # Helper compartilhado (Playwright + parsers)
│   ├── coleta_empenhos.py         # Coleta empenhos individuais
│   ├── coleta_servidores.py       # Coleta cadastro de servidores + salário base
│   ├── coleta_diarias.py          # Coleta diárias de viagem
│   ├── coleta_licitacoes.py       # Coleta licitações e contratos
│   ├── agrega_credores.py         # Agrega empenhos por CNPJ → ranking
│   ├── gera_jsons_site.py         # CSVs → JSONs para o site
│   ├── atualiza_index.py          # Gera index.html a partir dos JSONs
│   ├── _inspect.py                # (diagnóstico) inspeciona forms do PortalTP
│   └── _test_*.py                 # (diagnóstico) testes de export e render
├── data/
│   ├── _raw/                      # Exports XML brutos do PortalTP
│   ├── empenhos_completo.csv      # Todos os 2324 empenhos do ano
│   ├── credores_completo.csv      # 384 credores agregados
│   ├── servidores_completo.csv    # 825 servidores
│   ├── diarias_completo.csv
│   ├── licitacoes_completo.csv
│   ├── contratos_completo.csv
│   ├── *_top50.csv / *_top20.csv  # Subsets (artefato; o portal usa os _completo)
│   └── site/*.json                # JSONs completos prontos para embutir no HTML
└── debug/                         # Screenshots e HTMLs de exploração
```

## Como usar

### Ver o portal

Abra `index.html` no browser. Não precisa de servidor.

### Atualizar os dados

```bash
pip install playwright beautifulsoup4 lxml
playwright install chromium

python scraping/coleta_empenhos.py     # ~30s
python scraping/agrega_credores.py     # instantâneo
python scraping/coleta_servidores.py   # ~30s
python scraping/coleta_diarias.py      # ~30s
python scraping/coleta_licitacoes.py   # ~30s (licitações + contratos)
python scraping/gera_jsons_site.py     # instantâneo
python scraping/atualiza_index.py      # gera o index.html final
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
