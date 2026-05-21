"""Testa o export CSV nativo do PortalTP em empenhos.

Versão 2: monitora network + tenta JS API do DevExpress.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

BASE = "https://muzambinho-mg.portaltp.com.br"
DEBUG = Path(__file__).parent.parent / "debug"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 1024},
            accept_downloads=True,
        )
        page = ctx.new_page()

        requests_log = []
        page.on("request", lambda r: requests_log.append(("REQ", r.method, r.url[:200])))
        page.on("response", lambda r: requests_log.append(("RES", r.status, r.url[:200])))
        page.on("download", lambda d: print(f"  >>> DOWNLOAD evento: {d.suggested_filename} url={d.url[:200]}"))
        page.on("popup", lambda p: print(f"  >>> POPUP: {p.url}"))

        url = BASE + "/consultas/despesas/empenhos.aspx"
        print(f"Loading {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)

        print("\nPreenchendo datas 01/01/2026 - 21/05/2026...")
        page.fill("#ctl00_containerCorpo_edtDataIni_I", "01/01/2026")
        page.fill("#ctl00_containerCorpo_edtDataFim_I", "21/05/2026")

        print("Clicando Aplicar...")
        page.click("#ctl00_containerCorpo_btnAplicFiltro")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_selector("#ctl00_containerCorpo_grdData", timeout=30000)
        page.wait_for_timeout(2000)

        # Inspecionar a JS API do DevExpress para o grid
        print("\nInspecionando JS API do grid...")
        api = page.evaluate("""
            () => {
                const out = {has_grid: false, methods: [], grid_keys: []};
                const grid = window['ctl00_containerCorpo_grdData'];
                if (grid) {
                    out.has_grid = true;
                    let proto = grid;
                    while (proto && proto !== Object.prototype) {
                        Object.getOwnPropertyNames(proto).forEach(m => {
                            if (m.toLowerCase().includes('export') || m.toLowerCase().includes('csv') || m.toLowerCase().includes('print')) {
                                out.methods.push(m);
                            }
                        });
                        proto = Object.getPrototypeOf(proto);
                    }
                    out.grid_keys = Object.keys(grid).slice(0, 30);
                }
                return out;
            }
        """)
        print(f"  Grid encontrado: {api['has_grid']}")
        print(f"  Métodos export-related: {api['methods'][:20]}")
        print(f"  Grid keys: {api['grid_keys']}")

        # Limpar log
        requests_log.clear()

        print("\nAbrindo menu Imprimir Relatorio...")
        page.click("#ctl00_containerCorpo_grdData_DXCTMenu0_DXI2_T")
        page.wait_for_timeout(1500)

        # Testar XML em vez de CSV
        print(f"\nTentando export XML...")
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click("#ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i5_T")
            dl = dl_info.value
            target = DEBUG / "test_export_empenhos.xml"
            dl.save_as(str(target))
            size = target.stat().st_size
            print(f"OK XML: {size} bytes em {target}")
            print(f"Suggested filename: {dl.suggested_filename}")
            # primeiras 30 linhas
            for enc in ("utf-8-sig", "utf-8", "cp1252"):
                try:
                    text = target.read_text(encoding=enc)
                    print(f"\n=== XML primeiras 30 linhas (enc={enc}) ===")
                    for i, line in enumerate(text.splitlines()[:30]):
                        print(f"  {i}: {line[:250]}")
                    print(f"Total linhas: {len(text.splitlines())}")
                    break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"ERRO XML: {e}")
            return

        # Voltar pra primeira pagina e testar XLSX
        page.goto(BASE + "/consultas/despesas/empenhos.aspx", wait_until="networkidle")
        page.fill("#ctl00_containerCorpo_edtDataIni_I", "01/01/2026")
        page.fill("#ctl00_containerCorpo_edtDataFim_I", "21/05/2026")
        page.click("#ctl00_containerCorpo_btnAplicFiltro")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        page.click("#ctl00_containerCorpo_grdData_DXCTMenu0_DXI2_T")
        page.wait_for_timeout(1000)

        print(f"\nTentando export XLSX...")
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click("#ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i2_T")
            dl = dl_info.value
            target = DEBUG / "test_export_empenhos.xlsx"
            dl.save_as(str(target))
            print(f"OK XLSX: {target.stat().st_size} bytes")
            print(f"Suggested filename: {dl.suggested_filename}")
        except Exception as e:
            print(f"ERRO XLSX: {e}")

        # E o CSV original também (pra ter os 3 pra comparar)
        page.goto(BASE + "/consultas/despesas/empenhos.aspx", wait_until="networkidle")
        page.fill("#ctl00_containerCorpo_edtDataIni_I", "01/01/2026")
        page.fill("#ctl00_containerCorpo_edtDataFim_I", "21/05/2026")
        page.click("#ctl00_containerCorpo_btnAplicFiltro")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        page.click("#ctl00_containerCorpo_grdData_DXCTMenu0_DXI2_T")
        page.wait_for_timeout(1000)
        print(f"\nTentando export CSV...")
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click("#ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i4_T")
            dl = dl_info.value
            target = DEBUG / "test_export_empenhos.csv"
            dl.save_as(str(target))
            size = target.stat().st_size
            print(f"OK CSV: {size} bytes em {target}")
            print(f"Suggested filename: {dl.suggested_filename}")

            for enc in ("utf-8-sig", "cp1252", "utf-8", "latin1"):
                try:
                    text = target.read_text(encoding=enc)
                    print(f"\n=== Primeiras 10 linhas (encoding={enc}) ===")
                    for i, line in enumerate(text.splitlines()[:10]):
                        print(f"  {i}: {line[:200]}")
                    print(f"Total linhas: {len(text.splitlines())}")
                    return
                except UnicodeDecodeError as e:
                    print(f"  enc {enc}: {e}")
        except Exception as e:
            print(f"\nERRO: {e}")
            print(f"\n--- Network traffic (ultimas 30 entradas) ---")
            for entry in requests_log[-30:]:
                print(f"  {entry}")

        browser.close()


if __name__ == "__main__":
    main()
