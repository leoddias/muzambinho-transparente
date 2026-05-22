"""Investigacao das discrepancias reportadas pelo usuario:

1. Diarias: endpoint dedicado retorna 6, mas empenhos_completo tem 61 com elemento
   '33901400000 - Diarias'. Suspeita: outra entidade tem mais? Ou faltam meses?

2. Licitacoes: so 5 licitacoes e 30 contratos no ano. Faltam dispensas?
   inexigibilidades? Outra entidade?

Investiga:
  - Quais opcoes existem no dropdown cbxEntidades
  - Se URLs extras existem: passagens, dispensas, inexigibilidades, atas, restos_pagar
  - Quantos registros cada combinacao retorna
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

BASE = "https://muzambinho-mg.portaltp.com.br"
DEBUG = Path(__file__).parent.parent / "debug"


def listar_entidades(page) -> list[str]:
    """Lista todas as opcoes do cbxEntidades via DevExpress JS API."""
    page.goto(BASE + "/consultas/despesas/empenhos.aspx", wait_until="networkidle")
    page.wait_for_timeout(1500)
    opts = page.evaluate("""
        () => {
            const ctl = window['ctl00_containerCorpo_cbxEntidades'];
            if (!ctl || !ctl.GetItemCount) return ['(API DevExpress não disponível)'];
            const out = [];
            const n = ctl.GetItemCount();
            for (let i = 0; i < n; i++) {
                const it = ctl.GetItem(i);
                out.push({text: it.text, value: it.value, selected: i === ctl.GetSelectedIndex()});
            }
            return out;
        }
    """)
    return opts


def testar_url(page, url: str, label: str) -> dict:
    """Tenta abrir uma URL e detectar se eh uma consulta valida."""
    try:
        resp = page.goto(BASE + url, wait_until="networkidle", timeout=20000)
        ok = resp.status == 200 and bool(page.locator("#ctl00_containerCorpo_btnAplicFiltro").count())
        return {"url": url, "label": label, "status": resp.status, "consulta_valida": ok}
    except Exception as e:
        return {"url": url, "label": label, "erro": str(e)[:100]}


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
        page = ctx.new_page()

        print("=== 1. ENTIDADES DISPONIVEIS ===")
        entidades = listar_entidades(page)
        for e in entidades:
            if isinstance(e, dict):
                marker = "* " if e.get("selected") else "  "
                print(f"  {marker}{e.get('text')!r:50s} value={e.get('value')!r}")
            else:
                print(f"  {e!r}")

        print("\n=== 2. URLS CANDIDATAS ===")
        candidatas = [
            ("/consultas/despesas/empenhos.aspx", "empenhos (ja uso)"),
            ("/consultas/despesas/diarias.aspx", "diarias (ja uso, 6 registros)"),
            ("/consultas/despesas/passagens.aspx", "passagens (suspeita)"),
            ("/consultas/despesas/obras.aspx", "obras"),
            ("/consultas/despesas/restos_a_pagar.aspx", "restos a pagar (tentativa 1)"),
            ("/consultas/despesas/restosapagar.aspx", "restos a pagar (tentativa 2)"),
            ("/consultas/despesas/subvencoes.aspx", "subvencoes"),
            ("/consultas/despesas/liquidacoes.aspx", "liquidacoes"),
            ("/consultas/despesas/pagamentos.aspx", "pagamentos"),
            ("/consultas/compras/licitacoes.aspx", "licitacoes (ja uso)"),
            ("/consultas/compras/contratos.aspx", "contratos (ja uso)"),
            ("/consultas/compras/dispensas.aspx", "dispensas (suspeita)"),
            ("/consultas/compras/inexigibilidades.aspx", "inexigibilidades (tentativa)"),
            ("/consultas/compras/dispensas_inexigibilidades.aspx", "dispensas+inex (tentativa)"),
            ("/consultas/compras/atas.aspx", "atas de registro de preco"),
            ("/consultas/compras/ordens.aspx", "ordens de compra"),
            ("/consultas/repasses.aspx", "repasses"),
            ("/consultas/receitas.aspx", "receitas (overview)"),
        ]
        validas = []
        for url, label in candidatas:
            res = testar_url(page, url, label)
            if res.get("consulta_valida"):
                print(f"  [OK] {url}  ({label})")
                validas.append(url)
            elif res.get("status") == 200:
                print(f"  [200 mas sem form] {url}  ({label})")
            else:
                print(f"  [-]   {url}  ({label}): {res.get('status') or res.get('erro')}")

        b.close()
        print(f"\n{len(validas)} URLs validas com formulario de consulta.")


if __name__ == "__main__":
    main()
