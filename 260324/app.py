import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════════════════
#  페이지 설정 (반드시 첫 번째)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="주식 · 암호화폐 분석 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  종목 메타데이터  (ticker → 한국어/영문 표기명)
# ══════════════════════════════════════════════════════════════════════════════
TICKER_META = {
    # ── 미국 ──
    "AAPL":  {"name": "Apple",              "flag": "🇺🇸"},
    "MSFT":  {"name": "Microsoft",          "flag": "🇺🇸"},
    "NVDA":  {"name": "NVIDIA",             "flag": "🇺🇸"},
    "TSLA":  {"name": "Tesla",              "flag": "🇺🇸"},
    "AMZN":  {"name": "Amazon",             "flag": "🇺🇸"},
    "GOOGL": {"name": "Alphabet (Google)",  "flag": "🇺🇸"},
    "META":  {"name": "Meta",               "flag": "🇺🇸"},
    "BRK-B": {"name": "Berkshire Hathaway", "flag": "🇺🇸"},
    # ── 한국 ──
    "005930.KS": {"name": "삼성전자 (Samsung Electronics)", "flag": "🇰🇷"},
    "000660.KS": {"name": "SK하이닉스 (SK Hynix)",          "flag": "🇰🇷"},
    "035420.KS": {"name": "NAVER",                          "flag": "🇰🇷"},
    "035720.KS": {"name": "카카오 (Kakao)",                  "flag": "🇰🇷"},
    "051910.KS": {"name": "LG화학 (LG Chem)",               "flag": "🇰🇷"},
    "006400.KS": {"name": "삼성SDI",                         "flag": "🇰🇷"},
    "068270.KS": {"name": "셀트리온 (Celltrion)",            "flag": "🇰🇷"},
    "207940.KS": {"name": "삼성바이오로직스",                 "flag": "🇰🇷"},
    # ── 암호화폐 ──
    "BTC-USD": {"name": "Bitcoin",  "flag": "₿"},
    "ETH-USD": {"name": "Ethereum", "flag": "Ξ"},
    "SOL-USD": {"name": "Solana",   "flag": "◎"},
    "BNB-USD": {"name": "BNB",      "flag": "🔶"},
    "XRP-USD": {"name": "XRP",      "flag": "✕"},
}

PRESETS = {
    "🇺🇸 미국 주식": ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"],
    "🇰🇷 한국 주식": ["005930.KS", "000660.KS", "035420.KS", "035720.KS", "051910.KS", "006400.KS"],
    "₿ 암호화폐":   ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"],
}

def get_display_name(ticker: str) -> str:
    meta = TICKER_META.get(ticker)
    return f"{meta['flag']} {meta['name']}" if meta else ticker


