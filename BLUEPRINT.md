# BLUEPRINT — Portal de transparência cidadão (template replicável)

**Para a IA que está lendo isto:** este documento é um workflow completo. Siga-o para construir, de zero, um portal de transparência não-oficial para qualquer município brasileiro, espelhando a arquitetura validada de `muzambinho-transparente` (este repositório é a implementação de referência).

**Para o humano:** abra uma conversa com uma IA codante (Claude Code, Cursor, etc), cole este arquivo, e responda os inputs que ela vai solicitar. Em 30–60 minutos você tem um portal pronto.

---

## Fase 0 — Inputs que a IA deve solicitar

Antes de escrever uma linha de código, **pergunte ao usuário tudo abaixo**. Use uma única tela de perguntas se possível, mas não comece sem ter as respostas.

### 0.1 Identidade do município

| # | Pergunta | Exemplo |
|---|---|---|
| 1 | **Nome do município** | "Muzambinho" |
| 2 | **UF (estado)** | "MG" |
| 3 | **Apelido / curiosidade da cidade** (vai virar parte do branding e da paleta) | "Capital Nacional do Café", "Cidade Berço do Tropeirismo", "Capital Mundial do Sapato"… |

### 0.2 Fontes de dados

| # | Pergunta | Como descobrir |
|---|---|---|
| 4 | **URL do portal de transparência principal** | Geralmente um subdomínio ou rota tipo `https://<cidade-uf>.portaltp.com.br/`, `https://e-gov.betha.com.br/transparencia/<id>`, ou `https://transparencia.<cidade>.<uf>.gov.br/`. Verifique o site oficial da prefeitura. |
| 5 | **URL do site institucional da prefeitura** (opcional, complementar) | Tipo `https://www.<cidade>.<uf>.gov.br/` ou `https://prefeitura.<cidade>.<uf>.gov.br/` |
| 6 | **Sistema usado** (se já souber) — útil para escolher estratégia | PortalTP (Fiorilli), Cidade360 (PRONIM TB), IPM, BetHA, GovBR, TransparênciaFácil, Memory, e-Gov, etc. **Se não souber, a IA descobre na Fase 1.** |

### 0.3 Escopo

| # | Pergunta | Default sugerido |
|---|---|---|
| 7 | **Categorias de dados** (marque as desejadas) — empenhos por credor, salários/folha, diárias, licitações, contratos, obras, receitas, repasses, frota, bens patrimoniais. **Para cada categoria escolhida, o portal exibirá o dataset completo** — sem truncar para "top N". | Empenhos + credores + servidores + diárias + licitações + contratos (mesmo que `muzambinho-transparente`) |
| 8 | **Período de cobertura** | Ano corrente: `01/01/{ano} até hoje` |
| 9 | **Nome do projeto / repositório** | `<cidade>-transparente` (ex: `pocosdecaldas-transparente`) |

### 0.4 Estética

| # | Pergunta | Exemplo |
|---|---|---|
| 10 | **Paleta de cores** (a IA propõe uma baseada na curiosidade do item 3; o usuário aprova ou ajusta). **Use sempre tema escuro warm** — fundo claro cansa para leitura prolongada de tabelas/cards. | Para "Capital Nacional do Café" → dark coffee/gold/cream warm (`--bg: #1A100A`, `--gold: #D4A968`, `--ink: #F0E6D6`). Para cidade serrana → dark forest/moss. Para litoral → dark navy/coral. |
| 11 | **URL do brasão / logo oficial** (PNG/JPG/SVG do site da prefeitura — usar como `<img src="data:base64,...">` embutido) | Geralmente em `s3.amazonaws.com/.../uploads/.../brasao.png` ou no `<header>` do site oficial. Salvar em `assets/brasao.png` e converter para data URI no `atualiza_index.py`. Fallback: placeholder geométrico com inicial da cidade. |

### 0.5 Confirmações operacionais

