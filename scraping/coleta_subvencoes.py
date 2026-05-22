"""Coleta subvencoes e auxilios concedidos pela Prefeitura.

Fonte: /consultas/despesas/subvencoes.aspx

Subvencoes sao repasses a entidades do terceiro setor (ONGs, igrejas,
associacoes, hospitais filantropicos). Quem recebe dinheiro publico
sem ser fornecedor de produto/servico.
"""
from __future__ import annotations
from datetime import date

from _portaltp import (
    navegador, abrir_consulta, preencher_ano, preencher_mes, aplicar_filtro,
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, parse_data_brl,
    normaliza_doc, fmt_doc, escreve_csv, DATA, RAW,
)

ANO = 2026
PATH = "/consultas/despesas/subvencoes.aspx"


def main():
    print(f"Coletando subvencoes - {ANO}")
    raw = RAW / f"subvencoes_{ANO}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH)
        preencher_ano(page, ANO)
        preencher_mes(page, "")
        aplicar_filtro(page)
        baixar_export(page, raw, formato="xml")
        print(f"  Download: {raw.name} ({raw.stat().st_size:,} bytes)")

    rows = ler_xml_grid(raw)
    print(f"  XML parseado: {len(rows)} subvencoes")
    if not rows:
        return
    print(f"  Campos: {list(rows[0].keys())}")

    def pick(d, *keys):
        for k in keys:
            if k in d and d[k]:
                return d[k]
        return ""

    normalizados = []
    for r in rows:
        valor = to_float_brl(pick(r, "Valor"))
        doc_raw = pick(r, "CPF/CNPJ", "CNPJ")
        doc_digitos = normaliza_doc(doc_raw)
        normalizados.append({
            "Data": parse_data_brl(pick(r, "Data", "Data Concessão")),
            "Processo": pick(r, "Processo"),
            "Beneficiario": pick(r, "Favorecido", "Beneficiário"),
            "CPF/CNPJ": fmt_doc(doc_digitos) if doc_digitos else doc_raw,
            "_doc": doc_digitos,
            "Historico": pick(r, "Histórico", "Descrição"),
            "Pagamento": pick(r, "Pagamento"),
            "Valor": fmt_brl(valor),
            "_valor": valor,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "subvencoes_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total = sum(r["_valor"] for r in normalizados)
    print(f"\n  Total em subvencoes: {fmt_brl(total)} ({len(normalizados)} concessoes)")


if __name__ == "__main__":
    main()
