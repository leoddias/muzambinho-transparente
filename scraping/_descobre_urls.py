"""Descobre URLs reais dos endpoints de consulta web para os 8 datasets novos.

Tenta varios paths e reporta quais retornam form de consulta (com btnAplicFiltro).
"""
from playwright.sync_api import sync_playwright

BASE = "https://muzambinho-mg.portaltp.com.br"

# Candidatos para cada dataset - testaremos varios paths
CANDIDATOS = {
    "receitas": [
        "/consultas/receitas.aspx",
        "/consultas/receitas/execucaoreceitas.aspx",
        "/consultas/receitas/receita_realizada.aspx",
        "/consultas/receitas/receitas.aspx",
        "/consultas/receita.aspx",
    ],
    "transferencias_recebidas": [
        "/consultas/repasses/recebidos.aspx",
        "/consultas/repasses/conveniosrecebidos.aspx",
        "/consultas/repasses/transferencias_recebidas.aspx",
        "/consultas/repasses/recebidas.aspx",
    ],
    "transferencias_cedidas": [
        "/consultas/repasses/firmados.aspx",
        "/consultas/repasses/conveniosfirmados.aspx",
        "/consultas/repasses/cedidas.aspx",
    ],
    "restos_pagar": [
        "/consultas/despesas/restospagar.aspx",
        "/consultas/despesas/restos_pagar.aspx",
        "/consultas/despesas/restosapagar.aspx",
    ],
    "comissionados": [
        "/consultas/pessoal/cargosconfianca.aspx",
        "/consultas/pessoal/comissionados.aspx",
        "/consultas/pessoal/cargos_confianca.aspx",
        "/consultas/pessoal/cargosvagas.aspx",
    ],
    "subvencoes": [
        "/consultas/despesas/subvencoes.aspx",
    ],
    "pagamentos": [
        "/consultas/despesas/pagamentos.aspx",
    ],
    "frota": [
        "/consultas/frota/veiculos.aspx",
        "/consultas/materiais/frota.aspx",
        "/consultas/frota.aspx",
        "/consultas/bens/frota.aspx",
    ],
    "imoveis": [
        "/consultas/bens/imoveis.aspx",
        "/consultas/materiais/imoveis.aspx",
        "/consultas/imoveis.aspx",
    ],
    "estagiarios": [
        "/consultas/pessoal/estagiarios.aspx",
    ],
}


def teste(page, url, label):
    try:
        resp = page.goto(BASE + url, wait_until="networkidle", timeout=15000)
        if resp.status != 200:
            return None
        # Tem o formulario padrao?
        tem_filtro = page.locator("#ctl00_containerCorpo_btnAplicFiltro").count() > 0
        # Detectar campos
        campos = page.evaluate("""
            () => {
                const out = [];
                document.querySelectorAll('input[id*=containerCorpo],select[id*=containerCorpo]').forEach(e => {
                    if (e.id && !e.id.endsWith('_VI') && !e.id.endsWith('_DDD') && !e.id.endsWith('_L_VI')) {
                        const m = e.id.match(/containerCorpo_(\\w+?)(_I)?$/);
                        if (m) out.push(m[1]);
                    }
                });
                return [...new Set(out)];
            }
        """)
        return {"tem_filtro": tem_filtro, "campos": campos}
    except Exception as e:
        return {"erro": str(e)[:80]}


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()

        for label, urls in CANDIDATOS.items():
            print(f"\n=== {label.upper()} ===")
            for url in urls:
                r = teste(page, url, label)
                if r is None:
                    print(f"  [-] {url}  (404)")
                elif "erro" in r:
                    print(f"  [E] {url}  -> {r['erro']}")
                elif r["tem_filtro"]:
                    print(f"  [OK] {url}  campos: {r['campos']}")
                else:
                    print(f"  [200 sem form] {url}")

        b.close()


if __name__ == "__main__":
    main()
