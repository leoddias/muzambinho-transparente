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
    # Fonte agora eh empenhos filtrados por elemento de despesa "Diaria"
    # (ver coleta_diarias.py para racional)
    rows = ler_csv(DATA / "diarias_completo.csv")
    return [{
        "data": r["Data"],
        "empenho": r.get("Empenho", ""),
        "processo": r.get("Processo", ""),
        "beneficiario": r["Beneficiario"],
        "cpf": r.get("CPF/CNPJ", ""),
        "motivo": r["Motivo"],
        "funcao": r.get("Funcao", ""),
        "elemento": r.get("Elemento Despesa", ""),
        "valor": r["Valor"],
        "valor_num": to_float(r["_valor"]),
    } for r in rows]


def gera_licitacoes() -> dict:
    licitacoes = ler_csv(DATA / "licitacoes_completo.csv")
    contratos  = ler_csv(DATA / "contratos_completo.csv")
    dispensas  = ler_csv(DATA / "dispensas_completo.csv")
    atas       = ler_csv(DATA / "atas_completo.csv")
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
        "dispensas": [{
            "data": r["Data Abertura"],
            "numero": r["Numero"],
            "ano": r.get("Ano", ""),
            "modalidade": r["Modalidade"],
            "processo": r["Processo"],
            "objeto": r["Objeto"],
            "base_legal": r.get("Base Legal", ""),
            "situacao": r["Situacao"],
            "valor_estimado": r["Valor Estimado"],
            "valor_estimado_num": to_float(r["_valor_estimado"]),
            "valor_final": r["Valor Final"],
            "valor_final_num": to_float(r["_valor_final"]),
        } for r in dispensas],
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
        "atas": [{
            "assinatura": r["Assinatura"],
            "ata": r.get("Ata", r.get("Numero", "")),
            "ano": r.get("Ano", ""),
            "processo": r["Processo"],
            "contratado": r["Contratado"],
            "cnpj": r["CPF/CNPJ"],
            "categoria": r.get("Categoria", ""),
            "objeto": r["Objeto"],
            "situacao": r["Situacao"],
            "valor": r["Valor"],
            "valor_num": to_float(r["_valor"]),
        } for r in atas],
    }


