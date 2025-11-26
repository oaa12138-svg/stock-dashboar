import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# --- 1. 网页基础配置 ---
st.set_page_config(page_title="AI股票实战指挥部", layout="wide", page_icon="📈")

# --- 2. 侧边栏设置 ---
st.sidebar.header("🕹️ 操控台")
st.sidebar.info("国内A股请加后缀：.SS (上海) 或 .SZ (深圳)。\n例如：茅台 600519.SS，宁德时代 300750.SZ")
default_ticker = "600519.SS"
ticker = st.sidebar.text_input("输入股票代码", value=default_ticker).upper()

# --- 3. 核心功能：抓取数据+计算 ---
def analyze_stock(ticker_symbol):
    try:
        # A. 获取数据 (yfinance)
        stock = yf.Ticker(ticker_symbol)
        
        # 获取K线历史
        df = stock.history(period="6mo", interval="1d")
        if df.empty or len(df) < 30:
            return None, None, None, "数据获取失败，请检查代码或网络。"
            
        # 获取基本面信息
        info = stock.info
        
        # 获取新闻
        news = stock.news
        
        # B. 计算技术指标
        # EMA均线
        df['EMA_12'] = ta.ema(df['Close'], length=12)
        df['EMA_26'] = ta.ema(df['Close'], length=26)
        # RSI
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # C. 量化打分 (满分100)
        score = 50
        current = df.iloc[-1]
        
        # 趋势加分
        if current['Close'] > current['EMA_12'] > current['EMA_26']:
            score += 25 # 多头排列 (强)
        elif current['Close'] < current['EMA_12']:
            score -= 15 # 跌破快线 (弱)
            
        # RSI加分
        if current['RSI'] < 30: score += 15 # 超卖反弹机会
        elif current['RSI'] > 70: score -= 15 # 超买风险
        
        score = max(0, min(100, score))
        
        return df, info, news, score
    except Exception as e:
        return None, None, None, str(e)

# --- 4. 页面显示逻辑 ---
st.title(f"🚀 {ticker} 全维分析看板")

with st.spinner('正在连接全球交易所数据...'):
    df, info, news, score = analyze_stock(ticker)

if df is None:
    st.error(f"❌ 错误: {score}")
else:
    # === 模块一：仪表盘 (即时买卖信号) ===
    st.subheader("1️⃣ 趋势雷达 (技术面)")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        # 定义颜色和建议
        if score >= 75:
            color, signal, advice = "#FF0000", "💎 强烈买入", "多头趋势确立，资金流入明显。"
        elif score >= 55:
            color, signal, advice = "#FF7F50", "🔥 建议买入", "趋势向好，可尝试建仓。"
        elif score >= 40:
            color, signal, advice = "#FFD700", "⚖️ 观望/持有", "多空震荡，方向不明。"
        else:
            color, signal, advice = "#006400", "☠️ 坚决清仓/空仓", "空头趋势，下跌风险极大。"

        current_price = df['Close'].iloc[-1]
        st.metric("最新价格", f"{current_price:.2f}")
        st.markdown(f"### 信号: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
        st.info(advice)

    with col2:
        # 绘制仪表盘
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = score,
            title = {'text': "AI 多空评分 (0-100)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 40], 'color': '#90EE90'},
                    {'range': [40, 60], 'color': '#FFD700'},
                    {'range': [60, 100], 'color': '#FF7F50'}
                ]
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # === 模块二：基本面速览 ===
    st.markdown("---")
    st.subheader("2️⃣ 公司体检 (基本面)")
    pe = info.get('trailingPE', 'N/A')
    pb = info.get('priceToBook', 'N/A')
    mkt_cap = info.get('marketCap', 0)
    
    # 简单的估值判断
    val_status = "正常"
    if isinstance(pe, (int, float)) and pe < 0: val_status = "亏损 (警惕)"
    elif isinstance(pe, (int, float)) and pe > 60: val_status = "高估值 (风险)"
    
    c1, c2, c3 = st.columns(3)
    c1.metric("市盈率 (PE)", f"{pe}")
    c2.metric("市净率 (PB)", f"{pb}")
    c3.metric("估值状态", val_status)

    # === 模块三：AI 深度分析 (事件驱动) ===
    st.markdown("---")
    st.subheader("3️⃣ AI 深度分析 (事件与内幕)")
    st.write("将下方自动生成的指令**复制**，发给 ChatGPT、Kimi、文心一言或 Gemini，获取深度报告。")
    
    # 生成 AI 指令
    news_titles = [n['title'] for n in news[:3]] if news else ["暂无最新重大新闻"]
    
    prompt = f"""
    我正在关注股票【{ticker}】。请扮演一位资深金融分析师，帮我进行深度分析。
    
    【核心数据】：
    1. 技术面评分：{score}/100 (趋势判断)
    2. 当前价格：{current_price:.2f}
    3. 财务指标：PE={pe}, PB={pb}
    4. 最近新闻：{'; '.join(news_titles)}
    
    【请回答以下问题】：
    1. 结合当前国际局势（如美联储政策、地缘政治）和行业政策，这只股票面临哪些外部机遇或风险？
    2. 它的基本面数据（PE/PB）是否支撑当前股价？是否存在泡沫？
    3. 综合技术面和基本面，你建议我是【短线博弈】还是【长线持有】？
    4. 请给出具体的止损位建议。
    """
    
    st.text_area("点击右侧按钮复制 👉", value=prompt, height=250)
