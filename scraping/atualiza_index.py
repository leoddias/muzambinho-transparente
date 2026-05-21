"""Monta o index.html final embutindo os JSONs de data/site/*.json.

Estrategia: o HTML eh um template inline aqui (mais simples que manter um
.html.tpl separado em sincronia). Roda apos gera_jsons_site.py:

    python scraping/coleta_empenhos.py
    python scraping/agrega_credores.py
    python scraping/coleta_servidores.py
    python scraping/coleta_diarias.py
    python scraping/coleta_licitacoes.py
    python scraping/gera_jsons_site.py
    python scraping/atualiza_index.py   # <- gera index.html

Idempotente: rode quantas vezes quiser.
"""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = DATA / "site"
OUT = ROOT / "index.html"

MESES_PT = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def carrega(nome: str):
    return json.load((SITE / f"{nome}.json").open(encoding="utf-8"))


def fmt_brl(v: float) -> str:
    if v < 0:
        return "-" + fmt_brl(-v)
    inteiro, _, dec = f"{v:.2f}".partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return f"R$ {'.'.join(grupos)},{dec}"


def fmt_brl_compacto(v: float) -> str:
    """R$ 12,3M / R$ 423,5K / R$ 438,32"""
    if v >= 1_000_000:
        s = f"{v/1_000_000:.2f}".replace(".", ",")
        return f"R$ {s}M"
    if v >= 1_000:
        s = f"{v/1_000:.1f}".replace(".", ",")
        return f"R$ {s}K"
    return fmt_brl(v)


def main() -> None:
    credores = carrega("credores_top50")
    empenhos = carrega("empenhos_top50")
    servidores = carrega("servidores_top20")
    diarias = carrega("diarias")
    licitacoes = carrega("licitacoes")
    kpis = carrega("kpis")

    hoje = date.today()
    data_geracao = f"{hoje.day} de {MESES_PT[hoje.month]} de {hoje.year}"
    periodo = f"01/01/2026 a {hoje.strftime('%d/%m/%Y')}"

    # Serializa cada JSON como literal JS compacto (sem espacos)
    def js(o) -> str:
        return json.dumps(o, ensure_ascii=False, separators=(",", ":"))

    kpi_emp = fmt_brl_compacto(kpis["total_empenhado"])
    kpi_folha = fmt_brl_compacto(kpis["folha_base_mensal"])
    kpi_diarias = fmt_brl_compacto(kpis["total_diarias"])
    kpi_contratos = fmt_brl_compacto(kpis["total_contratos"])

    html = HTML_TEMPLATE.format(
        data_geracao=data_geracao,
        periodo=periodo,
        kpi_empenhado=kpi_emp,
        kpi_qtd_empenhos=f"{kpis['total_empenhos']:,}".replace(",", "."),
        kpi_qtd_credores=kpis["total_credores"],
        kpi_folha=kpi_folha,
        kpi_qtd_servidores_ativos=kpis["servidores_ativos"],
        kpi_qtd_servidores_total=kpis["total_servidores"],
        kpi_diarias=kpi_diarias,
        kpi_qtd_diarias=kpis["qtd_diarias"],
        kpi_contratos=kpi_contratos,
        kpi_qtd_contratos=kpis["qtd_contratos"],
        kpi_qtd_licitacoes=kpis["qtd_licitacoes"],
        json_credores=js(credores),
        json_empenhos=js(empenhos),
        json_servidores=js(servidores),
        json_diarias=js(diarias),
        json_licitacoes=js(licitacoes),
        json_kpis=js(kpis),
    )

    OUT.write_text(html, encoding="utf-8")
    print(f"  Gerado: {OUT.name} ({OUT.stat().st_size:,} bytes)")


