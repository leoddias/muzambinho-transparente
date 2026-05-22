"""Coleta restos a pagar - despesas dos anos anteriores ainda nao pagas.

Fonte: /consultas/despesas/restospagar.aspx

Indicador-chave de saude fiscal: quanto da despesa atual e pra pagar conta
antiga. Se restos a pagar acumularem muito, vira bola de neve.
"""
from __future__ import annotations
from datetime import date

from _portaltp import (
    navegador, abrir_consulta, preencher_periodo_datas, aplicar_filtro,
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, parse_data_brl,
    normaliza_doc, fmt_doc, escreve_csv, DATA, RAW,
)

ANO = 2026
# Restos a pagar = empenhos de exercicios ANTERIORES ainda pendentes.
# Periodo coincide com o ano atual (eles foram inscritos no anterior mas estão
# em execucao agora). Periodo curto pra acelerar o export.
DATA_INI = f"01/01/{ANO}"
DATA_FIM = date.today().strftime("%d/%m/%Y") if date.today().year == ANO else f"31/12/{ANO}"
PATH = "/consultas/despesas/restospagar.aspx"


def main():
    print(f"Coletando restos a pagar {DATA_INI} - {DATA_FIM}")
    raw = RAW / f"restos_pagar_{ANO}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH)
        preencher_periodo_datas(page, DATA_INI, DATA_FIM)
        aplicar_filtro(page)
        # Endpoint demora muito para gerar XML/CSV (293 itens travam o servidor).
        # Tenta XML primeiro com timeout alto; se falhar, tenta CSV.
        try:
            baixar_export(page, raw, formato="xml", timeout_ms=300000)
        except Exception as e:
            print(f"  XML falhou ({type(e).__name__}), tentando CSV...")
            raw_csv = RAW / f"restos_pagar_{ANO}.csv"
            from _portaltp import baixar_export as bex
            bex(page, raw_csv, formato="csv", timeout_ms=300000)
            print(f"  CSV: {raw_csv.name} ({raw_csv.stat().st_size:,} bytes)")
            # Por ora deixamos como pendente de parser CSV - retornamos sem rows
            print(f"  ATENCAO: parser CSV de restos a pagar nao implementado ainda")
            print(f"  Tente rodar este script novamente em horario de menor carga.")
            return
        print(f"  Download: {raw.name} ({raw.stat().st_size:,} bytes)")

    rows = ler_xml_grid(raw)
    print(f"  XML parseado: {len(rows)} restos a pagar")
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
        valor_inscrito = to_float_brl(pick(r, "Valor Inscrito", "Valor", "Valor Total"))
        valor_liquidado = to_float_brl(pick(r, "Valor Liquidado", "Liquidado"))
        valor_pago = to_float_brl(pick(r, "Valor Pago", "Pago"))
        valor_cancelado = to_float_brl(pick(r, "Valor Cancelado", "Cancelado"))
        valor_saldo = to_float_brl(pick(r, "Saldo", "Saldo a Pagar", "Valor Saldo"))
        doc_raw = pick(r, "CPF/CNPJ", "CPF", "CNPJ")
        doc_digitos = normaliza_doc(doc_raw)
        normalizados.append({
            "Data": parse_data_brl(pick(r, "Data", "Data Emissão", "Data Inscrição")),
            "Empenho": pick(r, "Empenho", "Número Empenho", "Nota Empenho"),
            "Exercicio": pick(r, "Exercício", "Exercicio", "Ano"),
            "Favorecido": pick(r, "Favorecido", "Credor", "Beneficiário"),
            "CPF/CNPJ": fmt_doc(doc_digitos) if doc_digitos else doc_raw,
            "_doc": doc_digitos,
            "Tipo": pick(r, "Tipo", "Tipo Restos", "Categoria"),
            "Historico": pick(r, "Histórico", "Descrição"),
            "Funcao": pick(r, "Função"),
            "Elemento": pick(r, "Elemento da Despesa", "Elemento Despesa"),
            "Valor Inscrito": fmt_brl(valor_inscrito),
            "_inscrito": valor_inscrito,
            "Valor Liquidado": fmt_brl(valor_liquidado),
            "_liquidado": valor_liquidado,
            "Valor Pago": fmt_brl(valor_pago),
            "_pago": valor_pago,
            "Valor Cancelado": fmt_brl(valor_cancelado),
            "_cancelado": valor_cancelado,
            "Saldo": fmt_brl(valor_saldo),
            "_saldo": valor_saldo,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "restos_pagar_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total_inscrito = sum(r["_inscrito"] for r in normalizados)
    total_pago = sum(r["_pago"] for r in normalizados)
    total_saldo = sum(r["_saldo"] for r in normalizados)
    print(f"\n  Inscrito: {fmt_brl(total_inscrito)}  Pago: {fmt_brl(total_pago)}  Saldo: {fmt_brl(total_saldo)}")


if __name__ == "__main__":
    main()
