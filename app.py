import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="주식 · 암호화폐 분석 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+KR:wght@300;400;600&display=swap');

  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
  h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; }

  .stApp { background-color: #0d1117; color: #e6edf3; }
  .sidebar .sidebar-content { background-color: #161b22; }

  .metric-card {
    background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
  }
  .metric-card:hover { border-color: #58a6ff; }
  .metric-label { font-size: 0.72rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.08em; }
  .metric-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.55rem; font-weight: 600; margin: 4px 0; }
  .metric-delta-up   { color: #3fb950; font-size: 0.85rem; }
  .metric-delta-down { color: #f85149; font-size: 0.85rem; }

  .section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #58a6ff;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    border-left: 3px solid #58a6ff;
    padding-left: 10px;
    margin: 24px 0 14px;
  }

  .signal-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
  }
  .signal-buy  { background: rgba(63,185,80,0.15);  color: #3fb950; border: 1px solid #3fb950; }
  .signal-sell { background: rgba(248,81,73,0.15);  color: #f85149; border: 1px solid #f85149; }
  .signal-hold { background: rgba(210,153,34,0.15); color: #d2993e; border: 1px solid #d2993e; }

  div[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 14px 18px;
  }
  div[data-testid="stMetric"] label { color: #8b949e !important; font-size: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  헬퍼 함수
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_data(ticker: str, period: str) -> pd.DataFrame:
    """yfinance로 주가 데이터 로드 (5분 캐시)"""
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        return df
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df.dropna(inplace=True)
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """기술적 지표 계산"""
    close = df["Close"]

    # 이동평균선
    for w in [5, 20, 60]:
        df[f"MA{w}"] = close.rolling(w).mean()

    # 볼린저 밴드 (20일, 2σ)
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    df["BB_upper"] = bb_mid + 2 * bb_std
    df["BB_lower"] = bb_mid - 2 * bb_std
    df["BB_mid"]   = bb_mid

    # RSI (14일)
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"]        = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"]   = df["MACD"] - df["MACD_signal"]

    return df


def trading_signal(df: pd.DataFrame) -> dict:
    """간단한 트레이딩 시그널 생성"""
    last = df.iloc[-1]
    signals = []

    # MA 크로스
    if last["MA5"] > last["MA20"]:
        signals.append(("buy", "MA5 > MA20 (골든크로스)"))
    else:
        signals.append(("sell", "MA5 < MA20 (데드크로스)"))

    # RSI
    rsi = last["RSI"]
    if rsi < 30:
        signals.append(("buy", f"RSI {rsi:.1f} — 과매도 구간"))
    elif rsi > 70:
        signals.append(("sell", f"RSI {rsi:.1f} — 과매수 구간"))
    else:
        signals.append(("hold", f"RSI {rsi:.1f} — 중립"))

    # MACD
    if last["MACD"] > last["MACD_signal"]:
        signals.append(("buy", "MACD > Signal"))
    else:
        signals.append(("sell", "MACD < Signal"))

    # Bollinger Band
    price = last["Close"]
    if price < last["BB_lower"]:
        signals.append(("buy", "볼린저 하단 이탈 — 반등 가능성"))
    elif price > last["BB_upper"]:
        signals.append(("sell", "볼린저 상단 이탈 — 조정 가능성"))
    else:
        signals.append(("hold", "볼린저 밴드 내부"))

    buy_cnt  = sum(1 for s, _ in signals if s == "buy")
    sell_cnt = sum(1 for s, _ in signals if s == "sell")
    overall  = "buy" if buy_cnt > sell_cnt else ("sell" if sell_cnt > buy_cnt else "hold")
    return {"overall": overall, "details": signals, "buy": buy_cnt, "sell": sell_cnt}


def forecast_prophet(df: pd.DataFrame, days: int = 7):
    """Prophet으로 가격 예측"""
    try:
        from prophet import Prophet
    except ImportError:
        return None, "Prophet 미설치 — pip install prophet"

    ts = df[["Close"]].reset_index()
    ts.columns = ["ds", "y"]
    ts["ds"] = pd.to_datetime(ts["ds"]).dt.tz_localize(None)

    m = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
    )
    m.fit(ts)
    future   = m.make_future_dataframe(periods=days)
    forecast = m.predict(future)
    return forecast, None


def forecast_arima(df: pd.DataFrame, days: int = 7):
    """ARIMA로 가격 예측 (Prophet 실패 시 폴백)"""
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        return None, "statsmodels 미설치"

    series = df["Close"].values
    model  = ARIMA(series, order=(5, 1, 0))
    result = model.fit()
    fc     = result.forecast(steps=days)
    last_date  = df.index[-1]
    fc_dates   = pd.date_range(start=last_date + timedelta(days=1), periods=days, freq="B")
    return pd.DataFrame({"ds": fc_dates, "yhat": fc}), None


# ══════════════════════════════════════════════════════════════════════════════
#  차트 함수
# ══════════════════════════════════════════════════════════════════════════════

CHART_THEME = {
    "paper_bgcolor": "#0d1117",
    "plot_bgcolor":  "#0d1117",
    "font":          {"color": "#e6edf3", "family": "IBM Plex Mono"},
    "gridcolor":     "#21262d",
    "zerolinecolor": "#30363d",
}

def candlestick_chart(df: pd.DataFrame, ticker: str):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.60, 0.20, 0.20],
        vertical_spacing=0.03,
    )

    # 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#3fb950", decreasing_line_color="#f85149",
        name="가격",
    ), row=1, col=1)

    # 이동평균선
    colors_ma = {"MA5": "#58a6ff", "MA20": "#f0883e", "MA60": "#bc8cff"}
    for ma, clr in colors_ma.items():
        if ma in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ma], name=ma,
                line=dict(color=clr, width=1.2), opacity=0.85,
            ), row=1, col=1)

    # 볼린저 밴드
    fig.add_trace(go.Scatter(
        x=pd.concat([df.index.to_series(), df.index.to_series()[::-1]]),
        y=pd.concat([df["BB_upper"], df["BB_lower"][::-1]]),
        fill="toself", fillcolor="rgba(88,166,255,0.06)",
        line=dict(color="rgba(0,0,0,0)"), name="볼린저 밴드", showlegend=True,
    ), row=1, col=1)

    # 거래량
    vol_colors = ["#3fb950" if c >= o else "#f85149"
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], name="거래량",
        marker_color=vol_colors, opacity=0.7,
    ), row=2, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"], name="RSI",
        line=dict(color="#f0883e", width=1.5),
    ), row=3, col=1)
    for level, clr in [(70, "#f85149"), (30, "#3fb950")]:
        fig.add_hline(y=level, line_dash="dot", line_color=clr,
                      opacity=0.6, row=3, col=1)

    fig.update_layout(
        height=700, title=dict(text=f"<b>{ticker}</b> 기술적 분석", x=0.02, font_size=15),
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=CHART_THEME["font"],
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1,
                    font_size=11, x=0.01, y=0.98),
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    for row_n in [1, 2, 3]:
        fig.update_xaxes(gridcolor=CHART_THEME["gridcolor"],
                         zerolinecolor=CHART_THEME["zerolinecolor"], row=row_n, col=1)
        fig.update_yaxes(gridcolor=CHART_THEME["gridcolor"],
                         zerolinecolor=CHART_THEME["zerolinecolor"], row=row_n, col=1)
    return fig