def gera_radar(empenhos, credores, licitacoes, servidores, kpis) -> list[dict]:
    """Heurísticas de anomalia/concentração para a seção 'Radar de Gastos'.

    Cada achado tem: tipo, severidade (alta/media/baixa/info), título, descrição,
    link interno. As heurísticas são CONSERVADORAS — apontam concentrações e
    valores atípicos para investigação, não acusam ilegalidade.
    """
    from collections import Counter
    achados = []
    total_emp = kpis.get("total_empenhado", 0)
    total_anul = kpis.get("total_anulacoes", 0)

    def brl(v):
        if v >= 1_000_000:
            return f"R$ {v/1_000_000:.2f}M".replace(".", ",")
        if v >= 1_000:
            return f"R$ {v/1_000:.0f}K"
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # 1. Concentração do maior credor
    if credores and total_emp > 0:
        top = credores[0]
        pct = top["valor_num"] / total_emp * 100
        if pct >= 10:
            sev = "alta" if pct >= 25 else "media"
            achados.append({
                "tipo": "concentracao", "icone": "👤", "severidade": sev,
                "titulo": f'{top["favorecido"][:60]} concentra {pct:.1f}% dos empenhos',
                "descricao": f'Recebeu {top["valor"]} de {brl(total_emp)} empenhados no ano. ' +
                             ('Em municípios pequenos, a "Folha de Pagamento" costuma liderar — verifique se é o caso.' if 'FOLHA' in top["favorecido"].upper() else 'Concentração alta em um único fornecedor merece atenção.'),
                "link": "#credores",
            })

    # 2. Dispensas de licitação com valor alto
    dispensas = licitacoes.get("dispensas", []) if isinstance(licitacoes, dict) else []
    grandes_disp = [d for d in dispensas if (d.get("valor_final_num") or d.get("valor_estimado_num") or 0) >= 100_000]
    if grandes_disp:
        total_d = sum(d.get("valor_final_num") or d.get("valor_estimado_num", 0) for d in grandes_disp)
        achados.append({
            "tipo": "dispensa", "icone": "⚠️", "severidade": "alta",
            "titulo": f'{len(grandes_disp)} dispensa(s) de licitação acima de R$ 100 mil',
            "descricao": f'Total {brl(total_d)} contratado sem certame competitivo. A Lei 14.133/21 permite dispensa "comum" só até R$ 59.906,02 — valores maiores geralmente exigem inexigibilidade fundamentada ou enquadramento em hipóteses específicas (calamidade, fornecedor único, etc.).',
            "link": "#licitacoes",
        })

    # 3. Anulações expressivas
    if total_emp > 0 and total_anul > 0:
        pct_anul = total_anul / total_emp * 100
        if pct_anul >= 8:
            sev = "alta" if pct_anul >= 15 else "media"
            achados.append({
                "tipo": "anulacao", "icone": "🔄", "severidade": sev,
                "titulo": f'{pct_anul:.1f}% dos empenhos foram anulados',
                "descricao": f'{brl(total_anul)} anulado de {brl(total_emp)} empenhado. Anulações são correções administrativas válidas, mas volume alto pode indicar falha recorrente no planejamento orçamentário ou cancelamento de contratações.',
                "link": "#empenhos",
            })

    # 4. Credores com muitas anulações
    com_anul = sorted([c for c in credores if c.get("anulacoes", 0) > 0],
                     key=lambda c: -c["anulacoes"])[:3]
    if com_anul and com_anul[0]["anulacoes"] >= 5:
        achados.append({
            "tipo": "anulacao", "icone": "🔄", "severidade": "media",
            "titulo": f'{com_anul[0]["favorecido"][:50]} teve {com_anul[0]["anulacoes"]} empenhos anulados',
            "descricao": 'Credores com mais anulações no ano: ' +
                         ' · '.join(f'{c["favorecido"][:30]} ({c["anulacoes"]})' for c in com_anul),
            "link": "#credores",
        })

    # 5. Concentração por função (área de governo)
    func_total = Counter()
    for e in empenhos:
        if e.get("valor_num", 0) > 0 and e.get("funcao"):
            func_total[e["funcao"]] += e["valor_num"]
    if func_total:
        top_funcs = func_total.most_common(3)
        nome, valor = top_funcs[0]
        pct = valor / total_emp * 100
        achados.append({
            "tipo": "funcao", "icone": "📊", "severidade": "info",
            "titulo": f'{nome} concentra {pct:.0f}% do orçamento empenhado',
            "descricao": 'Top 3 áreas: ' +
                         ' · '.join(f'{n} ({v/total_emp*100:.0f}%)' for n, v in top_funcs),
            "link": "#empenhos",
        })

    # 6. Fornecedores presentes em múltiplas categorias de compra
    contratos = licitacoes.get("contratos", []) if isinstance(licitacoes, dict) else []
    atas = licitacoes.get("atas", []) if isinstance(licitacoes, dict) else []
    docs_contratos = {c["cnpj"] for c in contratos if c.get("cnpj")}
    docs_atas = {a["cnpj"] for a in atas if a.get("cnpj")}
    docs_dispensas = {d.get("cnpj") for d in dispensas if d.get("cnpj")}
    intersec = docs_contratos & docs_atas
    if len(intersec) >= 1:
        nomes = []
        for c in contratos:
            if c["cnpj"] in intersec and c["contratado"] not in nomes:
                nomes.append(c["contratado"])
        achados.append({
            "tipo": "relacionamento", "icone": "🔗", "severidade": "info",
            "titulo": f'{len(intersec)} fornecedor(es) com contrato + ata de registro de preço',
            "descricao": 'Relacionamento prolongado: ' + ', '.join(n[:40] for n in nomes[:3]) +
                         ('...' if len(nomes) > 3 else '') + '. Não é irregular, mas indica dependência da Prefeitura nestes fornecedores.',
            "link": "#licitacoes",
        })

    # 7. Servidores afastados / em licença
    afastados = sum(1 for s in servidores if s.get("situacao", "") not in ("", "Ativo"))
    total_srv = len(servidores)
    if total_srv > 0 and afastados / total_srv >= 0.07:
        achados.append({
            "tipo": "pessoal", "icone": "🏥", "severidade": "baixa",
            "titulo": f'{afastados} servidores fora do regime ativo ({afastados/total_srv*100:.0f}% do quadro)',
            "descricao": 'Inclui aposentados na folha, licenças médicas, maternidade, comissionados afastados. Use o filtro de "Situação" na seção Servidores para detalhar.',
            "link": "#servidores",
        })

    # 8. Histórico genérico em empenhos de valor alto
    palavras_vagas = ["DIVERSAS", "DIVERSOS", "GERAIS", "VARIADOS", "OUTROS"]
    vagos = [e for e in empenhos
             if e.get("valor_num", 0) >= 50_000
             and any(p in (e.get("historico", "") or "").upper() for p in palavras_vagas)]
    if vagos:
        achados.append({
            "tipo": "transparencia", "icone": "❓", "severidade": "baixa",
            "titulo": f'{len(vagos)} empenho(s) acima de R$ 50k com histórico genérico',
            "descricao": f'Contêm termos como "diversas", "diversos", "outros". Total {brl(sum(v["valor_num"] for v in vagos))}. Descrição vaga dificulta auditoria cidadã — não é irregular, mas merece pedido de detalhamento via LAI.',
            "link": "#empenhos",
        })

    return achados