# ----------------------------------------------------------------------
# HTML TEMPLATE - usa {nome} para placeholders simples (.format)
# Chaves CSS/JS literais sao escapadas como {{ }}.
# ----------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Muzambinho Transparente · Gastos Públicos 2026</title>
<meta name="description" content="Portal não oficial de transparência da Prefeitura de Muzambinho/MG — empenhos, credores, servidores, diárias e licitações.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,500&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink:    #1A0E08;
    --coffee: #3D2418;
    --terra:  #8B4A2B;
    --clay:   #C97B4A;
    --cream:  #F5EDE0;
    --paper:  #FAF6EE;
    --moss:   #5C7548;
    --gold:   #B8893A;
    --line:   rgba(26,14,8,0.12);
    --shade:  rgba(26,14,8,0.04);
    --bar-bg: rgba(184,137,58,0.18);
    --bar-fg: linear-gradient(90deg, var(--clay), var(--gold));
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    font-family: 'DM Sans', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    color: var(--ink);
    background: var(--paper);
    line-height: 1.55;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
  }}
  body::before {{
    content: "";
    position: fixed; inset: 0;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.10 0 0 0 0 0.06 0 0 0 0 0.03 0 0 0 0.04 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
    pointer-events: none;
    z-index: 0;
    opacity: 0.6;
  }}
  main, header, footer {{ position: relative; z-index: 1; }}

  a {{ color: var(--terra); text-decoration: underline; text-underline-offset: 3px; text-decoration-thickness: 1px; }}
  a:hover {{ color: var(--coffee); }}

  h1, h2, h3, h4 {{ font-family: 'Playfair Display', Georgia, serif; font-weight: 700; line-height: 1.15; color: var(--coffee); margin: 0; }}
  h1 {{ font-size: clamp(1.8rem, 4.5vw, 3.2rem); letter-spacing: -0.02em; }}
  h2 {{ font-size: clamp(1.4rem, 3vw, 2.2rem); letter-spacing: -0.01em; margin-bottom: 0.5em; }}
  h3 {{ font-size: 1.15rem; }}

  .mono {{ font-family: 'DM Mono', ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .label {{ font-family: 'DM Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--terra); }}
  .num   {{ font-family: 'DM Mono', monospace; font-variant-numeric: tabular-nums; }}

  /* --- HEADER --- */
  header.site-head {{
    background: var(--coffee);
    color: var(--cream);
    padding: 1.25rem 1rem 1.5rem;
    border-bottom: 4px solid var(--gold);
  }}
  header.site-head .wrap {{ max-width: 1180px; margin: 0 auto; display: flex; gap: 1.25rem; align-items: center; }}
  .brasao {{
    width: 64px; height: 64px; border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, var(--gold), var(--terra) 70%);
    flex-shrink: 0;
    display: grid; place-items: center;
    color: var(--coffee);
    font-family: 'Playfair Display', serif;
    font-weight: 700; font-size: 1.5rem;
    border: 2px solid var(--cream);
    box-shadow: inset 0 0 0 4px rgba(26,14,8,0.15);
  }}
  header.site-head h1 {{ color: var(--cream); font-size: clamp(1.4rem, 3.5vw, 2.3rem); margin: 0; }}
  header.site-head .sub {{ display: block; font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); margin-top: 0.3rem; }}
  header.site-head .demo {{
    margin-left: auto; font-family: 'DM Mono', monospace; font-size: 0.65rem; padding: 0.35rem 0.7rem;
    border: 1px solid var(--gold); border-radius: 999px; color: var(--gold); letter-spacing: 0.1em; text-transform: uppercase;
    flex-shrink: 0;
  }}

  /* --- INTRO --- */
  .intro {{ max-width: 760px; margin: 2.5rem auto 1rem; padding: 0 1rem; }}
  .intro p {{ font-size: 1.1rem; }}
  .intro .label {{ display: block; margin-bottom: 0.6rem; }}

  /* --- STATS BAR --- */
  .stats {{
    background: var(--cream);
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    position: sticky; top: 0; z-index: 50;
    backdrop-filter: blur(8px);
  }}
  .stats .wrap {{ max-width: 1180px; margin: 0 auto; padding: 0.75rem 1rem; display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem 1.5rem; }}
  @media (min-width: 768px) {{ .stats .wrap {{ grid-template-columns: repeat(4, 1fr); }} }}
  .stat .label {{ display: block; }}
  .stat .v {{ font-family: 'Playfair Display', serif; font-size: clamp(1.15rem, 3vw, 1.7rem); font-weight: 700; color: var(--coffee); line-height: 1.1; }}
  .stat .desc {{ font-size: 0.78rem; color: var(--terra); margin-top: 0.15rem; }}

  /* --- SECTIONS --- */
  section {{ max-width: 1180px; margin: 0 auto; padding: 3.5rem 1rem 1rem; }}
  section.tight {{ padding-top: 2rem; }}
  section .lead {{ max-width: 720px; color: rgba(26,14,8,0.78); margin-top: 0.4rem; font-size: 1.02rem; }}

  /* --- TABLE (credores) --- */
  .toolbar {{ display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; margin: 1.25rem 0 0.75rem; }}
  .toolbar input, .toolbar select {{
    font-family: 'DM Sans', sans-serif; font-size: 0.95rem;
    padding: 0.55rem 0.85rem; border: 1px solid var(--line); border-radius: 8px;
    background: var(--paper); color: var(--ink);
    min-width: 0;
  }}
  .toolbar input {{ flex: 1; max-width: 360px; }}
  .toolbar select {{ background: var(--cream); }}
  .toolbar .count {{ font-family: 'DM Mono', monospace; font-size: 0.78rem; color: var(--terra); margin-left: auto; }}

  table.t {{
    width: 100%; border-collapse: collapse; font-size: 0.92rem;
    background: var(--paper); border: 1px solid var(--line); border-radius: 10px; overflow: hidden;
  }}
  table.t thead th {{
    text-align: left; padding: 0.7rem 0.9rem; background: var(--cream);
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--coffee); font-weight: 500; border-bottom: 1px solid var(--line);
  }}
  table.t tbody td {{ padding: 0.65rem 0.9rem; border-top: 1px solid var(--shade); vertical-align: middle; }}
  table.t tbody tr:hover {{ background: var(--shade); }}
  table.t td.r, table.t th.r {{ text-align: right; font-variant-numeric: tabular-nums; }}
  table.t td.num {{ font-family: 'DM Mono', monospace; }}
  table.t td.rank {{ font-family: 'DM Mono', monospace; color: var(--terra); width: 2.5rem; text-align: right; }}
  table.t td.fav {{ font-weight: 500; color: var(--coffee); }}
  table.t td.bar-cell {{ width: 30%; padding-right: 1.5rem; }}
  .bar {{ position: relative; height: 10px; border-radius: 999px; background: var(--bar-bg); overflow: hidden; min-width: 60px; }}
  .bar > i {{ position: absolute; top: 0; bottom: 0; left: 0; background: var(--bar-fg); display: block; border-radius: 999px; min-width: 4px; }}
  @media (max-width: 768px) {{
    table.t th.opt, table.t td.opt {{ display: none; }}
    table.t {{ font-size: 0.85rem; }}
    table.t thead th, table.t tbody td {{ padding: 0.55rem 0.6rem; }}
  }}

  /* --- CARDS --- */
  .cards {{ display: grid; gap: 0.85rem; grid-template-columns: 1fr; margin-top: 1rem; }}
  @media (min-width: 720px) {{ .cards {{ grid-template-columns: repeat(2, 1fr); }} }}
  @media (min-width: 1024px) {{ .cards {{ grid-template-columns: repeat(3, 1fr); }} }}
  .card {{
    background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.1rem;
    display: flex; flex-direction: column; gap: 0.5rem; position: relative;
  }}
  .card .top {{ display: flex; gap: 0.5rem; align-items: baseline; justify-content: space-between; }}
  .card .date {{ font-family: 'DM Mono', monospace; font-size: 0.78rem; color: var(--terra); }}
  .card .val {{ font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: var(--coffee); white-space: nowrap; }}
  .card .val.neg {{ color: #993311; }}
  .card .fav {{ font-weight: 500; font-size: 1rem; color: var(--coffee); }}
  .card .meta {{ display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.8rem; color: var(--terra); margin-top: 0.15rem; }}
  .card .meta span {{ display: inline-flex; gap: 0.3rem; align-items: center; }}
  .card .desc {{ font-size: 0.86rem; color: rgba(26,14,8,0.78); margin-top: 0.25rem; }}
  .card .tag {{
    display: inline-block; font-family: 'DM Mono', monospace; font-size: 0.65rem;
    background: var(--cream); color: var(--coffee); padding: 0.18rem 0.55rem; border-radius: 999px;
    letter-spacing: 0.08em; text-transform: uppercase;
  }}

  .note {{
    background: var(--cream); border-left: 3px solid var(--gold);
    padding: 0.85rem 1rem; margin: 1rem 0; font-size: 0.9rem; border-radius: 0 8px 8px 0;
  }}
  .note strong {{ color: var(--coffee); }}

  .tabs {{ display: flex; gap: 0.3rem; margin: 1rem 0 0.5rem; flex-wrap: wrap; }}
  .tabs button {{
    font-family: 'DM Mono', monospace; font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
    padding: 0.5rem 1rem; border: 1px solid var(--line); border-radius: 999px;
    background: var(--paper); color: var(--terra); cursor: pointer;
  }}
  .tabs button.active {{ background: var(--coffee); color: var(--cream); border-color: var(--coffee); }}
  .tabs button:hover {{ border-color: var(--terra); }}

  .chips {{ display: flex; gap: 0.3rem; flex-wrap: wrap; margin: 0.5rem 0; }}
  .chip {{
    font-family: 'DM Mono', monospace; font-size: 0.72rem;
    padding: 0.35rem 0.75rem; border: 1px solid var(--line); border-radius: 999px;
    background: var(--paper); color: var(--terra); cursor: pointer;
  }}
  .chip.active {{ background: var(--clay); color: var(--cream); border-color: var(--clay); }}

  .empty {{ padding: 2rem; text-align: center; color: var(--terra); font-style: italic; }}

  /* --- FOOTER --- */
  footer.site-foot {{
    background: var(--coffee); color: var(--cream); margin-top: 5rem; padding: 2rem 1rem 2.5rem;
    border-top: 4px solid var(--gold);
  }}
  footer .wrap {{ max-width: 1180px; margin: 0 auto; }}
  footer .grid {{ display: grid; gap: 1.5rem; grid-template-columns: 1fr; }}
  @media (min-width: 720px) {{ footer .grid {{ grid-template-columns: 2fr 1fr 1fr; }} }}
  footer h3 {{ color: var(--gold); font-family: 'DM Mono', monospace; font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.6rem; }}
  footer p, footer li {{ font-size: 0.88rem; color: rgba(245,237,224,0.85); }}
  footer ul {{ list-style: none; padding: 0; margin: 0; }}
  footer ul li {{ margin-bottom: 0.4rem; }}
  footer a {{ color: var(--cream); text-decoration: underline; text-decoration-color: var(--clay); }}
  footer a:hover {{ color: var(--gold); }}
  footer .small {{ font-size: 0.75rem; color: rgba(245,237,224,0.6); margin-top: 1.5rem; border-top: 1px solid rgba(184,137,58,0.3); padding-top: 1rem; }}
</style>
</head>
<body>

<header class="site-head">
  <div class="wrap">
    <div class="brasao" aria-hidden="true">M</div>
    <div>
      <h1>Muzambinho Transparente</h1>
      <span class="sub">Prefeitura Municipal · MG · Exercício {periodo}</span>
    </div>
    <span class="demo" title="Este portal não é gerido pela Prefeitura. Os dados são extraídos do PortalTP oficial.">Projeto independente</span>
  </div>
</header>

<div class="stats" role="region" aria-label="Indicadores principais">
  <div class="wrap">
    <div class="stat">
      <span class="label">Empenhado</span>
      <div class="v">{kpi_empenhado}</div>
      <div class="desc">{kpi_qtd_empenhos} empenhos a {kpi_qtd_credores} credores</div>
    </div>
    <div class="stat">
      <span class="label">Folha base</span>
      <div class="v">{kpi_folha}</div>
      <div class="desc">{kpi_qtd_servidores_ativos} ativos de {kpi_qtd_servidores_total} cadastrados</div>
    </div>
    <div class="stat">
      <span class="label">Diárias</span>
      <div class="v">{kpi_diarias}</div>
      <div class="desc">{kpi_qtd_diarias} concedidas no exercício</div>
    </div>
    <div class="stat">
      <span class="label">Contratos</span>
      <div class="v">{kpi_contratos}</div>
      <div class="desc">{kpi_qtd_contratos} contratos · {kpi_qtd_licitacoes} licitações</div>
    </div>
  </div>
</div>

<section class="intro tight">
  <span class="label">Como ler este portal</span>
  <p>Para onde vai o dinheiro público de Muzambinho? Este portal organiza, em uma única página, os dados que a Prefeitura já publica de forma fragmentada no PortalTP oficial — empenhos, credores, servidores, diárias e contratos do exercício de 2026. Cada número aqui pode ser conferido na fonte original. Os dados são atualizados periodicamente; veja o rodapé para a data da última coleta.</p>
</section>

<section>
  <h2>Top 50 credores</h2>
  <p class="lead">Fornecedores e beneficiários ordenados pelo valor líquido empenhado no ano (empenhos brutos menos anulações). Inclui pessoas jurídicas, físicas e rubricas internas como "Folha de Pagamento".</p>
  <div class="toolbar">
    <input id="credSearch" type="search" placeholder="Buscar por nome ou CNPJ..." aria-label="Buscar credor">
    <select id="credSort" aria-label="Ordenar credores">
      <option value="valor">Maior valor líquido</option>
      <option value="bruto">Maior valor bruto</option>
      <option value="empenhos">Mais empenhos</option>
      <option value="nome">Nome (A-Z)</option>
    </select>
    <span class="count" id="credCount"></span>
  </div>
  <div style="overflow-x:auto;">
    <table class="t" id="credTable">
      <thead>
        <tr>
          <th class="r">#</th>
          <th>Favorecido</th>
          <th class="opt">CNPJ / CPF</th>
          <th class="r opt">Empenhos</th>
          <th class="r">Valor líquido</th>
          <th class="opt"></th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</section>

<section>
  <h2>Top 50 empenhos individuais</h2>
  <p class="lead">As maiores despesas empenhadas em 2026, com filtro por área de governo (função). Empenhos com valor negativo são anulações e foram excluídos desta lista.</p>
  <div class="chips" id="empChips"></div>
  <div class="toolbar">
    <input id="empSearch" type="search" placeholder="Buscar por favorecido, número ou descrição..." aria-label="Buscar empenho">
    <span class="count" id="empCount"></span>
  </div>
  <div class="cards" id="empCards"></div>
</section>

<section>
  <h2>Servidores (top 20)</h2>
  <p class="lead">Os 20 maiores salários base de referência registrados na folha. Use a busca para encontrar um servidor específico.</p>
  <div class="note">
    <strong>O que estes valores significam?</strong> O PortalTP de Muzambinho expõe o <em>valor do nível salarial</em> do cargo de cada servidor — o salário base de referência, sem incluir adicionais (horas extras, gratificações, insalubridade) e antes dos descontos. <strong>Não é a remuneração líquida em folha.</strong> CPFs vêm parcialmente mascarados pela LGPD; a Matrícula é a chave única.
  </div>
  <div class="toolbar">
    <input id="srvSearch" type="search" placeholder="Buscar por nome, cargo ou lotação..." aria-label="Buscar servidor">
    <span class="count" id="srvCount"></span>
  </div>
  <div class="cards" id="srvCards"></div>
</section>

<section>
  <h2>Diárias de viagem</h2>
  <p class="lead">Diárias concedidas a servidores em deslocamentos. Em Muzambinho, parte destes registros são <em>devoluções</em> (valores negativos) de adiantamentos não usados — não são novas despesas.</p>
  <div class="cards" id="diaCards"></div>
</section>

<section>
  <h2>Licitações &amp; contratos</h2>
  <p class="lead">Processos licitatórios abertos no ano e contratos vigentes assinados pela Prefeitura.</p>
  <div class="tabs">
    <button id="tabLic" class="active" onclick="switchLicTab('lic')">Licitações</button>
    <button id="tabCon" onclick="switchLicTab('con')">Contratos</button>
  </div>
  <div class="toolbar">
    <input id="licSearch" type="search" placeholder="Buscar por objeto, fornecedor ou número..." aria-label="Buscar">
    <span class="count" id="licCount"></span>
  </div>
  <div class="cards" id="licCards"></div>
</section>

<footer class="site-foot">
  <div class="wrap">
    <div class="grid">
      <div>
        <h3>Sobre</h3>
        <p>Muzambinho Transparente é um projeto independente de jornalismo cívico. Não é gerido pela Prefeitura Municipal. Os dados aqui apresentados são extraídos do Portal da Transparência oficial e organizados para leitura rápida.</p>
        <p>Você pode auditar cada valor verificando-o diretamente no portal oficial. Se encontrar uma divergência, abra uma <em>issue</em> no repositório.</p>
      </div>
      <div>
        <h3>Fontes oficiais</h3>
        <ul>
          <li><a href="https://muzambinho-mg.portaltp.com.br/" target="_blank" rel="noopener">PortalTP Muzambinho</a></li>
          <li><a href="https://www.muzambinho.mg.gov.br/transparencia" target="_blank" rel="noopener">Site da Prefeitura</a></li>
          <li><a href="https://transparenciafacil.com.br/despesas/0184601" target="_blank" rel="noopener">TransparênciaFácil</a></li>
        </ul>
      </div>
      <div>
        <h3>Cobertura</h3>
        <ul>
          <li>Período: {periodo}</li>
          <li>Última coleta: {data_geracao}</li>
          <li>Categorias: empenhos, credores, servidores, diárias, licitações, contratos</li>
        </ul>
      </div>
    </div>
    <p class="small">Dados públicos extraídos do portal oficial via scraping (Python + Playwright). Código-fonte e CSVs brutos disponíveis no repositório. Última geração: {data_geracao}.</p>
  </div>
</footer>

<script>
const CREDORES_DATA   = {json_credores};
const EMPENHOS_DATA   = {json_empenhos};
const SERVIDORES_DATA = {json_servidores};
const DIARIAS_DATA    = {json_diarias};
const LICITACOES_DATA = {json_licitacoes};
const KPIS_DATA       = {json_kpis};

const MAX_VAL_CREDOR  = KPIS_DATA.max_credor || 1;
const MAX_VAL_EMPENHO = KPIS_DATA.max_empenho || 1;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));
const escapeHTML = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));

