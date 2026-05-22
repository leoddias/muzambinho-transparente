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


def gera_radar(empenhos, credores, licitacoes, servidores, kpis,
               receitas=None, comissionados=None, pagamentos=None, insights=None) -> list[dict]:
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

    # 9. Balança fiscal: gasta mais do que arrecada? (precisa de receitas)
    if receitas and insights:
        bal = insights.get("balanca", {})
        arrec = bal.get("arrecadado", 0)
        emp = bal.get("empenhado_liquido", 0)
        pago = bal.get("pago", 0)
        if arrec > 0 and emp > arrec:
            deficit = emp - arrec
            pct = deficit / arrec * 100
            sev = "alta" if pct > 30 else "media"
            achados.append({
                "tipo": "fiscal", "icone": "⚖️", "severidade": sev,
                "titulo": f'Empenhou {pct:.0f}% a mais do que arrecadou',
                "descricao": f'Arrecadou {brl(arrec)} mas empenhou {brl(emp)} no ano — déficit de compromisso de {brl(deficit)}. Pagamentos efetivos somam só {brl(pago)} ({pago/emp*100:.0f}% dos empenhos viraram saída de caixa). Diferença pode estar em caixa do ano anterior ou virará restos a pagar.',
                "link": "#receitas",
            })

    # 10. Dependência de transferências externas
    if receitas:
        # Identifica receitas de transferências (palavras-chave nas categorias/origens)
        kw_transf = ["TRANSFER", "FPM", "FUNDEB", "ICMS", "IPVA", "FNDE", "SUS", "REPASSE", "QUOTA-PARTE", "COTA-PARTE"]
        total = sum(r["realizado_num"] for r in receitas if r["realizado_num"] > 0)
        de_transf = sum(r["realizado_num"] for r in receitas
                        if r["realizado_num"] > 0 and any(
                            k in (r.get("categoria", "") + " " + r.get("origem", "") + " " + r.get("especie", "")).upper()
                            for k in kw_transf
                        ))
        if total > 0:
            pct = de_transf / total * 100
            if pct >= 60:
                sev = "alta" if pct >= 80 else "media"
                achados.append({
                    "tipo": "dependencia", "icone": "🏛️", "severidade": sev,
                    "titulo": f'{pct:.0f}% da receita vem de transferências externas',
                    "descricao": f'{brl(de_transf)} de {brl(total)} arrecadados vieram de transferências da União (FPM, FUNDEB, SUS) e do Estado (ICMS, IPVA). Cidades pequenas dependem disso, mas baixa autonomia tributária reduz a margem de manobra do município. Ver "De onde vem o dinheiro" abaixo.',
                    "link": "#receitas",
                })

    # 11. Comissionados consomem mais que seu peso no quadro
    if insights:
        c = insights.get("comissionados", {})
        if c.get("pct_quadro", 0) > 0 and c.get("pct_custo", 0) > 0:
            pct_quadro = c["pct_quadro"]
            pct_custo = c["pct_custo"]
            if pct_custo > pct_quadro * 1.3:  # cargos de confiança custam desproporcionalmente
                sev = "media" if pct_custo > pct_quadro * 1.8 else "baixa"
                achados.append({
                    "tipo": "pessoal", "icone": "🎩", "severidade": sev,
                    "titulo": f'Comissionados: {pct_quadro:.0f}% do quadro mas {pct_custo:.0f}% do custo',
                    "descricao": f'{c["qtd"]} cargos de confiança (livre nomeação) custam {brl(c["custo_mensal"])}/mês, equivalente a {pct_custo:.1f}% da folha base total. Salário médio dos comissionados é {brl(c["custo_mensal"]/c["qtd"]) if c["qtd"] else "R$ 0"}/mês.',
                    "link": "#comissionados",
                })
            else:
                # Mesmo equilibrado, mostrar informativo
                achados.append({
                    "tipo": "pessoal", "icone": "🎩", "severidade": "info",
                    "titulo": f'{c["qtd"]} cargos comissionados ({pct_quadro:.1f}% do quadro)',
                    "descricao": f'Custam {brl(c["custo_mensal"])}/mês, equivalente a {pct_custo:.1f}% da folha base. Salário médio: {brl(c["custo_mensal"]/c["qtd"]) if c["qtd"] else "R$ 0"}.',
                    "link": "#comissionados",
                })

    # 12. Pagamentos efetivos vs empenhos (% executado em caixa)
    if pagamentos is not None and kpis.get("total_empenhado", 0) > 0:
        pct_pago = kpis.get("total_pago", 0) / kpis["total_empenhado"] * 100
        if pct_pago < 35:
            achados.append({
                "tipo": "execucao", "icone": "💸", "severidade": "media",
                "titulo": f'Só {pct_pago:.0f}% dos empenhos viraram pagamento efetivo',
                "descricao": f'Empenhou {brl(kpis["total_empenhado"])} mas pagou só {brl(kpis["total_pago"])}. O restante está em estágios intermediários (a liquidar/a pagar) ou irá para restos a pagar do próximo exercício. Cuidado com a bola-de-neve fiscal.',
                "link": "#pagamentos",
            })

    return achados