def gera_kpis() -> dict:
    empenhos_all = ler_csv(DATA / "empenhos_completo.csv")
    total_empenhado = sum(to_float(r["_valor"]) for r in empenhos_all if to_float(r["_valor"]) > 0)
    total_anulacoes = sum(-to_float(r["_valor"]) for r in empenhos_all if to_float(r["_valor"]) < 0)

    credores_all = ler_csv(DATA / "credores_completo.csv")
    servidores_all = ler_csv(DATA / "servidores_completo.csv")
    folha_base = sum(to_float(r["_salario_base"]) for r in servidores_all)
    ativos = sum(1 for r in servidores_all if r["Situacao"] == "Ativo")

    diarias_all = ler_csv(DATA / "diarias_completo.csv")
    total_diarias = sum(to_float(r["_valor"]) for r in diarias_all if to_float(r["_valor"]) > 0)

    contratos_all = ler_csv(DATA / "contratos_completo.csv")
    total_contratos = sum(to_float(r["_valor"]) for r in contratos_all)
    licitacoes_all = ler_csv(DATA / "licitacoes_completo.csv")
    dispensas_all = ler_csv(DATA / "dispensas_completo.csv")
    atas_all = ler_csv(DATA / "atas_completo.csv")
    total_atas = sum(to_float(r["_valor"]) for r in atas_all)

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
        "qtd_dispensas": len(dispensas_all),
        "qtd_atas": len(atas_all),
        "total_atas": total_atas,
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
    radar = gera_radar(empenhos, credores, licitacoes, servidores, kpis)

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
    save("radar", radar)

    print(f"\n  KPIs:")
    print(f"    Empenhado: R$ {kpis['total_empenhado']:,.2f}  ({kpis['total_empenhos']} empenhos, {kpis['total_credores']} credores)")
    print(f"    Anulações: R$ {kpis['total_anulacoes']:,.2f}")
    print(f"    Folha base mensal: R$ {kpis['folha_base_mensal']:,.2f}  ({kpis['servidores_ativos']}/{kpis['total_servidores']} ativos)")
    print(f"    Diárias: R$ {kpis['total_diarias']:,.2f}  ({kpis['qtd_diarias']} registros)")
    print(f"    Contratos: R$ {kpis['total_contratos']:,.2f}  ({kpis['qtd_contratos']} vigentes)")
    print(f"    Compras: {kpis['qtd_licitacoes']} licitações + {kpis['qtd_dispensas']} dispensas + {kpis['qtd_atas']} atas (R$ {kpis['total_atas']:,.2f})")


if __name__ == "__main__":
    main()