// ===== CREDORES =====
function renderCredores() {{
  const q = $('#credSearch').value.trim().toLowerCase();
  const sort = $('#credSort').value;
  let rows = CREDORES_DATA.slice();
  if (q) rows = rows.filter(c => (c.favorecido + ' ' + c.cnpj).toLowerCase().includes(q));
  if (sort === 'valor')    rows.sort((a, b) => b.valor_num - a.valor_num);
  if (sort === 'bruto')    rows.sort((a, b) => b.valor_bruto_num - a.valor_bruto_num);
  if (sort === 'empenhos') rows.sort((a, b) => b.empenhos - a.empenhos);
  if (sort === 'nome')     rows.sort((a, b) => a.favorecido.localeCompare(b.favorecido, 'pt-BR'));
  const html = rows.map((c, i) => {{
    const pct = Math.max(0.5, (c.valor_num / MAX_VAL_CREDOR) * 100);
    return `<tr>
      <td class="rank">${{i + 1}}</td>
      <td class="fav">${{escapeHTML(c.favorecido)}}</td>
      <td class="opt mono">${{escapeHTML(c.cnpj || '—')}}</td>
      <td class="r opt num">${{c.empenhos}}</td>
      <td class="r num">${{escapeHTML(c.valor)}}</td>
      <td class="opt bar-cell"><div class="bar"><i style="width:${{pct.toFixed(1)}}%"></i></div></td>
    </tr>`;
  }}).join('');
  $('#credTable tbody').innerHTML = html || '<tr><td colspan="6" class="empty">Nenhum credor encontrado.</td></tr>';
  $('#credCount').textContent = rows.length + ' de ' + CREDORES_DATA.length;
}}