def gera_receitas() -> list[dict]:
    rows = ler_csv(DATA / "receitas_completo.csv")
    out = []
    for r in rows:
        out.append({
            "data": r.get("Data", ""),
            "categoria": r.get("Categoria", ""),
            "origem": r.get("Origem", ""),
            "especie": r.get("Especie", ""),
            "rubrica": r.get("Rubrica", ""),
            "alinea": r.get("Alinea", ""),
            "subalinea": r.get("Subalinea", ""),
            "plano_conta": r.get("Plano Conta", ""),
            "tipo": r.get("Tipo", ""),
            "previsao": r.get("Valor Previsto", ""),
            "previsao_num": to_float(r.get("_previsao", "")),
            "atualizado": r.get("Valor Atualizado", ""),
            "atualizado_num": to_float(r.get("_atualizado", "")),
            "realizado": r.get("Valor Realizado", ""),
            "realizado_num": to_float(r.get("_realizado", "")),
        })
    return out


def gera_transferencias() -> list[dict]:
    rows = ler_csv(DATA / "transferencias_completo.csv")
    return [{
        "data": r["Data"],
        "concedente": r["Concedente"],
        "beneficiario": r["Beneficiario"],
        "cnpj": r["CNPJ Beneficiario"],
        "objeto": r["Objeto"],
        "vigencia_inicial": r["Vigencia Inicial"],
        "vigencia_final": r["Vigencia Final"],
        "valor": r["Valor a Receber"],
        "valor_num": to_float(r["_valor"]),
        "contrapartida": r["Valor Contrapartida"],
        "contrapartida_num": to_float(r["_contrapartida"]),
    } for r in rows]


def gera_comissionados() -> list[dict]:
    rows = ler_csv(DATA / "comissionados_completo.csv")
    return [{
        "matricula": r["Matricula"],
        "nome": r["Nome"],
        "cpf": r["CPF"],
        "cargo": r["Cargo"],
        "lotacao": r["Lotacao"],
        "situacao": r["Situacao"],
        "admissao": r["Admissao"],
        "demissao": r["Demissao"],
        "carga_horaria": r.get("Carga Horaria", ""),
        "salario_base": r["Salario Base"],
        "salario_base_num": to_float(r["_salario"]),
    } for r in rows]


def gera_pagamentos() -> list[dict]:
    rows = ler_csv(DATA / "pagamentos_completo.csv")
    return [{
        "data": r["Data"],
        "pagamento": r["Pagamento"],
        "empenho": r["Empenho"],
        "liquidacao": r.get("Liquidacao", ""),
        "processo": r["Processo"],
        "favorecido": r["Favorecido"],
        "cnpj": r["CPF/CNPJ"],
        "tipo": r["Tipo"],
        "historico": r["Historico"],
        "funcao": r["Funcao"],
        "elemento": r["Elemento"],
        "categoria": r.get("Categoria", ""),
        "valor": r["Valor"],
        "valor_num": to_float(r["_valor"]),
    } for r in rows]


def gera_subvencoes() -> list[dict]:
    rows = ler_csv(DATA / "subvencoes_completo.csv")
    return [{
        "data": r["Data"],
        "processo": r["Processo"],
        "beneficiario": r["Beneficiario"],
        "cnpj": r["CPF/CNPJ"],
        "historico": r["Historico"],
        "pagamento": r.get("Pagamento", ""),
        "valor": r["Valor"],
        "valor_num": to_float(r["_valor"]),
    } for r in rows]


