"""Agrega empenhos individuais por credor (CPF/CNPJ) -> ranking de fornecedores.

Le data/empenhos_completo.csv e gera:
  data/credores_completo.csv  (todos os credores, ordenado por valor desc)
  data/credores_top50.csv     (top 50)

Cada linha tem:
  Rank | Favorecido | CPF/CNPJ | Empenhos (qtd) | Valor Total | _valor | _doc
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

from _portaltp import fmt_brl, fmt_doc, escreve_csv, DATA


def main() -> None:
    src = DATA / "empenhos_completo.csv"
    if not src.exists():
        print(f"ERRO: rode coleta_empenhos.py primeiro - {src} nao existe")
        return

    # Acumulador: _doc -> {nome, valor_liquido, valor_bruto_positivo, qtd_empenhos, qtd_anulacoes}
    acc: dict[str, dict] = defaultdict(lambda: {
        "nome": "", "_doc": "", "valor_liquido": 0.0, "valor_positivo": 0.0,
        "qtd": 0, "anulacoes": 0,
    })

    with src.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            doc = row["_doc"]
            valor = float(row["_valor"] or 0)
            # Empenhos sem CPF/CNPJ (raros, geralmente folha) vao para uma chave especial
            chave = doc if doc else f"sem_doc::{row['Favorecido']}"
            entry = acc[chave]
            # Mantem o primeiro nome encontrado (PortalTP costuma normalizar)
            if not entry["nome"]:
                entry["nome"] = row["Favorecido"]
                entry["_doc"] = doc
            entry["valor_liquido"] += valor
            if valor > 0:
                entry["valor_positivo"] += valor
                entry["qtd"] += 1
            else:
                entry["anulacoes"] += 1

    # Para o ranking, usamos valor_liquido (positivos menos anulacoes)
    credores = []
    for entry in acc.values():
        credores.append({
            "Favorecido": entry["nome"],
            "CPF/CNPJ": fmt_doc(entry["_doc"]) if entry["_doc"] else "",
            "_doc": entry["_doc"],
            "Empenhos": entry["qtd"],
            "Anulacoes": entry["anulacoes"],
            "Valor Liquido": fmt_brl(entry["valor_liquido"]),
            "_valor": round(entry["valor_liquido"], 2),
            "Valor Bruto": fmt_brl(entry["valor_positivo"]),
            "_valor_bruto": round(entry["valor_positivo"], 2),
        })

    credores.sort(key=lambda c: -c["_valor"])
    for i, c in enumerate(credores, 1):
        c["Rank"] = i

    cols = ["Rank", "Favorecido", "CPF/CNPJ", "Empenhos", "Anulacoes",
            "Valor Liquido", "_valor", "Valor Bruto", "_valor_bruto", "_doc"]

    completo = DATA / "credores_completo.csv"
    escreve_csv(completo, credores, cols)
    print(f"  CSV completo: {completo.name} ({len(credores)} credores)")

    top50 = credores[:50]
    top_path = DATA / "credores_top50.csv"
    escreve_csv(top_path, top50, cols)
    print(f"  CSV top 50: {top_path.name}")

    total_liquido = sum(c["_valor"] for c in credores)
    print(f"\n  Total liquido (todos): {fmt_brl(total_liquido)}")
    print(f"  Top 5 credores:")
    for c in credores[:5]:
        print(f"    {c['Rank']:3d}. {c['Favorecido'][:50]:50s} {c['Valor Liquido']}")


if __name__ == "__main__":
    main()
