"""Testa o index.html: abre no Playwright, captura erros de console,
verifica que as secoes renderizam, e tira screenshots desktop + mobile."""
from playwright.sync_api import sync_playwright
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
DEBUG = ROOT / "debug"


def main():
    url = INDEX.absolute().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Desktop
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        errors = []
        warnings = []
        page.on("console", lambda msg: (errors if msg.type == "error" else warnings).append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))

        page.goto(url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(1000)

        print("=== Console errors:", len(errors))
        for e in errors[:10]:
            print(f"  {e}")
        print("=== Console warnings:", len(warnings))
        for w in warnings[:5]:
            print(f"  {w}")

        # Verifica que as secoes renderizaram (procurando contadores)
        for sel in ["#credCount", "#empCount", "#srvCount", "#licCount"]:
            text = page.locator(sel).text_content()
            print(f"  {sel}: {text!r}")

        # Verifica que tabela de credores tem linhas
        n_rows = page.locator("#credTable tbody tr").count()
        n_emps = page.locator("#empCards .card").count()
        n_srv = page.locator("#srvCards .card").count()
        n_dia = page.locator("#diaCards .card").count()
        n_lic = page.locator("#licCards .card").count()
        print(f"  Credores rows: {n_rows}, Empenhos cards: {n_emps}, Servidores: {n_srv}, Diarias: {n_dia}, Licitacoes: {n_lic}")

        # Above-the-fold (1 viewport)
        page.screenshot(path=str(DEBUG / "site_desktop_top.png"), full_page=False)
        # Scroll para credores
        page.evaluate("document.querySelector('table.t').scrollIntoView({block:'center'})")
        page.wait_for_timeout(500)
        page.screenshot(path=str(DEBUG / "site_desktop_credores.png"), full_page=False)
        # Scroll para empenhos
        page.evaluate("document.querySelector('#empCards').scrollIntoView({block:'start'})")
        page.wait_for_timeout(500)
        page.screenshot(path=str(DEBUG / "site_desktop_empenhos.png"), full_page=False)
        # Scroll para servidores
        page.evaluate("document.querySelector('#srvCards').scrollIntoView({block:'start'})")
        page.wait_for_timeout(500)
        page.screenshot(path=str(DEBUG / "site_desktop_servidores.png"), full_page=False)
        # Scroll para licitações
        page.evaluate("document.querySelector('#licCards').scrollIntoView({block:'start'})")
        page.wait_for_timeout(500)
        page.screenshot(path=str(DEBUG / "site_desktop_licitacoes.png"), full_page=False)
        ctx.close()

        # Mobile - above the fold only
        ctx = browser.new_context(viewport={"width": 375, "height": 800})
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(1000)
        page.screenshot(path=str(DEBUG / "site_mobile_top.png"), full_page=False)
        page.evaluate("document.querySelector('table.t').scrollIntoView({block:'start'})")
        page.wait_for_timeout(500)
        page.screenshot(path=str(DEBUG / "site_mobile_credores.png"), full_page=False)
        ctx.close()

        browser.close()

        print(f"\nScreenshots:")
        print(f"  desktop: {(DEBUG / 'site_desktop.png').stat().st_size:,} bytes")
        print(f"  mobile:  {(DEBUG / 'site_mobile.png').stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
