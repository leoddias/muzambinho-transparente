"""Conta registros em cada endpoint novo descoberto. Baixa o XML de cada um
com filtro ano=2026, salva em debug/ pra inspecao, e reporta o numero de
<DOCUMENTO> em cada arquivo."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from _portaltp import (
    navegador, abrir_consulta, preencher_ano, preencher_mes, preencher_periodo_datas,
    aplicar_filtro, baixar_export, ler_xml_grid, RAW,
)

ANO = 2026

# (url, filtro_tipo, label) - filtro_tipo: "datas" ou "anomes"
ENDPOINTS = [
    ("/consultas/despesas/empenhos.aspx",     "datas",  "empenhos"),
    ("/consultas/despesas/diarias.aspx",      "anomes", "diarias"),
    ("/consultas/despesas/passagens.aspx",    "anomes", "passagens"),
    ("/consultas/despesas/obras.aspx",        "anomes", "obras"),
    ("/consultas/despesas/subvencoes.aspx",   "anomes", "subvencoes"),
    ("/consultas/despesas/liquidacoes.aspx",  "datas",  "liquidacoes"),
    ("/consultas/despesas/pagamentos.aspx",   "datas",  "pagamentos"),
    ("/consultas/compras/licitacoes.aspx",    "anomes", "licitacoes"),
    ("/consultas/compras/contratos.aspx",     "anomes", "contratos"),
    ("/consultas/compras/dispensas.aspx",     "anomes", "dispensas"),
    ("/consultas/compras/atas.aspx",          "anomes", "atas"),
]


def main():
    from datetime import date
    hoje = date.today().strftime('%d/%m/%Y')
    print(f"Coletando contagem para cada endpoint - {ANO}\n")
    resultados = []
    with navegador(headless=True) as (browser, ctx, page):
        for url, tipo, label in ENDPOINTS:
            print(f"[{label}] {url}")
            try:
                abrir_consulta(page, url)
                if tipo == "datas":
                    preencher_periodo_datas(page, f"01/01/{ANO}", hoje)
                else:
                    preencher_ano(page, ANO)
                    preencher_mes(page, "")
                aplicar_filtro(page)
                dest = RAW / f"contagem_{label}.xml"
                baixar_export(page, dest, formato="xml")
                rows = ler_xml_grid(dest)
                n = len(rows)
                first_keys = list(rows[0].keys()) if rows else []
                tam = dest.stat().st_size
                print(f"  {n} registros  ({tam:,} bytes)")
                if rows:
                    print(f"  campos: {first_keys[:8]}{'...' if len(first_keys) > 8 else ''}")
                resultados.append((label, n, tam, first_keys))
            except Exception as e:
                print(f"  ERRO: {e}")
                resultados.append((label, -1, 0, []))
            print()

    print("=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"{'Endpoint':<20} {'Registros':>10} {'Tamanho XML':>14}")
    print("-" * 60)
    for label, n, tam, _ in resultados:
        marker = ""
        if label in ("diarias", "passagens"): marker = "  [diárias+]"
        elif label in ("licitacoes", "contratos", "dispensas", "atas"): marker = "  [compras]"
        print(f"{label:<20} {n:>10,} {tam:>13,}B{marker}")


if __name__ == "__main__":
    main()
