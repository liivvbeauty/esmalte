import re
import unicodedata
import urllib.parse
from io import StringIO

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="LIIVV Beauty | Esmaltes", layout="wide")

SPREADSHEET_ID = st.secrets.get(
    "SPREADSHEET_ID",
    "12BCdp9_E8xbGZrIhw8-r7rYxkXyCDtGjYZ8fLXp0px4",
)
SHEET_NAME = st.secrets.get(
    "SHEET_NAME",
    "base_liivv_esmaltes_app",
)

DEFAULT_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq"
    f"?tqx=out:csv&sheet={urllib.parse.quote(SHEET_NAME)}"
)
SHEET_URL = st.secrets.get("GOOGLE_SHEET_CSV_URL", DEFAULT_CSV_URL)

st.markdown(
    '''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');
    .stApp { background-color: #F7F2F4; }
    .block-container { padding-top: 1.5rem; max-width: 1080px; }
    .liivv-header {
        background: linear-gradient(135deg, #7A3C4B 0%, #2B2B2B 100%);
        padding: 34px 18px 30px 18px;
        border-radius: 0 0 34px 34px;
        text-align: center;
        margin-bottom: 18px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }
    .liivv-logo {
        font-family: 'Montserrat', Arial, sans-serif;
        font-size: 4.6rem;
        color: #EBA6A6;
        margin: 0;
        letter-spacing: 12px;
        line-height: 0.95;
        font-weight: 300;
    }
    .liivv-subtitle {
        font-family: 'Montserrat', sans-serif;
        color: #F7F2F4;
        font-size: 0.84rem;
        letter-spacing: 5px;
        text-transform: uppercase;
        margin-top: 10px;
        font-weight: 700;
    }
    .intro-card, .filter-card, .result-card, .empty-card {
        background: #FFFFFF;
        border-radius: 22px;
        padding: 20px;
        box-shadow: 0 8px 20px rgba(43,43,43,0.08);
        border: 1px solid rgba(122,60,75,0.10);
        margin-bottom: 16px;
    }
    .intro-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.45rem;
        color: #7A3C4B;
        font-weight: 800;
        margin: 0 0 6px 0;
    }
    .intro-text, .small-text {
        font-family: 'Montserrat', sans-serif;
        color: #555;
        font-size: 0.96rem;
        line-height: 1.5;
        margin: 0;
    }
    .section-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        color: #7A3C4B;
        font-size: 1.05rem;
        margin-bottom: 12px;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #EBA6A6 0%, #7A3C4B 100%);
        color: white !important;
        border-radius: 999px;
        padding: 0.85rem 1.1rem;
        font-weight: 800;
        font-size: 1.02rem;
        width: 100%;
        border: none;
        box-shadow: 0 10px 20px rgba(122, 60, 75, 0.22);
        font-family: 'Montserrat', sans-serif;
    }
    div[data-baseweb="select"] > div {
        border-radius: 14px;
        border-color: rgba(122,60,75,0.22);
    }
    .result-rank {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: #7A3C4B;
        color: #FFFFFF;
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        margin-right: 10px;
        flex-shrink: 0;
    }
    .result-product {
        font-family: 'Montserrat', sans-serif;
        color: #2B2B2B;
        font-size: 1.26rem;
        font-weight: 800;
        margin: 0;
    }
    .result-brand {
        font-family: 'Montserrat', sans-serif;
        color: #7A3C4B;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.8px;
        margin-top: 2px;
    }
    .recommend-title {
        font-family: 'Montserrat', sans-serif;
        color: #7A3C4B;
        font-size: 1.02rem;
        font-weight: 800;
        margin: 14px 0 6px 0;
    }
    .recommend-text {
        font-family: 'Montserrat', sans-serif;
        color: #333;
        font-size: 0.94rem;
        line-height: 1.55;
        margin-bottom: 10px;
    }
    .technical-box {
        background: #F7F2F4;
        border-left: 5px solid #EBA6A6;
        border-radius: 14px;
        padding: 12px 14px;
        margin-top: 10px;
        font-family: 'Montserrat', sans-serif;
        color: #333;
        font-size: 0.92rem;
        line-height: 1.5;
    }
    .mini-label {
        font-weight: 800;
        color: #7A3C4B;
    }
    hr {
        border: none;
        border-top: 1px solid rgba(0,0,0,0.08);
        margin: 14px 0;
    }
    </style>
    ''',
    unsafe_allow_html=True,
)