| # | Pergunta | Default |
|---|---|---|
| 12 | **Apagar arquivos antigos do diretório?** (se for clone de outro projeto) | Sim, começar do zero |
| 13 | **Modo de execução** | Headless (sem janela do browser) |

**Não comece a Fase 1 sem ter os 13 inputs.** Se o usuário responder "decide você" em alguns, registre a decisão default explicitamente.

---

## Fase 1 — Reconhecimento do sistema (sem código de produção)

Objetivo: descobrir **qual sistema** é, **quais endpoints** existem, **quais IDs/seletores** os formulários usam, e **se existe export nativo** (CSV/XML/XLSX) que evite scraping de HTML.

### 1.1 Identificar o sistema

Acesse o portal de transparência (input #4) com **WebFetch** primeiro, depois com Playwright se precisar de mais detalhe. Procure por pistas:

| Pista no HTML | Sistema provável |
|---|---|
| `ctl00$containerCorpo$...` + DevExpress (`DXCT`, `DXR.axd`) | **PortalTP (Fiorilli)** ← caso de referência |
| `pronimtb`, cookie `ckAno`, `webapp*.cidade360.cloud` | **Cidade360 / PRONIM TB** |
| `transparenciafacil.com.br/.../<id>` | **TransparênciaFácil** |
| `e-gov.betha.com.br` ou `betha.com.br` | **BetHA** |
| `ipmbr.com.br`, `governancabrasil.com.br` | **IPM / GovBR** |
| `memory.com.br/transparencia` | **Memory** |
| Sem ASP.NET, rotas REST tipo `/api/...` | Sistema próprio / moderno |

### 1.2 Mapear endpoints

Crie `scraping/_inspect.py` (script descartável, não faz parte do pipeline) que:

1. Abre cada URL candidata para cada categoria
2. Dumpa: IDs de `<input>`/`<select>`/`<button>`, links de export (procurar por `.csv`, `.xlsx`, `.xml`, `.pdf` no texto), e screenshot da página
3. Imprime estrutura no console

URLs típicas para chutar (PortalTP):
- `/consultas/despesas/empenhos.aspx`
- `/consultas/pessoal/servidores.aspx`
- `/consultas/despesas/diarias.aspx`
- `/consultas/compras/licitacoes.aspx`
- `/consultas/compras/contratos.aspx`

URLs típicas para chutar (Cidade360):
- `/pronimtb/index.asp?...`

Adapte conforme o sistema. **Use o `_inspect.py` do `muzambinho-transparente` como base.**

### 1.3 Validar a estratégia de export

Para cada endpoint encontrado, escreva um `scraping/_test_export.py` (também descartável) que:

1. Preenche os filtros mínimos (ano, datas)
2. Clica "Pesquisar" / "Aplicar"
3. Aguarda o grid renderizar
4. **Tenta o export nativo**: localize o botão CSV/XML, capture com `page.expect_download()`
5. Salve em `debug/` e inspecione encoding + estrutura

**Se o export nativo funciona, use-o.** É mais limpo, mais rápido, mais robusto. Só caia para scraping HTML página-a-página se não houver alternativa.

### 1.4 Decida o formato (CSV vs XML vs XLSX)

- **XML estruturado** (`<DOCUMENTO><Campo>valor</Campo></DOCUMENTO>`) é o melhor — semântico, fácil de parsear.
- **CSV** muitas vezes vem em `cp1252`, separador `;`, com colunas mescladas via colspan. Útil mas requer pós-processamento.
- **XLSX** requer dependência extra (`openpyxl`). Evite se possível.

> **Armadilha**: o XML do PortalTP **não é XML válido** (tags `<CPF/CNPJ>`, `<Categoria Econômica>`, `&` cru em texto, sem root element). Você precisará de um saneador. Veja [scraping/_portaltp.py](scraping/_portaltp.py) função `ler_xml_grid` para a implementação de referência.

---

## Fase 2 — Helper compartilhado (`scraping/_portaltp.py` ou nome do sistema)

Crie um módulo único com:

```python
# Contexto manager para browser + cleanup garantido
@contextmanager
def navegador(headless=True) -> tuple[Browser, Context, Page]: ...

# Navegação
def abrir_consulta(page, path): ...

# Filtros (adapte para cada sistema)
def preencher_periodo_datas(page, ini, fim): ...
def preencher_ano(page, ano): ...
def preencher_mes(page, mes=""): ...  # tolerante (no-op se campo ausente)
def aplicar_filtro(page): ...

# Export
EXPORT_IDS = {"pdf": "...", "csv": "...", "xml": "...", "xlsx": "..."}
def baixar_export(page, destino, formato="xml"): ...

# Parser do formato escolhido (XML no caso de referência)
def ler_xml_grid(path) -> list[dict]: ...  # com saneamento se necessário

# Utilitários BR (sempre necessários)
def to_float_brl(s) -> float: ...       # "1.234,56" → 1234.56
def fmt_brl(v) -> str: ...              # 1234.56 → "R$ 1.234,56"
def normaliza_doc(cpf_cnpj) -> str: ... # só dígitos
def fmt_doc(digitos) -> str: ...        # CPF/CNPJ formatado
def parse_data_brl(s) -> str: ...       # normaliza "12/05/2026 00:00:00" → "12/05/2026"

# Escrita CSV (UTF-8-SIG, sep vírgula)
def escreve_csv(path, rows, colunas): ...
```

**Decisões obrigatórias:**

- **Não use pandas.** Use `csv` + `collections.defaultdict` do stdlib. Pandas tem problema de wheel em Python 32-bit e é dependência desnecessária.
- **Use Playwright (Chromium)**, não `requests`. ViewState/EventValidation do ASP.NET inviabilizam HTTP direto.
- **Encoding de saída: UTF-8 with BOM** (`utf-8-sig`). Garante que CSVs abram corretamente no Excel BR.
- **Coluna `_valor` (float)** ao lado da `R$` formatada; **coluna `_doc` (só dígitos)** ao lado do CPF/CNPJ formatado.

---

## Fase 3 — Coletores por categoria (um arquivo por categoria)

Para cada categoria escolhida (input #7), crie `scraping/coleta_<categoria>.py`.

**Por que um por categoria** (e não monolítico): cada endpoint tem campos distintos, falhas independentes, pode ser re-rodado isolado, e o helper já elimina a duplicação real.

Template de cada coletor (~50 linhas):

```python
from _portaltp import navegador, abrir_consulta, preencher_*, aplicar_filtro, \
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, normaliza_doc, \
    fmt_doc, parse_data_brl, escreve_csv, DATA, RAW

ANO = 2026
PATH = "/consultas/.../...aspx"

def main():
    raw_xml = RAW / f"<categoria>_{ANO}.xml"
    with navegador() as (browser, ctx, page):
        abrir_consulta(page, PATH)
        preencher_periodo_datas(page, "01/01/2026", hoje_str)  # ou ano+mês
        aplicar_filtro(page)
        baixar_export(page, raw_xml, formato="xml")

    rows = ler_xml_grid(raw_xml)
    normalizados = [{
        "Campo1": parse_data_brl(r.get("CampoOriginal", "")),
        "Campo2": r.get("Outro Campo", ""),
        ...
        "Valor": fmt_brl(to_float_brl(r.get("Valor", ""))),
        "_valor": to_float_brl(r.get("Valor", "")),
    } for r in rows]

    escreve_csv(DATA / "<categoria>_completo.csv", normalizados, list(normalizados[0]))
    top50 = sorted([r for r in normalizados if r["_valor"] > 0],
                   key=lambda r: -r["_valor"])[:50]
    for i, r in enumerate(top50, 1): r["Rank"] = i
    escreve_csv(DATA / "<categoria>_top50.csv", top50, ["Rank"] + list(normalizados[0]))

if __name__ == "__main__": main()
```

**Validação durante o desenvolvimento:**

- Rode o coletor uma vez. Inspecione os primeiros 3 registros do XML antes de finalizar os nomes de campos. Os campos exatos do PortalTP **variam por categoria** e nem sempre o nome que você espera (`Salário Bruto`) é o que existe (`Valor Nível Salarial`).
- Imprima o total monetário no final — comparar com o totalizador exibido no portal oficial é o smoke test mais útil.
- **Cuidado com LGPD**: CPFs de pessoas físicas (servidores, beneficiários de diárias) podem vir mascarados (`***.123.456-**`). Use Matrícula como chave única. CNPJs de pessoas jurídicas vêm completos.

---

## Fase 4 — Agregação de credores

Crie `scraping/agrega_credores.py` que lê `empenhos_completo.csv` e agrupa por `_doc` (CNPJ/CPF) somando:

- Quantidade de empenhos
- Quantidade de anulações (empenhos negativos)
- Valor bruto (só positivos)
- Valor líquido (positivos − anulações)

Ordene por valor líquido descendente. Gera `credores_completo.csv` + `credores_top50.csv`.

Use `collections.defaultdict(lambda: {...})`, não pandas.

---

## Fase 5 — Geração do site

### 5.1 `gera_jsons_site.py`

Converte CSVs **completos** em JSONs **compactos** (`separators=(",", ":")`) prontos para embutir. Lê os `*_completo.csv` (não os `*_top*.csv` — esses só existem como artefato em data/ caso alguém queira o subset).

Gera em `data/site/`:

- `credores.json` — todos os credores agregados
- `empenhos.json` — todos os empenhos do ano
- `servidores.json` — todos os servidores cadastrados
- `diarias.json` — todas as diárias
- `licitacoes.json` (objeto com `{licitacoes: [...], contratos: [...]}` completos)
- `kpis.json` — totais para a stats bar (total_empenhado, total_credores, folha_base_mensal, etc.) + `max_credor`/`max_empenho`/`max_salario` para normalizar barras visuais

**Tamanho esperado**: ~1.5–2MB total embutido no HTML. Aceitável para portal autocontido; carrega em 1–2s em qualquer conexão decente. Se exceder 5MB, considere remover campos pouco usados (subfuncao, processo redundante, etc.) — **nunca** truncar registros.

### 5.2 `atualiza_index.py`

Gera o `index.html` final. **HTML template inline em Python** (mais simples que arquivo separado), usando `str.format()`. Lembre de escapar chaves CSS/JS literais como `{{` e `}}`.

Estrutura do `index.html`:

1. **`<head>`**: Google Fonts (Playfair Display + DM Sans + DM Mono), CSS inline com paleta do input #10, SVG noise texture sutil
2. **`<header>` escuro** com brasão (input #11), nome da cidade, período, badge "Projeto independente"
3. **Stats bar sticky** com 4 KPIs (grid 2×2 mobile / 4×1 desktop)
4. **Intro curta** ("como ler este portal")
5. **Uma `<section>` por categoria** com:
   - **Chips de filtro** (situação, função, vínculo, etc.) com contadores `(N)` — em `.chips-group` separados por dimensão
   - **Toolbar**: `<input type="search">` + `<select>` de ordenação (default = `valor_desc`) + `<select>` de filtro categórico se aplicável + contador "N resultados" alinhado à direita
   - **Tabela responsiva** (coluna secundária esconde no mobile via `.opt { display:none }`) OU grid de cards
   - **Botão "Mostrar mais"** ao final, com texto dinâmico ("Mostrar mais 60 (de 324 restantes)")
   - Sem nenhum dataset truncado — todos os itens estão no JSON embutido
6. **Notas explicativas em `.note`** para qualquer dado que precise contexto (ex: "salário base ≠ remuneração líquida")
7. **`<footer>` escuro** com fontes oficiais linkadas, data da geração, atribuição
8. **`<script>`** com:
   - Constantes JSON literais com **datasets completos** (`CREDORES`, `EMPENHOS`, `SERVIDORES`, etc. — não `_TOP50`)
   - Função genérica `paginatedRender()` reutilizável + `appendBatch()` (ver padrão acima)
   - Funções `render*()` por categoria que chamam `paginatedRender()` com filterFn/sortFn específicos
   - Event listeners em search/sort/filtros disparam `render*()` (reseta paginação); botão "Mostrar mais" dispara `appendBatch()` (anexa próximo lote)

Idempotente. Re-rode quantas vezes quiser.

### 5.3 Pipeline completo

```bash
python scraping/coleta_empenhos.py
python scraping/agrega_credores.py
python scraping/coleta_servidores.py
python scraping/coleta_diarias.py
python scraping/coleta_licitacoes.py
python scraping/gera_jsons_site.py
python scraping/atualiza_index.py
```

---

## Fase 6 — Documentação

Escreva **depois** que o pipeline funcionar (você terá descoberto armadilhas que precisa documentar).

### `README.md`

- O que é o projeto
- Cobertura atual (números reais: X empenhos, R$ Y, Z credores…)
- Estrutura do diretório
- Como atualizar os dados (comandos)
- Fontes oficiais (input #4 + #5)
- Limitações conhecidas (LGPD, salário base vs remuneração, etc.)
- Aviso "projeto independente"

### `AGENTS.md`

- Stack
- **Peculiaridades do sistema** descobertas na prática (uma seção por armadilha)
- Pipeline (ordem de execução)
- Estrutura dos dados (convenções `_valor`, `_doc`, UTF-8-SIG)
- "O que não fazer" (anti-patterns)
- Scripts diagnósticos (`_inspect.py`, `_test_*.py`)

Veja [AGENTS.md](AGENTS.md) deste repo como referência exata.

---

## Fase 7 — Validação

Antes de declarar pronto, **rode**:

```bash
python scraping/_test_site.py   # 0 erros de console + contagem de cards
```

Verifique manualmente:

- [ ] Total empenhado bate com a soma exibida no portal oficial (cross-check de pelo menos 1–2 valores)
- [ ] Abrir `index.html` direto no browser (sem servidor) renderiza todas as seções
- [ ] Mobile (DevTools 375px) e desktop (1280px+) ambos legíveis
- [ ] Buscas e filtros funcionam offline
- [ ] Links de export no rodapé funcionam
- [ ] CPFs sensíveis estão mascarados (LGPD)

---

## Catálogo de sistemas (referência rápida)

### PortalTP (Fiorilli) — ✅ caso de referência

- **Domínio típico**: `<cidade>-<uf>.portaltp.com.br`
- **Stack**: ASP.NET WebForms + DevExpress
- **IDs**: `ctl00$containerCorpo$<nome>` (DOM usa `_` em vez de `$`)
- **Combos DevExpress**: `_I` (visível), `_VI` (valor), `_L` (lista)
- **Export**: dentro do menu "Imprimir Relatório" — **precisa clicar no pai primeiro**
- **XML válido?** Não — tags com chars inválidos + `&` cru + sem root
- **Encoding XML**: UTF-8 BOM. **Encoding CSV**: cp1252.
- **Endpoints úteis** (todos em `/consultas/`):
  - `despesas/empenhos.aspx`, `despesas/diarias.aspx` (cuidado: pode estar filtrado!), `despesas/passagens.aspx`, `despesas/liquidacoes.aspx`, `despesas/pagamentos.aspx`, `despesas/obras.aspx`, `despesas/subvencoes.aspx`
  - `compras/licitacoes.aspx`, `compras/dispensas.aspx`, `compras/contratos.aspx`, `compras/atas.aspx`
  - `pessoal/servidores.aspx`, `pessoal/cargosconfianca.aspx`
- **API REST de dados abertos**: `/api/dadosabertos.aspx` lista 30+ endpoints em JSON/CSV/XML/TXT, licença CC0 (domínio público). Inclui datasets que não estão nas consultas web: receitas detalhadas, frota, bens patrimoniais, convênios, estagiários. **Roadmap futuro: integrar via REST puro (sem Playwright).**
- **Armadilhas**: ver [AGENTS.md](AGENTS.md) seções 1–10

### Cidade360 / PRONIM TB

- **Domínio típico**: `webapp*-<cidade>.cidade360.cloud/pronimtb/`
- **Stack**: ASP legado
- **Armadilhas conhecidas**: botão `#confirma` oculto via CSS (`display:none` — precisa torná-lo visível via JS antes de clicar); sessão server-side via cookie `ckAno`; paginação via `javascript:location.href` (clicar em link quebra contexto JS — use `page.goto(extracted_url)`); requer datas explícitas em `#txtDataInicial`/`#txtDataFinal`.
- **Estratégia**: scraping HTML página-a-página com Playwright. Não tem export nativo.

### TransparênciaFácil

- **Domínio típico**: `transparenciafacil.com.br/<categoria>/<id-municipio>`
- **Estratégia**: REST API às vezes disponível; fallback HTML scraping. Mais simples que ASP.NET.

### BetHA / e-Gov

- **Domínio típico**: `e-gov.betha.com.br/transparencia/<id>`
- **Stack**: Java + Angular
- **Estratégia**: tem API REST documentada; preferir API a scraping.

### IPM / GovBR

- **Domínio típico**: `governancabrasil.com.br` ou subdomínio próprio
- **Stack**: ASP.NET
- **Estratégia**: similar ao PortalTP — provável export nativo de relatórios.

**Se o sistema não está no catálogo**: rode a Fase 1 com cuidado extra e documente o que descobrir num PR para este arquivo.

---

## Estrutura final esperada do projeto

```
<cidade>-transparente/
├── BLUEPRINT.md              # este arquivo (copie do repo de referência)
├── README.md                 # documentação do usuário
├── AGENTS.md                 # documentação para futuras IAs
├── index.html                # portal autocontido (~100KB)
├── scraping/
│   ├── _<sistema>.py         # helper compartilhado
│   ├── coleta_*.py           # um por categoria
│   ├── agrega_credores.py    # se houver categoria empenhos
│   ├── gera_jsons_site.py
│   ├── atualiza_index.py
│   └── _inspect.py, _test_*.py  # diagnósticos
├── data/
│   ├── _raw/*.xml            # exports brutos (debug)
│   ├── *_completo.csv        # normalizados
│   ├── *_top50.csv           # subsets para o site
│   └── site/*.json           # JSONs embutidos no index.html
└── debug/                    # screenshots, HTMLs de exploração
```

---

## Princípios não-negociáveis

1. **Máximo de informação, sem truncar.** O portal embute o **dataset completo** da fonte — todos os empenhos, todos os credores, todos os servidores, todas as diárias, todos os contratos. Nada de "top 20" ou "top 50". O leitor merece ver tudo que é público. Use paginação client-side (ver seção abaixo) para gerenciar performance sem esconder dados.
2. **Filtros, busca e ordenação em todas as seções.** Toda lista deve ter: input de busca livre (busca em múltiplos campos com `.toLowerCase().includes(q)`), dropdown de ordenação (mínimo: maior valor, mais recente, A-Z), e quando o domínio permitir, chips de filtro categórico (situação, função, vínculo, modalidade, etc.) com contadores `(N)` ao lado de cada categoria.
3. **Ordenação padrão: do maior para o menor.** A primeira coisa que o usuário vê é o que mais importa — defaults devem ser `valor_desc` ou equivalente, nunca alfabético ou data ascendente.
4. **NUNCA confiar em um único endpoint de subcategoria — sempre cruzar com empenhos por elemento de despesa.** A grande armadilha aprendida no Muzambinho: o endpoint `/consultas/despesas/diarias.aspx` retornou 6 registros; cruzando com `empenhos_completo.csv` filtrando pelo elemento contábil `33901400000 - Diárias - Pessoal Civil`, encontramos **57 empenhos**. Mesmo padrão para outras subcategorias (passagens, obras, restos a pagar). Os endpoints dedicados frequentemente filtram demais (só pegam registros com "Base Legal" preenchida ou similar) e dão uma falsa sensação de transparência. **A fonte de verdade é sempre o empenho contabilizado**. Documente a divergência em `<div class="note">` na seção, explicando ao leitor por que sua fonte é mais completa que o endpoint dedicado.
5. **Radar de Gastos como primeira seção.** Depois da intro, antes de qualquer lista, mostre um grid de cards com anomalias/concentrações detectadas automaticamente (heurísticas, não ML). Veja seção "Radar de Gastos" abaixo.
6. **Navegação sticky no topo.** Depois do header e stats, uma `<nav>` sticky com âncoras para cada seção. Inclua contadores `(N)` ao lado de cada link e scroll-spy (IntersectionObserver) para destacar a seção visível.
7. **Tema escuro warm**, nunca claro puro. Fundo `#1A100A` ou similar; texto `#F0E6D6`. Tabelas/cards levemente mais claros que o fundo. Acentos em gold luminoso (`#D4A968`). "Flashbang branco" cansa para leitura prolongada de tabelas.
8. **Dados públicos, projeto independente.** Sempre incluir aviso "não é gerido pela prefeitura" no footer e header.
9. **Auditabilidade.** Cada número deve ser verificável na fonte oficial. Sempre linke as fontes no footer.
10. **Autocontido.** `index.html` abre direto no browser, sem servidor, sem internet (exceto pelas Google Fonts). Brasão oficial embutido como data URI base64.
11. **LGPD.** Não desmasque CPFs que vêm mascarados pelo portal. Use chaves alternativas (Matrícula).
12. **Honestidade sobre limitações.** Se "salário" exibido é só o base de referência, diga isso em `<div class="note">` ao lado do dado. Não engane o leitor.
13. **Sem dependências pesadas.** stdlib + Playwright + BeautifulSoup. Sem pandas, sem React, sem build step.
14. **Re-executável.** Todos os scripts devem ser idempotentes — rodar de novo só atualiza dados, não quebra nada.

## Padrão de Radar de Gastos ("O que os dados revelam")

A **primeira seção** depois da intro (antes de qualquer lista) deve ser um grid de cards com **anomalias e concentrações** detectadas automaticamente — não acusações, mas **pistas para investigação cidadã**. Implementação em `scraping/gera_jsons_site.py:gera_radar()` que gera `data/site/radar.json` e é embutido como `RADAR` no template.

### Heurísticas obrigatórias (calcule cada uma; mostre só as que tiverem achado relevante)

| # | Heurística | Severidade | Threshold |
|---|---|---|---|
| 1 | **Concentração de credor** — top credor > X% do orçamento | alta se > 25%, media se > 10% | 10% |
| 2 | **Dispensas de licitação acima de R$ 100k** — total e quantidade | alta sempre que > 0 | R$ 100k (Lei 14.133/21 só permite "comum" até R$ 59.906) |
| 3 | **Anulações expressivas** — % de empenhos anulados sobre o total | alta se > 15%, media se > 8% | 8% |
| 4 | **Credores com muitas anulações** — top credor com ≥ 5 anulações | media | 5 anulações |
| 5 | **Concentração por função/área** — top 3 áreas de governo | info | mostrar sempre |
| 6 | **Fornecedores em múltiplas categorias** — CNPJs em contratos + atas + dispensas | info | mostrar se ≥ 1 |
| 7 | **Servidores em regime não-ativo** — % do quadro afastado/licenciado | baixa | 7% |
| 8 | **Histórico genérico em empenhos altos** — termos vagos ("diversas", "outros") + valor ≥ R$ 50k | baixa | mostrar se > 0 |

### Estrutura de cada achado (JSON)

```python
{{"tipo": "dispensa", "icone": "⚠️", "severidade": "alta",
 "titulo": "1 dispensa(s) acima de R$ 100 mil",
 "descricao": "Total R$ 7,79M contratado sem certame. Lei 14.133/21 permite dispensa comum só até R$ 59.906,02 — valores maiores devem ser inexigibilidade fundamentada.",
 "link": "#licitacoes"}}
```

Severidade vira cor da borda esquerda do card: `alta` (vermelho), `media` (laranja), `baixa` (gold), `info` (musgo verde). Ordenar do mais grave para o menos.

**Tom obrigatório**: conservador, explicativo, sem acusar irregularidade. Cada achado deve ter contexto que ajuda o leitor leigo a entender por que aquilo chamou atenção (ex: citar o limite legal, explicar o que é uma dispensa, etc.).

## Padrão de paginação client-side

Datasets podem ter milhares de itens (2.300+ empenhos não é incomum). Renderizar tudo no DOM de uma vez trava o browser. Padrão obrigatório:

```javascript
const PAGE_SIZE = 60;
const state = {{}};  // {{ key: {{ filtered: [...], cursor: 0 }} }}

function paginatedRender({{key, dataset, filterFn, sortFn, renderItem, container, moreBtn, countEl}}) {{
  // Aplica filtro + sort no DATASET INTEIRO, guarda no state
  const filtered = dataset.filter(filterFn).sort(sortFn);
  state[key] = {{ filtered, cursor: 0 }};
  $(container).innerHTML = '';
  appendBatch(key, renderItem, container, moreBtn, countEl);
}}

function appendBatch(key, renderItem, container, moreBtn, countEl) {{
  const s = state[key];
  const slice = s.filtered.slice(s.cursor, s.cursor + PAGE_SIZE);
  s.cursor += slice.length;
  $(container).insertAdjacentHTML('beforeend', slice.map(renderItem).join(''));
  // Botão "Mostrar mais N (de M restantes)"
  const rest = s.filtered.length - s.cursor;
  $(moreBtn).style.display = rest > 0 ? 'block' : 'none';
  $(moreBtn).textContent = `Mostrar mais ${{Math.min(PAGE_SIZE, rest)}} (de ${{rest}} restantes)`;
  $(countEl).textContent = `${{s.filtered.length}} resultados`;
}}
```

Regras de UX:
- **Busca/sort/filtro reseta cursor para 0** — toda mudança de input dispara `paginatedRender()`, não `appendBatch()`.
- **Botão "Mostrar mais" só dispara `appendBatch()`** (anexa próximo lote ao final, sem refiltrar).
- **Contador no canto direito do toolbar** ("384 resultados" / "175 resultados") informa o tamanho do dataset filtrado, não só o visível.
- **Datasets pequenos (<60)** podem dispensar a paginação — mas mantenha busca e sort.

---

## Implementação de referência

Este blueprint foi extraído de [`muzambinho-transparente`](https://github.com/) (Muzambinho/MG, sistema PortalTP/Fiorilli):

- 2.324 empenhos coletados (R$ 50,5M)
- 384 credores agregados
- 825 servidores
- 30 contratos + 5 licitações
- `index.html` final de 96KB, 0 erros de console
- Tempo total de implementação: ~1 hora

Use os arquivos `scraping/_portaltp.py`, `scraping/coleta_empenhos.py`, `scraping/atualiza_index.py` deste repo como template direto — copie e adapte.