// ===== EMPENHOS =====
let empFiltroFuncao = null;
function renderEmpenhos() {{
  const q = $('#empSearch').value.trim().toLowerCase();
  let rows = EMPENHOS_DATA.slice();
  if (empFiltroFuncao) rows = rows.filter(e => e.funcao === empFiltroFuncao);
  if (q) rows = rows.filter(e => (e.favorecido + ' ' + e.empenho + ' ' + e.historico + ' ' + e.elemento).toLowerCase().includes(q));
  const html = rows.map(e => `
    <div class="card">
      <div class="top">
        <span class="date">${{escapeHTML(e.data)}}  ·  emp. ${{escapeHTML(e.empenho)}}</span>
        <span class="val">${{escapeHTML(e.valor)}}</span>
      </div>
      <div class="fav">${{escapeHTML(e.favorecido)}}</div>
      <div class="meta">
        ${{e.funcao ? `<span>${{escapeHTML(e.funcao)}}</span>` : ''}}
        ${{e.elemento ? `<span>${{escapeHTML(e.elemento)}}</span>` : ''}}
      </div>
      <div class="desc">${{escapeHTML(e.historico)}}</div>
      ${{e.fonte ? `<span class="tag">${{escapeHTML(e.fonte)}}</span>` : ''}}
    </div>`).join('');
  $('#empCards').innerHTML = html || '<div class="empty">Nenhum empenho encontrado.</div>';
  $('#empCount').textContent = rows.length + ' de ' + EMPENHOS_DATA.length;
}}

