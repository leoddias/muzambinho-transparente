"""Screenshot ampliado da seçao de credores para ver os detalhes das barras."""
from playwright.sync_api import sync_playwright
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
DEBUG = ROOT / "debug"


def main():
    url = INDEX.absolute().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(1000)

        # Captura apenas as primeiras 15 linhas da tabela
        bbox = page.locator("table.t").bounding_box()
        if bbox:
            page.screenshot(
                path=str(DEBUG / "site_credores_zoom.png"),
                clip={"x": bbox["x"], "y": bbox["y"], "width": bbox["width"], "height": min(800, bbox["height"])},
            )
        # E sem zoom (scale 1) tambem
        ctx2 = browser.new_context(viewport={"width": 1280, "height": 800})
        page2 = ctx2.new_page()
        page2.goto(url, wait_until="networkidle", timeout=20000)
        page2.wait_for_timeout(500)
        bbox2 = page2.locator("table.t").bounding_box()
        if bbox2:
            page2.screenshot(
                path=str(DEBUG / "site_credores_normal.png"),
                clip={"x": bbox2["x"], "y": bbox2["y"], "width": bbox2["width"], "height": min(450, bbox2["height"])},
            )

        # Inspect: imprime a largura computada do <i> nas primeiras 5 barras
        widths = page.evaluate("""
            () => Array.from(document.querySelectorAll('.bar > i')).slice(0, 8).map(el => ({
                style_width: el.style.width,
                computed: getComputedStyle(el).width,
                bg: getComputedStyle(el).background.slice(0, 80),
                rect_w: el.getBoundingClientRect().width,
                parent_rect_w: el.parentElement.getBoundingClientRect().width,
            }))
        """)
        for i, w in enumerate(widths):
            print(f"  bar[{i}]: style={w['style_width']}, computed={w['computed']}, rect={w['rect_w']:.1f}/{w['parent_rect_w']:.1f}")

        browser.close()


if __name__ == "__main__":
    main()
