import re
import unicodedata
from io import StringIO

import pandas as pd
import requests
import streamlit as st


# =========================
# CONFIG
# =========================
st.set_page_config(page_title="LIIVV Beauty | Esmaltes", layout="wide")

DEFAULT_CSV_URL = "https://docs.google.com/spreadsheets/d/12BCdp9_E8xbGZrIhw8-r7rYxkXyCDtGjYZ8fLXp0px4/export?format=csv&gid=1837554661"
SHEET_URL = st.secrets.get("GOOGLE_SHEET_CSV_URL", DEFAULT_CSV_URL)


# =========================
# CSS
# =========================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@300;400;500;600;700;800&display=swap');

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
        font-family: 'Playfair Display', serif;
        font-size: 4.4rem;
        color: #EBA6A6;
        margin: 0;
        letter-spacing: 3px;
        line-height: 0.9;
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
    """,
    unsafe_allow_html=True,
)


def normalize_text(value: str) -> str:
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return value


def split_values(value: str):
    raw = str(value or "")
    parts = re.split(r"[;|,]", raw)
    return [p.strip() for p in parts if p and p.strip()]


def contains_choice(cell_value: str, choice: str) -> bool:
    if not choice or choice in ["Todas", "Todos", "Qualquer"]:
        return True

    c = normalize_text(choice)
    values = [normalize_text(v) for v in split_values(cell_value)]

    return c in values or c in normalize_text(cell_value)


def safe_get(row, col, default=""):
    return row[col] if col in row and pd.notna(row[col]) else default


@st.cache_data(ttl=300)
def load_data(url: str) -> pd.DataFrame:
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df.columns = [str(c).strip() for c in df.columns]

    if "Ativo App" in df.columns:
        df = df[df["Ativo App"].astype(str).str.strip().str.lower().eq("sim")]

    for col in [
        "Score Final Recomendação",
        "Score Cor",
        "Score Estilo",
        "Score Ocasião",
        "Score Sensação",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df.fillna("")


def unique_options(df: pd.DataFrame, column: str, default_label: str) -> list[str]:
    values = []

    if column in df.columns:
        for item in df[column].tolist():
            values.extend(split_values(item))

    clean = sorted(
        set(
            v for v in values
            if v and normalize_text(v) not in ["tratamento", "indefinida"]
        )
    )

    return [default_label] + clean


def calculate_app_score(row, cor, estilo, ocasiao, sensacao):
    score = 0
    selected = 0

    if cor != "Todas":
        selected += 1
        score += 35 if contains_choice(safe_get(row, "Filtro Cor"), cor) else 8

    if estilo != "Todos":
        selected += 1
        score += 25 if contains_choice(safe_get(row, "Filtro Estilo"), estilo) else 6

    if ocasiao != "Todas":
        selected += 1
        score += 20 if contains_choice(safe_get(row, "Filtro Ocasião"), ocasiao) else 4

    if sensacao != "Todas":
        selected += 1
        score += 20 if contains_choice(safe_get(row, "Filtro Sensação"), sensacao) else 4

    base_score = float(safe_get(row, "Score Final Recomendação", 0) or 0)
    score += base_score * 0.30

    if selected == 0:
        score = base_score

    return round(score, 2)


def render_result_card(row, rank):
    produto = safe_get(row, "Produto")
    fabricante = safe_get(row, "Fabricante")
    titulo = safe_get(row, "Título Recomendação") or "Recomendação LIIVV"
    descricao = safe_get(row, "Descrição Curta")
    porque = safe_get(row, "Por que combina")
    tecnica = safe_get(row, "Justificativa Técnica Simples")
    dica = safe_get(row, "Dica de Uso")
    combina = safe_get(row, "Combina com")
    evitar = safe_get(row, "Evitar quando")

    st.markdown('<div class="result-card">', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="display:flex; align-items:center;">
            <div class="result-rank">{rank}</div>
            <div>
                <p class="result-product">{produto}</p>
                <div class="result-brand">{fabricante}</div>
            </div>
        </div>

        <div class="recommend-title">{titulo}</div>
        <div class="recommend-text">{descricao}</div>
        """,
        unsafe_allow_html=True,
    )

    if porque:
        st.markdown(
            f"<div class='recommend-text'><span class='mini-label'>Por que recomendamos:</span> {porque}</div>",
            unsafe_allow_html=True,
        )

    if tecnica:
        st.markdown(
            f"<div class='technical-box'><span class='mini-label'>Base técnica simples:</span> {tecnica}</div>",
            unsafe_allow_html=True,
        )

    if dica:
        st.markdown(
            f"<div class='recommend-text'><span class='mini-label'>Dica de uso:</span> {dica}</div>",
            unsafe_allow_html=True,
        )

    if combina or evitar:
        st.markdown("<hr>", unsafe_allow_html=True)

    if combina:
        st.markdown(
            f"<div class='small-text'><span class='mini-label'>Combina com:</span> {combina}</div>",
            unsafe_allow_html=True,
        )

    if evitar:
        st.markdown(
            f"<div class='small-text'><span class='mini-label'>Evitar quando:</span> {evitar}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


st.markdown(
    """
    <div class="liivv-header">
        <div class="liivv-logo">LIIVV</div>
        <div class="liivv-subtitle">Beauty | Consultora de Cores</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="intro-card">
        <div class="intro-title">Qual esmalte combina com você hoje?</div>
        <p class="intro-text">Escolha suas preferências e veja 3 sugestões objetivas da LIIVV, com uma explicação clara do motivo da recomendação.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    df = load_data(SHEET_URL)
except Exception as exc:
    st.error("Não foi possível carregar a base de esmaltes. Confira se a aba está publicada como CSV ou se o secret GOOGLE_SHEET_CSV_URL está correto.")
    st.caption(str(exc))
    st.stop()

if df.empty:
    st.warning("A base de esmaltes está vazia ou sem itens ativos para o app.")
    st.stop()

st.markdown('<div class="filter-card"><div class="section-title">Escolha suas preferências</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    cor = st.selectbox("Cor", unique_options(df, "Filtro Cor", "Todas"), index=0)

with c2:
    estilo = st.selectbox("Estilo", unique_options(df, "Filtro Estilo", "Todos"), index=0)

with c3:
    ocasiao = st.selectbox("Ocasião", unique_options(df, "Filtro Ocasião", "Todas"), index=0)

with c4:
    sensacao = st.selectbox("Sensação", unique_options(df, "Filtro Sensação", "Todas"), index=0)

buscar = st.button("Ver minhas 3 sugestões")

st.markdown("</div>", unsafe_allow_html=True)

if buscar:
    base = df.copy()

    base["score_app"] = base.apply(
        lambda r: calculate_app_score(r, cor, estilo, ocasiao, sensacao),
        axis=1,
    )

    resultado = base.sort_values(
        ["score_app", "Score Final Recomendação"],
        ascending=False,
    ).head(3)

    if resultado.empty:
        st.markdown(
            """
            <div class="empty-card">
                <div class="section-title">Não encontramos uma combinação ideal com esses filtros.</div>
                <p class="intro-text">Tente reduzir uma preferência ou escolher opções mais amplas.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="section-title">Suas 3 sugestões LIIVV</div>', unsafe_allow_html=True)

        for i, (_, row) in enumerate(resultado.iterrows(), start=1):
            render_result_card(row, i)

else:
    sugestoes = df.sort_values("Score Final Recomendação", ascending=False).head(3)

    st.markdown('<div class="section-title">Sugestões em destaque</div>', unsafe_allow_html=True)

    for i, (_, row) in enumerate(sugestoes.iterrows(), start=1):
        render_result_card(row, i)
