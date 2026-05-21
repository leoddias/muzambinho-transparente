"""Coleta licitacoes e contratos do PortalTP de Muzambinho.

Fonte:
  https://muzambinho-mg.portaltp.com.br/consultas/compras/licitacoes.aspx
  https://muzambinho-mg.portaltp.com.br/consultas/compras/contratos.aspx

Usa filtro ano + mes vazio. Coleta os dois em sequencia.

Gera:
  data/_raw/licitacoes_{ano}.xml
  data/_raw/contratos_{ano}.xml
  data/licitacoes_completo.csv
  data/contratos_completo.csv
"""
from __future__ import annotations

from _portaltp import (
    navegador, abrir_consulta, preencher_ano, preencher_mes, aplicar_filtro,
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, parse_data_brl,
    escreve_csv, DATA, RAW,
)

ANO = 2026


def pick(d: dict, *keys: str) -> str:
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return ""


def coleta_licitacoes(page) -> None:
    print(f"Coletando licitacoes - {ANO}")
    raw_xml = RAW / f"licitacoes_{ANO}.xml"

    abrir_consulta(page, "/consultas/compras/licitacoes.aspx")
    preencher_ano(page, ANO)
    preencher_mes(page, "")
    aplicar_filtro(page)
    dl = baixar_export(page, raw_xml, formato="xml")
    print(f"  Download: {dl.suggested_filename} -> {raw_xml.name} ({raw_xml.stat().st_size} bytes)")

    rows_xml = ler_xml_grid(raw_xml)
    print(f"  XML parseado: {len(rows_xml)} licitacoes")
    if not rows_xml:
        return
    print(f"  Campos: {list(rows_xml[0].keys())}")

    normalizados = []
    for r in rows_xml:
        valor_est = to_float_brl(r.get("Valor Estimado", ""))
        valor_final = to_float_brl(r.get("Valor Final", ""))
        normalizados.append({
            "Data Abertura": parse_data_brl(r.get("Abertura", "")),
            "Numero": r.get("Número da Licitação", ""),
            "Modalidade": r.get("Modalidade Licitatória", ""),
            "Processo": r.get("Processo", ""),
            "Objeto": r.get("Objeto", ""),
            "Situacao": r.get("Situação", ""),
            "Valor Estimado": fmt_brl(valor_est),
            "_valor_estimado": valor_est,
            "Valor Final": fmt_brl(valor_final),
            "_valor_final": valor_final,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "licitacoes_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total_est = sum(r["_valor_estimado"] for r in normalizados)
    total_final = sum(r["_valor_final"] for r in normalizados)
    print(f"  Total estimado: {fmt_brl(total_est)} | Total final: {fmt_brl(total_final)}")


def coleta_contratos(page) -> None:
    print(f"\nColetando contratos - {ANO}")
    raw_xml = RAW / f"contratos_{ANO}.xml"

    abrir_consulta(page, "/consultas/compras/contratos.aspx")
    preencher_ano(page, ANO)
    preencher_mes(page, "")
    aplicar_filtro(page)
    dl = baixar_export(page, raw_xml, formato="xml")
    print(f"  Download: {dl.suggested_filename} -> {raw_xml.name} ({raw_xml.stat().st_size} bytes)")

    rows_xml = ler_xml_grid(raw_xml)
    print(f"  XML parseado: {len(rows_xml)} contratos")
    if not rows_xml:
        return
    print(f"  Campos: {list(rows_xml[0].keys())}")

    from _portaltp import normaliza_doc, fmt_doc
    normalizados = []
    for r in rows_xml:
        valor = to_float_brl(r.get("Valor", ""))
        doc_raw = r.get("CPF/CNPJ", "")
        doc_digitos = normaliza_doc(doc_raw)
        normalizados.append({
            "Assinatura": parse_data_brl(r.get("Assinatura", "")),
            "Contrato": r.get("Contrato", ""),
            "Processo": r.get("Processo", ""),
            "Contratado": r.get("Favorecido", ""),
            "CPF/CNPJ": fmt_doc(doc_digitos) if doc_digitos else doc_raw,
            "_doc": doc_digitos,
            "Categoria": r.get("Categoria", ""),
            "Objeto": r.get("Objeto", ""),
            "Situacao": r.get("Situação", ""),
            "Valor": fmt_brl(valor),
            "_valor": valor,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "contratos_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total = sum(r["_valor"] for r in normalizados)
    print(f"  Valor total contratado: {fmt_brl(total)}")


def main() -> None:
    with navegador(headless=True) as (browser, ctx, page):
        coleta_licitacoes(page)
        coleta_contratos(page)


if __name__ == "__main__":
    main()
