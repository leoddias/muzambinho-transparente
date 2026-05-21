"""Converte os CSVs em data/*.csv para JSONs prontos para embutir no index.html.

Gera em data/site/:
  credores_top50.json   - top 50 fornecedores agregados (CREDORES_DATA)
  empenhos_top50.json   - top 50 empenhos individuais
  servidores_top20.json - top 20 servidores por salario base
  diarias.json          - todas as diarias do ano
  licitacoes.json       - licitacoes + contratos combinados
  kpis.json             - totais para a stats bar

Estes JSONs sao embutidos como literais JS no index.html.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
SITE = DATA / "site"


def ler_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(s: str) -> float:
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def to_int(s: str) -> int:
    try:
        return int(s) if s else 0
    except ValueError:
        return 0


def gera_credores() -> tuple[list[dict], float]:
    rows = ler_csv(DATA / "credores_top50.csv")
    out = []
    for r in rows:
        out.append({
            "rank": to_int(r["Rank"]),
            "favorecido": r["Favorecido"],
            "cnpj": r["CPF/CNPJ"],
            "empenhos": to_int(r["Empenhos"]),
            "anulacoes": to_int(r["Anulacoes"]),
            "valor": r["Valor Liquido"],
            "valor_num": to_float(r["_valor"]),
            "valor_bruto": r["Valor Bruto"],
            "valor_bruto_num": to_float(r["_valor_bruto"]),
        })
    max_val = max((c["valor_num"] for c in out), default=1.0)
    return out, max_val


def gera_empenhos() -> tuple[list[dict], float]:
    rows = ler_csv(DATA / "empenhos_top50.csv")
    out = []
    for r in rows:
        out.append({
            "rank": to_int(r["Rank"]),
            "data": r["Data"],
            "empenho": r["Empenho"],
            "processo": r["Processo"],
            "favorecido": r["Favorecido"],
            "cnpj": r["CPF/CNPJ"],
            "valor": r["Valor"],
            "valor_num": to_float(r["_valor"]),
            "historico": r["Historico"],
            "funcao": r["Funcao"],
            "subfuncao": r["Subfuncao"],
            "categoria": r["Grupo Natureza"],
            "elemento": r["Elemento Despesa"],
            "fonte": r["Fonte Recurso"],
        })
    max_val = max((e["valor_num"] for e in out), default=1.0)
    return out, max_val


def gera_servidores() -> list[dict]:
    rows = ler_csv(DATA / "servidores_top20.csv")
    return [{
        "rank": to_int(r["Rank"]),
        "nome": r["Nome"],
        "matricula": r["Matricula"],
        "cargo": r["Cargo"],
        "lotacao": r["Lotacao"],
        "vinculo": r["Vinculo"],
        "situacao": r["Situacao"],
        "admissao": r["Admissao"],
        "carga_horaria": r["Carga Horaria"],
        "salario_base": r["Salario Base"],
        "salario_base_num": to_float(r["_salario_base"]),
    } for r in rows]


def gera_diarias() -> list[dict]:
    rows = ler_csv(DATA / "diarias_completo.csv")
    return [{
        "data": r["Data"],
        "beneficiario": r["Beneficiario"],
        "matricula": r["Matricula"],
        "cpf": r["CPF"],
        "cargo": r["Cargo"],
        "motivo": r["Motivo"],
        "valor": r["Valor"],
        "valor_num": to_float(r["_valor"]),
    } for r in rows]


def gera_licitacoes() -> dict:
    licitacoes = ler_csv(DATA / "licitacoes_completo.csv")
    contratos = ler_csv(DATA / "contratos_completo.csv")
    return {
        "licitacoes": [{
            "data": r["Data Abertura"],
            "numero": r["Numero"],
            "modalidade": r["Modalidade"],
            "processo": r["Processo"],
            "objeto": r["Objeto"],
            "situacao": r["Situacao"],
            "valor_estimado": r["Valor Estimado"],
            "valor_estimado_num": to_float(r["_valor_estimado"]),
            "valor_final": r["Valor Final"],
            "valor_final_num": to_float(r["_valor_final"]),
        } for r in licitacoes],
        "contratos": [{
            "assinatura": r["Assinatura"],
            "contrato": r["Contrato"],
            "processo": r["Processo"],
            "contratado": r["Contratado"],
            "cnpj": r["CPF/CNPJ"],
            "categoria": r["Categoria"],
            "objeto": r["Objeto"],
            "situacao": r["Situacao"],
            "valor": r["Valor"],
            "valor_num": to_float(r["_valor"]),
        } for r in contratos],
    }


def gera_kpis() -> dict:
    # Totais a partir dos completos (nao truncados)
    empenhos_all = ler_csv(DATA / "empenhos_completo.csv")
    total_empenhado = sum(to_float(r["_valor"]) for r in empenhos_all if to_float(r["_valor"]) > 0)

    credores_all = ler_csv(DATA / "credores_completo.csv")
    total_credores = len(credores_all)

    servidores_all = ler_csv(DATA / "servidores_completo.csv")
    folha_base = sum(to_float(r["_salario_base"]) for r in servidores_all)
    ativos = sum(1 for r in servidores_all if r["Situacao"] == "Ativo")

    diarias_all = ler_csv(DATA / "diarias_completo.csv")
    total_diarias = sum(to_float(r["_valor"]) for r in diarias_all)

    contratos_all = ler_csv(DATA / "contratos_completo.csv")
    total_contratos = sum(to_float(r["_valor"]) for r in contratos_all)
    licitacoes_all = ler_csv(DATA / "licitacoes_completo.csv")

    return {
        "total_empenhado": total_empenhado,
        "total_empenhos": len(empenhos_all),
        "total_credores": total_credores,
        "folha_base_mensal": folha_base,
        "total_servidores": len(servidores_all),
        "servidores_ativos": ativos,
        "total_diarias": total_diarias,
        "qtd_diarias": len(diarias_all),
        "total_contratos": total_contratos,
        "qtd_contratos": len(contratos_all),
        "qtd_licitacoes": len(licitacoes_all),
    }


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)

    credores, max_credor = gera_credores()
    empenhos, max_empenho = gera_empenhos()
    servidores = gera_servidores()
    diarias = gera_diarias()
    licitacoes = gera_licitacoes()
    kpis = gera_kpis()

    def save(name: str, obj) -> None:
        path = SITE / f"{name}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  {path.name}: {path.stat().st_size:>7d} bytes")

    save("credores_top50", credores)
    save("empenhos_top50", empenhos)
    save("servidores_top20", servidores)
    save("diarias", diarias)
    save("licitacoes", licitacoes)
    save("kpis", {**kpis, "max_credor": max_credor, "max_empenho": max_empenho})

    print(f"\n  KPIs:")
    print(f"    Empenhado total: R$ {kpis['total_empenhado']:,.2f}")
    print(f"    Credores: {kpis['total_credores']}")
    print(f"    Folha (base, mensal): R$ {kpis['folha_base_mensal']:,.2f}")
    print(f"    Servidores ativos: {kpis['servidores_ativos']}/{kpis['total_servidores']}")
    print(f"    Contratos vigentes: {kpis['qtd_contratos']} (R$ {kpis['total_contratos']:,.2f})")


if __name__ == "__main__":
    main()