# ─── Utilidades ──────────────────────────────────────────────────────────────

def normalize_text(value: str) -> str:
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


def split_values(value: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;|,]", str(value or "")) if p.strip()]


def contains_choice(cell_value: str, choice: str) -> bool:
    """Retorna True se 'choice' está entre os valores da célula."""
    if not choice or choice in {"Todas", "Todos", "Qualquer"}:
        return True
    normalized_choice = normalize_text(choice)
    normalized_values = [normalize_text(v) for v in split_values(cell_value)]
    return normalized_choice in normalized_values or normalized_choice in normalize_text(cell_value)


def safe_get(row, column: str, default=""):
    if column not in row.index:
        return default
    value = row[column]
    return value if pd.notna(value) else default


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        str(col).replace("\ufeff", "").replace("\xa0", " ").strip()
        for col in df.columns
    ]
    aliases = {
        "produto": "Produto",
        "fabricante": "Fabricante",
        "filtro cor": "Filtro Cor",
        "filtro estilo": "Filtro Estilo",
        "filtro ocasiao": "Filtro Ocasião",
        "filtro sensacao": "Filtro Sensação",
        "score cor": "Score Cor",
        "score estilo": "Score Estilo",
        "score ocasiao": "Score Ocasião",
        "score sensacao": "Score Sensação",
        "score final recomendacao": "Score Final Recomendação",
        "titulo recomendacao": "Título Recomendação",
        "descricao curta": "Descrição Curta",
        "por que combina": "Por que combina",
        "justificativa tecnica simples": "Justificativa Técnica Simples",
        "dica de uso": "Dica de Uso",
        "combina com": "Combina com",
        "evitar quando": "Evitar quando",
        "ativo app": "Ativo App",
    }
    rename_map = {}
    for col in df.columns:
        normalized = normalize_text(col)
        if normalized in aliases:
            rename_map[col] = aliases[normalized]
    return df.rename(columns=rename_map)


def validate_columns(df: pd.DataFrame) -> None:
    required = [
        "Produto", "Fabricante",
        "Filtro Cor", "Filtro Estilo", "Filtro Ocasião", "Filtro Sensação",
        "Score Final Recomendação", "Ativo App",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas ausentes: {missing}. "
            f"Colunas recebidas: {df.columns.tolist()}"
        )