def gera_insights(receitas, empenhos, comissionados, servidores, pagamentos, kpis) -> dict:
    """Agregacoes para os blocos visuais: balanca fiscal, origem do dinheiro,
    piramide do orcamento por funcao, comissionados vs efetivos."""
    from collections import Counter

    total_arrecadado = sum(r["realizado_num"] for r in receitas)
    total_previsto = sum(r["atualizado_num"] for r in receitas)
    total_empenhado = kpis["total_empenhado"] - kpis.get("total_anulacoes", 0)
    total_pago = sum(p["valor_num"] for p in pagamentos if p["valor_num"] > 0)

    # Balanca fiscal: arrecadado vs empenhado vs pago
    balanca = {
        "arrecadado": total_arrecadado,
        "previsto_atualizado": total_previsto,
        "empenhado_liquido": total_empenhado,
        "pago": total_pago,
        "saldo_caixa": total_arrecadado - total_pago,  # entrada vs saida real
        "compromisso": total_arrecadado - total_empenhado,  # entrada vs prometido
    }

    # De onde vem o dinheiro - por Categoria
    origem_categoria = Counter()
    for r in receitas:
        cat = r.get("categoria", "").strip()
        if cat and r["realizado_num"] > 0:
            origem_categoria[cat] += r["realizado_num"]
    # E por Origem (mais detalhado)
    origem_origem = Counter()
    for r in receitas:
        org = r.get("origem", "").strip()
        if org and r["realizado_num"] > 0:
            origem_origem[org] += r["realizado_num"]

    # Piramide do orcamento por funcao (despesa)
    func_total = Counter()
    for e in empenhos:
        if e.get("valor_num", 0) > 0 and e.get("funcao"):
            func_total[e["funcao"]] += e["valor_num"]

    # Comissionados vs efetivos
    custo_comissionados = sum(c["salario_base_num"] for c in comissionados)
    custo_total_folha_base = sum(s["salario_base_num"] for s in servidores)
    qtd_comissionados = len(comissionados)
    qtd_efetivos = sum(1 for s in servidores if s.get("vinculo", "") == "Efetivo")
    qtd_total = len(servidores)

    return {
        "balanca": balanca,
        "origem_categoria": dict(origem_categoria.most_common(8)),
        "origem_origem": dict(origem_origem.most_common(10)),
        "piramide_funcao": dict(func_total.most_common(12)),
        "comissionados": {
            "qtd": qtd_comissionados,
            "qtd_efetivos": qtd_efetivos,
            "qtd_total_quadro": qtd_total,
            "pct_quadro": qtd_comissionados / qtd_total * 100 if qtd_total else 0,
            "custo_mensal": custo_comissionados,
            "custo_folha_base_total": custo_total_folha_base,
            "pct_custo": custo_comissionados / custo_total_folha_base * 100 if custo_total_folha_base else 0,
        },
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
    total_diarias = sum(to_float(r["_valor"]) for r in diarias_all if to_float(r["_valor"]) > 0)

    contratos_all = ler_csv(DATA / "contratos_completo.csv")
    total_contratos = sum(to_float(r["_valor"]) for r in contratos_all)
    licitacoes_all = ler_csv(DATA / "licitacoes_completo.csv")
    dispensas_all = ler_csv(DATA / "dispensas_completo.csv")
    atas_all = ler_csv(DATA / "atas_completo.csv")
    total_atas = sum(to_float(r["_valor"]) for r in atas_all)

    # Novos: receitas, transferencias, comissionados, pagamentos, subvencoes
    receitas_all = ler_csv(DATA / "receitas_completo.csv")
    total_arrecadado = sum(to_float(r.get("_realizado", "")) for r in receitas_all)
    total_previsto = sum(to_float(r.get("_atualizado", "")) for r in receitas_all)

    transferencias_all = ler_csv(DATA / "transferencias_completo.csv")
    total_transferencias = sum(to_float(r.get("_valor", "")) for r in transferencias_all)

    comissionados_all = ler_csv(DATA / "comissionados_completo.csv")
    custo_comissionados = sum(to_float(r.get("_salario", "")) for r in comissionados_all)

    pagamentos_all = ler_csv(DATA / "pagamentos_completo.csv")
    total_pago = sum(to_float(r.get("_valor", "")) for r in pagamentos_all if to_float(r.get("_valor", "")) > 0)

    subvencoes_all = ler_csv(DATA / "subvencoes_completo.csv")
    total_subvencoes = sum(to_float(r.get("_valor", "")) for r in subvencoes_all)

    max_credor = max((to_float(r["_valor"]) for r in credores_all), default=1.0)
    # Max empenho positivo (anulações ignoradas para escala da barra)
    max_empenho = max((to_float(r["_valor"]) for r in empenhos_all if to_float(r["_valor"]) > 0), default=1.0)
    max_salario = max((to_float(r["_salario_base"]) for r in servidores_all), default=1.0)
    max_receita = max((to_float(r.get("_realizado", "")) for r in receitas_all), default=1.0)

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
        # Novos
        "total_arrecadado": total_arrecadado,
        "total_previsto": total_previsto,
        "qtd_receitas": len(receitas_all),
        "total_transferencias": total_transferencias,
        "qtd_transferencias": len(transferencias_all),
        "qtd_comissionados": len(comissionados_all),
        "custo_comissionados_mes": custo_comissionados,
        "total_pago": total_pago,
        "qtd_pagamentos": len(pagamentos_all),
        "total_subvencoes": total_subvencoes,
        "qtd_subvencoes": len(subvencoes_all),
        "saldo_fiscal": total_arrecadado - total_pago,
        "max_credor": max_credor,
        "max_empenho": max_empenho,
        "max_salario": max_salario,
        "max_receita": max_receita,
    }


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)

    credores = gera_credores()
    empenhos = gera_empenhos()
    servidores = gera_servidores()
    diarias = gera_diarias()
    licitacoes = gera_licitacoes()
    receitas = gera_receitas()
    transferencias = gera_transferencias()
    comissionados = gera_comissionados()
    pagamentos = gera_pagamentos()
    subvencoes = gera_subvencoes()
    kpis = gera_kpis()
    insights = gera_insights(receitas, empenhos, comissionados, servidores, pagamentos, kpis)
    radar = gera_radar(empenhos, credores, licitacoes, servidores, kpis,
                       receitas=receitas, comissionados=comissionados,
                       pagamentos=pagamentos, insights=insights)

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
    save("receitas", receitas)
    save("transferencias", transferencias)
    save("comissionados", comissionados)
    save("pagamentos", pagamentos)
    save("subvencoes", subvencoes)
    save("insights", insights)
    save("kpis", kpis)
    save("radar", radar)

    print(f"\n  KPIs:")
    print(f"    Arrecadado: R$ {kpis['total_arrecadado']:,.2f}  (de R$ {kpis['total_previsto']:,.2f} previstos)")
    print(f"    Empenhado:  R$ {kpis['total_empenhado']:,.2f}  ({kpis['total_empenhos']} empenhos)")
    print(f"    Pago:       R$ {kpis['total_pago']:,.2f}  ({kpis['qtd_pagamentos']} pagamentos)")
    print(f"    Saldo fiscal: R$ {kpis['saldo_fiscal']:,.2f}  (arrecadado − pago)")
    print(f"    Folha base mensal: R$ {kpis['folha_base_mensal']:,.2f}  ({kpis['servidores_ativos']}/{kpis['total_servidores']} ativos)")
    print(f"      dos quais {kpis['qtd_comissionados']} comissionados ({kpis['custo_comissionados_mes']:,.2f}/mês)")
    print(f"    Diárias: R$ {kpis['total_diarias']:,.2f}  ({kpis['qtd_diarias']} registros)")
    print(f"    Subvenções: R$ {kpis['total_subvencoes']:,.2f}  ({kpis['qtd_subvencoes']} concessões)")
    print(f"    Transferências recebidas: R$ {kpis['total_transferencias']:,.2f}  ({kpis['qtd_transferencias']} convênios)")
    print(f"    Compras: {kpis['qtd_licitacoes']}L + {kpis['qtd_dispensas']}D + {kpis['qtd_atas']}A + {kpis['qtd_contratos']}C")


if __name__ == "__main__":
    main()
