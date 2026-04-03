# 📈 Finance Prediction Dashboard

<div align="center">

Streamlit 기반의 **주식 · 암호화폐 분석 대시보드**  
실시간 시세 조회, 기술적 지표 분석, 트레이딩 시그널, 7일 가격 예측을 하나의 화면에서 제공합니다.

<br>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20App-ff4b4b?logo=streamlit&logoColor=white)](https://finance-prediction-nsvkibjcfcluudqxdwolng.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](#)
[![Plotly](https://img.shields.io/badge/Plotly-Visualization-3F4F75?logo=plotly&logoColor=white)](#)
[![Yahoo Finance](https://img.shields.io/badge/Data-Yahoo%20Finance-5F01D1?logo=yahoo&logoColor=white)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

</div>

---

## ✨ Overview

**Finance Prediction Dashboard**는 주식과 암호화폐 데이터를 빠르게 탐색하고,  
기술적 분석과 단기 가격 예측 결과를 직관적으로 확인할 수 있도록 만든 **금융 데이터 시각화 웹앱**입니다.

이 프로젝트는 다음 목표를 중심으로 제작되었습니다.

- 복잡한 금융 데이터를 **한 화면에서 이해하기 쉽게 시각화**
- 주요 기술적 지표를 자동 계산해 **분석 흐름 단순화**
- 간단한 매매 판단 보조를 위한 **트레이딩 시그널 제공**
- Prophet / ARIMA 기반의 **향후 7일 가격 예측**

---

## 🔗 Live Demo

- **Deploy URL**  
  https://finance-prediction-nsvkibjcfcluudqxdwolng.streamlit.app/

---

## 🧩 Key Features

### 1. 실시간 시세 데이터 조회
- `yfinance`를 통해 Yahoo Finance 데이터를 불러옵니다.
- 미국 주식, 한국 주식, 암호화폐 프리셋을 제공합니다.
- 티커를 직접 입력하여 원하는 자산을 분석할 수 있습니다.

### 2. 기술적 지표 자동 계산
다음 지표를 자동 계산합니다.

- **MA5 / MA20 / MA60**
- **Bollinger Bands**
- **RSI (14)**
- **MACD / Signal / Histogram**

### 3. 인터랙티브 금융 차트
Plotly 기반으로 다음 시각화를 제공합니다.

- 캔들스틱 차트
- 이동평균선
- 볼린저 밴드
- 거래량
- RSI
- MACD

### 4. 트레이딩 시그널 종합
아래 조건을 조합해 **매수 / 매도 / 중립** 신호를 제공합니다.

- 단기 이동평균 vs 중기 이동평균
- RSI 과매수 / 과매도 구간
- MACD와 Signal 비교
- 볼린저 밴드 상단 / 하단 이탈 여부

### 5. 향후 7일 가격 예측
- **Prophet**
- **ARIMA**

두 모델 중 선택해서 예측할 수 있으며, 환경에 따라 Prophet 대신 ARIMA 중심으로도 실행할 수 있습니다.

### 6. 최근 30일 데이터 테이블
최근 가격 및 일부 지표 데이터를 표 형태로 함께 제공합니다.

---

## 🛠 Tech Stack

### App Framework
- **Streamlit**

### Data Processing
- **pandas**
- **numpy**

### Data Source
- **yfinance**

### Visualization
- **plotly**

### Forecasting
- **Prophet**
- **statsmodels (ARIMA)**

---

## 🖥️ Screens

### Main Dashboard
```md
<img width="1600" height="2400" alt="screenshot_top_mock" src="https://github.com/user-attachments/assets/d8210ce1-2141-4031-9081-daea169ad77c" />

````

### Forecast & Trading Signal

```md
<img width="1600" height="2200" alt="screenshot_bottom_mock" src="https://github.com/user-attachments/assets/1a3187dd-a8c5-4a70-acd1-03deaf49c6eb" />

```

> `assets/` 폴더에 실제 스크린샷 파일을 넣으면 GitHub에서 바로 렌더링됩니다.

---

## 📂 Project Structure

```bash
.
├── app.py
├── README.md
├── LICENSE
└── assets/
    ├── screenshot_main.png
    └── screenshot_forecast.png
```

---

## 🚀 Getting Started

### 1) Clone the repository

```bash
git clone https://github.com/dktpxmdkalshvps/finance-prediction.git
cd finance-prediction
```

### 2) Create a virtual environment

#### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### 3) Install dependencies

#### Minimum install

```bash
pip install streamlit yfinance pandas numpy plotly statsmodels
```

#### Full install with Prophet

```bash
pip install streamlit yfinance pandas numpy plotly statsmodels prophet
```

### 4) Run the app

```bash
streamlit run app.py
```

기본 실행 주소:

```bash
http://localhost:8501
```

---

## 📌 How to Use

1. 사이드바에서 카테고리를 선택합니다.

   * 🇺🇸 US Stocks
   * 🇰🇷 KR Stocks
   * 💰 Crypto

2. 종목을 선택하거나 티커를 직접 입력합니다.

   * 예: `AAPL`, `TSLA`, `005930.KS`, `BTC-USD`

3. 조회 기간을 선택합니다.

   * 1개월, 3개월, 6개월, 1년, 2년, 5년

4. 예측 모델을 선택합니다.

   * Prophet
   * ARIMA

5. **분석 시작** 버튼을 클릭합니다.

---

## 📊 Dashboard Output

앱에서 확인할 수 있는 주요 정보는 다음과 같습니다.

* 현재가 및 전일 대비 등락률
* 시가 / 고가 / 저가
* 이동평균선
* RSI
* 52주 최고가
* 캔들스틱 차트
* 거래량
* MACD
* 종합 트레이딩 시그널
* 향후 7일 예측 차트
* 예측값 테이블
* 최근 30일 원시 데이터

---

## 🎨 UI Highlights

* 다크 테마 기반 대시보드
* 카드형 핵심 지표 UI
* 색상 기반 매매 시그널 배지
* 와이드 레이아웃
* 금융 데이터에 어울리는 Plotly 시각화 구성

---

## 🧠 Forecasting Notes

### Prophet

* 추세와 계절성을 반영하는 시계열 예측 모델입니다.
* 흐름을 직관적으로 파악하는 데 유용합니다.

### ARIMA

* 전통적인 시계열 예측 모델입니다.
* Prophet 사용이 어려운 환경에서 대안으로 활용할 수 있습니다.

> 예측 결과는 참고용이며, 실제 투자 판단의 근거로 단독 사용해서는 안 됩니다.

---

## ⚠️ Disclaimer

이 프로젝트는 **포트폴리오 목적**으로 제작되었습니다.
앱에서 제공하는 분석과 예측 결과는 투자 권유가 아니며, 실제 투자 판단과 책임은 사용자 본인에게 있습니다.

---

## 🗺 Roadmap

* [ ] 종목 비교 기능 추가
* [ ] 포트폴리오 분석 기능
* [ ] 뉴스 감성 분석 연동
* [ ] 재무제표 요약 기능
* [ ] 백테스트 기능
* [ ] 알림 기능
* [ ] 사용자 전략 저장 기능

---

## 🤝 Contributing

이슈 제안, 기능 개선, UI 개선, 문서 수정 PR을 환영합니다.

1. Fork the project
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.
See the [LICENSE](./LICENSE) file for details.

---

## 🙋‍♂️ Author

**dktpxmdkalshvps**
GitHub: [@ydktpxmdkalshvps](https://github.com/dktpxmdkalshvps)

프로젝트가 도움이 되었다면 ⭐ Star를 남겨 주세요.

````

```text
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*으로 바로 바꿔드릴게요.
