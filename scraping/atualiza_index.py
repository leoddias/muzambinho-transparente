"""Monta o index.html final embutindo os JSONs de data/site/*.json.

Princípios:
  - Embute TODOS os dados (não trunca). O portal mostra o dataset completo.
  - Paginação client-side (batch de 100) evita renderizar milhares de DOM nodes.
  - Busca/sort/filtros operam no dataset inteiro, não só no batch visível.
  - Idempotente: roda quantas vezes quiser após o pipeline.
"""
from __future__ import annotations
import base64
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = DATA / "site"
ASSETS = ROOT / "assets"
OUT = ROOT / "index.html"

MESES_PT = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def carrega(nome: str):
    return json.load((SITE / f"{nome}.json").open(encoding="utf-8"))


def img_data_uri(path: Path, mime: str = "image/png") -> str:
    """PNG/JPG -> data URI base64 para embutir inline no HTML.

    Mantém o portal autocontido (abre offline). Use para brasão, ícones pequenos.
    """
    if not path.exists():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


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
    if v >= 1_000_000:
        return f"R$ {f'{v/1_000_000:.2f}'.replace('.', ',')}M"
    if v >= 1_000:
        return f"R$ {f'{v/1_000:.1f}'.replace('.', ',')}K"
    return fmt_brl(v)


def main() -> None:
    credores = carrega("credores")
    empenhos = carrega("empenhos")
    servidores = carrega("servidores")
    diarias = carrega("diarias")
    licitacoes = carrega("licitacoes")
    kpis = carrega("kpis")
    radar = carrega("radar")

    hoje = date.today()
    data_geracao = f"{hoje.day} de {MESES_PT[hoje.month]} de {hoje.year}"
    periodo = f"01/01/2026 a {hoje.strftime('%d/%m/%Y')}"

    def js(o) -> str:
        return json.dumps(o, ensure_ascii=False, separators=(",", ":"))

    brasao_uri = img_data_uri(ASSETS / "brasao.png")

    qtd_compras = (kpis.get("qtd_licitacoes", 0) + kpis.get("qtd_dispensas", 0)
                   + kpis.get("qtd_contratos", 0) + kpis.get("qtd_atas", 0))

    html = HTML_TEMPLATE.format(
        data_geracao=data_geracao,
        periodo=periodo,
        brasao_uri=brasao_uri,
        kpi_empenhado=fmt_brl_compacto(kpis["total_empenhado"]),
        kpi_qtd_empenhos=f"{kpis['total_empenhos']:,}".replace(",", "."),
        kpi_qtd_credores=kpis["total_credores"],
        kpi_folha=fmt_brl_compacto(kpis["folha_base_mensal"]),
        kpi_qtd_servidores_ativos=kpis["servidores_ativos"],
        kpi_qtd_servidores_total=kpis["total_servidores"],
        kpi_diarias=fmt_brl_compacto(kpis["total_diarias"]),
        kpi_qtd_diarias=kpis["qtd_diarias"],
        kpi_contratos=fmt_brl_compacto(kpis["total_contratos"]),
        kpi_qtd_contratos=kpis["qtd_contratos"],
        kpi_qtd_licitacoes=kpis["qtd_licitacoes"],
        kpi_qtd_dispensas=kpis.get("qtd_dispensas", 0),
        kpi_qtd_atas=kpis.get("qtd_atas", 0),
        kpi_qtd_compras=qtd_compras,
        json_credores=js(credores),
        json_empenhos=js(empenhos),
        json_servidores=js(servidores),
        json_diarias=js(diarias),
        json_licitacoes=js(licitacoes),
        json_kpis=js(kpis),
        json_radar=js(radar),
        qtd_radar=len(radar),
    )

    OUT.write_text(html, encoding="utf-8")
    print(f"  Gerado: {OUT.name} ({OUT.stat().st_size:,} bytes / {OUT.stat().st_size/1024/1024:.2f} MB)")


