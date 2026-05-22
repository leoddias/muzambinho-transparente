"""Coleta cargos comissionados (cargos de confianca) do PortalTP.

Fonte: /consultas/pessoal/cargosconfianca.aspx

Lista quem ocupa cargos de confianca (livre nomeacao do prefeito) - o
chamado "cabide de empregos". Tema sensivel de transparencia: cidadao
deve poder conferir quem ocupa esses cargos, qual cargo, qual sec, qual
salário.
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
PATH = "/consultas/pessoal/cargosconfianca.aspx"


def main():
    print(f"Coletando cargos comissionados - {MES_NOME}/{ANO}")
    raw = RAW / f"comissionados_{ANO}_{MES_NUM:02d}.xml"

    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH)
        preencher_ano(page, ANO)
        preencher_mes(page, MES_NOME)
        aplicar_filtro(page)
        baixar_export(page, raw, formato="xml")
        print(f"  Download: {raw.name} ({raw.stat().st_size:,} bytes)")

    rows = ler_xml_grid(raw)
    print(f"  XML parseado: {len(rows)} comissionados")
    if not rows:
        return
    print(f"  Campos: {list(rows[0].keys())}")

    # Este endpoint nao traz salario - vamos cruzar com servidores_completo.csv
    # via Matricula para enriquecer com salario base, cargo, lotacao, vinculo.
    import csv as csv_mod
    srv_map = {}
    srv_csv = DATA / "servidores_completo.csv"
    if srv_csv.exists():
        with srv_csv.open(encoding="utf-8-sig", newline="") as f:
            for s in csv_mod.DictReader(f):
                srv_map[s["Matricula"]] = s
        print(f"  Cruzando com {len(srv_map)} servidores de servidores_completo.csv")

    normalizados = []
    for r in rows:
        mat = r.get("Matrícula", "")
        s = srv_map.get(mat, {})
        salario = to_float_brl(s.get("_salario_base", "0"))
        normalizados.append({
            "Matricula": mat,
            "Nome": r.get("Nome do Servidor", "") or s.get("Nome", ""),
            "CPF": r.get("CPF", "") or s.get("CPF", ""),
            "Cargo": r.get("Cargo", "") or s.get("Cargo", ""),
            "Lotacao": s.get("Lotacao", ""),  # so do cadastro
            "Situacao": r.get("Situação", "") or s.get("Situacao", ""),
            "Admissao": parse_data_brl(r.get("Admissão", "")) or s.get("Admissao", ""),
            "Demissao": parse_data_brl(r.get("Demissão", "")),
            "Carga Horaria": s.get("Carga Horaria", ""),
            "Salario Base": fmt_brl(salario),
            "_salario": salario,
        })

    cols = list(normalizados[0].keys())
    completo = DATA / "comissionados_completo.csv"
    escreve_csv(completo, normalizados, cols)
    print(f"  CSV: {completo.name}")

    total = sum(r["_salario"] for r in normalizados)
    print(f"\n  Total comissionados: {len(normalizados)}")
    print(f"  Custo mensal salarios base: {fmt_brl(total)}")


if __name__ == "__main__":
    main()
