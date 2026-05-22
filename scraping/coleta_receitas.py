"""Coleta receitas realizadas (arrecadação efetiva) do PortalTP.

Fonte: /consultas/receitas/execucaoreceitas.aspx

Esta categoria é fundamental para o portal: mostra de ONDE vem o dinheiro.
Permite calcular Balança Fiscal (Receita vs Despesa) e quebrar a arrecadação
por origem (tributos próprios vs transferências federais/estaduais).
"""
from __future__ import annotations
from datetime import date

from _portaltp import (
    navegador, abrir_consulta, preencher_periodo_datas, aplicar_filtro,
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, parse_data_brl,
    escreve_csv, DATA, RAW,
)

ANO = 2026
DATA_INI = f"01/01/{ANO}"
DATA_FIM = date.today().strftime("%d/%m/%Y") if date.today().year == ANO else f"31/12/{ANO}"
PATH = "/consultas/receitas/execucaoreceitas.aspx"


def pick(d, *keys):
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return ""


def main():
    print(f"Coletando receitas realizadas {DATA_INI} - {DATA_FIM}")
    raw = RAW / f"receitas_{ANO}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH)
        preencher_periodo_datas(page, DATA_INI, DATA_FIM)
        aplicar_filtro(page)
        dl = baixar_export(page, raw, formato="xml")
        print(f"  Download: {raw.name} ({raw.stat().st_size:,} bytes)")

    rows = ler_xml_grid(raw)
    print(f"  XML parseado: {len(rows)} receitas")
    if not rows:
        return
    print(f"  Campos: {list(rows[0].keys())}")

    normalizados = []
    for r in rows:
        prev = to_float_brl(r.get("Valor Previsto", ""))
        prev_atual = to_float_brl(r.get("Valor Atualizado", ""))
        realizado = to_float_brl(r.get("Valor Realizado", ""))
        normalizados.append({
            "Data": parse_data_brl(r.get("Data", "")),
            "Categoria": r.get("Categoria", ""),
            "Origem": r.get("Origem", ""),
            "Especie": r.get("Espécie", ""),
            "Rubrica": r.get("Rubrica", ""),
            "Alinea": r.get("Alínea", ""),
            "Subalinea": r.get("Subalínea", ""),
            "Plano Conta": r.get("Plano Conta", ""),
            "Tipo": r.get("Tipo da Receita", ""),
            "Valor Previsto": fmt_brl(prev),
            "_previsao": prev,
            "Valor Atualizado": fmt_brl(prev_atual),
            "_atualizado": prev_atual,
            "Valor Realizado": fmt_brl(realizado),
            "_realizado": realizado,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "receitas_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total_prev = sum(r["_previsao"] for r in normalizados)
    total_atual = sum(r["_atualizado"] for r in normalizados)
    total_real = sum(r["_realizado"] for r in normalizados)
    print(f"\n  Previsto inicial:  {fmt_brl(total_prev)}")
    print(f"  Previsao atualiz:  {fmt_brl(total_atual)}")
    print(f"  Realizado:         {fmt_brl(total_real)}")
    if total_atual > 0:
        print(f"  Execucao:          {total_real/total_atual*100:.1f}% da previsao atualizada")


if __name__ == "__main__":
    main()