function renderEmpChips() {{
  const funcoes = [...new Set(EMPENHOS_DATA.map(e => e.funcao).filter(Boolean))].sort();
  $('#empChips').innerHTML = `<button class="chip ${{!empFiltroFuncao ? 'active' : ''}}" onclick="setEmpFuncao(null)">Todas (${{EMPENHOS_DATA.length}})</button>` +
    funcoes.map(f => `<button class="chip ${{empFiltroFuncao === f ? 'active' : ''}}" onclick="setEmpFuncao('${{f.replace(/'/g, "&#39;")}}')">${{escapeHTML(f)}}</button>`).join('');
}}
function setEmpFuncao(f) {{ empFiltroFuncao = f; renderEmpChips(); renderEmpenhos(); }}

// ===== SERVIDORES =====
function renderServidores() {{
  const q = $('#srvSearch').value.trim().toLowerCase();
  let rows = SERVIDORES_DATA.slice();
  if (q) rows = rows.filter(s => (s.nome + ' ' + s.cargo + ' ' + s.lotacao).toLowerCase().includes(q));
  const html = rows.map(s => `
    <div class="card">
      <div class="top">
        <span class="date">#${{s.rank}}  ·  mat. ${{escapeHTML(s.matricula)}}</span>
        <span class="val">${{escapeHTML(s.salario_base)}}</span>
      </div>
      <div class="fav">${{escapeHTML(s.nome)}}</div>
      <div class="meta">
        <span>${{escapeHTML(s.cargo)}}</span>
        <span>${{escapeHTML(s.vinculo)}}</span>
      </div>
      <div class="desc">${{escapeHTML(s.lotacao)}}</div>
      <span class="tag">${{escapeHTML(s.situacao)}}</span>
    </div>`).join('');
  $('#srvCards').innerHTML = html || '<div class="empty">Nenhum servidor encontrado.</div>';
  $('#srvCount').textContent = rows.length + ' de ' + SERVIDORES_DATA.length;
}}

