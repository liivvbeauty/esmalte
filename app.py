import os
import re
from urllib.parse import quote

import pandas as pd
import streamlit as st

# =========================
# CONFIG LIIVV
# =========================
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID", "12BCdp9_E8xbGZrIhw8-r7rYxkXyCDtGjYZ8fLXp0px4")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "base_liivv_esmaltes_app")
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(SHEET_NAME)}"

st.set_page_config(page_title="LIIVV Beauty | Consultora de Cores", layout="centered")

# =========================
# CSS LIIVV
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@300;400;600;700;800&display=swap');
.stApp { background: #F7F2F4; }
.block-container { padding-top: 0.8rem; max-width: 980px; }
.header-container { background: linear-gradient(135deg, #7A3C4B 0%, #2B2B2B 100%); padding: 36px 18px 30px; border-radius: 0 0 34px 34px; text-align: center; margin: -16px -8px 22px; box-shadow: 0 10px 24px rgba(0,0,0,0.20); }
.header-title { font-family: 'Playfair Display', serif; font-size: 4.4rem; color: #EBA6A6 !important; margin: 0; letter-spacing: 4px; line-height: .92; }
.header-subtitle { font-family: 'Montserrat', sans-serif; color: #F7F2F4; font-size: .78rem; letter-spacing: 4px; text-transform: uppercase; margin-top: 10px; font-weight: 700; }
.intro-card, .filter-card, .result-card { background: white; padding: 18px; border-radius: 20px; box-shadow: 0 8px 18px rgba(0,0,0,0.08); margin-bottom: 14px; border: 1px solid rgba(122,60,75,.08); }
.section-title { font-family: 'Montserrat', sans-serif; font-weight: 800; color: #7A3C4B; margin: 0 0 8px 0; font-size: 1.05rem; }
.small-note, p, label, div { font-family: 'Montserrat', sans-serif; }
.small-note { color: #666; font-size: .92rem; line-height: 1.45; }
.badge { display:inline-block; padding: 6px 10px; border-radius: 999px; background:#F7F2F4; color:#7A3C4B; border:1px solid rgba(122,60,75,.18); font-size:.78rem; font-weight:700; margin-right:6px; margin-bottom:6px; }
div.stButton > button { background: linear-gradient(135deg, #EBA6A6 0%, #7A3C4B 100%); color: white !important; border-radius: 50px; padding: .9rem 1rem; font-weight: 800; font-size: 1rem; width: 100%; border: none; box-shadow: 0 10px 20px rgba(122,60,75,.20); }
.result-card { border-left: 8px solid #EBA6A6; }
.rank { color:#7A3C4B; font-weight:800; font-size:.9rem; letter-spacing:1px; }
.product { font-family:'Playfair Display', serif; color:#2B2B2B; font-size:1.65rem; margin: 2px 0 0; line-height:1.05; }
.brand { color:#777; font-weight:700; font-size:.78rem; text-transform:uppercase; letter-spacing:1.5px; }
.score-pill { background:#2B2B2B; color:#F7F2F4; border-radius: 999px; padding: 7px 11px; font-size:.82rem; font-weight:800; display:inline-block; margin-top:8px; }
.tech-box { background:#F7F2F4; border-radius: 14px; padding: 12px; margin-top: 10px; color:#333; border:1px solid rgba(122,60,75,.10); }
.tech-title { color:#7A3C4B; font-weight:800; font-size:.86rem; margin-bottom:4px; }
hr { border: none; border-top: 1px solid rgba(0,0,0,.08); margin: 12px 0; }
[data-testid="stMetricValue"] { color:#7A3C4B; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
  <h1 class="header-title">LIIVV</h1>
  <p class="header-subtitle">Consultora de Cores | Beauty</p>
</div>
""", unsafe_allow_html=True)

# =========================
# DATA
# =========================
@st.cache_data(ttl=300, show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_URL)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()
    if "Ativo App" in df.columns:
        df = df[df["Ativo App"].str.upper().eq("SIM")]
    if "Produto" in df.columns:
        df = df[df["Produto"].ne("")]
    if "Score Final Recomendação" in df.columns:
        df["Score Final Recomendação"] = pd.to_numeric(df["Score Final Recomendação"].str.replace(",", ".", regex=False), errors="coerce").fillna(0)
    return df

def split_values(series):
    vals=[]
    for x in series.dropna().astype(str):
        for part in re.split(r";|,", x):
            p=part.strip()
            if p and p.upper() not in {"NAN", ""}:
                vals.append(p)
    return sorted(set(vals))

def contains_filter(df, col, selected):
    if not selected or selected == "Todas":
        return pd.Series([True]*len(df), index=df.index)
    return df[col].astype(str).str.contains(re.escape(selected), case=False, na=False)

try:
    df = load_data()
except Exception as e:
    st.error("Não consegui carregar a base da planilha. Verifique se a aba está publicada/compartilhada para leitura ou se o nome da aba está correto.")
    st.caption(str(e))
    st.stop()

st.markdown(f"""
<div class="intro-card">
  <div class="section-title">Encontre seu esmalte em 30 segundos</div>
  <div class="small-note">Escolha uma opção em cada filtro. A LIIVV mostra até 3 recomendações com explicação objetiva, usando os atributos da planilha enriquecida.</div>
  <hr>
  <span class="badge">{len(df)} opções ativas</span>
  <span class="badge">resultado direto</span>
  <span class="badge">explicação técnica simples</span>
</div>
""", unsafe_allow_html=True)

# =========================
# FILTERS
# =========================
with st.container():
    st.markdown('<div class="filter-card"><div class="section-title">Como você quer sua unha hoje?</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        cor = st.selectbox("Cor", ["Todas"] + split_values(df.get("Filtro Cor", pd.Series(dtype=str))))
        ocasiao = st.selectbox("Ocasião", ["Todas"] + split_values(df.get("Filtro Ocasião", pd.Series(dtype=str))))
    with c2:
        estilo = st.selectbox("Estilo", ["Todas"] + split_values(df.get("Filtro Estilo", pd.Series(dtype=str))))
        sensacao = st.selectbox("Sensação", ["Todas"] + split_values(df.get("Filtro Sensação", pd.Series(dtype=str))))
    buscar = st.button("Ver minhas 3 sugestões")
    st.markdown('</div>', unsafe_allow_html=True)

filtered = df.copy()
for col, val in [("Filtro Cor", cor), ("Filtro Estilo", estilo), ("Filtro Ocasião", ocasiao), ("Filtro Sensação", sensacao)]:
    if col in filtered.columns:
        filtered = filtered[contains_filter(filtered, col, val)]

if len(filtered) == 0:
    st.warning("Não encontrei opções com essa combinação. Tente deixar um dos filtros como 'Todas'.")
    st.stop()

filtered = filtered.sort_values("Score Final Recomendação", ascending=False).head(3)

# =========================
# RESULTS
# =========================
if buscar or True:
    st.markdown('<div class="section-title" style="margin: 18px 0 10px;">Suas recomendações LIIVV</div>', unsafe_allow_html=True)
    for i, (_, row) in enumerate(filtered.iterrows(), start=1):
        produto = row.get("Produto", "")
        fabricante = row.get("Fabricante", "")
        score = int(float(row.get("Score Final Recomendação", 0) or 0))
        titulo = row.get("Título Recomendação", "Recomendação LIIVV")
        desc = row.get("Descrição Curta", "")
        porque = row.get("Por que combina", "")
        tecnica = row.get("Justificativa Técnica Simples", "")
        dica = row.get("Dica de Uso", "")
        combina = row.get("Combina com", "")
        evitar = row.get("Evitar quando", "")
        familia = row.get("Família Cor", "")
        acabamento = row.get("Acabamento", "")
        contraste = row.get("Contraste", "")
        formalidade = row.get("Formalidade", "")
        estoque = row.get("Quantidade em Estoque", "")

        st.markdown(f"""
        <div class="result-card">
          <div class="rank">OPÇÃO {i}</div>
          <div class="product">{produto}</div>
          <div class="brand">{fabricante}</div>
          <div class="score-pill">Compatibilidade LIIVV: {score}%</div>
          <p style="font-weight:800;color:#7A3C4B;margin-top:14px;margin-bottom:4px;">{titulo}</p>
          <p style="margin-top:0;color:#333;line-height:1.45;">{desc}</p>
          <div class="tech-box">
            <div class="tech-title">Por que recomendamos</div>
            <div>{porque}</div>
          </div>
          <div class="tech-box">
            <div class="tech-title">Base técnica simples</div>
            <div>{tecnica}</div>
          </div>
          <div style="margin-top:10px;">
            <span class="badge">{familia}</span>
            <span class="badge">{acabamento}</span>
            <span class="badge">Contraste {contraste}</span>
            <span class="badge">Formalidade {formalidade}</span>
            <span class="badge">Estoque {estoque}</span>
          </div>
          <hr>
          <p style="margin-bottom:6px;"><b>Dica de uso:</b> {dica}</p>
          <p style="margin-bottom:6px;"><b>Combina com:</b> {combina}</p>
          <p style="margin-bottom:0;color:#777;"><b>Evitar quando:</b> {evitar}</p>
        </div>
        """, unsafe_allow_html=True)

st.caption("LIIVV Beauty | As recomendações dependem da base enriquecida na planilha e podem ser ajustadas pela equipe sem alterar o código do app.")
