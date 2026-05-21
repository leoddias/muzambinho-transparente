# AGENTS.md

Instruções para agentes de IA trabalhando neste repositório.

## Contexto do projeto

Scraper + portal estático de transparência para a Prefeitura de Muzambinho (MG).
O portal de origem é o **PortalTP da Fiorilli** (versão 3.26.x), um sistema ASP.NET WebForms com **DevExpress** — moderno o bastante para ter export CSV/XML nativo, mas suficientemente quirky para ter armadilhas próprias.

## Arquitetura

- **Coleta**: Python (stdlib + Playwright + BeautifulSoup). Sem pandas.
- **Estratégia**: baixar **XML estruturado** via botão de export nativo do PortalTP — muito melhor que scrapear HTML página-a-página.
- **Dados**: CSVs UTF-8-SIG em `data/`, JSONs em `data/site/`, XML brutos em `data/_raw/`.
- **Apresentação**: `index.html` único, autocontido, com dados embutidos como JSON literal no `<script>`. Gerado por `scraping/atualiza_index.py` a partir dos JSONs.

## Princípio editorial: dataset completo, nunca truncado

O `index.html` embute **todos** os registros de cada categoria (~1.7MB total no caso de Muzambinho). Não há "top 20" ou "top 50" no portal — o leitor pode navegar todos os 2.324 empenhos, 825 servidores, 384 credores etc. Toda lista tem:

- **Busca** livre por múltiplos campos
- **Ordenação** padrão de maior valor para menor (`valor_desc`)
- **Filtros** categóricos quando o domínio permitir (chips de situação, função, vínculo, modalidade…) com contadores `(N)`
- **Paginação client-side** de 60 itens por batch — botão "Mostrar mais X (de Y restantes)" — para não travar o DOM ao renderizar milhares de cards

Implementação em `atualiza_index.py`: funções genéricas `paginatedRender()` + `appendBatch()` reutilizadas por todas as seções. Filtros/sort operam no dataset inteiro, depois pagina o resultado.

Os CSVs `*_top50.csv` e `*_top20.csv` em `data/` ainda são gerados pelos coletores como artefato/cache, mas o portal lê **apenas** os `*_completo.csv` (via `gera_jsons_site.py`).

## Peculiaridades do PortalTP/Fiorilli (descobertas na prática)

Leia estas regras antes de mexer no scraper. Foram pagas em tentativa-e-erro.

### 1. Stack ASP.NET WebForms + DevExpress

Todos os controles seguem o padrão `ctl00$containerCorpo$xxx`. As IDs no DOM vêm com `_` em vez de `$` (e.g. `ctl00_containerCorpo_cbxEntidades_I`). Comboboxes DevExpress têm sufixos: `_I` (input visível), `_VI` (hidden value), `_L` (listbox). Para preencher o combo, basta `page.fill()` no `_I` e dar Tab.

### 2. Campos comuns em todas as consultas

| ID | O que é |
|---|---|
| `ctl00_containerCorpo_cbxEntidades_I` | Combo "Entidade" (Prefeitura, Câmara…) |
| `ctl00_containerCorpo_btnAplicFiltro` | Botão "Aplicar" |
| `ctl00_containerCorpo_grdData` | Grid de resultados |

Empenhos usa intervalo de datas (`edtDataIni_I`, `edtDataFim_I`).
Servidores, diárias, licitações, contratos usam combos ano+mês (`cbxAno_I`, `cbxMes_I`).
Contratos **não** tem `cbxMes_I` — por isso `preencher_mes()` em `_portaltp.py` é no-op se o campo não existe.

### 3. Export nativo via menu suspenso

O PortalTP tem botões `.pdf`, `.xlsx`, `.csv`, `.xml` mas estão **dentro de um submenu** "Imprimir Relatório" que não está visível por padrão. Você precisa **clicar no menu pai primeiro**:

```python
# 1. Abre o submenu (sem isso o link de export fica invisível)
page.click("#ctl00_containerCorpo_grdData_DXCTMenu0_DXI2_T")
page.wait_for_timeout(1000)
# 2. Captura o download
with page.expect_download() as dl_info:
    page.click("#ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i5_T")  # .xml
```

IDs dos exports (sob `DXI2`):

| Formato | ID |
|---|---|
| .pdf | `...DXI2i0_T` |
| .xlsx | `...DXI2i2_T` |
| .csv | `...DXI2i4_T` |
| .xml | `...DXI2i5_T` ← escolhido |

### 4. Por que XML (e não CSV)

O CSV do PortalTP é **bagunçado**: separador `;`, encoding **Windows-1252**, cabeçalho com colunas mescladas via colspan (`Detalhes;;Data;;;;;;;Processo;;;;;;...`), e dados auxiliares (função, subfunção) ocupando 2 linhas extras por empenho. 6974 linhas para 2324 empenhos.