// ===== DIÁRIAS =====
function renderDiarias() {{
  const html = DIARIAS_DATA.map(d => `
    <div class="card">
      <div class="top">
        <span class="date">${{escapeHTML(d.data)}}</span>
        <span class="val ${{d.valor_num < 0 ? 'neg' : ''}}">${{escapeHTML(d.valor)}}</span>
      </div>
      <div class="fav">${{escapeHTML(d.beneficiario)}}</div>
      <div class="meta">
        ${{d.cargo ? `<span>${{escapeHTML(d.cargo)}}</span>` : ''}}
        ${{d.matricula ? `<span>mat. ${{escapeHTML(d.matricula)}}</span>` : ''}}
      </div>
      <div class="desc">${{escapeHTML(d.motivo)}}</div>
    </div>`).join('');
  $('#diaCards').innerHTML = html || '<div class="empty">Nenhuma diária registrada no período.</div>';
}}

// ===== LICITAÇÕES / CONTRATOS =====
let licTab = 'lic';
function switchLicTab(t) {{
  licTab = t;
  $('#tabLic').classList.toggle('active', t === 'lic');
  $('#tabCon').classList.toggle('active', t === 'con');
  renderLicitacoes();
}}
function renderLicitacoes() {{
  const q = $('#licSearch').value.trim().toLowerCase();
  let html;
  if (licTab === 'lic') {{
    let rows = LICITACOES_DATA.licitacoes.slice();
    if (q) rows = rows.filter(l => (l.objeto + ' ' + l.numero + ' ' + l.modalidade).toLowerCase().includes(q));
    html = rows.map(l => `
      <div class="card">
        <div class="top">
          <span class="date">${{escapeHTML(l.data)}}  ·  nº ${{escapeHTML(l.numero)}}</span>
          <span class="val">${{escapeHTML(l.valor_final && l.valor_final_num > 0 ? l.valor_final : l.valor_estimado)}}</span>
        </div>
        <div class="fav">${{escapeHTML(l.modalidade)}}</div>
        <div class="desc">${{escapeHTML(l.objeto)}}</div>
        <div class="meta">
          <span>Proc. ${{escapeHTML(l.processo)}}</span>
          <span>${{escapeHTML(l.situacao)}}</span>
        </div>
      </div>`).join('');
    $('#licCount').textContent = rows.length + ' de ' + LICITACOES_DATA.licitacoes.length;
  }} else {{
    let rows = LICITACOES_DATA.contratos.slice();
    if (q) rows = rows.filter(c => (c.objeto + ' ' + c.contratado + ' ' + c.contrato).toLowerCase().includes(q));
    html = rows.map(c => `
      <div class="card">
        <div class="top">
          <span class="date">assinado ${{escapeHTML(c.assinatura)}}  ·  nº ${{escapeHTML(c.contrato)}}</span>
          <span class="val">${{escapeHTML(c.valor)}}</span>
        </div>
        <div class="fav">${{escapeHTML(c.contratado)}}</div>
        <div class="desc">${{escapeHTML(c.objeto)}}</div>
        <div class="meta">
          ${{c.cnpj ? `<span class="mono">${{escapeHTML(c.cnpj)}}</span>` : ''}}
          ${{c.categoria ? `<span>${{escapeHTML(c.categoria)}}</span>` : ''}}
          <span>${{escapeHTML(c.situacao)}}</span>
        </div>
      </div>`).join('');
    $('#licCount').textContent = rows.length + ' de ' + LICITACOES_DATA.contratos.length;
  }}
  $('#licCards').innerHTML = html || '<div class="empty">Nada encontrado.</div>';
}}

// ===== INIT =====
$('#credSearch').addEventListener('input', renderCredores);
$('#credSort').addEventListener('change', renderCredores);
$('#empSearch').addEventListener('input', renderEmpenhos);
$('#srvSearch').addEventListener('input', renderServidores);
$('#licSearch').addEventListener('input', renderLicitacoes);

renderCredores();
renderEmpChips();
renderEmpenhos();
renderServidores();
renderDiarias();
renderLicitacoes();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
