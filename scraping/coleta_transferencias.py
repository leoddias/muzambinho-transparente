"""Coleta transferencias/convenios RECEBIDOS pela Prefeitura.

Fonte: /consultas/repasses/conveniosrecebidos.aspx

Cidades pequenas dependem fortemente de transferencias da União (FPM, FUNDEB,
SUS, FNDE) e do Estado (ICMS, IPVA). Este dataset mostra quem está mandando
dinheiro pra Prefeitura e quanto.
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
PATH = "/consultas/repasses/conveniosrecebidos.aspx"


def main():
    print(f"Coletando transferencias recebidas {DATA_INI} - {DATA_FIM}")
    raw = RAW / f"transferencias_{ANO}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH)
        preencher_periodo_datas(page, DATA_INI, DATA_FIM)
        aplicar_filtro(page)
        baixar_export(page, raw, formato="xml")
        print(f"  Download: {raw.name} ({raw.stat().st_size:,} bytes)")

    rows = ler_xml_grid(raw)
    print(f"  XML parseado: {len(rows)} transferencias")
    if not rows:
        return
    print(f"  Campos: {list(rows[0].keys())}")

    # Sera ajustado depois de ver os campos reais
    def pick(d, *keys):
        for k in keys:
            if k in d and d[k]:
                return d[k]
        return ""

    from _portaltp import normaliza_doc, fmt_doc
    normalizados = []
    for r in rows:
        valor = to_float_brl(r.get("Valor a Receber", ""))
        contrap = to_float_brl(r.get("Valor Contrapartida", ""))
        doc_raw = r.get("CNPJ", "")
        doc_digitos = normaliza_doc(doc_raw)
        normalizados.append({
            "Data": parse_data_brl(r.get("Data", "")),
            "Concedente": r.get("Concedente", ""),
            "Beneficiario": r.get("Beneficiário", ""),
            "CNPJ Beneficiario": fmt_doc(doc_digitos) if doc_digitos else doc_raw,
            "_doc": doc_digitos,
            "Objeto": r.get("Objeto", ""),
            "Vigencia Inicial": parse_data_brl(r.get("Vigência Inicial", "")),
            "Vigencia Final": parse_data_brl(r.get("Vigência Final", "")),
            "Valor a Receber": fmt_brl(valor),
            "_valor": valor,
            "Valor Contrapartida": fmt_brl(contrap),
            "_contrapartida": contrap,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "transferencias_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total = sum(r["_valor"] for r in normalizados)
    print(f"\n  Total recebido em transferencias: {fmt_brl(total)}")


if __name__ == "__main__":
    main()