# ----------------------------------------------------------------------
# HTML TEMPLATE
# ----------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Muzambinho Transparente · Gastos Públicos 2026</title>
<meta name="description" content="Portal não oficial de transparência da Prefeitura de Muzambinho/MG — todos os empenhos, credores, servidores, diárias e licitações.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,500&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    /* Dark warm "coffee" palette - calmo, sem flashbang, identidade café */
    --bg:        #1A100A;   /* fundo base, café muito escuro warm */
    --surface:   #221610;   /* cards, tabelas */
    --surface-2: #2C1D14;   /* hover, header de tabela, stats bar */
    --header-bg: #0E0805;   /* header/footer, ainda mais escuro */

    --ink:       #F0E6D6;   /* texto principal warm cream */
    --ink-soft:  rgba(240,230,214,0.78);
    --ink-mute:  rgba(240,230,214,0.55);

    --gold:   #D4A968;      /* accent dourado, luminoso o suficiente em dark */
    --clay:   #E59568;      /* laranja terracota */
    --moss:   #94B576;      /* verde musgo claro */
    --danger: #E07A52;      /* anulações / negativo */

    --line:   rgba(240,230,214,0.10);
    --shade:  rgba(240,230,214,0.04);
    --bar-bg: rgba(212,169,104,0.15);
    --bar-fg: linear-gradient(90deg, var(--clay), var(--gold));

    /* aliases legados (alguns lugares no template ainda usam estes nomes) */
    --coffee: var(--header-bg);
    --terra:  var(--gold);
    --cream:  var(--surface-2);
    --paper:  var(--bg);
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    font-family: 'DM Sans', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    color: var(--ink); background: var(--bg); line-height: 1.55; font-size: 16px;
    -webkit-font-smoothing: antialiased;
  }}
  /* Texture sutil warm sobre o fundo escuro (não branca!) */
  body::before {{
    content: ""; position: fixed; inset: 0;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.94 0 0 0 0 0.90 0 0 0 0 0.84 0 0 0 0.025 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
    pointer-events: none; z-index: 0;
  }}
  main, header, footer, section {{ position: relative; z-index: 1; }}

  a {{ color: var(--gold); text-decoration: underline; text-underline-offset: 3px; text-decoration-thickness: 1px; }}
  a:hover {{ color: var(--clay); }}

  h1, h2, h3, h4 {{ font-family: 'Playfair Display', Georgia, serif; font-weight: 700; line-height: 1.15; color: var(--ink); margin: 0; }}
  h1 {{ font-size: clamp(1.8rem, 4.5vw, 3.2rem); letter-spacing: -0.02em; }}
  h2 {{ font-size: clamp(1.4rem, 3vw, 2.2rem); letter-spacing: -0.01em; margin-bottom: 0.5em; }}
  h3 {{ font-size: 1.15rem; }}

  .mono {{ font-family: 'DM Mono', ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .label {{ font-family: 'DM Mono', monospace; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--gold); }}
  .num   {{ font-family: 'DM Mono', monospace; font-variant-numeric: tabular-nums; }}

  /* HEADER */
  header.site-head {{
    background: var(--header-bg); color: var(--ink);
    padding: 1.25rem 1rem 1.5rem; border-bottom: 3px solid var(--gold);
  }}
  header.site-head .wrap {{ max-width: 1180px; margin: 0 auto; display: flex; gap: 1.25rem; align-items: center; }}
  .brasao {{
    width: 64px; height: 64px; border-radius: 50%;
    background: #F0E6D6;  /* cream claro pra contraste com brasão colorido */
    flex-shrink: 0; display: grid; place-items: center;
    border: 2px solid var(--gold); padding: 4px;
  }}
  .brasao img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
  .brasao.placeholder {{
    background: radial-gradient(circle at 35% 30%, var(--gold), var(--clay) 70%);
    color: var(--header-bg); font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.5rem;
    box-shadow: inset 0 0 0 4px rgba(14,8,5,0.15);
  }}
  header.site-head h1 {{ color: var(--ink); font-size: clamp(1.4rem, 3.5vw, 2.3rem); margin: 0; }}
  header.site-head .sub {{ display: block; font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); margin-top: 0.3rem; }}
  header.site-head .demo {{
    margin-left: auto; font-family: 'DM Mono', monospace; font-size: 0.65rem; padding: 0.35rem 0.7rem;
    border: 1px solid var(--gold); border-radius: 999px; color: var(--gold); letter-spacing: 0.1em; text-transform: uppercase;
    flex-shrink: 0;
  }}

  /* INTRO */
  .intro {{
    max-width: 880px; margin: 2.5rem auto 1rem; padding: 0 1rem;
    display: flex; gap: 1.5rem; align-items: flex-start;
  }}
  .intro p {{ font-size: 1.1rem; margin: 0; }}
  .intro .label {{ display: block; margin-bottom: 0.6rem; }}
  .intro .brasao-big {{
    width: 110px; height: 110px; flex-shrink: 0;
    object-fit: contain; display: block;
    margin-top: 0.4rem;
  }}
  .intro .txt {{ min-width: 0; }}
  @media (max-width: 560px) {{
    .intro {{ flex-direction: column; align-items: center; text-align: left; gap: 1rem; }}
    .intro .brasao-big {{ width: 84px; height: 84px; }}
  }}

  /* STATS */
  .stats {{
    background: var(--surface-2); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
  }}
  .stats .wrap {{ max-width: 1180px; margin: 0 auto; padding: 0.9rem 1rem; display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem 1.5rem; }}
  @media (min-width: 768px) {{ .stats .wrap {{ grid-template-columns: repeat(4, 1fr); }} }}
  .stat .label {{ display: block; }}
  .stat .v {{ font-family: 'Playfair Display', serif; font-size: clamp(1.15rem, 3vw, 1.7rem); font-weight: 700; color: var(--ink); line-height: 1.1; }}
  .stat .desc {{ font-size: 0.78rem; color: var(--ink-mute); margin-top: 0.15rem; }}

  /* NAV (sticky) */
  nav.site-nav {{
    background: var(--header-bg); color: var(--ink);
    position: sticky; top: 0; z-index: 60;
    border-bottom: 2px solid var(--gold);
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  }}
  nav.site-nav .wrap {{
    max-width: 1180px; margin: 0 auto; padding: 0 1rem;
    display: flex; gap: 0.25rem; align-items: center;
    overflow-x: auto; scrollbar-width: thin; scrollbar-color: var(--gold) transparent;
  }}
  nav.site-nav .wrap::-webkit-scrollbar {{ height: 4px; }}
  nav.site-nav .wrap::-webkit-scrollbar-thumb {{ background: var(--gold); border-radius: 4px; }}
  nav.site-nav a {{
    flex-shrink: 0; text-decoration: none; color: var(--ink-soft);
    padding: 0.85rem 1.1rem; font-family: 'DM Mono', monospace;
    font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
    border-bottom: 3px solid transparent; margin-bottom: -2px; transition: all 0.15s;
    white-space: nowrap;
  }}
  nav.site-nav a:hover {{ color: var(--gold); border-bottom-color: rgba(212,169,104,0.4); }}
  nav.site-nav a.active {{ color: var(--gold); border-bottom-color: var(--gold); }}
  nav.site-nav a .n {{ font-size: 0.65rem; opacity: 0.7; margin-left: 0.4rem; }}

  /* Scroll-offset para anchors com nav sticky */
  section[id] {{ scroll-margin-top: 60px; }}

  /* SECTIONS */
  section {{ max-width: 1180px; margin: 0 auto; padding: 3.5rem 1rem 1rem; }}
  section.tight {{ padding-top: 2rem; }}
  section .lead {{ max-width: 720px; color: var(--ink-soft); margin-top: 0.4rem; font-size: 1.02rem; }}

  /* TOOLBAR */
  .toolbar {{ display: flex; gap: 0.6rem; flex-wrap: wrap; align-items: center; margin: 1.25rem 0 0.75rem; }}
  .toolbar input, .toolbar select {{
    font-family: 'DM Sans', sans-serif; font-size: 0.95rem;
    padding: 0.55rem 0.85rem; border: 1px solid var(--line); border-radius: 8px;
    background: var(--surface); color: var(--ink); min-width: 0;
  }}
  .toolbar input::placeholder {{ color: var(--ink-mute); }}
  .toolbar input:focus, .toolbar select:focus {{ outline: 2px solid var(--gold); outline-offset: 1px; border-color: var(--gold); }}
  .toolbar input[type=search] {{ flex: 1; min-width: 180px; max-width: 360px; }}
  .toolbar select {{ background: var(--surface-2); }}
  .toolbar .count {{ font-family: 'DM Mono', monospace; font-size: 0.78rem; color: var(--ink-mute); margin-left: auto; }}
  .toolbar label.check {{ display: flex; gap: 0.4rem; align-items: center; font-size: 0.85rem; color: var(--ink-soft); cursor: pointer; }}
  .toolbar label.check input {{ accent-color: var(--gold); }}

  /* CHIPS */
  .chips {{ display: flex; gap: 0.3rem; flex-wrap: wrap; margin: 0.5rem 0; }}
  .chip {{
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.04em;
    padding: 0.35rem 0.75rem; border: 1px solid var(--line); border-radius: 999px;
    background: var(--surface); color: var(--ink-soft); cursor: pointer; transition: all 0.15s;
  }}
  .chip:hover {{ border-color: var(--gold); color: var(--ink); }}
  .chip.active {{ background: var(--gold); color: var(--header-bg); border-color: var(--gold); font-weight: 500; }}
  .chips-group {{ display: flex; gap: 0.5rem; flex-direction: column; margin: 0.5rem 0; }}
  .chips-group .row-label {{ font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-mute); }}

  /* TABLE */
  table.t {{
    width: 100%; border-collapse: collapse; font-size: 0.92rem;
    background: var(--surface); border: 1px solid var(--line); border-radius: 10px; overflow: hidden;
  }}
  table.t thead th {{
    text-align: left; padding: 0.7rem 0.9rem; background: var(--surface-2);
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--gold); font-weight: 500; border-bottom: 1px solid var(--line);
  }}
  table.t tbody td {{ padding: 0.65rem 0.9rem; border-top: 1px solid var(--shade); vertical-align: middle; color: var(--ink); }}
  table.t tbody tr:hover {{ background: var(--surface-2); }}
  table.t td.r, table.t th.r {{ text-align: right; font-variant-numeric: tabular-nums; }}
  table.t td.num {{ font-family: 'DM Mono', monospace; }}
  table.t td.rank {{ font-family: 'DM Mono', monospace; color: var(--ink-mute); width: 2.5rem; text-align: right; }}
  table.t td.fav {{ font-weight: 500; color: var(--ink); }}
  table.t td.bar-cell {{ width: 28%; padding-right: 1.5rem; }}
  .bar {{ position: relative; height: 10px; border-radius: 999px; background: var(--bar-bg); overflow: hidden; min-width: 60px; }}
  .bar > i {{ position: absolute; top: 0; bottom: 0; left: 0; background: var(--bar-fg); border-radius: 999px; min-width: 4px; }}
  @media (max-width: 768px) {{
    table.t th.opt, table.t td.opt {{ display: none; }}
    table.t {{ font-size: 0.85rem; }}
    table.t thead th, table.t tbody td {{ padding: 0.55rem 0.6rem; }}
  }}

  /* RADAR DE GASTOS - cards de anomalia */
  .radar-intro {{ display: flex; align-items: baseline; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.4rem; }}
  .radar-intro h2 {{ margin: 0; }}
  .radar-intro .badge {{
    font-family: 'DM Mono', monospace; font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase;
    padding: 0.25rem 0.6rem; border-radius: 999px;
    background: rgba(224,122,82,0.12); color: var(--danger); border: 1px solid rgba(224,122,82,0.3);
  }}
  .radar-grid {{
    display: grid; gap: 0.85rem; grid-template-columns: 1fr;
    margin-top: 1.25rem;
  }}
  @media (min-width: 720px) {{ .radar-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  @media (min-width: 1080px) {{ .radar-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
  .radar-card {{
    background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--ink-mute);
    border-radius: 8px; padding: 1rem 1.1rem; display: flex; flex-direction: column; gap: 0.45rem;
    text-decoration: none; color: inherit; transition: all 0.15s;
  }}
  .radar-card:hover {{ border-color: var(--gold); transform: translateY(-1px); }}
  .radar-card.sev-alta   {{ border-left-color: var(--danger); }}
  .radar-card.sev-media  {{ border-left-color: var(--clay); }}
  .radar-card.sev-baixa  {{ border-left-color: var(--gold); }}
  .radar-card.sev-info   {{ border-left-color: var(--moss); }}
  .radar-card .head {{ display: flex; align-items: baseline; gap: 0.5rem; justify-content: space-between; }}
  .radar-card .icon {{ font-size: 1.4rem; line-height: 1; }}
  .radar-card .sev {{
    font-family: 'DM Mono', monospace; font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase;
    padding: 0.15rem 0.5rem; border-radius: 999px; background: var(--surface-2); color: var(--ink-mute);
  }}
  .radar-card.sev-alta .sev  {{ color: var(--danger); background: rgba(224,122,82,0.12); }}
  .radar-card.sev-media .sev {{ color: var(--clay); background: rgba(229,149,104,0.12); }}
  .radar-card.sev-info .sev  {{ color: var(--moss); background: rgba(148,181,118,0.12); }}
  .radar-card .titulo {{
    font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: var(--ink); line-height: 1.25;
  }}
  .radar-card .desc {{ font-size: 0.86rem; color: var(--ink-soft); line-height: 1.5; }}
  .radar-card .cta {{
    margin-top: auto; font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--gold); padding-top: 0.4rem;
  }}

  /* CARDS */
  .cards {{ display: grid; gap: 0.85rem; grid-template-columns: 1fr; margin-top: 1rem; }}
  @media (min-width: 720px) {{ .cards {{ grid-template-columns: repeat(2, 1fr); }} }}
  @media (min-width: 1024px) {{ .cards {{ grid-template-columns: repeat(3, 1fr); }} }}
  .card {{
    background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.1rem;
    display: flex; flex-direction: column; gap: 0.5rem; position: relative;
    transition: border-color 0.15s, transform 0.15s;
  }}
  .card:hover {{ border-color: rgba(212,169,104,0.4); }}
  .card .top {{ display: flex; gap: 0.5rem; align-items: baseline; justify-content: space-between; }}
  .card .date {{ font-family: 'DM Mono', monospace; font-size: 0.78rem; color: var(--ink-mute); }}
  .card .val {{ font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: var(--gold); white-space: nowrap; }}
  .card .val.neg {{ color: var(--danger); }}
  .card .fav {{ font-weight: 500; font-size: 1rem; color: var(--ink); }}
  .card .meta {{ display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.8rem; color: var(--ink-mute); margin-top: 0.15rem; }}
  .card .meta span {{ display: inline-flex; gap: 0.3rem; align-items: center; }}
  .card .desc {{ font-size: 0.86rem; color: var(--ink-soft); margin-top: 0.25rem; }}
  .card .tag {{
    display: inline-block; font-family: 'DM Mono', monospace; font-size: 0.65rem;
    background: var(--surface-2); color: var(--ink-soft); padding: 0.18rem 0.55rem; border-radius: 999px;
    letter-spacing: 0.08em; text-transform: uppercase;
    border: 1px solid var(--line);
  }}
  .card .tag.warn {{ background: rgba(224,122,82,0.15); color: var(--danger); border-color: rgba(224,122,82,0.3); }}
  .card .tag.ok   {{ background: rgba(148,181,118,0.15); color: var(--moss); border-color: rgba(148,181,118,0.3); }}

  .note {{
    background: var(--surface); border-left: 3px solid var(--gold);
    padding: 0.85rem 1rem; margin: 1rem 0; font-size: 0.9rem; border-radius: 0 8px 8px 0;
    color: var(--ink-soft);
  }}
  .note strong {{ color: var(--gold); }}

  .tabs {{ display: flex; gap: 0.3rem; margin: 1rem 0 0.5rem; flex-wrap: wrap; }}
  .tabs button {{
    font-family: 'DM Mono', monospace; font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
    padding: 0.5rem 1rem; border: 1px solid var(--line); border-radius: 999px;
    background: var(--surface); color: var(--ink-soft); cursor: pointer;
  }}
  .tabs button.active {{ background: var(--gold); color: var(--header-bg); border-color: var(--gold); }}
  .tabs button:hover {{ border-color: var(--gold); color: var(--ink); }}

  .more-btn {{
    display: block; margin: 1.5rem auto 0;
    padding: 0.7rem 1.5rem; font-family: 'DM Mono', monospace; font-size: 0.8rem; letter-spacing: 0.1em; text-transform: uppercase;
    background: var(--surface-2); color: var(--gold); border: 1px solid var(--gold); border-radius: 999px; cursor: pointer;
    transition: all 0.15s;
  }}
  .more-btn:hover {{ background: var(--gold); color: var(--header-bg); }}
  .more-btn:disabled {{ background: var(--surface); color: var(--ink-mute); border-color: var(--line); cursor: not-allowed; }}

  .empty {{ padding: 2rem; text-align: center; color: var(--ink-mute); font-style: italic; }}

  /* FOOTER */
  footer.site-foot {{
    background: var(--header-bg); color: var(--ink); margin-top: 5rem; padding: 2.5rem 1rem;
    border-top: 3px solid var(--gold);
  }}
  footer .wrap {{ max-width: 1180px; margin: 0 auto; }}
  footer .grid {{ display: grid; gap: 1.5rem; grid-template-columns: 1fr; }}
  @media (min-width: 720px) {{ footer .grid {{ grid-template-columns: 2fr 1fr 1fr; }} }}
  footer h3 {{ color: var(--gold); font-family: 'DM Mono', monospace; font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.6rem; }}
  footer p, footer li {{ font-size: 0.88rem; color: var(--ink-soft); }}
  footer ul {{ list-style: none; padding: 0; margin: 0; }}
  footer ul li {{ margin-bottom: 0.4rem; }}
  footer a {{ color: var(--ink); text-decoration: underline; text-decoration-color: var(--gold); }}
  footer a:hover {{ color: var(--gold); }}
  footer .small {{ font-size: 0.75rem; color: var(--ink-mute); margin-top: 1.5rem; border-top: 1px solid rgba(212,169,104,0.2); padding-top: 1rem; }}
</style>
</head>
<body>

<header class="site-head">
  <div class="wrap">
    <div class="brasao" aria-hidden="true"><img src="{brasao_uri}" alt="Brasão de Muzambinho"></div>
    <div>
      <h1>Muzambinho Transparente</h1>
      <span class="sub">Prefeitura Municipal · MG · Exercício {periodo}</span>
    </div>
    <span class="demo" title="Este portal não é gerido pela Prefeitura. Os dados são extraídos do PortalTP oficial.">Projeto independente</span>
  </div>
</header>

<div class="stats" role="region" aria-label="Indicadores principais">
  <div class="wrap">
    <div class="stat"><span class="label">Empenhado</span><div class="v">{kpi_empenhado}</div><div class="desc">{kpi_qtd_empenhos} empenhos a {kpi_qtd_credores} credores</div></div>
    <div class="stat"><span class="label">Folha base</span><div class="v">{kpi_folha}</div><div class="desc">{kpi_qtd_servidores_ativos} ativos de {kpi_qtd_servidores_total} cadastrados</div></div>
    <div class="stat"><span class="label">Diárias</span><div class="v">{kpi_diarias}</div><div class="desc">{kpi_qtd_diarias} concedidas no exercício</div></div>
    <div class="stat"><span class="label">Contratos</span><div class="v">{kpi_contratos}</div><div class="desc">{kpi_qtd_contratos} contratos · {kpi_qtd_licitacoes} licitações</div></div>
  </div>
</div>

<nav class="site-nav" aria-label="Navegação entre seções">
  <div class="wrap">
    <a href="#radar">Radar <span class="n">{qtd_radar}</span></a>
    <a href="#credores">Credores <span class="n">{kpi_qtd_credores}</span></a>
    <a href="#empenhos">Empenhos <span class="n">{kpi_qtd_empenhos}</span></a>
    <a href="#servidores">Servidores <span class="n">{kpi_qtd_servidores_total}</span></a>
    <a href="#diarias">Diárias <span class="n">{kpi_qtd_diarias}</span></a>
    <a href="#licitacoes">Compras <span class="n">{kpi_qtd_compras}</span></a>
  </div>
</nav>

<section class="intro tight">
  <img src="{brasao_uri}" alt="" class="brasao-big" aria-hidden="true">
  <div class="txt">
    <span class="label">Como ler este portal</span>
    <p>Para onde vai o dinheiro público de Muzambinho? Este portal organiza, em uma única página, <strong>todos os dados</strong> que a Prefeitura já publica de forma fragmentada no PortalTP oficial — cada empenho, cada credor, cada servidor, cada diária, cada contrato do exercício de 2026. Nada está agregado, resumido ou filtrado; use as buscas e ordenações para explorar.</p>
  </div>
</section>

<section id="radar">
  <div class="radar-intro">
    <h2>Radar de gastos</h2>
    <span class="badge">O que os dados revelam</span>
  </div>
  <p class="lead">Concentrações, contratações sem licitação, anulações expressivas e outros pontos que <strong>chamaram atenção nos dados oficiais</strong>. Não são acusações de irregularidade — são pistas para investigação cidadã. Cada cartão é clicável e leva à seção com os dados detalhados.</p>
  <div class="radar-grid" id="radarGrid"></div>
</section>

<section id="credores">
  <h2>Credores e fornecedores</h2>
  <p class="lead">Todos os <span id="credTotal"></span> beneficiários que receberam ao menos um empenho em 2026, ordenados pelo valor líquido (bruto menos anulações).</p>
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
      <thead><tr>
        <th class="r">#</th>
        <th>Favorecido</th>
        <th class="opt">CNPJ / CPF</th>
        <th class="r opt">Empenhos</th>
        <th class="r">Valor líquido</th>
        <th class="opt"></th>
      </tr></thead>
      <tbody></tbody>
    </table>
  </div>
  <button id="credMore" class="more-btn">Mostrar mais</button>
</section>

<section id="empenhos">
  <h2>Empenhos</h2>
  <p class="lead">Cada despesa empenhada pela Prefeitura em 2026 — todas as <span id="empTotal"></span>, do maior R$ 993K (THV Saneamento) ao menor centavo. Use os filtros por área de governo (função) para investigar.</p>
  <div class="chips-group">
    <div class="row-label">Função</div>
    <div class="chips" id="empChips"></div>
  </div>
  <div class="toolbar">
    <input id="empSearch" type="search" placeholder="Buscar por favorecido, número, histórico..." aria-label="Buscar empenho">
    <select id="empSort" aria-label="Ordenar empenhos">
      <option value="valor_desc">Maior valor</option>
      <option value="data_desc">Mais recente</option>
      <option value="data_asc">Mais antigo</option>
      <option value="favorecido">Favorecido (A-Z)</option>
    </select>
    <label class="check"><input type="checkbox" id="empHideAnul" checked> ocultar anulações</label>
    <span class="count" id="empCount"></span>
  </div>
  <div class="cards" id="empCards"></div>
  <button id="empMore" class="more-btn">Mostrar mais</button>
</section>

<section id="servidores">
  <h2>Servidores</h2>
  <p class="lead">Todos os <span id="srvTotal"></span> servidores cadastrados na folha — efetivos, comissionados, contratados, ativos, em licença ou afastados.</p>
  <div class="note">
    <strong>O que estes valores significam?</strong> O PortalTP de Muzambinho expõe o <em>valor do nível salarial</em> do cargo — o salário base de referência, sem adicionais (horas extras, gratificações) e antes dos descontos. <strong>Não é a remuneração líquida em folha.</strong> CPFs vêm parcialmente mascarados pela LGPD; a Matrícula é a chave única. Servidores em licença sem vencimento aparecem com salário R$ 0,00.
  </div>
  <div class="chips-group">
    <div class="row-label">Situação</div>
    <div class="chips" id="srvSituacaoChips"></div>
    <div class="row-label">Vínculo</div>
    <div class="chips" id="srvVinculoChips"></div>
  </div>
  <div class="toolbar">
    <input id="srvSearch" type="search" placeholder="Buscar por nome, cargo, lotação, matrícula..." aria-label="Buscar servidor">
    <select id="srvLotacao" aria-label="Filtrar por lotação"><option value="">Toda lotação</option></select>
    <select id="srvSort" aria-label="Ordenar servidores">
      <option value="salario_desc">Maior salário base</option>
      <option value="salario_asc">Menor salário base</option>
      <option value="nome">Nome (A-Z)</option>
      <option value="cargo">Cargo (A-Z)</option>
      <option value="admissao_desc">Admissão mais recente</option>
      <option value="admissao_asc">Admissão mais antiga</option>
    </select>
    <span class="count" id="srvCount"></span>
  </div>
  <div class="cards" id="srvCards"></div>
  <button id="srvMore" class="more-btn">Mostrar mais</button>
</section>

<section id="diarias">
  <h2>Diárias e adiantamentos a servidores</h2>
  <p class="lead">Todos os <span id="diaTotal"></span> empenhos classificados como <em>diárias para pessoal civil</em> no orçamento (código 33901400000). Valores negativos são devoluções de adiantamentos não utilizados.</p>
  <div class="note">
    <strong>Por que esta fonte?</strong> O endpoint dedicado de diárias do PortalTP retorna apenas registros formalmente abertos sob a rubrica "Adiantamento de Diárias" (no caso de Muzambinho/2026, apenas 6). Para mostrar <strong>todas</strong> as diárias do exercício, cruzamos com o registro contábil oficial — todo empenho com elemento de despesa <code>33901400000 - Diárias - Pessoal Civil</code>.
  </div>
  <div class="toolbar">
    <input id="diaSearch" type="search" placeholder="Buscar por beneficiário, motivo, função..." aria-label="Buscar diária">
    <select id="diaSort" aria-label="Ordenar diárias">
      <option value="valor_desc">Maior valor (absoluto)</option>
      <option value="data_desc">Mais recente</option>
      <option value="data_asc">Mais antiga</option>
      <option value="beneficiario">Beneficiário (A-Z)</option>
    </select>
    <span class="count" id="diaCount"></span>
  </div>
  <div class="cards" id="diaCards"></div>
  <button id="diaMore" class="more-btn">Mostrar mais</button>
</section>

<section id="licitacoes">
  <h2>Compras e contratações</h2>
  <p class="lead">Todos os processos de contratação pública do ano — <span id="licTotalL"></span> licitações, <span id="licTotalD"></span> dispensas, <span id="licTotalC"></span> contratos vigentes e <span id="licTotalA"></span> atas de registro de preço.</p>
  <div class="note">
    <strong>Por que 4 categorias?</strong> No PortalTP, processos de compra ficam divididos em endpoints separados. <em>Licitações</em> são certames formais (pregão, concorrência). <em>Dispensas</em> são contratações sem licitação por baixo valor ou emergência (Lei 14.133/21). <em>Contratos</em> são acordos vigentes (podem vir de licitação ou dispensa). <em>Atas de registro de preço</em> são compromissos de fornecimento futuro com preços travados. Cada uma é um ângulo diferente das despesas com terceiros.
  </div>
  <div class="tabs">
    <button id="tabLic" class="active" onclick="switchLicTab('lic')">Licitações <span class="n" id="tabLicN"></span></button>
    <button id="tabDis" onclick="switchLicTab('dis')">Dispensas <span class="n" id="tabDisN"></span></button>
    <button id="tabCon" onclick="switchLicTab('con')">Contratos <span class="n" id="tabConN"></span></button>
    <button id="tabAta" onclick="switchLicTab('ata')">Atas RP <span class="n" id="tabAtaN"></span></button>
  </div>
  <div class="chips-group" id="licCatRow" style="display:none;">
    <div class="row-label">Categoria</div>
    <div class="chips" id="licCatChips"></div>
  </div>
  <div class="toolbar">
    <input id="licSearch" type="search" placeholder="Buscar por objeto, contratado, número..." aria-label="Buscar">
    <select id="licSort" aria-label="Ordenar">
      <option value="valor_desc">Maior valor</option>
      <option value="data_desc">Mais recente</option>
      <option value="data_asc">Mais antigo</option>
      <option value="contratado">A-Z</option>
    </select>
    <span class="count" id="licCount"></span>
  </div>
  <div class="cards" id="licCards"></div>
  <button id="licMore" class="more-btn">Mostrar mais</button>
</section>

<footer class="site-foot">
  <div class="wrap">
    <div class="grid">
      <div>
        <h3>Sobre</h3>
        <p>Muzambinho Transparente é um projeto independente de jornalismo cívico. Não é gerido pela Prefeitura Municipal. <strong>Todos os dados aqui são extraídos integralmente do Portal da Transparência oficial</strong> — nada é resumido, filtrado ou interpretado. Cada número pode ser auditado na fonte.</p>
        <p>Se encontrar uma divergência, confira primeiro na fonte oficial e, se confirmada, abra uma <em>issue</em> no repositório.</p>
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
          <li>Empenhos, credores, servidores, diárias, licitações, contratos</li>
        </ul>
      </div>
    </div>
    <p class="small">Dados públicos extraídos integralmente do portal oficial via scraping (Python + Playwright). Código-fonte e CSVs brutos disponíveis no repositório. Última geração: {data_geracao}.</p>
  </div>
</footer>

<script>
const CREDORES   = {json_credores};
const EMPENHOS   = {json_empenhos};
const SERVIDORES = {json_servidores};
const DIARIAS    = {json_diarias};
const LICITACOES = {json_licitacoes};
const KPIS       = {json_kpis};
const RADAR      = {json_radar};

const PAGE_SIZE = 60;

const $  = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
// parse "dd/mm/aaaa" -> Date (or 0 if invalid)
const parseDate = (s) => {{ if (!s) return 0; const [d,m,y] = s.split('/'); return new Date(+y, +m-1, +d).getTime() || 0; }};

// =========== Estado por seção (datasetFiltrado + cursor de paginação) ===========
const state = {{}};

function paginatedRender({{key, dataset, filterFn, sortFn, renderItem, renderEmpty, container, moreBtn, countEl}}) {{
  // Aplica filtro + sort, guarda no state e renderiza primeiro batch
  const filtered = (dataset || []).filter(filterFn || (() => true));
  if (sortFn) filtered.sort(sortFn);
  state[key] = {{ filtered, cursor: 0 }};
  $(container).innerHTML = '';
  appendBatch(key, renderItem, container, moreBtn, countEl, renderEmpty);
}}

function appendBatch(key, renderItem, container, moreBtn, countEl, renderEmpty) {{
  const s = state[key];
  const slice = s.filtered.slice(s.cursor, s.cursor + PAGE_SIZE);
  if (s.cursor === 0 && slice.length === 0) {{
    $(container).innerHTML = renderEmpty ? renderEmpty() : '<div class="empty">Nada encontrado.</div>';
  }} else {{
    const html = slice.map(renderItem).join('');
    if (s.cursor === 0) $(container).innerHTML = html;
    else $(container).insertAdjacentHTML('beforeend', html);
  }}
  s.cursor += slice.length;
  if (moreBtn) {{
    const btn = $(moreBtn);
    const rest = s.filtered.length - s.cursor;
    if (rest > 0) {{
      btn.style.display = 'block';
      btn.disabled = false;
      btn.textContent = `Mostrar mais ${{Math.min(PAGE_SIZE, rest).toLocaleString('pt-BR')}} (de ${{rest.toLocaleString('pt-BR')}} restantes)`;
    }} else {{
      btn.style.display = 'none';
    }}
  }}
  if (countEl) $(countEl).textContent = `${{s.filtered.length.toLocaleString('pt-BR')}} resultado${{s.filtered.length !== 1 ? 's' : ''}}`;
}}

// =========== CREDORES ===========
function renderCredores() {{
  const q = $('#credSearch').value.trim().toLowerCase();
  const sort = $('#credSort').value;
  const sorters = {{
    valor:    (a, b) => b.valor_num - a.valor_num,
    bruto:    (a, b) => b.valor_bruto_num - a.valor_bruto_num,
    empenhos: (a, b) => b.empenhos - a.empenhos,
    nome:     (a, b) => a.favorecido.localeCompare(b.favorecido, 'pt-BR'),
  }};
  paginatedRender({{
    key: 'cred', dataset: CREDORES,
    filterFn: c => !q || (c.favorecido + ' ' + c.cnpj).toLowerCase().includes(q),
    sortFn: sorters[sort],
    renderItem: (c, i) => {{
      const pct = Math.max(0.5, (c.valor_num / (KPIS.max_credor || 1)) * 100);
      const idx = state.cred.cursor + i + 1;
      return `<tr>
        <td class="rank">${{idx}}</td>
        <td class="fav">${{esc(c.favorecido)}}</td>
        <td class="opt mono">${{esc(c.cnpj || '—')}}</td>
        <td class="r opt num">${{c.empenhos}}${{c.anulacoes > 0 ? `<span style="color:var(--danger); font-size:0.8em"> (-${{c.anulacoes}})</span>` : ''}}</td>
        <td class="r num">${{esc(c.valor)}}</td>
        <td class="opt bar-cell"><div class="bar"><i style="width:${{pct.toFixed(1)}}%"></i></div></td>
      </tr>`;
    }},
    container: '#credTable tbody', moreBtn: '#credMore', countEl: '#credCount',
    renderEmpty: () => '<tr><td colspan="6" class="empty">Nenhum credor encontrado.</td></tr>',
  }});
}}

// =========== EMPENHOS ===========
let empFiltroFuncao = null;
function renderEmpenhos() {{
  const q = $('#empSearch').value.trim().toLowerCase();
  const sort = $('#empSort').value;
  const hideAnul = $('#empHideAnul').checked;
  const sorters = {{
    valor_desc:  (a, b) => Math.abs(b.valor_num) - Math.abs(a.valor_num),
    data_desc:   (a, b) => parseDate(b.data) - parseDate(a.data),
    data_asc:    (a, b) => parseDate(a.data) - parseDate(b.data),
    favorecido:  (a, b) => a.favorecido.localeCompare(b.favorecido, 'pt-BR'),
  }};
  paginatedRender({{
    key: 'emp', dataset: EMPENHOS,
    filterFn: e => {{
      if (hideAnul && e.valor_num < 0) return false;
      if (empFiltroFuncao && e.funcao !== empFiltroFuncao) return false;
      if (q && !(e.favorecido + ' ' + e.empenho + ' ' + e.historico + ' ' + e.elemento + ' ' + e.cnpj).toLowerCase().includes(q)) return false;
      return true;
    }},
    sortFn: sorters[sort],
    renderItem: e => `
      <div class="card">
        <div class="top">
          <span class="date">${{esc(e.data)}}  ·  emp. ${{esc(e.empenho)}}</span>
          <span class="val ${{e.valor_num < 0 ? 'neg' : ''}}">${{esc(e.valor)}}</span>
        </div>
        <div class="fav">${{esc(e.favorecido)}}</div>
        <div class="meta">
          ${{e.funcao ? `<span>${{esc(e.funcao)}}</span>` : ''}}
          ${{e.elemento ? `<span>${{esc(e.elemento)}}</span>` : ''}}
          ${{e.tipo ? `<span>${{esc(e.tipo)}}</span>` : ''}}
        </div>
        <div class="desc">${{esc(e.historico)}}</div>
        ${{e.fonte ? `<span class="tag">${{esc(e.fonte).slice(0, 80)}}</span>` : ''}}
      </div>`,
    container: '#empCards', moreBtn: '#empMore', countEl: '#empCount',
  }});
}}

function renderEmpChips() {{
  const counts = {{}};
  EMPENHOS.forEach(e => {{ if (e.funcao) counts[e.funcao] = (counts[e.funcao] || 0) + 1; }});
  const funcoes = Object.keys(counts).sort();
  $('#empChips').innerHTML =
    `<button class="chip ${{!empFiltroFuncao ? 'active' : ''}}" onclick="setEmpFuncao(null)">Todas (${{EMPENHOS.length.toLocaleString('pt-BR')}})</button>` +
    funcoes.map(f => `<button class="chip ${{empFiltroFuncao === f ? 'active' : ''}}" onclick="setEmpFuncao('${{f.replace(/'/g, "&#39;")}}')">${{esc(f)}} (${{counts[f]}})</button>`).join('');
}}
function setEmpFuncao(f) {{ empFiltroFuncao = f; renderEmpChips(); renderEmpenhos(); }}

// =========== SERVIDORES ===========
let srvSituacao = null;
let srvVinculo = null;
function renderServidores() {{
  const q = $('#srvSearch').value.trim().toLowerCase();
  const lot = $('#srvLotacao').value;
  const sort = $('#srvSort').value;
  const sorters = {{
    salario_desc:  (a, b) => b.salario_base_num - a.salario_base_num,
    salario_asc:   (a, b) => a.salario_base_num - b.salario_base_num,
    nome:          (a, b) => a.nome.localeCompare(b.nome, 'pt-BR'),
    cargo:         (a, b) => a.cargo.localeCompare(b.cargo, 'pt-BR'),
    admissao_desc: (a, b) => parseDate(b.admissao) - parseDate(a.admissao),
    admissao_asc:  (a, b) => parseDate(a.admissao) - parseDate(b.admissao),
  }};
  paginatedRender({{
    key: 'srv', dataset: SERVIDORES,
    filterFn: s => {{
      if (srvSituacao && s.situacao !== srvSituacao) return false;
      if (srvVinculo && s.vinculo !== srvVinculo) return false;
      if (lot && s.lotacao !== lot) return false;
      if (q && !(s.nome + ' ' + s.cargo + ' ' + s.lotacao + ' ' + s.matricula).toLowerCase().includes(q)) return false;
      return true;
    }},
    sortFn: sorters[sort],
    renderItem: s => {{
      const pct = Math.max(0.5, (s.salario_base_num / (KPIS.max_salario || 1)) * 100);
      const sitClass = s.situacao === 'Ativo' ? 'ok' : (s.salario_base_num === 0 ? 'warn' : '');
      return `<div class="card">
        <div class="top">
          <span class="date">mat. ${{esc(s.matricula)}}</span>
          <span class="val">${{esc(s.salario_base)}}</span>
        </div>
        <div class="bar" style="margin-top:-0.2rem"><i style="width:${{pct.toFixed(1)}}%"></i></div>
        <div class="fav">${{esc(s.nome)}}</div>
        <div class="meta">
          <span>${{esc(s.cargo)}}</span>
          ${{s.vinculo ? `<span>${{esc(s.vinculo)}}</span>` : ''}}
          ${{s.carga_horaria ? `<span>${{esc(s.carga_horaria)}}h/mês</span>` : ''}}
          ${{s.admissao ? `<span>desde ${{esc(s.admissao)}}</span>` : ''}}
        </div>
        <div class="desc">${{esc(s.lotacao)}}</div>
        <span class="tag ${{sitClass}}">${{esc(s.situacao)}}</span>
      </div>`;
    }},
    container: '#srvCards', moreBtn: '#srvMore', countEl: '#srvCount',
  }});
}}

function renderSrvFiltros() {{
  // Situações
  const sitCounts = {{}};
  SERVIDORES.forEach(s => {{ if (s.situacao) sitCounts[s.situacao] = (sitCounts[s.situacao] || 0) + 1; }});
  const situacoes = Object.keys(sitCounts).sort((a, b) => sitCounts[b] - sitCounts[a]);
  $('#srvSituacaoChips').innerHTML =
    `<button class="chip ${{!srvSituacao ? 'active' : ''}}" onclick="setSrvSituacao(null)">Todas (${{SERVIDORES.length}})</button>` +
    situacoes.map(s => `<button class="chip ${{srvSituacao === s ? 'active' : ''}}" onclick="setSrvSituacao('${{s.replace(/'/g, "&#39;")}}')">${{esc(s)}} (${{sitCounts[s]}})</button>`).join('');
  // Vínculos
  const vinCounts = {{}};
  SERVIDORES.forEach(s => {{ if (s.vinculo) vinCounts[s.vinculo] = (vinCounts[s.vinculo] || 0) + 1; }});
  const vinculos = Object.keys(vinCounts).sort((a, b) => vinCounts[b] - vinCounts[a]);
  $('#srvVinculoChips').innerHTML =
    `<button class="chip ${{!srvVinculo ? 'active' : ''}}" onclick="setSrvVinculo(null)">Todos</button>` +
    vinculos.map(v => `<button class="chip ${{srvVinculo === v ? 'active' : ''}}" onclick="setSrvVinculo('${{v.replace(/'/g, "&#39;")}}')">${{esc(v)}} (${{vinCounts[v]}})</button>`).join('');
  // Lotações no dropdown
  const lots = [...new Set(SERVIDORES.map(s => s.lotacao).filter(Boolean))].sort();
  $('#srvLotacao').innerHTML = '<option value="">Toda lotação (' + SERVIDORES.length + ')</option>' +
    lots.map(l => {{ const n = SERVIDORES.filter(s => s.lotacao === l).length; return `<option value="${{esc(l)}}">${{esc(l)}} (${{n}})</option>`; }}).join('');
}}
function setSrvSituacao(s) {{ srvSituacao = s; renderSrvFiltros(); renderServidores(); }}
function setSrvVinculo(v) {{ srvVinculo = v; renderSrvFiltros(); renderServidores(); }}

// =========== DIÁRIAS ===========
function renderDiaria(d) {{
  return `<div class="card">
    <div class="top">
      <span class="date">${{esc(d.data)}}${{d.empenho ? '  ·  emp. ' + esc(d.empenho) : ''}}</span>
      <span class="val ${{d.valor_num < 0 ? 'neg' : ''}}">${{esc(d.valor)}}</span>
    </div>
    <div class="fav">${{esc(d.beneficiario)}}</div>
    <div class="meta">
      ${{d.funcao ? `<span>${{esc(d.funcao)}}</span>` : ''}}
      ${{d.cpf ? `<span class="mono">${{esc(d.cpf)}}</span>` : ''}}
    </div>
    <div class="desc">${{esc(d.motivo)}}</div>
  </div>`;
}}
function renderDiarias() {{
  const q = $('#diaSearch').value.trim().toLowerCase();
  const sort = $('#diaSort').value;
  const sorters = {{
    data_desc:    (a, b) => parseDate(b.data) - parseDate(a.data),
    data_asc:     (a, b) => parseDate(a.data) - parseDate(b.data),
    valor_desc:   (a, b) => Math.abs(b.valor_num) - Math.abs(a.valor_num),
    beneficiario: (a, b) => a.beneficiario.localeCompare(b.beneficiario, 'pt-BR'),
  }};
  paginatedRender({{
    key: 'dia', dataset: DIARIAS,
    filterFn: d => !q || (d.beneficiario + ' ' + d.motivo + ' ' + (d.funcao || '')).toLowerCase().includes(q),
    sortFn: sorters[sort],
    renderItem: renderDiaria,
    container: '#diaCards', moreBtn: '#diaMore', countEl: '#diaCount',
  }});
}}

// =========== COMPRAS (Licitações / Dispensas / Contratos / Atas) ===========
let licTab = 'lic';
let licCategoria = null;

const LIC_RENDERERS = {{
  lic: {{
    dataset: () => LICITACOES.licitacoes,
    hasCat: false,
    search: l => (l.objeto + ' ' + l.numero + ' ' + l.modalidade + ' ' + l.processo).toLowerCase(),
    sorters: {{
      data_desc:  (a, b) => parseDate(b.data) - parseDate(a.data),
      data_asc:   (a, b) => parseDate(a.data) - parseDate(b.data),
      valor_desc: (a, b) => (b.valor_estimado_num || 0) - (a.valor_estimado_num || 0),
      contratado: (a, b) => (a.objeto || '').localeCompare(b.objeto || '', 'pt-BR'),
    }},
    render: l => `<div class="card">
      <div class="top">
        <span class="date">${{esc(l.data)}}  ·  nº ${{esc(l.numero)}}</span>
        <span class="val">${{esc(l.valor_final && l.valor_final_num > 0 ? l.valor_final : l.valor_estimado)}}</span>
      </div>
      <div class="fav">${{esc(l.modalidade)}}</div>
      <div class="desc">${{esc(l.objeto)}}</div>
      <div class="meta">
        <span>Proc. ${{esc(l.processo)}}</span>
        <span>${{esc(l.situacao)}}</span>
      </div>
    </div>`,
  }},
  dis: {{
    dataset: () => LICITACOES.dispensas,
    hasCat: false,
    search: d => (d.objeto + ' ' + d.numero + ' ' + d.modalidade + ' ' + d.processo).toLowerCase(),
    sorters: {{
      data_desc:  (a, b) => parseDate(b.data) - parseDate(a.data),
      data_asc:   (a, b) => parseDate(a.data) - parseDate(b.data),
      valor_desc: (a, b) => (b.valor_final_num || b.valor_estimado_num || 0) - (a.valor_final_num || a.valor_estimado_num || 0),
      contratado: (a, b) => (a.objeto || '').localeCompare(b.objeto || '', 'pt-BR'),
    }},
    render: d => `<div class="card">
      <div class="top">
        <span class="date">${{esc(d.data)}}  ·  nº ${{esc(d.numero)}}${{d.ano ? '/' + esc(d.ano) : ''}}</span>
        <span class="val">${{esc(d.valor_final && d.valor_final_num > 0 ? d.valor_final : d.valor_estimado)}}</span>
      </div>
      <div class="fav">${{esc(d.modalidade)}}</div>
      <div class="desc">${{esc(d.objeto)}}</div>
      <div class="meta">
        <span>Proc. ${{esc(d.processo)}}</span>
        ${{d.base_legal ? `<span>${{esc(d.base_legal).slice(0, 60)}}</span>` : ''}}
        <span>${{esc(d.situacao)}}</span>
      </div>
    </div>`,
  }},
  con: {{
    dataset: () => LICITACOES.contratos,
    hasCat: true,
    search: c => (c.objeto + ' ' + c.contratado + ' ' + c.contrato + ' ' + c.cnpj).toLowerCase(),
    catKey: c => c.categoria,
    sorters: {{
      data_desc:  (a, b) => parseDate(b.assinatura) - parseDate(a.assinatura),
      data_asc:   (a, b) => parseDate(a.assinatura) - parseDate(b.assinatura),
      valor_desc: (a, b) => b.valor_num - a.valor_num,
      contratado: (a, b) => a.contratado.localeCompare(b.contratado, 'pt-BR'),
    }},
    render: c => `<div class="card">
      <div class="top">
        <span class="date">assinado ${{esc(c.assinatura)}}  ·  nº ${{esc(c.contrato)}}</span>
        <span class="val">${{esc(c.valor)}}</span>
      </div>
      <div class="fav">${{esc(c.contratado)}}</div>
      <div class="desc">${{esc(c.objeto)}}</div>
      <div class="meta">
        ${{c.cnpj ? `<span class="mono">${{esc(c.cnpj)}}</span>` : ''}}
        ${{c.categoria ? `<span>${{esc(c.categoria)}}</span>` : ''}}
        <span>${{esc(c.situacao)}}</span>
      </div>
    </div>`,
  }},
  ata: {{
    dataset: () => LICITACOES.atas,
    hasCat: true,
    search: a => (a.objeto + ' ' + a.contratado + ' ' + a.ata + ' ' + a.cnpj).toLowerCase(),
    catKey: a => a.categoria,
    sorters: {{
      data_desc:  (a, b) => parseDate(b.assinatura) - parseDate(a.assinatura),
      data_asc:   (a, b) => parseDate(a.assinatura) - parseDate(b.assinatura),
      valor_desc: (a, b) => b.valor_num - a.valor_num,
      contratado: (a, b) => a.contratado.localeCompare(b.contratado, 'pt-BR'),
    }},
    render: a => `<div class="card">
      <div class="top">
        <span class="date">assinada ${{esc(a.assinatura)}}  ·  ata ${{esc(a.ata)}}${{a.ano ? '/' + esc(a.ano) : ''}}</span>
        <span class="val">${{esc(a.valor)}}</span>
      </div>
      <div class="fav">${{esc(a.contratado)}}</div>
      <div class="desc">${{esc(a.objeto)}}</div>
      <div class="meta">
        ${{a.cnpj ? `<span class="mono">${{esc(a.cnpj)}}</span>` : ''}}
        ${{a.categoria ? `<span>${{esc(a.categoria)}}</span>` : ''}}
        <span>${{esc(a.situacao)}}</span>
      </div>
    </div>`,
  }},
}};

function switchLicTab(t) {{
  licTab = t; licCategoria = null;
  ['lic', 'dis', 'con', 'ata'].forEach(k => {{
    $('#tab' + k.charAt(0).toUpperCase() + k.slice(1)).classList.toggle('active', t === k);
  }});
  const cfg = LIC_RENDERERS[t];
  $('#licCatRow').style.display = cfg.hasCat ? 'flex' : 'none';
  renderLicChips();
  renderLicitacoes();
}}

function renderLicChips() {{
  const cfg = LIC_RENDERERS[licTab];
  if (!cfg.hasCat) return;
  const data = cfg.dataset();
  const counts = {{}};
  data.forEach(item => {{
    const cat = cfg.catKey(item);
    if (cat) counts[cat] = (counts[cat] || 0) + 1;
  }});
  const cats = Object.keys(counts).sort();
  $('#licCatChips').innerHTML =
    `<button class="chip ${{!licCategoria ? 'active' : ''}}" onclick="setLicCat(null)">Todas (${{data.length}})</button>` +
    cats.map(c => `<button class="chip ${{licCategoria === c ? 'active' : ''}}" onclick="setLicCat('${{c.replace(/'/g, "&#39;")}}')">${{esc(c)}} (${{counts[c]}})</button>`).join('');
}}
function setLicCat(c) {{ licCategoria = c; renderLicChips(); renderLicitacoes(); }}

function renderLicitacoes() {{
  const q = $('#licSearch').value.trim().toLowerCase();
  const sort = $('#licSort').value;
  const cfg = LIC_RENDERERS[licTab];
  paginatedRender({{
    key: 'lic', dataset: cfg.dataset(),
    filterFn: item => {{
      if (cfg.hasCat && licCategoria && cfg.catKey(item) !== licCategoria) return false;
      if (q && !cfg.search(item).includes(q)) return false;
      return true;
    }},
    sortFn: cfg.sorters[sort],
    renderItem: cfg.render,
    container: '#licCards', moreBtn: '#licMore', countEl: '#licCount',
  }});
}}

// =========== EVENTS ===========
$('#credSearch').addEventListener('input', renderCredores);
$('#credSort').addEventListener('change', renderCredores);
$('#credMore').addEventListener('click', () => appendBatch('cred',
  (c, i) => {{
    const pct = Math.max(0.5, (c.valor_num / (KPIS.max_credor || 1)) * 100);
    const idx = state.cred.cursor + i + 1;
    return `<tr><td class="rank">${{idx}}</td><td class="fav">${{esc(c.favorecido)}}</td><td class="opt mono">${{esc(c.cnpj || '—')}}</td><td class="r opt num">${{c.empenhos}}${{c.anulacoes > 0 ? `<span style="color:var(--danger); font-size:0.8em"> (-${{c.anulacoes}})</span>` : ''}}</td><td class="r num">${{esc(c.valor)}}</td><td class="opt bar-cell"><div class="bar"><i style="width:${{pct.toFixed(1)}}%"></i></div></td></tr>`;
  }},
  '#credTable tbody', '#credMore', '#credCount'));

$('#empSearch').addEventListener('input', renderEmpenhos);
$('#empSort').addEventListener('change', renderEmpenhos);
$('#empHideAnul').addEventListener('change', renderEmpenhos);
$('#empMore').addEventListener('click', () => appendBatch('emp',
  e => `<div class="card"><div class="top"><span class="date">${{esc(e.data)}}  ·  emp. ${{esc(e.empenho)}}</span><span class="val ${{e.valor_num < 0 ? 'neg' : ''}}">${{esc(e.valor)}}</span></div><div class="fav">${{esc(e.favorecido)}}</div><div class="meta">${{e.funcao ? `<span>${{esc(e.funcao)}}</span>` : ''}}${{e.elemento ? `<span>${{esc(e.elemento)}}</span>` : ''}}${{e.tipo ? `<span>${{esc(e.tipo)}}</span>` : ''}}</div><div class="desc">${{esc(e.historico)}}</div>${{e.fonte ? `<span class="tag">${{esc(e.fonte).slice(0, 80)}}</span>` : ''}}</div>`,
  '#empCards', '#empMore', '#empCount'));

$('#srvSearch').addEventListener('input', renderServidores);
$('#srvLotacao').addEventListener('change', renderServidores);
$('#srvSort').addEventListener('change', renderServidores);
$('#srvMore').addEventListener('click', () => appendBatch('srv',
  s => {{
    const pct = Math.max(0.5, (s.salario_base_num / (KPIS.max_salario || 1)) * 100);
    const sitClass = s.situacao === 'Ativo' ? 'ok' : (s.salario_base_num === 0 ? 'warn' : '');
    return `<div class="card"><div class="top"><span class="date">mat. ${{esc(s.matricula)}}</span><span class="val">${{esc(s.salario_base)}}</span></div><div class="bar" style="margin-top:-0.2rem"><i style="width:${{pct.toFixed(1)}}%"></i></div><div class="fav">${{esc(s.nome)}}</div><div class="meta"><span>${{esc(s.cargo)}}</span>${{s.vinculo ? `<span>${{esc(s.vinculo)}}</span>` : ''}}${{s.carga_horaria ? `<span>${{esc(s.carga_horaria)}}h/mês</span>` : ''}}${{s.admissao ? `<span>desde ${{esc(s.admissao)}}</span>` : ''}}</div><div class="desc">${{esc(s.lotacao)}}</div><span class="tag ${{sitClass}}">${{esc(s.situacao)}}</span></div>`;
  }},
  '#srvCards', '#srvMore', '#srvCount'));

$('#diaSearch').addEventListener('input', renderDiarias);
$('#diaSort').addEventListener('change', renderDiarias);

$('#licSearch').addEventListener('input', renderLicitacoes);
$('#licSort').addEventListener('change', renderLicitacoes);
$('#licMore').addEventListener('click', () => {{
  if (licTab === 'lic') {{
    appendBatch('lic',
      l => `<div class="card"><div class="top"><span class="date">${{esc(l.data)}}  ·  nº ${{esc(l.numero)}}</span><span class="val">${{esc(l.valor_final && l.valor_final_num > 0 ? l.valor_final : l.valor_estimado)}}</span></div><div class="fav">${{esc(l.modalidade)}}</div><div class="desc">${{esc(l.objeto)}}</div><div class="meta"><span>Proc. ${{esc(l.processo)}}</span><span>${{esc(l.situacao)}}</span></div></div>`,
      '#licCards', '#licMore', '#licCount');
  }} else {{
    appendBatch('lic',
      c => `<div class="card"><div class="top"><span class="date">assinado ${{esc(c.assinatura)}}  ·  nº ${{esc(c.contrato)}}</span><span class="val">${{esc(c.valor)}}</span></div><div class="fav">${{esc(c.contratado)}}</div><div class="desc">${{esc(c.objeto)}}</div><div class="meta">${{c.cnpj ? `<span class="mono">${{esc(c.cnpj)}}</span>` : ''}}${{c.categoria ? `<span>${{esc(c.categoria)}}</span>` : ''}}<span>${{esc(c.situacao)}}</span></div></div>`,
      '#licCards', '#licMore', '#licCount');
  }}
}});

// Totais inline nos leads
$('#credTotal').textContent = CREDORES.length.toLocaleString('pt-BR');
$('#empTotal').textContent  = EMPENHOS.length.toLocaleString('pt-BR');
$('#srvTotal').textContent  = SERVIDORES.length.toLocaleString('pt-BR');
$('#diaTotal').textContent  = DIARIAS.length.toLocaleString('pt-BR');
$('#licTotalL').textContent = LICITACOES.licitacoes.length;
$('#licTotalC').textContent = LICITACOES.contratos.length;

// =========== RADAR DE GASTOS ===========
function renderRadar() {{
  const ordem = {{ alta: 0, media: 1, baixa: 2, info: 3 }};
  const sorted = RADAR.slice().sort((a, b) => (ordem[a.severidade] ?? 4) - (ordem[b.severidade] ?? 4));
  $('#radarGrid').innerHTML = sorted.map(a => `
    <a class="radar-card sev-${{esc(a.severidade)}}" href="${{esc(a.link)}}">
      <div class="head">
        <span class="icon" aria-hidden="true">${{esc(a.icone)}}</span>
        <span class="sev">${{esc(a.severidade)}}</span>
      </div>
      <div class="titulo">${{esc(a.titulo)}}</div>
      <div class="desc">${{esc(a.descricao)}}</div>
      <div class="cta">Ver dados →</div>
    </a>`).join('') || '<div class="empty">Nenhuma anomalia detectada.</div>';
}}

// Inicialização
renderRadar();
renderCredores();
renderEmpChips();
renderEmpenhos();
renderSrvFiltros();
renderServidores();
renderDiarias();
renderLicitacoes();

// Scroll-spy: highlight do link da seção visível na nav
(function() {{
  const navLinks = $$('nav.site-nav a');
  const sections = navLinks
    .map(a => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);
  if (!sections.length) return;
  const map = new Map(sections.map((sec, i) => [sec, navLinks[i]]));
  const obs = new IntersectionObserver((entries) => {{
    // Mantém o último que entrou no terço superior da viewport
    entries.forEach(en => {{
      if (en.isIntersecting) {{
        navLinks.forEach(a => a.classList.remove('active'));
        const link = map.get(en.target);
        if (link) link.classList.add('active');
      }}
    }});
  }}, {{ rootMargin: '-15% 0px -70% 0px', threshold: 0 }});
  sections.forEach(s => obs.observe(s));
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
