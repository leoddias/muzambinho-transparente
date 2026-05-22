"""Inspecao profunda da API de dados abertos do PortalTP de Muzambinho.

  1. Renderiza /api/dadosabertos.aspx no Playwright para pegar links reais
     e parametros de cada endpoint.
  2. Testa 5-10 endpoints com variacoes de parametros para entender o formato.
  3. Reporta o que esta funcional, o que faltou capturar, e o tamanho real.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import urllib.parse

BASE = "https://muzambinho-mg.portaltp.com.br"
DEBUG = Path(__file__).parent.parent / "debug"
DEBUG.mkdir(exist_ok=True)


def coleta_links_api(page) -> list[dict]:
    """Carrega /api/dadosabertos.aspx e extrai todos os links de endpoint."""
    page.goto(BASE + "/api/dadosabertos.aspx", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1500)
    (DEBUG / "dadosabertos.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(DEBUG / "dadosabertos.png"), full_page=True)
    info = page.evaluate("""
        () => {
            const links = Array.from(document.querySelectorAll('a[href*="/api/"]'));
            return links.map(a => ({
                text: (a.innerText || '').trim().slice(0, 60),
                href: a.href,
                title: a.title || '',
                parent: (a.closest('div,section,article,li,tr')?.textContent || '').trim().slice(0, 150),
            })).filter(x => x.text || x.href.includes('api-'));
        }
    """)
    seen = set()
    out = []
    for x in info:
        if x['href'] in seen:
            continue
        seen.add(x['href'])
        out.append(x)
    return out


def testa_endpoint(page, url: str, label: str) -> dict:
    """Testa GET no endpoint, retorna primeiros bytes + tipo."""
    try:
        resp = page.context.request.get(url, timeout=30000)
        ct = resp.headers.get("content-type", "")
        body = resp.body()
        return {
            "label": label, "url": url, "status": resp.status,
            "content_type": ct[:80], "size": len(body),
            "head": body[:400].decode("utf-8", errors="replace"),
        }
    except Exception as e:
        return {"label": label, "url": url, "erro": str(e)[:200]}


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()

        print("=== 1. EXTRAINDO LINKS DA PÁGINA /api/dadosabertos.aspx ===\n")
        links = coleta_links_api(page)
        print(f"Total de links únicos para /api/...: {len(links)}\n")
        for x in links[:40]:
            print(f"  {x['text']!r:35s} {x['href']}")

        print("\n=== 2. TESTANDO ENDPOINTS COM VARIAÇÕES DE PARÂMETROS ===\n")
        # Pega URLs unicas dos endpoints API (sem dadosabertos.aspx em si)
        candidatas = [x['href'] for x in links
                     if '/api/' in x['href'] and 'dadosabertos' not in x['href']
                     and not x['href'].endswith('/api/')][:25]

        # Variacoes de query string para descobrir o que cada endpoint aceita
        variacoes = ["", "?ano=2026", "?ano=2026&formato=json", "?ano=2026&mes=01",
                     "?formato=json&ano=2026", "?dataini=01/01/2026&datafim=31/05/2026"]

        for url in candidatas[:8]:  # limitar pra nao demorar muito
            label = url.split("/")[-1]
            print(f"\n--- {label} ---")
            for v in variacoes[:3]:
                r = testa_endpoint(page, url + v, label + v)
                if "erro" in r:
                    print(f"  {v or '(sem params)'}: ERRO {r['erro'][:80]}")
                else:
                    print(f"  {v or '(sem params)'}: {r['status']} {r['content_type']} - {r['size']} bytes")
                    if r['size'] > 0 and r['size'] < 50000:
                        # preview do conteudo
                        h = r['head'].replace('\n', ' ').replace('\r', ' ')[:120]
                        print(f"    head: {h!r}")

        b.close()


if __name__ == "__main__":
    main()
