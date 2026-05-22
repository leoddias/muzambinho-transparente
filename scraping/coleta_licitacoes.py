"""Coleta licitacoes, dispensas, contratos e atas de registro de preco.

Fontes (todos /consultas/compras/...):
  - licitacoes.aspx  - processos licitatorios formais
  - dispensas.aspx   - dispensas de licitacao
  - contratos.aspx   - contratos vigentes
  - atas.aspx        - atas de registro de preco

ARMADILHA APRENDIDA: nao basta puxar licitacoes+contratos. As atas de
registro de preco (43 registros em 2026 para Muzambinho) sao compromissos
de compra importantes que ficam num endpoint separado. Em alguns municipios
sao mais frequentes que licitacoes formais.

Gera:
  data/_raw/{categoria}_{ano}.xml para cada uma das 4 categorias
  data/{categoria}_completo.csv para cada uma
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


def coleta_dispensas(page) -> None:
    print(f"\nColetando dispensas - {ANO}")
    raw_xml = RAW / f"dispensas_{ANO}.xml"

    abrir_consulta(page, "/consultas/compras/dispensas.aspx")
    preencher_ano(page, ANO)
    preencher_mes(page, "")
    aplicar_filtro(page)
    dl = baixar_export(page, raw_xml, formato="xml")
    print(f"  Download: {dl.suggested_filename} -> {raw_xml.name} ({raw_xml.stat().st_size} bytes)")

    rows_xml = ler_xml_grid(raw_xml)
    print(f"  XML parseado: {len(rows_xml)} dispensas")
    if not rows_xml:
        return
    print(f"  Campos: {list(rows_xml[0].keys())}")

    normalizados = []
    for r in rows_xml:
        valor_est = to_float_brl(r.get("Valor Estimado", ""))
        valor_final = to_float_brl(r.get("Valor Final", "")) or to_float_brl(r.get("Valor Contrato", ""))
        normalizados.append({
            "Data Abertura": parse_data_brl(r.get("Abertura", r.get("Data", ""))),
            "Numero": r.get("Número", r.get("Numero", "")),
            "Ano": r.get("Ano", str(ANO)),
            "Modalidade": r.get("Modalidade", "Dispensa"),
            "Processo": r.get("Processo", ""),
            "Objeto": r.get("Objeto", ""),
            "Base Legal": r.get("Base Legal", ""),
            "Situacao": r.get("Situação", ""),
            "Valor Estimado": fmt_brl(valor_est),
            "_valor_estimado": valor_est,
            "Valor Final": fmt_brl(valor_final),
            "_valor_final": valor_final,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "dispensas_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total = sum(r["_valor_final"] or r["_valor_estimado"] for r in normalizados)
    print(f"  Valor total: {fmt_brl(total)}")


def coleta_atas(page) -> None:
    print(f"\nColetando atas de registro de preco - {ANO}")
    raw_xml = RAW / f"atas_{ANO}.xml"

    abrir_consulta(page, "/consultas/compras/atas.aspx")
    preencher_ano(page, ANO)
    preencher_mes(page, "")
    aplicar_filtro(page)
    dl = baixar_export(page, raw_xml, formato="xml")
    print(f"  Download: {dl.suggested_filename} -> {raw_xml.name} ({raw_xml.stat().st_size} bytes)")

    rows_xml = ler_xml_grid(raw_xml)
    print(f"  XML parseado: {len(rows_xml)} atas")
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
            "Ata": r.get("Contrato", r.get("Numero", "")),  # PortalTP usa "Contrato" como label da ata
            "Ano": r.get("Ano", str(ANO)),
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
    completo = DATA / "atas_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total = sum(r["_valor"] for r in normalizados)
    print(f"  Valor total das atas: {fmt_brl(total)}")


def main() -> None:
    with navegador(headless=True) as (browser, ctx, page):
        coleta_licitacoes(page)
        coleta_dispensas(page)
        coleta_contratos(page)
        coleta_atas(page)


if __name__ == "__main__":
    main()
