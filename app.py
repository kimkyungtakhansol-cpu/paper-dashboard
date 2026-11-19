"""천안공장 지종별 손익 분석 — 새 디자인(Stitch 시안 'Precision Industrial Telemetry' 기반).

기존 앱(../app.py)과 데이터(../data)·계정(../users.json)을 함께 사용합니다.
실행: app_v2 폴더에서  streamlit run app.py --server.port 8503
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent  # 배포용: 이 폴더 안의 data 사용

st.set_page_config(page_title="천안공장 지종별 손익 분석", page_icon="📊", layout="wide")
METRICS = ["판매량(톤)", "매출액(원)", "EBITDA원가(원)", "EBITDA(원)", "공헌이익(원)"]

# ---------- 디자인 토큰 (Stitch DESIGN.md) ----------
INK, INK2, MUTED = "#0F172A", "#334155", "#475569"
LINE, LINE2, HEAD = "#E2E8F0", "#F1F5F9", "#F1F5F9"
DOM, DOM_BG, DOM_BD = "#2563EB", "#EFF6FF", "#BFDBFE"
EXP, EXP_BG, EXP_BD, EXP_TX = "#10B981", "#ECFDF5", "#A7F3D0", "#047857"
NEG, NEG_BG = "#DC2626", "#FEF2F2"
DOM_CELL, EXP_CELL = "#93C5FD", "#6EE7B7"  # 비교도 매트릭스 칸 색 (내수 우위 / 수출 우위)
CHART = ["#2563EB", "#0D9488", "#F59E0B", "#8B5CF6", "#EC4899"]
ACCENT = ["#2563EB", "#0D9488", "#F59E0B"]
FONT = "Inter, 'Noto Sans KR', 'Malgun Gothic', sans-serif"
MONO = "'JetBrains Mono', 'Noto Sans KR', monospace"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&family=Noto+Sans+KR:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
.stApp {{background:#F8FAFC; font-family:{FONT};}}
.block-container {{padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1480px;}}
.stDeployButton, footer {{display:none !important;}}
header[data-testid="stHeader"] {{background: transparent;}}
.stApp, .stApp p, .stApp li, .stApp label {{color:{INK};}}
.stApp [data-testid="stMarkdownContainer"] p {{font-size: 15px;}}
.stApp label p, .stApp [data-testid="stWidgetLabel"] p {{font-size: 14px !important; font-weight: 600 !important; color:{INK2} !important;}}
.mono {{font-family:{MONO}; font-variant-numeric: tabular-nums;}}

/* 카드 */
div[data-testid="stVerticalBlockBorderWrapper"] {{background:#fff; border-radius:14px; border:1px solid {LINE} !important; box-shadow:none;}}
.card-h {{display:flex; align-items:center; gap:10px; margin:2px 0 2px 0;}}
.card-bar {{width:5px; height:24px; border-radius:3px; display:inline-block;}}
.card-t {{font-family:'Space Grotesk', {FONT}; font-size: 21px; font-weight:700; color:{INK}; letter-spacing:-.3px;}}
.card-s {{font-size:14px; color:{MUTED}; margin:2px 0 6px 15px;}}

/* 상단 바 */
.topbar {{display:flex; align-items:center; gap:12px;}}
.topbar .t {{font-family:'Space Grotesk', {FONT}; font-size:24px; font-weight:700; color:{INK}; letter-spacing:-.4px;}}
.topbar .s {{font-size:13.5px; color:{MUTED}; margin-top:2px;}}
.tag {{display:inline-block; font-size:11.5px; font-weight:700; letter-spacing:.06em; padding:3px 10px; border-radius:9999px; background:{LINE2}; color:{INK2};}}
.chip {{display:inline-flex; align-items:center; gap:8px; padding:8px 16px; border-radius:9999px; background:{DOM_BG}; color:{INK}; font-size:14px; font-weight:600; white-space:nowrap;}}
.chip b {{font-family:{MONO}; font-weight:700;}}
.who {{display:flex; align-items:center; justify-content:flex-end; gap:10px; white-space:nowrap;}}
.who .av {{width:34px; height:34px; border-radius:50%; background:{INK}; color:#fff; display:flex; align-items:center; justify-content:center; font-size:15px;}}
.who .n {{font-weight:700; font-size:14.5px; line-height:1.2;}}
.who .r {{font-size:12.5px; color:{MUTED};}}

/* 탭 → 알약 */
[data-testid="stTabs"] [role="tablist"] {{gap:6px; background:{LINE2}; padding:5px; border-radius:9999px; width:fit-content; border:none !important; box-shadow:none !important;}}
[data-testid="stTabs"] [role="tablist"]::after, [data-testid="stTabs"] [role="tablist"]::before {{display:none !important;}}
[data-testid="stTab"] {{border-radius:9999px !important; padding:8px 22px !important; background:transparent; border:none !important; box-shadow:none !important;}}
[data-testid="stTab"]::after, [data-testid="stTab"]::before {{display:none !important;}}
[data-testid="stTab"] p {{font-size:15px !important; font-weight:600 !important; color:{INK2} !important; margin:0;}}
[data-testid="stTab"][aria-selected="true"] {{background:{INK} !important;}}
[data-testid="stTab"][aria-selected="true"] p {{color:#fff !important;}}
.stApp button[data-variant="segmented_control"] {{background:{LINE2} !important; border:1px solid transparent !important; margin-right:4px;}}
.stApp button[data-variant="segmented_control"][aria-checked="true"] {{background:{INK} !important; border-color:{INK} !important;}}
.stApp button[data-variant="segmented_control"][aria-checked="true"] p {{color:#fff !important;}}

/* 버튼 */
.stApp button {{border-radius:9999px !important;}}
.stApp button p {{font-size:14px; font-weight:600;}}
.stApp [data-testid="stBaseButton-primary"], .stApp [data-testid="stBaseButton-primaryFormSubmit"] {{background:{INK} !important; border-color:{INK} !important;}}
.stApp [data-testid="stBaseButton-primary"] p, .stApp [data-testid="stBaseButton-primaryFormSubmit"] p {{color:#fff !important;}}
.stApp [data-testid="stBaseButton-segmented_control"] {{background:{LINE2} !important; border:1px solid transparent !important; margin-right:4px;}}
.stApp [data-testid="stBaseButton-segmented_controlActive"] {{background:{INK} !important; border-color:{INK} !important; margin-right:4px;}}
.stApp [data-testid="stBaseButton-segmented_controlActive"] p {{color:#fff !important;}}
.stApp [data-testid="stPopover"] button {{background:#fff; border:1px solid #CBD5E1 !important;}}
.stApp [data-testid="stPopover"] button p {{font-weight:700; color:{INK};}}
.stApp input {{font-size:15px !important;}}
.stApp [data-testid="stExpander"] summary p {{font-size:14.5px; font-weight:700;}}

/* 조건 선택 미니 카드 */
.f-h {{display:flex; justify-content:space-between; align-items:center; margin-bottom:-6px;}}
.f-sel {{font-size:14.5px; font-weight:700; color:{INK}; text-align:center; line-height:1.35; margin-top:-6px;}}
.f-l {{font-size:13.5px; font-weight:700; color:{INK2};}}
.f-b {{font-family:{MONO}; font-size:12.5px; font-weight:700; background:{INK}; color:#fff; padding:2px 10px; border-radius:9999px;}}
.f-r {{font-size:12.5px; color:{MUTED}; text-align:center; margin-top:3px;}}

/* 범례 알약 */
.lg {{display:inline-flex; align-items:center; gap:6px; padding:5px 14px; border-radius:9999px; font-size:13.5px; font-weight:700; margin-right:6px;}}
.lg i {{width:9px; height:9px; border-radius:50%; display:inline-block;}}

/* 로그인 */
.lg-side {{background:{INK}; color:#fff; border-radius:20px; padding:36px 34px; min-height:420px;}}
.lg-side .k {{display:inline-block; background:{EXP_TX}; color:#ECFDF5; font-family:{MONO}; font-size:12px; font-weight:700; padding:3px 10px; border-radius:6px;}}
.lg-side h2 {{font-family:'Space Grotesk', {FONT}; color:#fff; font-size:28px; line-height:1.35; margin:18px 0 10px;}}
.lg-side p {{color:#CBD5E1 !important; font-size:15px; line-height:1.6;}}
.lg-tile {{background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.12); border-radius:12px; padding:14px 16px; margin-top:12px;}}
.lg-tile b {{color:#fff; font-size:15px;}}
.lg-tile span {{color:#CBD5E1; font-size:13.5px;}}
.err {{background:{NEG_BG}; border:1px solid #FECACA; color:{NEG}; border-radius:12px; padding:12px 16px; font-size:14.5px; font-weight:700;}}
.err span {{display:block; font-weight:500; font-size:13px; margin-top:3px;}}
.note {{background:{LINE2}; border-radius:12px; padding:10px 16px; font-size:13.5px; color:{INK2};}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- 데이터 위치 ----------
DATA_DIR = ROOT / "data"
PL_PATH = DATA_DIR / "지종별 손익.xlsx"
PROD_PATH = DATA_DIR / "지종별 생산성.xlsx"
META_PATH = DATA_DIR / "meta.json"


def load_meta():
    try:
        return json.loads(META_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_meta(meta):
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def norm_period(v):
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return str(v)


meta = load_meta()

# ---------- 상단 바 (로그인 없음: 접속하면 바로 조회) ----------
with st.container(border=True):
    tb1, tb2 = st.columns([4.2, 2.2])
    tb1.markdown(
        "<div class='topbar'><div><div class='t'>천안공장 지종별 손익 분석 <span class='tag'>CHEONAN PLANT</span></div>"
        "<div class='s'>내수·수출 / 호기별 판매·손익과 일 기여이익 분석</div></div></div>",
        unsafe_allow_html=True,
    )
    tb2.markdown(f"<div style='padding-top:8px;text-align:right'><span class='chip'>📅 데이터 기준일 <b>{meta.get('date', '-')}</b></span></div>",
                 unsafe_allow_html=True)

if not PL_PATH.exists():
    st.error("데이터 파일(data 폴더의 '지종별 손익.xlsx')을 찾을 수 없습니다.")
    st.stop()

# ---------- 데이터 읽기 ----------
sheets = pd.read_excel(PL_PATH, sheet_name=None)
if len(sheets) < 2:
    st.error("손익 파일에는 시트가 2개(손익, 호기) 있어야 합니다.")
    st.stop()
names = list(sheets)
df = sheets[names[0]].copy()
mapping = sheets[names[1]].copy()
df["기간"] = df["기간"].map(norm_period)
df = df.merge(mapping, on="지종", how="left")
df["호기"] = df["호기"].fillna("미지정")
if PROD_PATH.exists():
    prod = pd.read_excel(PROD_PATH)
    prod["기간"] = prod["기간"].map(norm_period)
    df = df.merge(prod, on=["기간", "지종"], how="left")
df_all = df.copy()


def fnum(v, f):
    """숫자 표기: 쉼표, 음수는 붉은색."""
    if pd.isna(v):
        return "-"
    s = format(v, f)
    return f"<span style='color:{NEG}'>{s}</span>" if v < 0 else s


def nm(k):
    """긴 이름 줄바꿈: '_' 뒤, '(' 앞, 한글→영문 경계 우선, 그래도 넘치면 적당히 두 줄."""
    t = k.replace(" ", "&nbsp;").replace("_", "⁠_<wbr>")
    t = re.sub(r"([가-힣])([A-Za-z])", r"\1<wbr>\2", t)
    t = re.sub(r"\([^)]*\)", lambda m: f"<wbr><span style='white-space:nowrap'>{m.group(0)}</span>", t)
    return f"<span style='overflow-wrap:anywhere;word-break:keep-all'>{t}</span>"


def card_head(title, desc, color):
    st.markdown(f"<div class='card-h'><span class='card-bar' style='background:{color}'></span>"
                f"<span class='card-t'>{title}</span></div><div class='card-s'>{desc}</div>", unsafe_allow_html=True)


tab_main, tab_cmp = st.tabs(["기본 분석", "일기여이익 비교도"])

# =====================================================================
# 일기여이익 비교도
# =====================================================================
MIN_QTY = 10  # 일기여이익 비교도 표시 기준: 내수/수출별 월 판매량(톤)


def cmp_data(month, ho):
    d = df_all[(df_all["기간"] == month) & (df_all["호기"] == ho)]
    res = {}
    for ch in ["내수", "수출"]:
        x = d[d["유통경로"] == ch].groupby("지종").agg(
            qty=("판매량(톤)", "sum"), mar=("공헌이익(원)", "sum"),
            eb=("EBITDA(원)", "sum"), prod=("생산성(톤/일)", "mean"))
        x = x[x["qty"] >= MIN_QTY].copy()  # 해당 월 판매량 10톤 이상 지종만 표시
        x["tmar"] = x["mar"] / x["qty"] / 1000                   # 톤당 공헌이익(천원/톤)
        x["dmar"] = x["tmar"] * x["prod"] / 1000                 # 일 기여이익(백만원/일)
        x["deb"] = x["eb"] / x["qty"] / 1000 * x["prod"] / 1000  # 일 EBITDA(백만원/일)
        res[ch] = x.sort_values("dmar", ascending=False)
    return res


def cmp_html(month, ho):
    """기존 앱(8502)과 같은 셀 구조(계단형 헤더 + 매트릭스), 스타일만 새 디자인."""
    r = cmp_data(month, ho)
    dom, exp = r["내수"], r["수출"]
    if dom.empty or exp.empty:
        return None
    ncols = 5 + len(exp)
    colgroup = "<colgroup>" + f"<col style='width:{100 / ncols:.4f}%'>" * ncols + "</colgroup>"
    TD = (f"border:1px solid {LINE};padding:4px 6px;text-align:center;font-size:14px;line-height:1.3;height:50px;"
          "vertical-align:middle;overflow:hidden;overflow-wrap:anywhere;word-break:keep-all;text-wrap:balance;")

    def cell(t, bg="#fff", attrs="", color=INK, bold=True, mono=False):
        fam = f"font-family:{MONO};" if mono else ""
        # 셀 높이 고정: 내용은 최대 두 줄까지만 표시 (열이 좁아져도 행 높이가 늘어나지 않음)
        inner = (f"<div style='display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;"
                 f"overflow:hidden;max-height:2.6em'>{t}</div>")
        return (f"<td {attrs} style='{TD}background:{bg};color:{color};{fam}"
                f"{'font-weight:700;' if bold else ''}'>{inner}</td>")

    LBL, LBL_C = "#CBD5E1", INK                                     # 구분/수출/내수 (옅은 슬레이트)
    # 판매량 / 공헌이익 / 일 기여이익 / 일 EBITDA : 서로 구분되는 연한 색
    C_QTY, C_MAR, C_DM, C_EB = "#DCFCE7", "#E0E7FF", "#FEF3C7", "#E2E8F0"
    h = [f"<div style='display:flex;justify-content:space-between;align-items:flex-end;margin:2px 0 10px'>"
         f"<span class='card-t'># 일 기여이익 비교도 · {ho} · {month}</span>"
         f"<span style='font-size:13.5px;color:{INK2}'>( 단위 : 톤, 천원, 백만원 )</span></div>",
         f"<div style='overflow-x:auto;border-radius:12px'>"
         f"<table style='border-collapse:collapse;width:100%;table-layout:fixed'>{colgroup}"]
    h.append("<tr>" + cell("구분", LBL, color=LBL_C) + cell("수출", LBL, "colspan=4", LBL_C)
             + "".join(cell(nm(k), EXP_TX, color="#fff") for k in exp.index) + "</tr>")
    h.append("<tr>" + cell("내수", LBL, "rowspan=4", LBL_C) + cell(nm("판매량(톤)"), C_QTY, "colspan=4")
             + "".join(cell(f"{v:,.0f}", C_QTY, mono=True) for v in exp["qty"]) + "</tr>")
    h.append("<tr>" + cell(nm("판매량(톤)"), C_QTY, "rowspan=3") + cell(nm("공헌이익(천원/톤)"), C_MAR, "colspan=3")
             + "".join(cell(fnum(v, ',.1f'), C_MAR, mono=True) for v in exp["tmar"]) + "</tr>")
    h.append("<tr>" + cell(nm("공헌이익(천원/톤)"), C_MAR, "rowspan=2") + cell(nm("일 기여이익(백만원/일)"), C_DM, "colspan=2")
             + "".join(cell(fnum(v, ',.1f'), C_DM, mono=True) for v in exp["dmar"]) + "</tr>")
    h.append("<tr>" + cell(nm("일 기여이익(백만원/일)"), C_DM) + cell(nm("일 EBITDA(백만원/일)"), C_EB)
             + "".join(cell(fnum(v, ',.1f'), C_EB, mono=True) for v in exp["deb"]) + "</tr>")
    for k, row in dom.iterrows():
        h.append("<tr>" + cell(nm(k), DOM, color="#fff") + cell(f"{row.qty:,.0f}", C_QTY, mono=True)
                 + cell(fnum(row.tmar, ',.1f'), C_MAR, mono=True) + cell(fnum(row.dmar, ',.1f'), C_DM, mono=True)
                 + cell(fnum(row.deb, ',.1f'), C_EB, mono=True))
        for e in exp["dmar"]:
            a_, b_ = round(row.dmar, 1), round(e, 1)
            if a_ == b_:
                h.append(cell("동일", DOM_CELL, color="#1D4ED8"))
            else:
                h.append(cell("", DOM_CELL if a_ > b_ else EXP_CELL))
        h.append("</tr>")
    h.append("</table></div>")
    return "".join(h)


with tab_cmp:
    if "생산성(톤/일)" not in df_all.columns:
        st.info("일 기여이익 비교도는 생산성 데이터(지종별 생산성.xlsx)가 있어야 표시됩니다.")
    else:
        with st.container(border=True):
            c1, c2 = st.columns([1, 2.4])
            months = sorted(df_all["기간"].unique())
            month = c1.selectbox("📅 기간 선택", months, index=len(months) - 1)
            c2.markdown(
                f"<div style='padding-top:30px;text-align:right'>"
                f"<span class='lg' style='background:{DOM_CELL};color:#1E3A8A'>내수가 이익 높음</span>"
                f"<span class='lg' style='background:{EXP_CELL};color:#065F46'>수출이 이익 높음</span>"
                f"<span style='font-size:13px;color:{MUTED}'>ⓘ 일 기여이익 기준 · 동률 시 내수 색상으로 '동일' 표기</span></div>",
                unsafe_allow_html=True,
            )
        hos = [h_ for h_ in ["PM513", "PM52"] if h_ in set(df_all["호기"])] or sorted(df_all["호기"].unique())
        for sub, ho in zip(st.tabs(hos), hos):
            with sub, st.container(border=True):
                html = cmp_html(month, ho)
                if html is None:
                    st.warning("해당 기간·호기의 내수/수출 데이터가 없습니다.")
                else:
                    st.markdown(html, unsafe_allow_html=True)

# =====================================================================
# 기본 분석
# =====================================================================
with tab_main:
    def summary(sel, limit=18):
        s = " · ".join(sel) if sel else "선택 없음"
        return s if len(s) <= limit else s[:limit - 1] + "…"

    def pick_multi(container, label, col, all_opts, enabled, min_n, max_n, rule):
        enabled = [o for o in all_opts if o in set(enabled)]
        keys = {o: f"{col}::{o}" for o in all_opts}
        sig_key = f"sig::{col}"
        if st.session_state.get(sig_key) != tuple(enabled):
            for o in all_opts:
                st.session_state[keys[o]] = (o in enabled) and (enabled.index(o) < max_n)
            st.session_state[sig_key] = tuple(enabled)
        for o in [o for o in enabled if st.session_state[keys[o]]][max_n:]:
            st.session_state[keys[o]] = False
        n_sel = sum(bool(st.session_state[keys[o]]) for o in enabled)
        sel = [o for o in enabled if st.session_state[keys[o]]]
        with container, st.container(border=True):
            # 버튼에는 조건 이름과 선택 개수, 아래에는 선택한 항목 전체와 안내 문구
            with st.popover(f"{label} ({n_sel}/{max_n})", width="stretch"):
                for o in all_opts:
                    on = bool(st.session_state[keys[o]])
                    st.checkbox(o, key=keys[o],
                                disabled=(o not in enabled) or (not on and n_sel >= max_n) or (on and n_sel <= min_n))
            st.markdown(f"<div class='f-sel'>{', '.join(sel) if sel else '선택 없음'}</div>"
                        f"<div class='f-r'>({rule})</div>", unsafe_allow_html=True)
        return [o for o in enabled if st.session_state[keys[o]]]

    def pick_single(container, label, col, opts, rule):
        key = f"{col}::sel"
        if st.session_state.get(key) not in opts:
            st.session_state[key] = opts[0]
        with container, st.container(border=True):
            with st.popover(f"{label} ({st.session_state[key]})", width="stretch"):
                st.radio(label, opts, key=key, label_visibility="collapsed")
            st.markdown(f"<div class='f-sel'>{st.session_state[key]}</div>"
                        f"<div class='f-r'>({rule})</div>", unsafe_allow_html=True)
        return st.session_state[key]

    with st.container(border=True):
        h1, h2 = st.columns([2, 3])
        h1.markdown("<div class='card-h'><span class='card-t'>⛛ 조건 선택</span></div>", unsafe_allow_html=True)
        h2.markdown(f"<div style='text-align:right;font-size:13.5px;color:{MUTED};padding-top:6px'>"
                    f"조건을 변경하면 아래 모든 차트와 데이터 표가 함께 바뀝니다.</div>", unsafe_allow_html=True)
        cols = st.columns(4)
        ch = pick_multi(cols[0], "유통경로", "유통경로", sorted(df_all["유통경로"].unique()),
                        sorted(df_all["유통경로"].unique()), 1, 2, "1~2개 선택, 최소 1개")
        ho = pick_single(cols[1], "호기", "호기", sorted(df_all["호기"].unique()), "1개만 선택")
        df_ho = df_all[df_all["호기"] == ho]
        grp = pick_multi(cols[2], "계획지류", "계획지류", sorted(df_all["계획지류"].unique()),
                         df_ho["계획지류"].unique(), 1, 3, "호기에 해당하는 항목만 · 최대 3개")
        df_gr = df_ho[df_ho["계획지류"].isin(grp)]
        kind = pick_multi(cols[3], "지종", "지종", sorted(df_all["지종"].unique()),
                          df_gr["지종"].unique(), 1, 3, "호기에 해당하는 항목만 · 최대 3개")
        df = df[df["유통경로"].isin(ch) & (df["호기"] == ho) & df["계획지류"].isin(grp) & df["지종"].isin(kind)]

    if not kind or df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        st.stop()

    # 기간×지종 집계 (비율 지표는 합계 기준 = 판매량 가중)
    g = df.groupby(["기간", "지종"])[METRICS].sum()
    if "생산성(톤/일)" in df.columns:
        g["생산성(톤/일)"] = df.groupby(["기간", "지종"])["생산성(톤/일)"].mean()
    g["톤당 공헌이익(천원/톤)"] = g["공헌이익(원)"] / g["판매량(톤)"] / 1000
    g["톤당 EBITDA(천원/톤)"] = g["EBITDA(원)"] / g["판매량(톤)"] / 1000
    g["단가(천원/톤)"] = g["매출액(원)"] / g["판매량(톤)"] / 1000
    if "생산성(톤/일)" in g.columns:
        g["일 기여이익(백만원/일)"] = g["톤당 공헌이익(천원/톤)"] * g["생산성(톤/일)"] / 1000
        g["일 EBITDA액(백만원/일)"] = g["톤당 EBITDA(천원/톤)"] * g["생산성(톤/일)"] / 1000
    for _c in ["매출액", "EBITDA원가", "EBITDA", "공헌이익"]:
        g[f"{_c}(백만원)"] = g[f"{_c}(원)"] / 1_000_000
        g = g.drop(columns=f"{_c}(원)")
    g = g.reset_index()

    # 선택한 지종 순서대로 차트 색상 지정 (모든 차트에서 같은 지종은 같은 색)
    COLOR_MAP = {k: CHART[i % len(CHART)] for i, k in enumerate(kind)}

    CATEGORIES = [
        ("일 기여이익 · 일 EBITDA액 추이", "선택한 지종의 월별 일 기여이익과 일 EBITDA액을 비교합니다.",
         ["일 기여이익(백만원/일)", "일 EBITDA액(백만원/일)"], "line"),
        ("톤당 수익성 · 이익 금액", "톤당 공헌이익·EBITDA와 이익 금액의 월별 흐름을 비교합니다.",
         ["톤당 공헌이익(천원/톤)", "톤당 EBITDA(천원/톤)", "공헌이익(백만원)", "EBITDA(백만원)", "EBITDA원가(백만원)"], "line"),
        ("판매량 · 매출액 · 단가 · 생산성", "지종별로 그래프를 나누어 월별 수치를 비교합니다.",
         ["판매량(톤)", "매출액(백만원)", "단가(천원/톤)", "생산성(톤/일)"], "bar"),
    ]
    RATIO = {"톤당 공헌이익(천원/톤)", "톤당 EBITDA(천원/톤)", "단가(천원/톤)"}

    def fmt_of(metric):
        return ",.0f" if metric in CATEGORIES[2][2] else ",.1f"

    def agg_of(metric):
        if metric.startswith("생산성"):
            return "mean"
        return "ratio" if metric in RATIO else "sum"

    def unit_of(metric):
        return metric[metric.rfind("(") + 1:-1]

    def style_fig(fig, height):
        fig.update_layout(
            template="plotly_white", height=height,
            font=dict(family=FONT, size=14, color=INK),
            margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified", legend_title_text="",
            hoverlabel=dict(font=dict(family=MONO, size=13)),
        )
        fig.update_xaxes(type="category", showgrid=False, linecolor="#CBD5E1", title_text="기간(월)",
                         title_font=dict(size=13.5, color=MUTED), title_standoff=8,
                         tickfont=dict(family=MONO, size=13, color=INK2))
        return fig

    def render(idx, title, desc, options, chart):
        options = [o for o in options if o in g.columns]
        with st.container(border=True):
            hl, hr = st.columns([1.4, 2])
            with hl:
                card_head(title, desc, ACCENT[idx - 1])
            if not options:
                st.info("생산성 데이터(지종별 생산성.xlsx)가 있어야 표시되는 항목입니다.")
                return None
            with hr:
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                metric = st.segmented_control("항목 선택", options, default=options[0], key=f"metric{idx}",
                                              label_visibility="collapsed") or options[0]
            agg, f = agg_of(metric), fmt_of(metric)
            pivot = g.pivot(index="기간", columns="지종", values=metric).sort_index()
            pivot = pivot[[k for k in kind if k in pivot.columns]]
            st.markdown(f"<div style='font-size:13px;color:{MUTED};margin:0 0 -6px 2px'>{metric}"
                        f"{ {'mean': ' (평균)', 'ratio': ' (가중평균)', 'sum': ' (합계)'}[agg] }</div>", unsafe_allow_html=True)
            long = pivot.reset_index().melt(id_vars="기간", var_name="지종", value_name=metric)
            if chart == "bar":
                n = long["지종"].nunique()
                fig = px.bar(long, x="기간", y=metric, color="지종", facet_row="지종", color_discrete_map=COLOR_MAP,
                             category_orders={"지종": list(pivot.columns)}, facet_row_spacing=0.12 / max(n, 1))
                style_fig(fig, 220 * n + 60)
                fig.update_traces(texttemplate="%{y:" + f + "}", textposition="outside", cliponaxis=False,
                                  textfont=dict(family=MONO, size=13, color=INK), marker_line_width=0,
                                  marker_cornerradius=6)
                fig.update_yaxes(matches=None, showticklabels=False, showgrid=False, title_text="", zeroline=False)
                avg = pivot.mean()
                labels = {}
                for a in fig.layout.annotations:
                    k = a.text.split("=")[-1]
                    labels[k] = f"평균 {format(avg[k], f)} {unit_of(metric)}"
                name_w = max(max(sum(14.5 if ord(c_) > 127 else 8.5 for c_ in k), len(v) * 8.5) for k, v in labels.items())
                # 지종명 + 평균값: 모든 그래프에서 같은 세로 중심선에 가운데 정렬
                for a in fig.layout.annotations:
                    k = a.text.split("=")[-1]
                    a.update(text=f"<b>{k}</b><br><span style='font-size:12px;color:{COLOR_MAP[k]}'>{labels[k]}</span>",
                             textangle=0, x=0, xref="paper", xanchor="center", xshift=-(12 + name_w / 2), yanchor="middle",
                             align="center", font=dict(size=14.5, color=INK))
                lab_x = -(name_w + 12 + 44)
                fig.add_annotation(xref="paper", yref="paper", x=0, xshift=lab_x, y=0.5, text=f"<b>{metric}</b>",
                                   textangle=-90, showarrow=False, font=dict(size=15, color=INK2))
                for ax in fig.select_xaxes():
                    if ax.anchor not in (None, "y"):
                        ax.update(title_text="")
                fig.update_layout(showlegend=False, bargap=0.3, margin=dict(l=int(name_w + 12 + 44 + 4), r=10, t=20, b=10))
            else:
                fig = px.line(long, x="기간", y=metric, color="지종", markers=True, color_discrete_map=COLOR_MAP,
                              category_orders={"지종": list(pivot.columns)})
                style_fig(fig, 460)
                ncol = pivot.shape[1]
                pos_map = {c: [] for c in pivot.columns}
                for _, row in pivot.iterrows():
                    order = row.sort_values(ascending=False)
                    vals = order.tolist()
                    for rk, name in enumerate(order.index):
                        if ncol == 1 or rk == 0:
                            p = "top"
                        elif rk == ncol - 1:
                            p = "bottom"
                        else:
                            p = "top" if (vals[rk - 1] - vals[rk]) >= (vals[rk] - vals[rk + 1]) else "bottom"
                        pos_map[name].append(p)
                for tr in fig.data:
                    tr.update(mode="lines+markers", line=dict(width=3.5), marker=dict(size=9, line=dict(width=2, color="#fff")))
                    for i_, (y_, p_) in enumerate(zip(tr.y, pos_map[tr.name])):
                        fig.add_annotation(x=i_, y=y_, text=format(y_, f), showarrow=False,
                                           yshift=19 if p_ == "top" else -19,
                                           font=dict(family=MONO, size=13, color=tr.line.color),
                                           bgcolor="rgba(255,255,255,0.95)", bordercolor=tr.line.color,
                                           borderwidth=1, borderpad=3)
                lo, hi = float(pivot.min().min()), float(pivot.max().max())
                pad = (hi - lo) * 0.18 or 1
                fig.update_yaxes(gridcolor=LINE2, zeroline=True, zerolinecolor=NEG, zerolinewidth=1.2,
                                 title_text=f"<b>{metric}</b>", title_font=dict(size=15, color=INK2), title_standoff=30,
                                 tickfont=dict(family=MONO, size=13, color=INK2), range=[lo - pad, hi + pad],
                                 tickformat=",", hoverformat=f)
                fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5,
                                              font=dict(size=14.5, color=INK)))
            st.plotly_chart(fig, width="stretch", key=f"chart{idx}")
            return metric

    chosen = [render(i, t, d, o, c) for i, (t, d, o, c) in enumerate(CATEGORIES, 1)]
    chosen = [m for m in chosen if m]

    # ---------- 기간 별 지표 데이터 ----------
    with st.container(border=True):
        a1, a2, a3 = st.columns([2.2, 1.6, 0.8])
        a1.markdown("<div class='card-h' style='padding-top:26px'><span class='card-t'>▦ 기간 별 지표 데이터</span></div>",
                    unsafe_allow_html=True)
        if chosen:
            tmetric = a2.selectbox("표시할 지표", chosen)
            unit, agg, f = unit_of(tmetric), agg_of(tmetric), fmt_of(tmetric)
            table = g.pivot(index="기간", columns="지종", values=tmetric).sort_index().T
            table = table.loc[[k for k in kind if k in table.index]]
            if agg == "sum":
                table.loc["합계"] = table.sum()
            elif agg == "mean":
                table.loc["평균"] = table.mean()
            mon = {c: int(c.split(".")[1]) for c in table.columns}
            hf1 = [c for c in table.columns if mon[c] <= 6]
            hf2 = [c for c in table.columns if mon[c] > 6]
            out = table.copy()
            out["상반기 평균"] = table[hf1].mean(axis=1) if hf1 else float("nan")
            out["하반기 평균"] = table[hf2].mean(axis=1) if hf2 else float("nan")
            out["전체 평균"] = table.mean(axis=1)
            has_total = agg in ("sum", "mean")
            with a3:
                st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
                st.download_button("⬇ 표 CSV", out.to_csv().encode("utf-8-sig"), f"{tmetric}.csv", "text/csv", width="stretch")

            AVG_H, AVG_C, AVG_T = "#FEF3C7", "#FFFBEB", "#FDE68A"
            cs = f"padding:10px 10px;font-size:14.5px;color:{INK};border-bottom:1px solid {LINE2};"
            thc = f"padding:12px 10px;font-size:15.5px;font-weight:700;color:{INK};background:{HEAD};text-align:right;white-space:nowrap;"
            avg_cols = ["상반기 평균", "하반기 평균", "전체 평균"]
            head = (f"<tr><th style='{thc}text-align:center'>지종 구분</th>"
                    + "".join(f"<th class='mono' style='{thc}'>{c}</th>" for c in table.columns)
                    + "".join(f"<th style='{thc}background:{AVG_H};color:#92400E;text-align:center'>{c.replace(' ', '<br>')}</th>"
                              for c in avg_cols) + "</tr>")
            rows = []
            for i, (k, r) in enumerate(out.iterrows()):
                is_total = has_total and i == len(out) - 1
                rs = f"background:#E2E8F0;font-weight:700;border-top:2px solid {INK};border-bottom:2px solid {INK};" if is_total else ""
                dot = "" if is_total else f"<span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:{COLOR_MAP.get(k, MUTED)};margin-right:8px'></span>"
                label = k
                tds = f"<td style='{cs}{rs}text-align:center;font-weight:{700 if is_total else 600};white-space:nowrap'>{dot}{label}</td>"
                for c in table.columns:
                    v = r[c]
                    neg = f"background:{NEG_BG};" if (pd.notna(v) and v < 0 and not is_total) else ""
                    tds += f"<td class='mono' style='{cs}{rs}{neg}text-align:right'>{fnum(v, f)}</td>"
                for c in avg_cols:
                    bg = f"background:{AVG_T};" if is_total else f"background:{AVG_C};"
                    tds += f"<td class='mono' style='{cs}{rs}{bg}text-align:right;font-weight:700'>{fnum(r[c], f)}</td>"
                rows.append(f"<tr>{tds}</tr>")
            st.markdown(
                f"<div style='text-align:right;font-size:14px;font-weight:500;color:{INK2};margin:4px 2px 6px 0'>( 단위 : {unit} )</div>"
                f"<div style='overflow-x:auto;border:1px solid {LINE};border-radius:12px'>"
                f"<table style='border-collapse:collapse;width:100%'>{head}{''.join(rows)}</table></div>"
                f"<div style='font-size:12.5px;color:{MUTED};margin-top:8px'>* 상반기(1~6월)·하반기(7~12월)·전체 평균은 월별 값의 단순 평균입니다.</div>",
                unsafe_allow_html=True,
            )

st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:12.5px;color:{MUTED};margin-top:18px'>"
            f"<span>© 2026 천안공장 지종별 손익 분석</span><span>데이터 기준일 {meta.get('date', '-')}</span></div>",
            unsafe_allow_html=True)
