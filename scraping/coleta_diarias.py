"""Coleta diarias e adiantamentos a servidores.

ARMADILHA APRENDIDA na pratica:
  - O endpoint /consultas/despesas/diarias.aspx do PortalTP de Muzambinho
    retornou apenas 6 registros para 2026 (foram apenas adiantamentos
    formalmente cadastrados sob esse tipo).
  - A classificação contábil oficial "33901400000 - Diarias -Pessoal Civil"
    aparece em 61 empenhos no mesmo período no /consultas/despesas/empenhos.aspx.

  Decidimos por usar a fonte mais completa: filtrar o empenhos_completo.csv
  pelo elemento de despesa "Diarias". O endpoint /diarias.aspx pode ser
  útil em outros municípios; aqui mantemos o download em _raw/ para auditoria,
  mas o CSV final vem dos empenhos.

Gera:
  data/_raw/diarias_endpoint_{ano}.xml  (download bruto - audit trail)
  data/diarias_completo.csv             (extraído dos empenhos por elemento)
"""
from __future__ import annotations
import csv

from _portaltp import (
    navegador, abrir_consulta, preencher_ano, preencher_mes, aplicar_filtro,
    baixar_export, fmt_brl, parse_data_brl, escreve_csv, DATA, RAW,
)

ANO = 2026
PATH_CONSULTA = "/consultas/despesas/diarias.aspx"
EMPENHOS_CSV = DATA / "empenhos_completo.csv"
# Codigo oficial do elemento contabil de Diarias Pessoal Civil
ELEMENTO_DIARIAS = "33901400000"


def baixa_endpoint_audit() -> int:
    """Baixa o XML do endpoint dedicado (para auditoria), retorna count."""
    raw = RAW / f"diarias_endpoint_{ANO}.xml"
    with navegador(headless=True) as (browser, ctx, page):
        abrir_consulta(page, PATH_CONSULTA)
        preencher_ano(page, ANO)
        preencher_mes(page, "")
        aplicar_filtro(page)
        baixar_export(page, raw, formato="xml")
    return raw.stat().st_size


def extrai_dos_empenhos() -> list[dict]:
    """Le empenhos_completo.csv, filtra por Elemento Despesa de Diaria."""
    if not EMPENHOS_CSV.exists():
        raise FileNotFoundError(
            f"{EMPENHOS_CSV} não existe. Rode coleta_empenhos.py primeiro."
        )
    out = []
    with EMPENHOS_CSV.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            elem = r.get("Elemento Despesa", "")
            if ELEMENTO_DIARIAS not in elem:
                continue
            valor = float(r["_valor"] or 0)
            out.append({
                "Data": parse_data_brl(r["Data"]),
                "Empenho": r["Empenho"],
                "Processo": r["Processo"],
                "Beneficiario": r["Favorecido"],
                "CPF/CNPJ": r["CPF/CNPJ"],
                "_doc": r["_doc"],
                "Valor": fmt_brl(valor),
                "_valor": valor,
                "Motivo": r["Historico"],
                "Funcao": r["Funcao"],
                "Subfuncao": r["Subfuncao"],
                "Acao": r["Acao"],
                "Elemento Despesa": elem,
            })
    return out


def main() -> None:
    print(f"Coletando diarias - {ANO}")
    print(f"  1) Download endpoint dedicado (audit trail)...")
    try:
        size = baixa_endpoint_audit()
        print(f"     OK ({size:,} bytes salvos em data/_raw/)")
    except Exception as e:
        print(f"     SKIP (endpoint pode estar fora do ar): {e}")

    print(f"  2) Extraindo de empenhos_completo.csv (elemento {ELEMENTO_DIARIAS})...")
    rows = extrai_dos_empenhos()
    print(f"     {len(rows)} empenhos classificados como diaria")

    cols = list(rows[0].keys()) if rows else []
    completo = DATA / "diarias_completo.csv"
    escreve_csv(completo, rows, cols)
    print(f"  CSV: {completo.name} ({len(rows)} linhas)")

    total = sum(r["_valor"] for r in rows if r["_valor"] > 0)
    devolucoes = sum(-r["_valor"] for r in rows if r["_valor"] < 0)
    print(f"\n  Total empenhado em diarias: {fmt_brl(total)}")
    print(f"  Devolucoes/anulacoes:       {fmt_brl(devolucoes)}")


if __name__ == "__main__":
    main()