def macd_chart(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"],
                             name="MACD", line=dict(color="#58a6ff", width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"],
                             name="Signal", line=dict(color="#f0883e", width=1.5)))
    hist_colors = ["#3fb950" if v >= 0 else "#f85149" for v in df["MACD_hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"],
                         name="Histogram", marker_color=hist_colors, opacity=0.7))
    fig.update_layout(
        height=280, title=dict(text="MACD", x=0.02, font_size=13),
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=CHART_THEME["font"],
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor=CHART_THEME["gridcolor"]),
        yaxis=dict(gridcolor=CHART_THEME["gridcolor"]),
    )
    return fig


def forecast_chart(df: pd.DataFrame, forecast, ticker: str, method: str):
    fig = go.Figure()

    # 실제 가격 (최근 60일)
    recent = df.tail(60)
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent["Close"],
        name="실제 가격", line=dict(color="#58a6ff", width=2),
    ))

    if forecast is not None and "yhat" in forecast.columns:
        future = forecast[forecast["ds"] > df.index[-1]]
        fig.add_trace(go.Scatter(
            x=future["ds"], y=future["yhat"],
            name=f"예측 ({method})", line=dict(color="#f0883e", width=2, dash="dash"),
        ))
        if "yhat_lower" in forecast.columns and "yhat_upper" in forecast.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([future["ds"], future["ds"][::-1]]),
                y=pd.concat([future["yhat_upper"], future["yhat_lower"][::-1]]),
                fill="toself", fillcolor="rgba(240,136,62,0.12)",
                line=dict(color="rgba(0,0,0,0)"), name="신뢰 구간",
            ))

    fig.update_layout(
        height=350,
        title=dict(text=f"<b>{ticker}</b> — 향후 7일 가격 예측", x=0.02, font_size=14),
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=CHART_THEME["font"],
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(gridcolor=CHART_THEME["gridcolor"]),
        yaxis=dict(gridcolor=CHART_THEME["gridcolor"]),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  사이드바 UI
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 📈 설정")
    st.markdown("---")

    presets = {
        "🇺🇸 주식": {
            "애플": "AAPL",
            "마이크로소프트": "MSFT",
            "엔비디아": "NVDA",
            "테슬라": "TSLA",
            "아마존": "AMZN",
            "알파벳 A": "GOOGL",
            "AMD": "AMD",
            "SPY": "SPY",
            "IVV": "IVV",
            "버크셔해서웨이 B": "BRK-B",
            "아메리칸 익스프레스": "AXP",
            "웨이스트 매니저먼트": "WM",
            "웨이스트 커넥션스": "WCN",
            "쇼피파이": "SHOP",
            "캐나디언 내셔널 레일웨이": "CNI",
            "뱅크오브아메리카": "BAC",
            "로쿠": "ROKU",
            "코카콜라": "KO",
            "코카콜라 펨사(ADR)": "KOF",
            "코인베이스": "COIN",
            "램 리서치": "LRCX",
            "캐터필러": "CAT",
            "셰브론": "CVX",
            "팔란티어": "PLTR",
            "세일즈포스": "CRM",
            "디어": "DE",
            "무디스": "MCO",
            "크리스퍼 테라퓨틱스": "CRSP",
            "에코랩": "ECL",
            "옥시덴탈 페트롤리움": "OXY",
            "월마트": "WMT",
            "처브": "CB",
            "로빈후드": "HOOD",
            "페덱스": "FDX",
            "크래프트 하인즈": "KHC",
            "테라다인": "TER",
            "어도비": "ADBE",
            "템퍼스 AI": "TEM",
            "GE 버노바": "GEV",
            "다비타": "DVA",
            "로블록스": "RBLX",
            "부킹 홀딩스": "BKNG",
            "쿠팡": "CPNG",
            "크로거": "KR",
            "빔 테라퓨틱스": "BEAM",
            "브로드컴": "AVGO",
            "매디슨 스퀘어 가든 스포츠": "MSGS",
            "비자": "V",
            "써클 인터넷 그룹": "CRCL",
            "오라클": "ORCL",
            "슈뢰딩거": "SDGR",
            "시리우스 XM 홀딩스": "SIRI",
            "웨스트 파마슈티컬 서비시스": "WST",
            "마스터카드": "MA",
            "아처 에비에이션": "ACHR",
            "존슨 앤 존슨": "JNJ",
            "파카": "PH",
            "베리사인": "VRSN",
            "크라토스 디펜스 & 시큐리티": "KTOS",
            "마이크론 테크놀로지": "MU",
            "안호이저부시 인베브(ADR)": "BUD",
            "콘스텔레이션 브랜즈": "STZ",
            "비트마인 이머션 테크놀로지스": "BMAS",
            "맥도날드": "MCD",
            "캐피탈 원 파이낸셜": "COF",
            "트위스트 바이오사이언스": "TWST",
            "뉴몬트": "NEM",
            "다나허": "DHR",
            "유나이티드 헬스 그룹": "UNH",
            "워크데이": "WDAY",
            "도미노 피자": "DPZ",
            "TSMC(ADR)": "TSM",
            "서비스나우": "NOW",
        },
        "🇰🇷 주식": {
            "삼성전자": "005930.KS",
            "삼성전자우": "005935.KS",
            "SK하이닉스": "000660.KS",
            "LG에너지솔루션": "373220.KS",
            "삼성바이오로직스": "207940.KS",
            "한화에어로스페이스": "012450.KS",
            "현대차": "005380.KS",
            "현대차우": "005385.KS",
            "현대차2우B": "005387.KS",
            "현대차3우B": "005389.KS",
            "기아": "000270.KS",
            "셀트리온": "068270.KS",
            "KB금융": "105560.KS",
            "신한지주": "055550.KS",
            "삼성물산": "028260.KS",
            "삼성물산우B": "028265.KS",
            "삼성생명": "032830.KS",
            "SK스퀘어": "402340.KS",
            "HD현대중공업": "329180.KS",
            "두산에너빌리티": "034020.KS",
            "NAVER": "035420.KS",
            "카카오": "035720.KS",
            "에코프로": "086520.KQ",
            "에코프로비엠": "247540.KQ",
            "알테오젠": "196170.KQ",
            "HLB": "028300.KQ",
            "레인보우로보틱스": "277810.KQ",
            "에이비엘바이오": "298380.KQ",
            "리가켐바이오": "141080.KQ",
            "리노공업": "058470.KQ",
            "보로노이": "310210.KQ",
            "원익IPS": "240810.KQ",
            "이오테크닉스": "039030.KQ",
            "ISC": "095340.KQ",
            "HPSP": "403870.KQ",
            "케어젠": "214370.KQ",
            "올릭스": "226950.KQ",
            "로보티즈": "108490.KQ",
            "펩트론": "087010.KQ",
            "코오롱티슈진": "950160.KQ",
            "삼천당제약": "000250.KS",
            "우리기술": "032820.KQ",
        },
        "💰 암호화폐": {
            "비트코인": "BTC-USD",
            "이더리움": "ETH-USD",
            "솔라나": "SOL-USD",
            "BNB": "BNB-USD",
        },
    }

    category = st.selectbox("카테고리", list(presets.keys()))
    ticker_names = list(presets[category].keys())
    ticker_name_select = st.selectbox("종목 선택", ticker_names)
    ticker_select = presets[category][ticker_name_select]
    ticker_input  = st.text_input("직접 입력 (예: TSLA, 005930.KS, BTC-USD)", "")
    ticker = ticker_input.strip().upper() if ticker_input.strip() else ticker_select

    period_map = {
        "1개월": "1mo", "3개월": "3mo", "6개월": "6mo",
        "1년": "1y",    "2년": "2y",    "5년": "5y",
    }
    period_label = st.selectbox("조회 기간", list(period_map.keys()), index=2)
    period = period_map[period_label]

    forecast_model = st.radio("예측 모델", ["Prophet", "ARIMA"], horizontal=True)

    st.markdown("---")
    run_btn = st.button("🔍 분석 시작", use_container_width=True, type="primary")

    st.markdown("""
    <small style='color:#8b949e;line-height:1.6'>
    ⚠️ 본 대시보드는 교육·참고 목적으로만 사용하세요.<br>
    실제 투자 결정에 활용하지 마세요.
    </small>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  메인 대시보드
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style='padding: 8px 0 20px'>
  <span style='font-family:"IBM Plex Mono",monospace; font-size:1.6rem; font-weight:600; color:#e6edf3'>
    주식 · 암호화폐 분석 대시보드
  </span><br>
  <span style='color:#8b949e; font-size:0.85rem'>
    실시간 데이터 · 기술적 지표 · AI 가격 예측
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

df = compute_indicators(df)
signal = trading_signal(df)

try:
    info = yf.Ticker(ticker).info
except Exception:
    info = {}

# ── 종목 헤더 ─────────────────────────────────────────────────────────────────
name     = info.get("longName") or info.get("shortName") or ticker
currency = info.get("currency", "")
price    = df["Close"].iloc[-1]
prev     = df["Close"].iloc[-2]
chg      = price - prev
chg_pct  = chg / prev * 100
arrow    = "▲" if chg >= 0 else "▼"
clr_val  = "#3fb950" if chg >= 0 else "#f85149"

st.markdown(f"""
<div style='background:#161b22; border:1px solid #30363d; border-radius:14px;
            padding:20px 28px; margin-bottom:20px;'>
  <div style='font-size:0.78rem; color:#8b949e; text-transform:uppercase; letter-spacing:.1em'>{ticker}</div>
  <div style='font-family:"IBM Plex Mono",monospace; font-size:1.9rem; font-weight:600'>{name}</div>
  <div style='margin-top:6px'>
    <span style='font-family:"IBM Plex Mono",monospace; font-size:2.2rem; font-weight:600'>
      {price:,.2f}
    </span>
    <span style='color:#8b949e; font-size:1rem; margin-left:6px'>{currency}</span>
    <span style='color:{clr_val}; font-size:1rem; margin-left:14px'>
      {arrow} {abs(chg):,.2f} ({abs(chg_pct):.2f}%)
    </span>
  </div>
  <div style='color:#8b949e; font-size:0.78rem; margin-top:4px'>
    마지막 업데이트: {df.index[-1].strftime("%Y-%m-%d")}
  </div>
</div>
""", unsafe_allow_html=True)

# ── 핵심 지표 카드 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">핵심 지표</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)
last = df.iloc[-1]

metrics = [
    (c1, "시가 (Open)",       f"{last['Open']:,.2f}",      None),
    (c2, "고가 (High)",        f"{last['High']:,.2f}",      None),
    (c3, "저가 (Low)",         f"{last['Low']:,.2f}",       None),
    (c4, "MA20",              f"{last['MA20']:,.2f}",       None),
    (c5, "RSI (14)",           f"{last['RSI']:.1f}",        "과매도" if last['RSI'] < 30 else ("과매수" if last['RSI'] > 70 else "중립")),
    (c6, "52주 최고가",
         f"{df['High'].tail(252).max():,.2f}",              None),
]
for col, label, value, delta in metrics:
    with col:
        st.metric(label, value, delta)

# ── 캔들스틱 + MA + 볼린저 + 거래량 + RSI ──────────────────────────────────────
st.markdown('<div class="section-title">캔들스틱 · 이동평균 · RSI</div>', unsafe_allow_html=True)
st.plotly_chart(candlestick_chart(df, ticker), use_container_width=True)

# ── MACD ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">MACD</div>', unsafe_allow_html=True)
st.plotly_chart(macd_chart(df), use_container_width=True)

# ── 트레이딩 시그널 ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">트레이딩 시그널 종합</div>', unsafe_allow_html=True)

overall = signal["overall"]
badge_cls = {"buy": "signal-buy", "sell": "signal-sell", "hold": "signal-hold"}[overall]
badge_txt = {"buy": "📗 매수 우세", "sell": "📕 매도 우세", "hold": "📒 중립"}[overall]

col_sig, col_detail = st.columns([1, 2])
with col_sig:
    st.markdown(f"""
    <div style='background:#161b22; border:1px solid #30363d; border-radius:12px;
                padding:24px; text-align:center; height:100%'>
      <div style='font-size:0.75rem; color:#8b949e; margin-bottom:10px'>종합 판단</div>
      <span class='signal-badge {badge_cls}' style='font-size:1.1rem; padding:8px 22px'>
        {badge_txt}
      </span>
      <div style='margin-top:16px; font-size:0.82rem; color:#8b949e'>
        매수 신호 {signal['buy']}개 · 매도 신호 {signal['sell']}개
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_detail:
    rows = ""
    for s, desc in signal["details"]:
        cls = badge_cls = {"buy": "signal-buy", "sell": "signal-sell", "hold": "signal-hold"}[s]
        icon = {"buy": "▲", "sell": "▼", "hold": "●"}[s]
        rows += f"""
        <tr>
          <td style='padding:7px 12px'>
            <span class='signal-badge {cls}'>{icon} {s.upper()}</span>
          </td>
          <td style='padding:7px 12px; color:#c9d1d9'>{desc}</td>
        </tr>"""
    st.markdown(f"""
    <div style='background:#161b22; border:1px solid #30363d; border-radius:12px; overflow:hidden'>
      <table style='width:100%; border-collapse:collapse'>
        <thead>
          <tr style='border-bottom:1px solid #30363d'>
            <th style='padding:10px 12px; text-align:left; color:#8b949e; font-size:0.75rem'>신호</th>
            <th style='padding:10px 12px; text-align:left; color:#8b949e; font-size:0.75rem'>근거</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

# ── 가격 예측 ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">향후 7일 가격 예측</div>', unsafe_allow_html=True)

with st.spinner(f"🔮 {forecast_model} 모델 학습 중…"):
    if forecast_model == "Prophet":
        forecast, err = forecast_prophet(df, days=7)
        if err:
            st.warning(f"Prophet 실패: {err} — ARIMA로 전환합니다.")
            forecast, err = forecast_arima(df, days=7)
            used_model = "ARIMA"
        else:
            used_model = "Prophet"
    else:
        forecast, err = forecast_arima(df, days=7)
        used_model = "ARIMA"

if err:
    st.error(f"예측 실패: {err}")
else:
    st.plotly_chart(forecast_chart(df, forecast, ticker, used_model), use_container_width=True)

    # 예측 수치 테이블
    if forecast is not None:
        future_fc = forecast[forecast["ds"] > df.index[-1]].head(7).copy()
        future_fc["날짜"] = future_fc["ds"].dt.strftime("%Y-%m-%d")
        future_fc["예측 가격"] = future_fc["yhat"].map(lambda x: f"{x:,.2f}")
        cols_show = ["날짜", "예측 가격"]
        if "yhat_lower" in future_fc.columns:
            future_fc["하한"] = future_fc["yhat_lower"].map(lambda x: f"{x:,.2f}")
            future_fc["상한"] = future_fc["yhat_upper"].map(lambda x: f"{x:,.2f}")
            cols_show += ["하한", "상한"]
        st.dataframe(
            future_fc[cols_show].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

# ── 최근 데이터 테이블 ────────────────────────────────────────────────────────
with st.expander("📋 최근 30일 원시 데이터 보기"):
    show_cols = ["Open", "High", "Low", "Close", "Volume", "MA5", "MA20", "RSI"]
    show_cols = [c for c in show_cols if c in df.columns]
    recent_df = df[show_cols].tail(30).copy()
    recent_df.index = recent_df.index.strftime("%Y-%m-%d")
    for col in ["Open", "High", "Low", "Close", "MA5", "MA20"]:
        if col in recent_df.columns:
            recent_df[col] = recent_df[col].map(lambda x: f"{x:,.2f}")
    if "Volume" in recent_df.columns:
        recent_df["Volume"] = recent_df["Volume"].map(lambda x: f"{x:,.0f}")
    if "RSI" in recent_df.columns:
        recent_df["RSI"] = recent_df["RSI"].map(lambda x: f"{x:.1f}")
    st.dataframe(recent_df, use_container_width=True)

st.markdown("""
<div style='text-align:center; color:#8b949e; font-size:0.72rem; margin-top:30px; padding-top:20px;
            border-top:1px solid #21262d'>
  데이터 출처: Yahoo Finance (yfinance) · 예측 모델: Prophet / ARIMA<br>
  ⚠️ 본 분석은 참고용이며 투자 권유가 아닙니다.
</div>
""", unsafe_allow_html=True)
