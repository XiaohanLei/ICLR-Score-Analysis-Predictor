import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import ast

# --- 1. 数据加载与预处理 ---
@st.cache_data
def load_data():
    """
    加载真实的 ICLR CSV 数据并预处理
    """
    try:
        # 读取 CSV
        df = pd.read_csv('iclr_2025_real_data.csv')
        
        # 1. 解析分数: "[8, 6, 5]" -> [8, 6, 5]
        df['scores'] = df['scores'].apply(ast.literal_eval)
        
        # 2. 生成"分数签名"用于精确匹配
        # 将分数转为浮点数并排序，转为字符串或元组，忽略顺序差异 (e.g., [6, 8] 和 [8, 6] 视为相同)
        df['score_signature'] = df['scores'].apply(lambda x: tuple(sorted([float(s) for s in x])))
        
        return df
    except FileNotFoundError:
        st.error("未找到数据文件 iclr_2024_real_data.csv，请先运行爬虫脚本！")
        return pd.DataFrame()

# --- 2. 核心分析逻辑 ---

def analyze_exact_match(df, user_scores):
    """
    查找分数完全一致的论文（忽略顺序）
    """
    # 将用户输入也转换为签名格式：排序、浮点化、元组化
    user_signature = tuple(sorted([float(s) for s in user_scores]))
    
    # 筛选
    exact_matches = df[df['score_signature'] == user_signature]
    
    if len(exact_matches) == 0:
        return 0, 0, pd.DataFrame()
    
    accepted_count = len(exact_matches[exact_matches['status'] == 'Accept'])
    total_count = len(exact_matches)
    rate = (accepted_count / total_count) * 100
    
    return rate, total_count, exact_matches

def analyze_mean_match(df, user_scores):
    """
    查找均分相近的论文（原来的逻辑）
    """
    user_mean = np.mean(user_scores)
    
    # 设定搜索范围：均分 ±0.15 (稍微缩小范围以提高相关性)
    range_window = 0.15
    similar_papers = df[
        (df['mean_score'] >= user_mean - range_window) & 
        (df['mean_score'] <= user_mean + range_window)
    ]
    
    if len(similar_papers) == 0:
        return 0, 0, pd.DataFrame()
    
    accepted_count = len(similar_papers[similar_papers['status'] == 'Accept'])
    total_count = len(similar_papers)
    rate = (accepted_count / total_count) * 100
    
    return rate, total_count, similar_papers

# --- 3. 网站 UI 布局 ---
st.set_page_config(page_title="ICLR 接收率预测器", page_icon="🎓", layout="wide")

st.title("🎓 ICLR 历史分数接收率统计")
st.markdown("""
输入你今年的 Review 分数，我们将对比 ICLR 2024 的真实数据，从 **"精确匹配"** 和 **"均分相似"** 两个维度进行分析。
""")

# --- 侧边栏：用户输入 ---
with st.sidebar:
    st.header("📝 输入你的分数")
    st.caption("请用逗号分隔，例如: 8, 6, 6, 3")
    input_str = st.text_input("Scores", "8, 6, 6, 3")
    
    user_scores = []
    try:
        if input_str.strip():
            user_scores = [float(x.strip()) for x in input_str.split(',') if x.strip()]
            user_mean = np.mean(user_scores)
            st.info(f"你的均分: **{user_mean:.2f}**")
            st.write(f"你的分数构成: {sorted([int(s) for s in user_scores], reverse=True)}")
    except:
        st.error("请输入有效的数字格式")

# 加载数据
df = load_data()

if user_scores and not df.empty:
    st.markdown("---")
    
    # === 分析 1: 精确匹配 (Exact Match) ===
    exact_rate, exact_count, exact_df = analyze_exact_match(df, user_scores)
    
    # === 分析 2: 均分相似 (Similar Mean) ===
    mean_rate, mean_count, mean_df = analyze_mean_match(df, user_scores)

    # --- 展示结果 ---
    
    # 容器 1: 精确匹配结果 (高亮显示)
    st.subheader("🎯 精确匹配 (Exact Score Match)")
    if exact_count > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "接收率 (Acceptance Rate)", 
                f"{exact_rate:.1f}%", 
                delta=f"基于 {exact_count} 篇完全相同的历史论文"
            )
        with col2:
            st.metric("样本数量", f"{exact_count} 篇")
        with col3:
            if exact_rate >= 80:
                st.success("极大概率接收 (High Chance)")
            elif exact_rate >= 50:
                st.warning("机会很大 (Good Chance)")
            elif exact_rate >= 25:
                st.warning("处于边缘 (Borderline)")
            else:
                st.error("危险 (Risky)")
                
        with st.expander(f"查看这 {exact_count} 篇完全相同分数的论文详情"):
             st.dataframe(
                 exact_df[['title', 'scores', 'status', 'raw_decision']],
                 use_container_width=True
             )
    else:
        st.warning(f"⚠️ 数据库中没有找到完全匹配分数 ({user_scores}) 的论文。请参考下方的均分预测。")

    st.markdown("---")

    # 容器 2: 均分参考 (作为补充)
    st.subheader("B. 均分相似参考 (Similar Mean Score)")
    st.caption(f"基于均分 {np.mean(user_scores):.2f} ± 0.15 范围内的论文统计")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("估算接收率", f"{mean_rate:.1f}%")
    c2.metric("参考样本数", f"{mean_count} 篇")
    
    # --- 图表可视化 ---
    st.subheader("📊 全局分布图")
    
    tab1, tab2 = st.tabs(["分数分布直方图", "均分vs接收率趋势"])
    
    with tab1:
        # 创建分组统计数据
        hist_data = df.groupby(['mean_score', 'status']).size().reset_index(name='count')
        fig = px.bar(hist_data, x="mean_score", y="count", color="status",
                     title="ICLR 2024 往年分数与接收状态分布",
                     labels={"mean_score": "平均分", "count": "论文数量"},
                     color_discrete_map={"Accept": "#28a745", "Reject": "#dc3545"},
                     opacity=0.8)
        # 标记用户的位置
        fig.add_vline(x=np.mean(user_scores), line_dash="dash", line_color="black", annotation_text="你的均分")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # 计算每个均分的接收率趋势
        trend_data = df.groupby('mean_score')['status'].apply(lambda x: (x == 'Accept').mean()).reset_index(name='accept_rate')
        # 只保留样本数大于5的数据点，避免噪音
        counts = df['mean_score'].value_counts()
        trend_data = trend_data[trend_data['mean_score'].isin(counts[counts > 5].index)]
        
        fig2 = px.line(trend_data, x='mean_score', y='accept_rate', markers=True, 
                       title="均分 vs 接收率趋势线",
                       labels={'mean_score': '平均分', 'accept_rate': '接收率 (0-1)'})
        fig2.add_vline(x=np.mean(user_scores), line_dash="dash", line_color="red", annotation_text="你的位置")
        st.plotly_chart(fig2, use_container_width=True)

elif not user_scores:
    st.info("👈 请在左侧输入你的分数以开始分析")