"""Reconhecimento manual dos endpoints do PortalTP de Muzambinho.

Abre cada página, dumpa o HTML pra debug/, e tenta identificar:
  - IDs de campos de data (data inicial, data final)
  - Dropdown de entidade
  - Botão de pesquisar
  - Botões de export (CSV, XLSX, XML)
  - Estrutura da tabela de resultados

Não é parte do pipeline final - é script de exploração one-off.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import re

BASE = "https://muzambinho-mg.portaltp.com.br"
DEBUG = Path(__file__).parent.parent / "debug"
DEBUG.mkdir(exist_ok=True)

ENDPOINTS = {
    "empenhos": "/consultas/despesas/empenhos.aspx",
    "servidores": "/consultas/pessoal/servidores.aspx",
    "diarias": "/consultas/despesas/diarias.aspx",
    "licitacoes": "/consultas/compras/licitacoes.aspx",
    "contratos": "/consultas/compras/contratos.aspx",
}


def inspect(page, name, path):
    url = BASE + path
    print(f"\n=== {name}: {url} ===")
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"  ERRO ao abrir: {e}")
        return

    html = page.content()
    (DEBUG / f"inspect_{name}.html").write_text(html, encoding="utf-8")
    page.screenshot(path=str(DEBUG / f"inspect_{name}.png"), full_page=True)

    # IDs de input/select/button
    ids = page.evaluate("""
        () => {
            const out = {inputs: [], selects: [], buttons: [], links: []};
            document.querySelectorAll('input').forEach(el => {
                out.inputs.push({id: el.id, name: el.name, type: el.type, placeholder: el.placeholder, value: el.value});
            });
            document.querySelectorAll('select').forEach(el => {
                const opts = Array.from(el.options).slice(0, 5).map(o => o.text);
                out.selects.push({id: el.id, name: el.name, options: opts});
            });
            document.querySelectorAll('button, input[type=submit], input[type=button]').forEach(el => {
                out.buttons.push({id: el.id, name: el.name, text: (el.innerText || el.value || '').trim().slice(0, 80)});
            });
            document.querySelectorAll('a').forEach(el => {
                const t = (el.innerText || '').trim();
                if (t.match(/excel|csv|xml|pdf|xlsx|exportar|baixar/i)) {
                    out.links.push({id: el.id, href: el.href, text: t, onclick: (el.getAttribute('onclick') || '').slice(0, 200)});
                }
            });
            return out;
        }
    """)

    print(f"  Inputs ({len(ids['inputs'])}):")
    for i in ids['inputs'][:15]:
        if i['id'] or i['placeholder'] or i['type'] in ('text', 'submit', 'button'):
            print(f"    [{i['type']}] id={i['id']!r} name={i['name']!r} ph={i['placeholder']!r}")

    print(f"  Selects ({len(ids['selects'])}):")
    for s in ids['selects']:
        print(f"    id={s['id']!r} name={s['name']!r} opts={s['options']}")

    print(f"  Buttons ({len(ids['buttons'])}):")
    for b in ids['buttons'][:10]:
        if b['text']:
            print(f"    id={b['id']!r} text={b['text']!r}")

    print(f"  Export links ({len(ids['links'])}):")
    for l in ids['links']:
        print(f"    text={l['text']!r}  href={l['href'][:100]!r}")
        if l['onclick']:
            print(f"      onclick={l['onclick']!r}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 1024})
        page = ctx.new_page()
        for name, path in ENDPOINTS.items():
            inspect(page, name, path)
        browser.close()


if __name__ == "__main__":
    main()
