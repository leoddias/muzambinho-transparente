"""Coleta empenhos individuais do PortalTP de Muzambinho.

Fonte: https://muzambinho-mg.portaltp.com.br/consultas/despesas/empenhos.aspx
Periodo: 01/01/2026 ate hoje (configuravel abaixo)

Gera:
  data/_raw/empenhos_2026.xml          (export bruto do PortalTP)
  data/empenhos_completo.csv           (normalizado, UTF-8-SIG, com _valor float)
  data/empenhos_top50.csv              (top 50 por valor)
"""
from __future__ import annotations
from datetime import date

from _portaltp import (
    navegador, abrir_consulta, preencher_periodo_datas, aplicar_filtro,
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, normaliza_doc,
    fmt_doc, parse_data_brl, escreve_csv, DATA, RAW,
)

ANO = 2026
DATA_INI = f"01/01/{ANO}"
DATA_FIM = date.today().strftime("%d/%m/%Y") if date.today().year == ANO else f"31/12/{ANO}"

PATH_CONSULTA = "/consultas/despesas/empenhos.aspx"


def main() -> None:
    print(f"Coletando empenhos {DATA_INI} - {DATA_FIM}")
    raw_xml = RAW / f"empenhos_{ANO}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH_CONSULTA)
        preencher_periodo_datas(page, DATA_INI, DATA_FIM)
        aplicar_filtro(page)
        dl = baixar_export(page, raw_xml, formato="xml")
        print(f"  Download: {dl.suggested_filename} -> {raw_xml.name} ({raw_xml.stat().st_size} bytes)")

    rows_xml = ler_xml_grid(raw_xml)
    print(f"  XML parseado: {len(rows_xml)} empenhos")

    # Normalizar
    normalizados = []
    for r in rows_xml:
        valor = to_float_brl(r.get("Valor", ""))
        doc_raw = r.get("CPF/CNPJ", "")
        doc_digitos = normaliza_doc(doc_raw)
        normalizados.append({
            "Data": parse_data_brl(r.get("Data", "")),
            "Processo": r.get("Processo", ""),
            "Empenho": r.get("Empenho", ""),
            "Tipo": r.get("Tipo do Empenho", ""),
            "Favorecido": r.get("Favorecido", ""),
            "CPF/CNPJ": fmt_doc(doc_digitos) if doc_digitos else doc_raw,
            "_doc": doc_digitos,
            "Valor": fmt_brl(valor),
            "_valor": valor,
            "Historico": r.get("Histórico", ""),
            "Funcao": r.get("Função", ""),
            "Subfuncao": r.get("Subfunção", ""),
            "Programa": r.get("Programa/Atividade/Ação", ""),
            "Acao": r.get("Ação", ""),
            "Categoria Economica": r.get("Categoria Econômica", ""),
            "Grupo Natureza": r.get("Grupo Natureza da Despesa", ""),
            "Elemento Despesa": r.get("Elemento da Despesa", ""),
            "Fonte Recurso": r.get("Complemento Fonte de Recurso", ""),
        })

    colunas = list(normalizados[0].keys()) if normalizados else []

    completo = DATA / "empenhos_completo.csv"
    escreve_csv(completo, normalizados, colunas)
    print(f"  CSV completo: {completo.name} ({len(normalizados)} linhas)")

    # Top 50 por valor (descartar anulacoes negativas para nao distorcer)
    positivos = [r for r in normalizados if r["_valor"] > 0]
    top50 = sorted(positivos, key=lambda r: -r["_valor"])[:50]
    for i, r in enumerate(top50, 1):
        r["Rank"] = i
    if top50:
        cols_top = ["Rank"] + [c for c in colunas if c != "Rank"]
        top_path = DATA / "empenhos_top50.csv"
        escreve_csv(top_path, top50, cols_top)
        print(f"  CSV top 50: {top_path.name}")

    # Stats
    total = sum(r["_valor"] for r in normalizados if r["_valor"] > 0)
    print(f"\n  Total empenhado (positivos): {fmt_brl(total)}")
    print(f"  Empenhos negativos (anulacoes): {sum(1 for r in normalizados if r['_valor'] < 0)}")


if __name__ == "__main__":
    main()
