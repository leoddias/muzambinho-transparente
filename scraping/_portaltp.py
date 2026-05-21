"""Helpers compartilhados para scraping do PortalTP (Fiorilli) de Muzambinho.

Este modulo NAO e executavel - so e importado pelos scripts coleta_*.py.

Convencoes do PortalTP descobertas em reconhecimento (ver scraping/_inspect.py
e scraping/_test_export.py para os scripts diagnostico originais):

  - Stack: ASP.NET WebForms + DevExpress (DX controls com sufixo _I/_VI/_L)
  - Campos comuns em todas as consultas:
      ctl00_containerCorpo_cbxEntidades_I  (DevExpress combo "Entidade")
      ctl00_containerCorpo_btnAplicFiltro  (botao "Aplicar")
      ctl00_containerCorpo_grdData         (DevExpress grid)
  - Empenhos usa intervalo de datas:
      ctl00_containerCorpo_edtDataIni_I
      ctl00_containerCorpo_edtDataFim_I
  - Outros endpoints usam combos:
      ctl00_containerCorpo_cbxAno_I
      ctl00_containerCorpo_cbxMes_I
  - Export e' um submenu dentro de "Imprimir Relatorio":
      ctl00_containerCorpo_grdData_DXCTMenu0_DXI2_T    (parent, abre o menu)
      ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i0_T  (.pdf)
      ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i2_T  (.xlsx)
      ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i4_T  (.csv)
      ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i5_T  (.xml)  <- escolhido
  - XML export retorna um arquivo bem estruturado com <DOCUMENTO> por linha,
    encoding UTF-8 BOM. CSV vem em cp1252 com colunas com merge bagunçado.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
import re
import xml.etree.ElementTree as ET

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Download

BASE = "https://muzambinho-mg.portaltp.com.br"
PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"
RAW = DATA / "_raw"
DEBUG = PROJ / "debug"


# ----- browser -----------------------------------------------------------

@contextmanager
def navegador(headless: bool = True) -> Iterator[tuple[Browser, BrowserContext, Page]]:
    """Inicia Playwright + Chromium + contexto + page. Garante cleanup."""
    DEBUG.mkdir(exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 1024},
            accept_downloads=True,
        )
        page = ctx.new_page()
        try:
            yield browser, ctx, page
        finally:
            browser.close()


def abrir_consulta(page: Page, path: str) -> None:
    """Navega ate uma pagina /consultas/... e aguarda DOM + DevExpress inicializar."""
    url = BASE + path
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_selector("#ctl00_containerCorpo_btnAplicFiltro", timeout=30000)


# ----- filtros -----------------------------------------------------------

def preencher_periodo_datas(page: Page, ini: str, fim: str) -> None:
    """Preenche edtDataIni/edtDataFim no formato dd/MM/yyyy.

    Usado em /consultas/despesas/empenhos.aspx e /consultas/despesas/diarias.aspx
    quando habilitados intervalos de data.
    """
    page.fill("#ctl00_containerCorpo_edtDataIni_I", ini)
    page.fill("#ctl00_containerCorpo_edtDataFim_I", fim)


def preencher_ano(page: Page, ano: int) -> None:
    """Seleciona ano no cbxAno (DevExpress combo). Usa o campo _I texto."""
    page.fill("#ctl00_containerCorpo_cbxAno_I", str(ano))
    # da tempo do combo confirmar o valor (sem precisar abrir dropdown)
    page.keyboard.press("Tab")
    page.wait_for_timeout(300)


def preencher_mes(page: Page, mes: str = "") -> None:
    """Seleciona mes no cbxMes. Vazio = "Todos". No-op se o campo nao existe."""
    if page.locator("#ctl00_containerCorpo_cbxMes_I").count() == 0:
        return
    page.fill("#ctl00_containerCorpo_cbxMes_I", mes or "")
    page.keyboard.press("Tab")
    page.wait_for_timeout(300)


def aplicar_filtro(page: Page) -> None:
    """Clica botao Aplicar e aguarda grid atualizar (UpdatePanel async)."""
    page.click("#ctl00_containerCorpo_btnAplicFiltro")
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_selector("#ctl00_containerCorpo_grdData", timeout=60000)
    page.wait_for_timeout(2000)  # paranoia: DevExpress as vezes renderiza o grid em duas fases


# ----- export ------------------------------------------------------------

EXPORT_IDS = {
    "pdf":  "ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i0_T",
    "xlsx": "ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i2_T",
    "csv":  "ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i4_T",
    "xml":  "ctl00_containerCorpo_grdData_DXCTMenu0_DXI2i5_T",
}
MENU_IMPRIMIR_ID = "ctl00_containerCorpo_grdData_DXCTMenu0_DXI2_T"


def baixar_export(page: Page, destino: Path, formato: str = "xml") -> Download:
    """Abre o menu Imprimir Relatorio e dispara o export do formato escolhido.

    Salva em `destino` e retorna o objeto Download (com suggested_filename, etc).
    """
    if formato not in EXPORT_IDS:
        raise ValueError(f"formato desconhecido: {formato!r}")
    # Abre o submenu primeiro (sem isso o link de export fica invisivel)
    page.click(f"#{MENU_IMPRIMIR_ID}")
    page.wait_for_timeout(1000)
    with page.expect_download(timeout=180000) as dl_info:
        page.click(f"#{EXPORT_IDS[formato]}")
    dl = dl_info.value
    destino.parent.mkdir(parents=True, exist_ok=True)
    dl.save_as(str(destino))
    return dl


# ----- parsing XML do GridViewExport ------------------------------------

_TAG_OPEN  = re.compile(r"<([A-Za-zÀ-ÿ][^<>/][^<>]*)>")
_TAG_CLOSE = re.compile(r"</([A-Za-zÀ-ÿ][^<>]*)>")
_TAG_SELFCLOSE = re.compile(r"<([A-Za-zÀ-ÿ][^<>/][^<>]*)/>")


def _sanitize_tag(name: str) -> str:
    """Substitui chars invalidos em nome de tag XML por '_'.

    O PortalTP gera tags como <CPF/CNPJ>, <Programa/Atividade/Acao>, <Categoria Economica>.
    Barras, parenteses e espacos quebram o parser XML padrao - precisam ser saneados.
    """
    out_chars = []
    for c in name:
        if c.isalnum() or c in "_-":
            out_chars.append(c)
        else:
            out_chars.append("_")
    return "".join(out_chars) or "_"


_AMP_RAW = re.compile(r"&(?!(?:amp|lt|gt|apos|quot|#\d+|#x[0-9a-fA-F]+);)")


def _sanitize_xml(text: str) -> tuple[str, dict[str, str]]:
    """Retorna (xml_saneado, mapa_tag_saneada->tag_original).

    Trata 3 problemas do export do PortalTP:
      1. Tags com chars invalidos: <CPF/CNPJ>, <Categoria Econômica>, <Programa/Atividade/Ação>
      2. & cru em texto (e.g. "COMERCIAL J & C") — XML exige &amp;
      3. Sem root element — o caller envolve com <ROOT>.
    """
    mapa: dict[str, str] = {}

    def replace_open(m):
        orig = m.group(1)
        san = _sanitize_tag(orig)
        mapa[san] = orig
        return f"<{san}>"

    def replace_close(m):
        orig = m.group(1)
        san = _sanitize_tag(orig)
        mapa[san] = orig
        return f"</{san}>"

    out = _TAG_OPEN.sub(replace_open, text)
    out = _TAG_CLOSE.sub(replace_close, out)
    # Escapa & cru (mas preserva entidades validas existentes)
    out = _AMP_RAW.sub("&amp;", out)
    return out, mapa


def ler_xml_grid(path: Path) -> list[dict[str, str]]:
    """Le o XML exportado pelo PortalTP (GridViewExport.xml) -> lista de dicts.

    O XML tem estrutura:
        <RESULTSET>
          <DOCUMENTO>
            <Data>12/05/2026 00:00:00</Data>
            <Empenho>0002838/2026</Empenho>
            ...
          </DOCUMENTO>
        </RESULTSET>

    PORÉM, o PortalTP gera tags com caracteres invalidos para XML, tipo
    <CPF/CNPJ>, <Programa/Atividade/Ação>, <Categoria Econômica>. ElementTree
    rejeita esses nomes. Saneamos antes de parsear (substituindo / espaco () por _)
    e remapeamos para os nomes originais no retorno.

    As chaves devolvidas usam os nomes ORIGINAIS (com espacos e barras).
    """
    text = path.read_text(encoding="utf-8-sig")
    saneado, mapa = _sanitize_xml(text)
    # O export do PortalTP NAO tem root element - eh uma sequencia de <DOCUMENTO>.
    # Envolvemos para satisfazer o parser.
    saneado = f"<ROOT>{saneado}</ROOT>"
    root = ET.fromstring(saneado)
    rows: list[dict[str, str]] = []
    for doc in root.iter("DOCUMENTO"):
        row: dict[str, str] = {}
        for child in doc:
            tag_orig = mapa.get(child.tag, child.tag)
            row[tag_orig] = (child.text or "").strip()
        if row:
            rows.append(row)
    return rows


# ----- parsers de valores brasileiros -----------------------------------

_NAO_DIGITOS = re.compile(r"[^\d]")


def to_float_brl(s: str | None) -> float:
    """Converte string monetaria BR para float.

    Aceita:
      "1.234,56"       -> 1234.56
      "R$ 1.234,56"    -> 1234.56
      "-23535,720000"  -> -23535.72  (formato do XML do PortalTP)
      "1234.56"        -> 1234.56    (ja float-like)
      ""               -> 0.0
      None             -> 0.0
    """
    if not s:
        return 0.0
    s = s.strip().replace("R$", "").replace("\xa0", "").strip()
    if not s:
        return 0.0
    # Se tem ',' e '.', o ',' eh decimal (formato BR): 1.234,56
    # Se tem so ',', tambem eh decimal: 1234,56
    # Se tem so '.', pode ser decimal ingles ou separador de milhar
    #   - heuristica: se '.' aparece na posicao "milhar" (3 digitos depois), eh milhar
    #   - mais simples: se nao tem ',', assume '.' como decimal
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def fmt_brl(valor: float) -> str:
    """Formata float como 'R$ 1.234,56'."""
    if valor < 0:
        return "-" + fmt_brl(-valor)
    inteiro, _, dec = f"{valor:.2f}".partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return f"R$ {'.'.join(grupos)},{dec}"


def normaliza_doc(cpf_cnpj: str | None) -> str:
    """Remove formatacao de CPF/CNPJ. '38.300.757/0001-73' -> '38300757000173'."""
    if not cpf_cnpj:
        return ""
    return _NAO_DIGITOS.sub("", cpf_cnpj)


def fmt_doc(digitos: str) -> str:
    """Formata CPF (11 digitos) ou CNPJ (14 digitos). Retorna como veio se outro tamanho."""
    d = normaliza_doc(digitos)
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return digitos or ""


def parse_data_brl(s: str | None) -> str:
    """Normaliza '12/05/2026 00:00:00' ou '12/05/2026' -> '12/05/2026'."""
    if not s:
        return ""
    return s.split(" ")[0].strip()


# ----- escrita CSV (stdlib, sem pandas) ---------------------------------

import csv


def escreve_csv(path: Path, rows: list[dict], colunas: list[str]) -> None:
    """Escreve CSV UTF-8-SIG com separador virgula. Mantem ordem das colunas."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
