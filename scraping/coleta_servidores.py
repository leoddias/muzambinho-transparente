"""Coleta cadastro de servidores do PortalTP de Muzambinho.

Fonte: https://muzambinho-mg.portaltp.com.br/consultas/pessoal/servidores.aspx

ATENCAO sobre dados disponiveis:
  - O PortalTP NAO expoe remuneracao bruta/liquida individual por servidor
    nesta consulta. So expoe "Valor Nivel Salarial" (salario base de referencia
    do nivel do cargo - sem gratificacoes, horas extras, descontos).
  - CPF vem mascarado por LGPD (***.123.456-**). A Matricula eh a chave unica.
  - O ranking de "maiores salarios" portanto usa o salario base de referencia,
    nao a remuneracao real. Isso eh documentado no site para nao induzir o leitor.

Gera:
  data/_raw/servidores_{ano}_{mes}.xml
  data/servidores_completo.csv
  data/servidores_top20.csv
"""
from __future__ import annotations
from datetime import date

from _portaltp import (
    navegador, abrir_consulta, preencher_ano, preencher_mes, aplicar_filtro,
    baixar_export, ler_xml_grid, to_float_brl, fmt_brl, parse_data_brl,
    escreve_csv, DATA, RAW,
)

ANO = 2026
hoje = date.today()
MES_NUM = (hoje.month - 1) if hoje.year == ANO and hoje.month > 1 else 12
MESES = ["", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MES_NOME = MESES[MES_NUM]

PATH_CONSULTA = "/consultas/pessoal/servidores.aspx"


def main() -> None:
    print(f"Coletando servidores - {MES_NOME}/{ANO}")
    raw_xml = RAW / f"servidores_{ANO}_{MES_NUM:02d}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH_CONSULTA)
        preencher_ano(page, ANO)
        preencher_mes(page, MES_NOME)
        aplicar_filtro(page)
        dl = baixar_export(page, raw_xml, formato="xml")
        print(f"  Download: {dl.suggested_filename} -> {raw_xml.name} ({raw_xml.stat().st_size} bytes)")

    rows_xml = ler_xml_grid(raw_xml)
    print(f"  XML parseado: {len(rows_xml)} servidores")
    if not rows_xml:
        return

    normalizados = []
    for r in rows_xml:
        salario_base = to_float_brl(r.get("Valor Nível Salarial", ""))
        normalizados.append({
            "Matricula": r.get("Matrícula", ""),
            "Nome": r.get("Nome", ""),
            "CPF": r.get("CPF", ""),  # mascarado
            "Cargo": r.get("Cargo", ""),
            "Lotacao": r.get("Lotação", ""),
            "Vinculo": r.get("Vínculo", ""),
            "Situacao": r.get("Situação Funcional", ""),
            "Admissao": parse_data_brl(r.get("Admissão", "")),
            "Carga Horaria": r.get("Carga Horária Mensal", ""),
            "Salario Base": fmt_brl(salario_base),
            "_salario_base": salario_base,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "servidores_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV completo: {completo.name} ({len(normalizados)} linhas)")

    # Top 20 por salario base de referencia (descartar zerados e licenças sem vencimento)
    com_valor = [r for r in normalizados if r["_salario_base"] > 0]
    top20 = sorted(com_valor, key=lambda r: -r["_salario_base"])[:20]
    for i, r in enumerate(top20, 1):
        r["Rank"] = i
    if top20:
        cols_top = ["Rank"] + cols
        top_path = DATA / "servidores_top20.csv"
        escreve_csv(top_path, top20, cols_top)
        print(f"  CSV top 20: {top_path.name}")

    total_base = sum(r["_salario_base"] for r in normalizados)
    ativos = sum(1 for r in normalizados if r["Situacao"] == "Ativo")
    print(f"\n  Total salarios base: {fmt_brl(total_base)}")
    print(f"  Servidores ativos:   {ativos}/{len(normalizados)}")


if __name__ == "__main__":
    main()