@st.cache_data(ttl=60, show_spinner=False)
def load_data(url: str) -> pd.DataFrame:
    response = requests.get(
        url, timeout=30, allow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "text/csv,text/plain,*/*"},
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    response_start = response.text.lstrip()[:500].lower()
    if (
        "text/html" in content_type
        or response_start.startswith("<!doctype html")
        or response_start.startswith("<html")
    ):
        raise ValueError(
            "O Google não retornou um CSV. "
            "Verifique se a planilha está acessível para leitura por link."
        )

    if not response.text.strip():
        raise ValueError("O Google retornou uma resposta vazia.")

    df = pd.read_csv(StringIO(response.text), encoding="utf-8-sig")
    df = normalize_columns(df)
    validate_columns(df)

    df = df[
        df["Ativo App"].astype(str).str.strip().str.casefold().eq("sim")
    ].copy()

    numeric_cols = [
        "Score Final Recomendação", "Score Cor", "Score Estilo",
        "Score Ocasião", "Score Sensação",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df.fillna("")


def unique_options(df: pd.DataFrame, column: str, default_label: str) -> list[str]:
    """Retorna lista de opções únicas e ordenadas de uma coluna de filtro."""
    EXCLUIR = {"tratamento", "indefinida", "indefinido", ""}
    values = []
    if column in df.columns:
        for item in df[column].tolist():
            values.extend(split_values(item))
    clean = sorted({
        v for v in values
        if normalize_text(v) not in EXCLUIR
    })
    return [default_label] + clean


# ─── Lógica de pontuação e filtragem ─────────────────────────────────────────

def match_filters(row, sensacao, cor, estilo, ocasiao) -> bool:
    """
    Retorna False se o produto NÃO atende a algum filtro obrigatório selecionado.
    Um filtro no valor padrão ("Todas"/"Todos") é ignorado.
    """
    checks = [
        (sensacao, "Filtro Sensação"),
        (cor,      "Filtro Cor"),
        (estilo,   "Filtro Estilo"),
        (ocasiao,  "Filtro Ocasião"),
    ]
    for choice, col in checks:
        if choice in {"Todas", "Todos", "Qualquer"}:
            continue
        if not contains_choice(safe_get(row, col), choice):
            return False
    return True


def calculate_app_score(row, sensacao, cor, estilo, ocasiao) -> float:
    """
    Calcula pontuação ponderada.
    Sensação tem o maior peso (30), depois Cor (25), Estilo (25) e Ocasião (20).
    O Score Final da planilha contribui com 30% extra como desempate.
    """
    score = 0.0
    active = 0  # quantos filtros foram realmente selecionados

    weights = [
        (sensacao, "Filtro Sensação", 30),
        (cor,      "Filtro Cor",      25),
        (estilo,   "Filtro Estilo",   25),
        (ocasiao,  "Filtro Ocasião",  20),
    ]

    for choice, col, w in weights:
        if choice not in {"Todas", "Todos", "Qualquer"}:
            active += 1
            if contains_choice(safe_get(row, col), choice):
                score += w

    base = float(safe_get(row, "Score Final Recomendação", 0) or 0)

    if active == 0:
        # nenhum filtro selecionado → usa só o score da planilha
        return round(base, 2)

    # desempate proporcional pelo score da planilha (max 30 pontos extras)
    score += base * 0.30
    return round(score, 2)


# ─── Renderização ─────────────────────────────────────────────────────────────

def escape_html(value) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_result_card(row, rank: int) -> None:
    produto    = escape_html(safe_get(row, "Produto"))
    fabricante = escape_html(safe_get(row, "Fabricante"))
    titulo     = escape_html(safe_get(row, "Título Recomendação", "Recomendação LIIVV") or "Recomendação LIIVV")
    descricao  = escape_html(safe_get(row, "Descrição Curta"))
    porque     = escape_html(safe_get(row, "Por que combina"))
    tecnica    = escape_html(safe_get(row, "Justificativa Técnica Simples"))
    dica       = escape_html(safe_get(row, "Dica de Uso"))
    combina    = escape_html(safe_get(row, "Combina com"))
    evitar     = escape_html(safe_get(row, "Evitar quando"))

    html = f'''
    <div class="result-card">
        <div style="display:flex; align-items:center;">
            <div class="result-rank">{rank}</div>
            <div>
                <p class="result-product">{produto}</p>
                <div class="result-brand">{fabricante}</div>
            </div>
        </div>
        <div class="recommend-title">{titulo}</div>
        <div class="recommend-text">{descricao}</div>
    '''

    if porque:
        html += f"<div class='recommend-text'><span class='mini-label'>Por que recomendamos:</span> {porque}</div>"
    if tecnica:
        html += f"<div class='technical-box'><span class='mini-label'>Base técnica simples:</span> {tecnica}</div>"
    if dica:
        html += f"<div class='recommend-text'><span class='mini-label'>Dica de uso:</span> {dica}</div>"
    if combina or evitar:
        html += "<hr>"
    if combina:
        html += f"<div class='small-text'><span class='mini-label'>Combina com:</span> {combina}</div>"
    if evitar:
        html += f"<div class='small-text'><span class='mini-label'>Evitar quando:</span> {evitar}</div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ─── Interface ────────────────────────────────────────────────────────────────

st.markdown(
    '''
    <div class="liivv-header">
        <div class="liivv-logo">LIIVV</div>
        <div class="liivv-subtitle">Beauty | Consultora de Cores</div>
    </div>
    ''',
    unsafe_allow_html=True,
)

st.markdown(
    '''
    <div class="intro-card">
        <div class="intro-title">Qual esmalte combina com você hoje?</div>
        <p class="intro-text">
            Escolha suas preferências e veja 3 sugestões objetivas da LIIVV,
            com uma explicação clara do motivo da recomendação.
        </p>
    </div>
    ''',
    unsafe_allow_html=True,
)

# ─── Carga dos dados ──────────────────────────────────────────────────────────

try:
    with st.spinner("Carregando opções..."):
        df = load_data(SHEET_URL)
except Exception as exc:
    st.error("Não foi possível carregar a base de esmaltes.")
    st.caption(
        "Verifique se a planilha está acessível para leitura e se a aba "
        "configurada é 'base_liivv_esmaltes_app'."
    )
    with st.expander("Detalhes técnicos"):
        st.code(str(exc))
    st.stop()

if df.empty:
    st.warning("A base não possui esmaltes ativos para exibição.")
    st.stop()

score_column = "Score Final Recomendação"
if score_column not in df.columns:
    st.error("A base foi carregada, mas a coluna de pontuação não foi encontrada.")
    with st.expander("Colunas recebidas"):
        st.write(df.columns.tolist())
    st.stop()

# ─── Filtros — Sensação primeiro ─────────────────────────────────────────────

# Usamos um contêiner para manter o HTML do card íntegro
with st.container():
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Escolha suas preferências</div>', unsafe_allow_html=True)

    # SENSAÇÃO como primeiro filtro (coluna maior para destaque)
    c_sens, c_cor, c_est, c_oc = st.columns(4)

    with c_sens:
        sensacao = st.selectbox(
            "✨ Sensação",
            unique_options(df, "Filtro Sensação", "Todas"),
            index=0,
        )
    with c_cor:
        cor = st.selectbox(
            "🎨 Cor",
            unique_options(df, "Filtro Cor", "Todas"),
            index=0,
        )
    with c_est:
        estilo = st.selectbox(
            "💅 Estilo",
            unique_options(df, "Filtro Estilo", "Todos"),
            index=0,
        )
    with c_oc:
        ocasiao = st.selectbox(
            "🌟 Ocasião",
            unique_options(df, "Filtro Ocasião", "Todas"),
            index=0,
        )

    buscar = st.button("Ver minhas 3 sugestões")
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Resultados ───────────────────────────────────────────────────────────────

if buscar:
    base = df.copy()

    # 1. Filtra somente produtos que atendem a TODOS os filtros selecionados
    mask = base.apply(
        lambda row: match_filters(row, sensacao, cor, estilo, ocasiao),
        axis=1,
    )
    base_filtrada = base[mask].copy()

    if base_filtrada.empty:
        st.markdown(
            '''
            <div class="empty-card">
                <div class="section-title">Não encontramos uma combinação ideal.</div>
                <p class="intro-text">
                    Nenhum esmalte combina com todas as preferências escolhidas ao mesmo tempo.
                    Tente ajustar ou remover um dos filtros.
                </p>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    else:
        # 2. Pontua e ordena os produtos que passaram pelo filtro
        base_filtrada["score_app"] = base_filtrada.apply(
            lambda row: calculate_app_score(row, sensacao, cor, estilo, ocasiao),
            axis=1,
        )
        resultado = (
            base_filtrada
            .sort_values(by=["score_app", score_column], ascending=[False, False])
            .head(3)
        )

        st.markdown(
            '<div class="section-title">Suas 3 sugestões LIIVV</div>',
            unsafe_allow_html=True,
        )
        for rank, (_, row) in enumerate(resultado.iterrows(), start=1):
            render_result_card(row, rank)

else:
    # Estado inicial: mostra destaques gerais
    sugestoes = (
        df.sort_values(by=score_column, ascending=False)
        .head(3)
    )
    st.markdown(
        '<div class="section-title">Sugestões em destaque</div>',
        unsafe_allow_html=True,
    )
    for rank, (_, row) in enumerate(sugestoes.iterrows(), start=1):
        render_result_card(row, rank)