# ══════════════════════════════════════════════════════════════════════════════
#  테마 팔레트 (다크 / 라이트)
# ══════════════════════════════════════════════════════════════════════════════
PALETTES = {
    "dark": {
        "bg":           "#0d1117",
        "bg2":          "#161b22",
        "bg3":          "#1c2128",
        "border":       "#30363d",
        "border_focus": "#58a6ff",
        "text":         "#e6edf3",
        "text_muted":   "#8b949e",
        "text_sub":     "#c9d1d9",
        "accent":       "#58a6ff",
        "green":        "#3fb950",
        "red":          "#f85149",
        "orange":       "#f0883e",
        "purple":       "#bc8cff",
        "plotly_tpl":   "plotly_dark",
        "grid":         "#21262d",
        "zeroline":     "#30363d",
        "bb_fill":      "rgba(88,166,255,0.07)",
        "fc_fill":      "rgba(240,136,62,0.12)",
    },
    "light": {
        "bg":           "#ffffff",
        "bg2":          "#f6f8fa",
        "bg3":          "#edf0f3",
        "border":       "#d0d7de",
        "border_focus": "#0969da",
        "text":         "#1f2328",
        "text_muted":   "#57606a",
        "text_sub":     "#24292f",
        "accent":       "#0969da",
        "green":        "#1a7f37",
        "red":          "#cf222e",
        "orange":       "#bc4c00",
        "purple":       "#8250df",
        "plotly_tpl":   "plotly_white",
        "grid":         "#e8ecf0",
        "zeroline":     "#d0d7de",
        "bb_fill":      "rgba(9,105,218,0.07)",
        "fc_fill":      "rgba(188,76,0,0.10)",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  사이드바 (테마 선택 → 팔레트 결정 후 나머지 UI)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📈 대시보드 설정")
    st.markdown("---")

    theme_choice = st.radio("🎨 테마", ["🌙 다크", "☀️ 라이트"], horizontal=True)
    P = PALETTES["dark"] if "다크" in theme_choice else PALETTES["light"]

    st.markdown("---")

    category = st.selectbox("카테고리", list(PRESETS.keys()))
    tickers_in_cat = PRESETS[category]

    # ▶ 드롭다운에는 '삼성전자 (Samsung Electronics)' 같은 이름 표시
    display_options = {get_display_name(t): t for t in tickers_in_cat}
    selected_display = st.selectbox("종목 선택", list(display_options.keys()))
    ticker_select = display_options[selected_display]

    ticker_input = st.text_input(
        "직접 입력 (예: TSLA, 005930.KS, BTC-USD)",
        placeholder="티커 코드를 직접 입력…",
    )
    ticker = ticker_input.strip().upper() if ticker_input.strip() else ticker_select
    ticker_display_name = get_display_name(ticker)

    period_map = {
        "1개월": "1mo", "3개월": "3mo", "6개월": "6mo",
        "1년": "1y",    "2년": "2y",    "5년": "5y",
    }
    period_label = st.selectbox("조회 기간", list(period_map.keys()), index=2)
    period = period_map[period_label]

    forecast_model = st.radio("예측 모델", ["Prophet", "ARIMA"], horizontal=True)

    st.markdown("---")
    run_btn = st.button("🔍 분석 시작", use_container_width=True, type="primary")

    st.markdown(f"""
    <small style='color:{P["text_muted"]};line-height:1.8'>
    ⚠️ 교육·참고 목적으로만 사용하세요.<br>실제 투자 결정에 활용하지 마세요.
    </small>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  동적 CSS  ── 팔레트 변수 기반으로 전체 테마 주입
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+KR:wght@300;400;600&display=swap');

/* ── 전역 리셋 ── */
html, body, [class*="css"] {{
  font-family: 'Noto Sans KR', sans-serif !important;
  background-color: {P["bg"]} !important;
  color: {P["text"]} !important;
}}
h1, h2, h3 {{ font-family: 'IBM Plex Mono', monospace !important; color: {P["text"]} !important; }}

/* ── 앱 배경 ── */
.stApp {{ background-color: {P["bg"]} !important; }}
.main .block-container {{ background-color: {P["bg"]} !important; max-width: 1400px; }}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] > div {{
  background-color: {P["bg2"]} !important;
  border-right: 1px solid {P["border"]};
}}
section[data-testid="stSidebar"] * {{ color: {P["text"]} !important; }}
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stSelectbox > div > div {{
  background-color: {P["bg3"]} !important;
  color: {P["text"]} !important;
  border-color: {P["border"]} !important;
}}

/* ── Streamlit 위젯 전역 ── */
.stTextInput input, .stSelectbox > div > div, .stMultiselect > div {{
  background-color: {P["bg2"]} !important;
  color: {P["text"]} !important;
  border-color: {P["border"]} !important;
}}
.stRadio label, .stCheckbox label {{ color: {P["text"]} !important; }}
.stSelectbox svg {{ fill: {P["text_muted"]} !important; }}
.stAlert {{ background-color: {P["bg2"]} !important; color: {P["text"]} !important; border-color: {P["border"]} !important; }}
.stSpinner > div {{ color: {P["accent"]} !important; }}

/* ── Metric 카드 ── */
div[data-testid="stMetric"] {{
  background: {P["bg2"]};
  border: 1px solid {P["border"]};
  border-radius: 10px;
  padding: 14px 18px;
  transition: border-color .2s;
}}
div[data-testid="stMetric"]:hover {{ border-color: {P["border_focus"]}; }}
div[data-testid="stMetric"] label  {{ color: {P["text_muted"]} !important; font-size: 0.74rem !important; }}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ color: {P["text"]} !important; font-family: 'IBM Plex Mono', monospace !important; }}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{ font-size: 0.78rem !important; }}

/* ── Expander ── */
[data-testid="stExpander"] {{
  background: {P["bg2"]} !important;
  border: 1px solid {P["border"]} !important;
  border-radius: 10px !important;
}}
[data-testid="stExpander"] * {{ color: {P["text"]} !important; }}
[data-testid="stExpander"] summary {{ color: {P["text"]} !important; font-weight: 600; }}

/* ── 데이터프레임 ── */
.stDataFrame, .stDataFrame table, .stDataFrame th, .stDataFrame td {{
  background-color: {P["bg2"]} !important;
  color: {P["text"]} !important;
  border-color: {P["border"]} !important;
}}

/* ── 섹션 타이틀 ── */
.section-title {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.73rem;
  color: {P["accent"]};
  text-transform: uppercase;
  letter-spacing: .12em;
  border-left: 3px solid {P["accent"]};
  padding-left: 10px;
  margin: 28px 0 14px;
}}

/* ── 종목 헤더 카드 ── */
.ticker-hero {{
  background: {P["bg2"]};
  border: 1px solid {P["border"]};
  border-radius: 14px;
  padding: 20px 28px;
  margin-bottom: 20px;
  transition: border-color .2s;
}}
.ticker-hero:hover {{ border-color: {P["border_focus"]}; }}
.ticker-label {{ font-size:.73rem; color:{P["text_muted"]}; text-transform:uppercase; letter-spacing:.1em; }}
.ticker-name  {{ font-family:'IBM Plex Mono',monospace; font-size:1.7rem; font-weight:600; color:{P["text"]}; }}
.ticker-meta  {{ color:{P["text_muted"]}; font-size:.77rem; margin-top:4px; }}

/* ── 시그널 배지 ── */
.signal-badge {{
  display:inline-block; padding:3px 14px; border-radius:20px;
  font-size:.77rem; font-weight:600; font-family:'IBM Plex Mono',monospace;
}}
.signal-buy  {{ background:rgba(26,127,55,.12);  color:{P["green"]}; border:1px solid {P["green"]}; }}
.signal-sell {{ background:rgba(207,34,46,.12);  color:{P["red"]};   border:1px solid {P["red"]}; }}
.signal-hold {{ background:rgba(188,76,0,.12);   color:{P["orange"]};border:1px solid {P["orange"]}; }}

/* ── 시그널 패널 ── */
.signal-panel, .signal-table-wrap {{
  background: {P["bg2"]};
  border: 1px solid {P["border"]};
  border-radius: 12px;
  overflow: hidden;
}}
.signal-table-wrap table  {{ width:100%; border-collapse:collapse; }}
.signal-table-wrap thead tr {{ border-bottom:1px solid {P["border"]}; }}
.signal-table-wrap th {{ padding:10px 14px; text-align:left; color:{P["text_muted"]}; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; }}
.signal-table-wrap td {{ padding:9px 14px; color:{P["text_sub"]}; font-size:.88rem; }}

/* ── 푸터 ── */
.dash-footer {{
  text-align:center; color:{P["text_muted"]}; font-size:.71rem;
  margin-top:36px; padding-top:18px; border-top:1px solid {P["border"]};
  line-height:1.8;
}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  데이터 & 지표 함수
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_data(ticker: str, period: str) -> pd.DataFrame:
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        return df
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df.dropna(inplace=True)
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"]
    for w in [5, 20, 60]:
        df[f"MA{w}"] = close.rolling(w).mean()
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    df["BB_upper"] = bb_mid + 2 * bb_std
    df["BB_lower"] = bb_mid - 2 * bb_std
    df["BB_mid"]   = bb_mid
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"]        = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"]   = df["MACD"] - df["MACD_signal"]
    return df


def trading_signal(df: pd.DataFrame) -> dict:
    last = df.iloc[-1]
    signals = []
    if last["MA5"] > last["MA20"]:
        signals.append(("buy",  "MA5 > MA20 (골든크로스)"))
    else:
        signals.append(("sell", "MA5 < MA20 (데드크로스)"))
    rsi = last["RSI"]
    if rsi < 30:
        signals.append(("buy",  f"RSI {rsi:.1f} — 과매도 구간"))
    elif rsi > 70:
        signals.append(("sell", f"RSI {rsi:.1f} — 과매수 구간"))
    else:
        signals.append(("hold", f"RSI {rsi:.1f} — 중립"))
    if last["MACD"] > last["MACD_signal"]:
        signals.append(("buy",  "MACD > Signal"))
    else:
        signals.append(("sell", "MACD < Signal"))
    price = last["Close"]
    if price < last["BB_lower"]:
        signals.append(("buy",  "볼린저 하단 이탈 — 반등 가능성"))
    elif price > last["BB_upper"]:
        signals.append(("sell", "볼린저 상단 이탈 — 조정 가능성"))
    else:
        signals.append(("hold", "볼린저 밴드 내부"))
    buy_cnt  = sum(1 for s, _ in signals if s == "buy")
    sell_cnt = sum(1 for s, _ in signals if s == "sell")
    overall  = "buy" if buy_cnt > sell_cnt else ("sell" if sell_cnt > buy_cnt else "hold")
    return {"overall": overall, "details": signals, "buy": buy_cnt, "sell": sell_cnt}


def forecast_prophet(df: pd.DataFrame, days: int = 7):
    try:
        from prophet import Prophet
    except ImportError:
        return None, "Prophet 미설치"
    ts = df[["Close"]].reset_index()
    ts.columns = ["ds", "y"]
    ts["ds"] = pd.to_datetime(ts["ds"]).dt.tz_localize(None)
    m = Prophet(daily_seasonality=False, weekly_seasonality=True,
                yearly_seasonality=True, changepoint_prior_scale=0.05)
    m.fit(ts)
    future   = m.make_future_dataframe(periods=days)
    return m.predict(future), None


def forecast_arima(df: pd.DataFrame, days: int = 7):
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        return None, "statsmodels 미설치"
    result   = ARIMA(df["Close"].values, order=(5, 1, 0)).fit()
    fc       = result.forecast(steps=days)
    fc_dates = pd.date_range(start=df.index[-1] + timedelta(days=1), periods=days, freq="B")
    return pd.DataFrame({"ds": fc_dates, "yhat": fc}), None


# ══════════════════════════════════════════════════════════════════════════════
#  차트 함수
# ══════════════════════════════════════════════════════════════════════════════

def _base(height: int, title: str) -> dict:
    """공통 Plotly 레이아웃 kwargs"""
    return dict(
        height=height,
        template=P["plotly_tpl"],
        paper_bgcolor=P["bg"],
        plot_bgcolor=P["bg"],
        font=dict(color=P["text"], family="IBM Plex Mono, Noto Sans KR, sans-serif"),
        title=dict(text=title, x=0.02, font=dict(size=14, color=P["text"])),
        legend=dict(bgcolor=P["bg2"], bordercolor=P["border"], borderwidth=1,
                    font=dict(size=11, color=P["text"])),
        margin=dict(l=10, r=10, t=52, b=10),
        xaxis=dict(gridcolor=P["grid"], zerolinecolor=P["zeroline"],
                   linecolor=P["border"], tickfont=dict(color=P["text_muted"])),
        yaxis=dict(gridcolor=P["grid"], zerolinecolor=P["zeroline"],
                   linecolor=P["border"], tickfont=dict(color=P["text_muted"])),
    )


def candlestick_chart(df: pd.DataFrame, label: str) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.60, 0.20, 0.20], vertical_spacing=0.03,
    )
    # 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color=P["green"], decreasing_line_color=P["red"],
        name="가격",
    ), row=1, col=1)
    # 이동평균선
    for ma, clr in [("MA5", P["accent"]), ("MA20", P["orange"]), ("MA60", P["purple"])]:
        if ma in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ma], name=ma,
                line=dict(color=clr, width=1.3), opacity=0.9,
            ), row=1, col=1)
    # 볼린저 밴드
    fig.add_trace(go.Scatter(
        x=pd.concat([df.index.to_series(), df.index.to_series()[::-1]]),
        y=pd.concat([df["BB_upper"], df["BB_lower"][::-1]]),
        fill="toself", fillcolor=P["bb_fill"],
        line=dict(color="rgba(0,0,0,0)"), name="볼린저 밴드",
    ), row=1, col=1)
    # 거래량
    vol_c = [P["green"] if c >= o else P["red"] for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="거래량",
                         marker_color=vol_c, opacity=0.65), row=2, col=1)
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                             line=dict(color=P["orange"], width=1.6)), row=3, col=1)
    for lv, lc in [(70, P["red"]), (30, P["green"])]:
        fig.add_hline(y=lv, line_dash="dot", line_color=lc, opacity=0.55, row=3, col=1)

    ax_style = dict(gridcolor=P["grid"], zerolinecolor=P["zeroline"],
                    linecolor=P["border"], tickfont=dict(color=P["text_muted"]))
    fig.update_layout(
        height=720,
        template=P["plotly_tpl"],
        paper_bgcolor=P["bg"], plot_bgcolor=P["bg"],
        font=dict(color=P["text"], family="IBM Plex Mono, sans-serif"),
        title=dict(text=f"<b>{label}</b> — 기술적 분석", x=0.02, font=dict(size=14, color=P["text"])),
        legend=dict(bgcolor=P["bg2"], bordercolor=P["border"], borderwidth=1,
                    font=dict(size=11, color=P["text"])),
        margin=dict(l=10, r=10, t=52, b=10),
        xaxis_rangeslider_visible=False,
    )
    for i in [1, 2, 3]:
        fig.update_xaxes(**ax_style, row=i, col=1)
        fig.update_yaxes(**ax_style, row=i, col=1)
    return fig


def macd_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"],
                             name="MACD", line=dict(color=P["accent"], width=1.6)))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"],
                             name="Signal", line=dict(color=P["orange"], width=1.6)))
    hist_c = [P["green"] if v >= 0 else P["red"] for v in df["MACD_hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"],
                         name="Histogram", marker_color=hist_c, opacity=0.7))
    fig.update_layout(**_base(280, "MACD"))
    return fig


def forecast_chart(df: pd.DataFrame, forecast, label: str, method: str) -> go.Figure:
    fig = go.Figure()
    recent = df.tail(60)
    fig.add_trace(go.Scatter(x=recent.index, y=recent["Close"],
                             name="실제 가격", line=dict(color=P["accent"], width=2)))
    if forecast is not None and "yhat" in forecast.columns:
        future = forecast[forecast["ds"] > df.index[-1]]
        fig.add_trace(go.Scatter(x=future["ds"], y=future["yhat"],
                                 name=f"예측 ({method})",
                                 line=dict(color=P["orange"], width=2, dash="dash")))
        if "yhat_lower" in forecast.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([future["ds"], future["ds"][::-1]]),
                y=pd.concat([future["yhat_upper"], future["yhat_lower"][::-1]]),
                fill="toself", fillcolor=P["fc_fill"],
                line=dict(color="rgba(0,0,0,0)"), name="신뢰 구간",
            ))
    fig.update_layout(**_base(360, f"<b>{label}</b> — 향후 7일 가격 예측"))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  메인 대시보드
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style='padding:6px 0 22px'>
  <span style='font-family:"IBM Plex Mono",monospace;font-size:1.5rem;font-weight:600;color:{P["text"]}'>
    주식 · 암호화폐 분석 대시보드
  </span><br>
  <span style='color:{P["text_muted"]};font-size:.85rem'>
    실시간 데이터 &nbsp;·&nbsp; 기술적 지표 &nbsp;·&nbsp; AI 가격 예측
  </span>
</div>
""", unsafe_allow_html=True)

if not run_btn:
    st.info("👈 사이드바에서 종목과 기간을 선택한 뒤 **분석 시작** 버튼을 누르세요.")
    st.stop()

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
with st.spinner(f"📡 {ticker} 데이터 로드 중…"):
    df = load_data(ticker, period)

if df.empty:
    st.error(f"❌ '{ticker}' 데이터를 불러올 수 없습니다. 종목 코드를 확인하세요.")
    st.stop()

df     = compute_indicators(df)
signal = trading_signal(df)
info   = yf.Ticker(ticker).info

# ── 종목 헤더 카드 ────────────────────────────────────────────────────────────
name_info     = info.get("longName") or info.get("shortName", "")
display_label = ticker_display_name if ticker in TICKER_META else (name_info or ticker)
currency      = info.get("currency", "")
price         = df["Close"].iloc[-1]
prev          = df["Close"].iloc[-2]
chg           = price - prev
chg_pct       = chg / prev * 100
arrow         = "▲" if chg >= 0 else "▼"
chg_clr       = P["green"] if chg >= 0 else P["red"]

st.markdown(f"""
<div class="ticker-hero">
  <div class="ticker-label">{ticker}</div>
  <div class="ticker-name">{display_label}</div>
  <div style='margin-top:8px'>
    <span style='font-family:"IBM Plex Mono",monospace;font-size:2.1rem;font-weight:600;color:{P["text"]}'>
      {price:,.2f}
    </span>
    <span style='color:{P["text_muted"]};font-size:.95rem;margin-left:6px'>{currency}</span>
    <span style='color:{chg_clr};font-size:1rem;margin-left:14px'>
      {arrow} {abs(chg):,.2f} ({abs(chg_pct):.2f}%)
    </span>
  </div>
  <div class="ticker-meta">마지막 업데이트: {df.index[-1].strftime("%Y-%m-%d")}</div>
</div>
""", unsafe_allow_html=True)

# ── 핵심 지표 ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">핵심 지표</div>', unsafe_allow_html=True)
last = df.iloc[-1]
c1, c2, c3, c4, c5, c6 = st.columns(6)
rsi_note = "과매도 🟢" if last["RSI"] < 30 else ("과매수 🔴" if last["RSI"] > 70 else "중립 🟡")
for col, label, val, delta in [
    (c1, "시가 (Open)",  f"{last['Open']:,.2f}",         None),
    (c2, "고가 (High)",  f"{last['High']:,.2f}",         None),
    (c3, "저가 (Low)",   f"{last['Low']:,.2f}",          None),
    (c4, "MA20",         f"{last['MA20']:,.2f}",         None),
    (c5, "RSI (14)",     f"{last['RSI']:.1f}",           rsi_note),
    (c6, "52주 최고가",  f"{df['High'].tail(252).max():,.2f}", None),
]:
    with col:
        st.metric(label, val, delta)

# ── 캔들스틱 차트 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">캔들스틱 · 이동평균 · 볼린저 · RSI</div>', unsafe_allow_html=True)
st.plotly_chart(candlestick_chart(df, display_label), use_container_width=True)

# ── MACD ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">MACD</div>', unsafe_allow_html=True)
st.plotly_chart(macd_chart(df), use_container_width=True)

# ── 트레이딩 시그널 ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">트레이딩 시그널 종합</div>', unsafe_allow_html=True)

overall   = signal["overall"]
badge_cls = {"buy": "signal-buy", "sell": "signal-sell", "hold": "signal-hold"}[overall]
badge_txt = {"buy": "📗 매수 우세", "sell": "📕 매도 우세", "hold": "📒 중립"}[overall]

col_sig, col_detail = st.columns([1, 2])
with col_sig:
    st.markdown(f"""
    <div class="signal-panel" style="padding:28px;text-align:center;">
      <div style='font-size:.72rem;color:{P["text_muted"]};margin-bottom:10px;text-transform:uppercase;letter-spacing:.06em'>
        종합 판단
      </div>
      <span class='signal-badge {badge_cls}' style='font-size:1.05rem;padding:9px 24px'>
        {badge_txt}
      </span>
      <div style='margin-top:18px;font-size:.82rem;color:{P["text_muted"]}'>
        매수 신호 <b style="color:{P["green"]}">{signal['buy']}</b>개
        &nbsp;·&nbsp;
        매도 신호 <b style="color:{P["red"]}">{signal['sell']}</b>개
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_detail:
    rows = "".join(f"""
      <tr>
        <td style='padding:9px 14px'>
          <span class='signal-badge {"signal-buy" if s=="buy" else "signal-sell" if s=="sell" else "signal-hold"}'>
            {"▲" if s=="buy" else "▼" if s=="sell" else "●"} {s.upper()}
          </span>
        </td>
        <td style='padding:9px 14px;color:{P["text_sub"]};font-size:.87rem'>{desc}</td>
      </tr>"""
    for s, desc in signal["details"])
    st.markdown(f"""
    <div class="signal-table-wrap">
      <table>
        <thead><tr><th>신호</th><th>판단 근거</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

# ── 가격 예측 ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">향후 7일 가격 예측</div>', unsafe_allow_html=True)

with st.spinner(f"🔮 {forecast_model} 모델 학습 중…"):
    if forecast_model == "Prophet":
        forecast, err = forecast_prophet(df)
        if err:
            st.warning(f"Prophet 실패: {err} — ARIMA로 전환합니다.")
            forecast, err = forecast_arima(df)
            used_model = "ARIMA"
        else:
            used_model = "Prophet"
    else:
        forecast, err = forecast_arima(df)
        used_model = "ARIMA"

if err:
    st.error(f"예측 실패: {err}")
else:
    st.plotly_chart(forecast_chart(df, forecast, display_label, used_model),
                    use_container_width=True)
    if forecast is not None:
        future_fc = forecast[forecast["ds"] > df.index[-1]].head(7).copy()
        future_fc["날짜"]    = future_fc["ds"].dt.strftime("%Y-%m-%d")
        future_fc["예측 가격"] = future_fc["yhat"].map(lambda x: f"{x:,.2f}")
        cols_show = ["날짜", "예측 가격"]
        if "yhat_lower" in future_fc.columns:
            future_fc["하한"] = future_fc["yhat_lower"].map(lambda x: f"{x:,.2f}")
            future_fc["상한"] = future_fc["yhat_upper"].map(lambda x: f"{x:,.2f}")
            cols_show += ["하한", "상한"]
        st.dataframe(future_fc[cols_show].reset_index(drop=True),
                     use_container_width=True, hide_index=True)

# ── 원시 데이터 ───────────────────────────────────────────────────────────────
with st.expander("📋 최근 30일 원시 데이터 보기"):
    show_cols = [c for c in ["Open","High","Low","Close","Volume","MA5","MA20","RSI"] if c in df.columns]
    recent_df = df[show_cols].tail(30).copy()
    recent_df.index = recent_df.index.strftime("%Y-%m-%d")
    for col in ["Open","High","Low","Close","MA5","MA20"]:
        if col in recent_df.columns:
            recent_df[col] = recent_df[col].map(lambda x: f"{x:,.2f}")
    if "Volume" in recent_df.columns:
        recent_df["Volume"] = recent_df["Volume"].map(lambda x: f"{x:,.0f}")
    if "RSI" in recent_df.columns:
        recent_df["RSI"] = recent_df["RSI"].map(lambda x: f"{x:.1f}")
    st.dataframe(recent_df, use_container_width=True)

# ── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-footer">
  데이터 출처: Yahoo Finance (yfinance) &nbsp;·&nbsp; 예측 모델: Prophet / ARIMA<br>
  ⚠️ 본 분석은 참고용이며 투자 권유가 아닙니다.
</div>
""", unsafe_allow_html=True)
