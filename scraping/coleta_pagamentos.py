"""Coleta pagamentos efetivos da Prefeitura.

Fonte: /consultas/despesas/pagamentos.aspx

Pagamentos sao o estagio final da despesa: empenho -> liquidacao -> pagamento.
Cruzar com empenhos mostra quanto efetivamente saiu do cofre (vs quanto foi
so prometido).
"""
from __future__ import annotations
from datetime import date

from _portaltp import (
    navegador, abrir_consulta, preencher_periodo_datas, aplicar_filtro,
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, parse_data_brl,
    normaliza_doc, fmt_doc, escreve_csv, DATA, RAW,
)

ANO = 2026
DATA_INI = f"01/01/{ANO}"
DATA_FIM = date.today().strftime("%d/%m/%Y") if date.today().year == ANO else f"31/12/{ANO}"
PATH = "/consultas/despesas/pagamentos.aspx"


def main():
    print(f"Coletando pagamentos {DATA_INI} - {DATA_FIM}")
    raw = RAW / f"pagamentos_{ANO}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH)
        preencher_periodo_datas(page, DATA_INI, DATA_FIM)
        aplicar_filtro(page)
        baixar_export(page, raw, formato="xml")
        print(f"  Download: {raw.name} ({raw.stat().st_size:,} bytes)")

    rows = ler_xml_grid(raw)
    print(f"  XML parseado: {len(rows)} pagamentos")
    if not rows:
        return
    print(f"  Campos: {list(rows[0].keys())}")

    normalizados = []
    for r in rows:
        valor = to_float_brl(r.get("Valor Pagamento", ""))
        valor_emp = to_float_brl(r.get("Valor Empenho", ""))
        valor_liq = to_float_brl(r.get("Valor Liquidação", ""))
        doc_raw = r.get("CPF/CNPJ", "")
        doc_digitos = normaliza_doc(doc_raw)
        normalizados.append({
            "Data": parse_data_brl(r.get("Data do Pagamento", "")),
            "Pagamento": r.get("Pagamento", ""),
            "Empenho": r.get("Empenho", ""),
            "Liquidacao": r.get("Liquidação", ""),
            "Processo": r.get("Processo", ""),
            "Favorecido": r.get("Favorecido", ""),
            "CPF/CNPJ": fmt_doc(doc_digitos) if doc_digitos else doc_raw,
            "_doc": doc_digitos,
            "Tipo": r.get("Tipo do Pagamento", ""),
            "Historico": r.get("Histórico", ""),
            "Funcao": r.get("Função", ""),
            "Elemento": r.get("Elemento da Despesa", ""),
            "Categoria": r.get("Grupo Natureza da Despesa", ""),
            "Valor": fmt_brl(valor),
            "_valor": valor,
            "Valor Empenho": fmt_brl(valor_emp),
            "_valor_empenho": valor_emp,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "pagamentos_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total = sum(r["_valor"] for r in normalizados if r["_valor"] > 0)
    print(f"\n  Total pago: {fmt_brl(total)} em {len(normalizados)} pagamentos")


if __name__ == "__main__":
    main()