O XML (`GridViewExport.xml`) tem `<DOCUMENTO>` por item com tags semânticas. **É a melhor fonte**.

### 5. O XML não é XML válido

Três problemas. `scraping/_portaltp.py:ler_xml_grid` resolve todos:

a) **Sem root element** — é só uma sequência de `<DOCUMENTO>`. Envolvemos com `<ROOT>` antes de parsear.

b) **Tags com chars inválidos**: `<CPF/CNPJ>`, `<Categoria Econômica>`, `<Programa/Atividade/Ação>`, `<Tipo do Empenho>` — barras, espaços e parênteses não são permitidos. Saneamos substituindo por `_` e remapeamos para o nome original ao construir o dicionário.

c) **`&` cru em texto** — "COMERCIAL J & C COMEX LTDA". Em XML deve ser `&amp;`. Escapamos via regex que preserva entidades válidas existentes.

### 6. CPFs mascarados por LGPD

CPFs de servidores e diaristas vêm como `***.694.078-**` (só 6 dígitos no meio). Não use como chave única — use **Matrícula**.

CNPJs de fornecedores e contratos vêm completos.

### 7. "Salário" de servidor é só o valor do nível

A consulta `/consultas/pessoal/servidores.aspx` expõe **`Valor Nível Salarial`** — o salário base do nível do cargo, **sem** adicionais e antes dos descontos. Não é a remuneração real. O portal documenta isso para o leitor numa nota explicativa. A folha real agregada aparece como crédito de "FOLHA DE PAGAMENTO" no ranking de credores (linha do orçamento).

### 8. UpdatePanel async

Após clicar "Aplicar", o grid é renderizado via UpdatePanel. `page.wait_for_load_state("networkidle")` **não basta** — preciso também `wait_for_selector("#ctl00_containerCorpo_grdData")` e um `wait_for_timeout(2000)` paranoico (a renderização do grid às vezes acontece em duas fases).

### 9. Encoding do CSV: cp1252

Caso precise cair no fallback de CSV (não use), leia com `encoding="cp1252"` e reescreva como UTF-8-SIG. XML vem em UTF-8 (com BOM).

## Pipeline

```bash
python scraping/coleta_empenhos.py     # gera empenhos_completo.csv
python scraping/agrega_credores.py     # depende de empenhos → credores_*.csv
python scraping/coleta_servidores.py   # servidores_*.csv
python scraping/coleta_diarias.py      # diarias_*.csv
python scraping/coleta_licitacoes.py   # licitacoes + contratos
python scraping/gera_jsons_site.py     # data/site/*.json
python scraping/atualiza_index.py      # index.html
```

Cada `coleta_*.py` é **independente** — pode rodar isolado. `agrega_credores.py` depende do `empenhos_completo.csv`.

## Estrutura dos dados

CSVs UTF-8-SIG, separador vírgula, sempre com colunas auxiliares:
- `_valor` (float) ao lado da `R$` formatada
- `_doc` (só dígitos) ao lado de CPF/CNPJ formatado

Convenção preservada do projeto Divinolândia original.

## Atualizar o portal

O `index.html` é **regerado do zero** por `atualiza_index.py` — não tem markers manuais. Para mudar layout, edite o `HTML_TEMPLATE` (string raw f-format) dentro do script. Lembre que chaves CSS/JS literais precisam ser escapadas como `{{` e `}}`.

## O que não fazer

- **Não usar `requests`** — o PortalTP exige ViewState/EventValidation por POST; vai retornar erro 500 ou HTML de erro.
- **Não pular o click no menu pai "Imprimir Relatório"** antes de clicar no botão de export — o link de download fica invisível.
- **Não remover `wait_for_timeout(2000)` após Aplicar** — o grid renderiza em duas fases e pode dar timing race.
- **Não usar CPF como chave única** para servidores ou diaristas — vem mascarado pela LGPD.
- **Não assumir que o XML do PortalTP é XML válido** — passe sempre pelo `ler_xml_grid` do helper.
- **Não instalar pandas** — Python 32-bit deste ambiente não tem wheel; o projeto roda com stdlib pura.

## Scripts diagnósticos

Os arquivos com prefixo `_` em `scraping/` são utilitários para inspeção, não fazem parte do pipeline:

- `_inspect.py` — dumpa IDs/forms/exports de todos os endpoints (útil quando PortalTP for atualizado e os IDs `ctl00$...` mudarem)
- `_test_export.py` — testa export CSV/XML em empenhos com network logging
- `_test_site.py` / `_test_site_close.py` — testa render do `index.html` (console errors, contagem de cards, screenshots)

Mantém-se aqui por serem úteis em manutenção futura.
