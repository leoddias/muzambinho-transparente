"""Coleta diarias de viagem do PortalTP de Muzambinho.

Fonte: https://muzambinho-mg.portaltp.com.br/consultas/despesas/diarias.aspx

Usa filtros ano + mes vazio (= todos os meses do ano).

Gera:
  data/_raw/diarias_{ano}.xml
  data/diarias_completo.csv
"""
from __future__ import annotations

from _portaltp import (
    navegador, abrir_consulta, preencher_ano, preencher_mes, aplicar_filtro,
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, parse_data_brl,
    escreve_csv, DATA, RAW,
)

ANO = 2026
PATH_CONSULTA = "/consultas/despesas/diarias.aspx"


def pick(d: dict, *keys: str) -> str:
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return ""


def main() -> None:
    print(f"Coletando diarias - {ANO}")
    raw_xml = RAW / f"diarias_{ANO}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH_CONSULTA)
        preencher_ano(page, ANO)
        preencher_mes(page, "")  # todos os meses
        aplicar_filtro(page)
        dl = baixar_export(page, raw_xml, formato="xml")
        print(f"  Download: {dl.suggested_filename} -> {raw_xml.name} ({raw_xml.stat().st_size} bytes)")

    rows_xml = ler_xml_grid(raw_xml)
    print(f"  XML parseado: {len(rows_xml)} diarias")
    if not rows_xml:
        return

    print(f"  Campos do XML: {list(rows_xml[0].keys())}")

    normalizados = []
    for r in rows_xml:
        valor = to_float_brl(pick(r, "Valor", "Valor da Diaria", "Valor Total"))
        doc_raw = pick(r, "CPF/CNPJ", "CPF")
        normalizados.append({
            "Data": parse_data_brl(pick(r, "Data", "Data da Diaria", "Data Emissao")),
            "Processo": pick(r, "Processo"),
            "Beneficiario": pick(r, "Favorecido", "Beneficiario", "Servidor", "Nome"),
            "Matricula": pick(r, "Matrícula", "Matricula"),  # chave unica (CPF vem mascarado LGPD)
            "CPF": doc_raw,  # mascarado pelo portal
            "Cargo": pick(r, "Cargo"),
            "Motivo": pick(r, "Motivo", "Objetivo", "Finalidade", "Histórico"),
            "Base Legal": pick(r, "Base Legal"),
            "Valor": fmt_brl(valor),
            "_valor": valor,
            "Fonte Recurso": pick(r, "Fonte de Recurso", "Complemento Fonte de Recurso"),
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "diarias_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV completo: {completo.name} ({len(normalizados)} linhas)")

    total = sum(r["_valor"] for r in normalizados)
    print(f"\n  Total em diarias {ANO}: {fmt_brl(total)}")


if __name__ == "__main__":
    main()
