"""Converte os CSVs completos em JSONs para embutir no index.html.

Principio: gera o DATASET COMPLETO de cada categoria (nao trunca para top N).
O site exibe tudo com paginação client-side + busca + filtros que percorrem
o dataset inteiro. O leitor merece ver todo o dado público.

Gera em data/site/:
  credores.json      - todos os ~384 fornecedores agregados
  empenhos.json      - todos os ~2300 empenhos individuais
  servidores.json    - todos os ~825 servidores
  diarias.json       - todas as diárias do ano
  licitacoes.json    - licitacoes + contratos completos
  kpis.json          - totais para a stats bar
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


def gera_credores() -> list[dict]:
    """TODOS os credores (nao só top 50)."""
    rows = ler_csv(DATA / "credores_completo.csv")
    return [{
        "rank": to_int(r["Rank"]),
        "favorecido": r["Favorecido"],
        "cnpj": r["CPF/CNPJ"],
        "empenhos": to_int(r["Empenhos"]),
        "anulacoes": to_int(r["Anulacoes"]),
        "valor": r["Valor Liquido"],
        "valor_num": to_float(r["_valor"]),
        "valor_bruto": r["Valor Bruto"],
        "valor_bruto_num": to_float(r["_valor_bruto"]),
    } for r in rows]


def gera_empenhos() -> list[dict]:
    """TODOS os empenhos do ano (positivos + anulações)."""
    rows = ler_csv(DATA / "empenhos_completo.csv")
    out = []
    for r in rows:
        v = to_float(r["_valor"])
        out.append({
            "data": r["Data"],
            "empenho": r["Empenho"],
            "processo": r["Processo"],
            "favorecido": r["Favorecido"],
            "cnpj": r["CPF/CNPJ"],
            "valor": r["Valor"],
            "valor_num": v,
            "historico": r["Historico"],
            "funcao": r["Funcao"],
            "subfuncao": r["Subfuncao"],
            "categoria": r["Grupo Natureza"],
            "elemento": r["Elemento Despesa"],
            "fonte": r["Fonte Recurso"],
            "tipo": r["Tipo"],
        })
    return out


def gera_servidores() -> list[dict]:
    """TODOS os servidores cadastrados (ativos + licenças + comissionados)."""
    rows = ler_csv(DATA / "servidores_completo.csv")
    return [{
        "matricula": r["Matricula"],
        "nome": r["Nome"],
        "cpf": r["CPF"],
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
        "processo": r.get("Processo", ""),
        "beneficiario": r["Beneficiario"],
        "matricula": r["Matricula"],
        "cpf": r["CPF"],
        "cargo": r["Cargo"],
        "motivo": r["Motivo"],
        "base_legal": r.get("Base Legal", ""),
        "fonte_recurso": r.get("Fonte Recurso", ""),
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
    empenhos_all = ler_csv(DATA / "empenhos_completo.csv")
    total_empenhado = sum(to_float(r["_valor"]) for r in empenhos_all if to_float(r["_valor"]) > 0)
    total_anulacoes = sum(-to_float(r["_valor"]) for r in empenhos_all if to_float(r["_valor"]) < 0)

    credores_all = ler_csv(DATA / "credores_completo.csv")
    servidores_all = ler_csv(DATA / "servidores_completo.csv")
    folha_base = sum(to_float(r["_salario_base"]) for r in servidores_all)
    ativos = sum(1 for r in servidores_all if r["Situacao"] == "Ativo")

    diarias_all = ler_csv(DATA / "diarias_completo.csv")
    total_diarias = sum(to_float(r["_valor"]) for r in diarias_all)

    contratos_all = ler_csv(DATA / "contratos_completo.csv")
    total_contratos = sum(to_float(r["_valor"]) for r in contratos_all)
    licitacoes_all = ler_csv(DATA / "licitacoes_completo.csv")

    max_credor = max((to_float(r["_valor"]) for r in credores_all), default=1.0)
    # Max empenho positivo (anulações ignoradas para escala da barra)
    max_empenho = max((to_float(r["_valor"]) for r in empenhos_all if to_float(r["_valor"]) > 0), default=1.0)
    max_salario = max((to_float(r["_salario_base"]) for r in servidores_all), default=1.0)

    return {
        "total_empenhado": total_empenhado,
        "total_anulacoes": total_anulacoes,
        "total_empenhos": len(empenhos_all),
        "total_credores": len(credores_all),
        "folha_base_mensal": folha_base,
        "total_servidores": len(servidores_all),
        "servidores_ativos": ativos,
        "total_diarias": total_diarias,
        "qtd_diarias": len(diarias_all),
        "total_contratos": total_contratos,
        "qtd_contratos": len(contratos_all),
        "qtd_licitacoes": len(licitacoes_all),
        "max_credor": max_credor,
        "max_empenho": max_empenho,
        "max_salario": max_salario,
    }


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)

    credores = gera_credores()
    empenhos = gera_empenhos()
    servidores = gera_servidores()
    diarias = gera_diarias()
    licitacoes = gera_licitacoes()
    kpis = gera_kpis()

    def save(name: str, obj) -> None:
        path = SITE / f"{name}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        size_kb = path.stat().st_size / 1024
        n = len(obj) if isinstance(obj, list) else "—"
        print(f"  {path.name:<22} {size_kb:>7.1f} KB  ({n} itens)")

    save("credores", credores)
    save("empenhos", empenhos)
    save("servidores", servidores)
    save("diarias", diarias)
    save("licitacoes", licitacoes)
    save("kpis", kpis)

    print(f"\n  KPIs:")
    print(f"    Empenhado: R$ {kpis['total_empenhado']:,.2f}  ({kpis['total_empenhos']} empenhos, {kpis['total_credores']} credores)")
    print(f"    Anulações: R$ {kpis['total_anulacoes']:,.2f}")
    print(f"    Folha base mensal: R$ {kpis['folha_base_mensal']:,.2f}  ({kpis['servidores_ativos']}/{kpis['total_servidores']} ativos)")
    print(f"    Diárias: R$ {kpis['total_diarias']:,.2f}  ({kpis['qtd_diarias']} registros)")
    print(f"    Contratos: R$ {kpis['total_contratos']:,.2f}  ({kpis['qtd_contratos']} vigentes, {kpis['qtd_licitacoes']} licitações)")


if __name__ == "__main__":
    main()
