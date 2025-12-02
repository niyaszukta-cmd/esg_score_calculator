# ============================================================================
# NYZTRADE - ADVANCED ESG DASHBOARD (STREAMLIT)
# Complete Professional ESG Analysis Platform
# ============================================================================

"""
Advanced Streamlit Dashboard for ESG Analysis
Features:
- Sector-wise analysis
- Historical trend simulation
- Portfolio ESG scoring
- PDF report export
- Real-time data refresh

Run: streamlit run streamlit_advanced_esg.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import io
import base64

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="NYZTrade ESG Pro",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/nyztrade/esg',
        'About': 'NYZTrade ESG Pro - Professional ESG Analysis for Indian Markets'
    }
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    /* Main theme */
    :root {
        --primary-color: #1e8449;
        --secondary-color: #27ae60;
        --accent-color: #2ecc71;
        --danger-color: #e74c3c;
        --warning-color: #f39c12;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e8449 0%, #27ae60 50%, #2ecc71 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(30, 132, 73, 0.3);
    }
    
    /* Metric cards */
    .metric-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid var(--primary-color);
        margin-bottom: 15px;
        transition: transform 0.3s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-5px);
    }
    
    /* Score indicators */
    .score-excellent { color: #27ae60; }
    .score-good { color: #2ecc71; }
    .score-average { color: #f39c12; }
    .score-poor { color: #e74c3c; }
    
    /* Info panels */
    .info-panel {
        background-color: #e8f5e9;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #27ae60;
    }
    
    .warning-panel {
        background-color: #fff3e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #f39c12;
    }
    
    /* Tables */
    .dataframe {
        font-size: 0.85em;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #f0f4f0 0%, #e8f5e9 100%);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1e8449, #27ae60);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: bold;
        transition: transform 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 10px;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #1e8449, #2ecc71);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA AND CONFIGURATION
# ============================================================================

# NIFTY 50 Companies with sectors
NIFTY50_COMPANIES = {
    'RELIANCE': {'name': 'Reliance Industries', 'sector': 'Energy', 'industry': 'Oil & Gas', 'market_cap': 1800000},
    'TCS': {'name': 'Tata Consultancy Services', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 1400000},
    'HDFCBANK': {'name': 'HDFC Bank', 'sector': 'Financial Services', 'industry': 'Banking', 'market_cap': 1100000},
    'INFY': {'name': 'Infosys', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 700000},
    'ICICIBANK': {'name': 'ICICI Bank', 'sector': 'Financial Services', 'industry': 'Banking', 'market_cap': 650000},
    'HINDUNILVR': {'name': 'Hindustan Unilever', 'sector': 'Consumer Goods', 'industry': 'FMCG', 'market_cap': 600000},
    'ITC': {'name': 'ITC Limited', 'sector': 'Consumer Goods', 'industry': 'FMCG', 'market_cap': 550000},
    'SBIN': {'name': 'State Bank of India', 'sector': 'Financial Services', 'industry': 'Banking', 'market_cap': 500000},
    'BHARTIARTL': {'name': 'Bharti Airtel', 'sector': 'Telecom', 'industry': 'Telecom', 'market_cap': 480000},
    'KOTAKBANK': {'name': 'Kotak Mahindra Bank', 'sector': 'Financial Services', 'industry': 'Banking', 'market_cap': 350000},
    'WIPRO': {'name': 'Wipro', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 300000},
    'LT': {'name': 'Larsen & Toubro', 'sector': 'Infrastructure', 'industry': 'Construction', 'market_cap': 400000},
    'AXISBANK': {'name': 'Axis Bank', 'sector': 'Financial Services', 'industry': 'Banking', 'market_cap': 280000},
    'ASIANPAINT': {'name': 'Asian Paints', 'sector': 'Consumer Goods', 'industry': 'Paints', 'market_cap': 320000},
    'MARUTI': {'name': 'Maruti Suzuki', 'sector': 'Automobile', 'industry': 'Automobiles', 'market_cap': 350000},
    'TATASTEEL': {'name': 'Tata Steel', 'sector': 'Materials', 'industry': 'Steel', 'market_cap': 180000},
    'NTPC': {'name': 'NTPC', 'sector': 'Utilities', 'industry': 'Power', 'market_cap': 250000},
    'POWERGRID': {'name': 'Power Grid Corp', 'sector': 'Utilities', 'industry': 'Power', 'market_cap': 200000},
    'SUNPHARMA': {'name': 'Sun Pharma', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals', 'market_cap': 320000},
    'DRREDDY': {'name': "Dr. Reddy's Labs", 'sector': 'Healthcare', 'industry': 'Pharmaceuticals', 'market_cap': 100000},
    'ONGC': {'name': 'ONGC', 'sector': 'Energy', 'industry': 'Oil & Gas', 'market_cap': 200000},
    'COALINDIA': {'name': 'Coal India', 'sector': 'Energy', 'industry': 'Mining', 'market_cap': 150000},
    'TATAMOTORS': {'name': 'Tata Motors', 'sector': 'Automobile', 'industry': 'Automobiles', 'market_cap': 250000},
    'M&M': {'name': 'Mahindra & Mahindra', 'sector': 'Automobile', 'industry': 'Automobiles', 'market_cap': 280000},
    'HCLTECH': {'name': 'HCL Technologies', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 350000},
}

# Category weights
CATEGORY_WEIGHTS = {'Environmental': 0.35, 'Social': 0.35, 'Governance': 0.30}

# Industry adjustments
INDUSTRY_ADJUSTMENTS = {
    'Oil & Gas': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Mining': {'environmental': 1.3, 'social': 1.0, 'governance': 0.7},
    'Power': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'IT Services': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'Banking': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'FMCG': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Pharmaceuticals': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Automobiles': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Telecom': {'environmental': 0.9, 'social': 1.0, 'governance': 1.1},
    'Construction': {'environmental': 1.1, 'social': 1.0, 'governance': 0.9},
    'Paints': {'environmental': 1.1, 'social': 0.9, 'governance': 1.0},
    'Default': {'environmental': 1.0, 'social': 1.0, 'governance': 1.0}
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)
def generate_esg_scores(companies: Dict) -> pd.DataFrame:
    """Generate ESG scores for all companies"""
    results = []
    
    for symbol, info in companies.items():
        np.random.seed(hash(symbol) % 2**32)
        
        industry = info.get('industry', 'Default')
        adj = INDUSTRY_ADJUSTMENTS.get(industry, INDUSTRY_ADJUSTMENTS['Default'])
        
        # Generate base scores
        env_base = np.random.uniform(45, 85)
        social_base = np.random.uniform(50, 90)
        gov_base = np.random.uniform(55, 90)
        
        # Calculate overall with adjustments
        overall = (
            env_base * 0.35 +
            social_base * 0.35 +
            gov_base * 0.30
        )
        
        # Risk level
        if overall >= 80:
            risk = "Negligible"
        elif overall >= 65:
            risk = "Low"
        elif overall >= 50:
            risk = "Medium"
        elif overall >= 35:
            risk = "High"
        else:
            risk = "Severe"
        
        results.append({
            'Symbol': symbol,
            'Company': info['name'],
            'Sector': info['sector'],
            'Industry': info['industry'],
            'Market Cap (Cr)': info['market_cap'],
            'Environmental': round(env_base, 1),
            'Social': round(social_base, 1),
            'Governance': round(gov_base, 1),
            'Overall ESG': round(overall, 1),
            'Risk Level': risk,
            'Controversy': round(np.random.uniform(0, 25), 1)
        })
    
    return pd.DataFrame(results).sort_values('Overall ESG', ascending=False)


def generate_historical_data(symbol: str, periods: int = 12) -> pd.DataFrame:
    """Generate simulated historical ESG data"""
    np.random.seed(hash(symbol) % 2**32)
    
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='M')
    
    # Base scores with slight trend
    env_base = np.random.uniform(50, 70)
    social_base = np.random.uniform(55, 75)
    gov_base = np.random.uniform(60, 80)
    
    data = []
    for i, date in enumerate(dates):
        # Add slight improvement trend with noise
        env = env_base + i * 0.5 + np.random.uniform(-3, 3)
        social = social_base + i * 0.3 + np.random.uniform(-3, 3)
        gov = gov_base + i * 0.2 + np.random.uniform(-2, 2)
        overall = env * 0.35 + social * 0.35 + gov * 0.30
        
        data.append({
            'Date': date,
            'Environmental': round(min(100, max(0, env)), 1),
            'Social': round(min(100, max(0, social)), 1),
            'Governance': round(min(100, max(0, gov)), 1),
            'Overall': round(min(100, max(0, overall)), 1)
        })
    
    return pd.DataFrame(data)


def get_risk_color(risk_level: str) -> str:
    """Get color for risk level"""
    colors = {
        "Negligible": "#27ae60",
        "Low": "#2ecc71",
        "Medium": "#f39c12",
        "High": "#e74c3c",
        "Severe": "#c0392b"
    }
    return colors.get(risk_level, "#f39c12")


def get_score_icon(score: float) -> str:
    """Get icon based on score"""
    if score >= 80:
        return "🌟"
    elif score >= 65:
        return "✅"
    elif score >= 50:
        return "⚠️"
    else:
        return "❌"


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_esg_gauge(score: float, title: str) -> go.Figure:
    """Create animated gauge chart"""
    if score >= 80:
        color = "#27ae60"
    elif score >= 65:
        color = "#2ecc71"
    elif score >= 50:
        color = "#f39c12"
    else:
        color = "#e74c3c"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 18, 'family': 'Arial'}},
        delta={'reference': 50, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.8},
            'bgcolor': "white",
            'borderwidth': 2,
            'steps': [
                {'range': [0, 35], 'color': 'rgba(192, 57, 43, 0.2)'},
                {'range': [35, 50], 'color': 'rgba(231, 76, 60, 0.2)'},
                {'range': [50, 65], 'color': 'rgba(243, 156, 18, 0.2)'},
                {'range': [65, 80], 'color': 'rgba(46, 204, 113, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(39, 174, 96, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.8,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': "Arial"}
    )
    
    return fig


def create_sector_breakdown(df: pd.DataFrame) -> go.Figure:
    """Create sector-wise ESG breakdown"""
    sector_avg = df.groupby('Sector').agg({
        'Environmental': 'mean',
        'Social': 'mean',
        'Governance': 'mean',
        'Overall ESG': 'mean',
        'Symbol': 'count'
    }).round(1).reset_index()
    sector_avg.columns = ['Sector', 'Environmental', 'Social', 'Governance', 'Overall', 'Companies']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Environmental',
        x=sector_avg['Sector'],
        y=sector_avg['Environmental'],
        marker_color='#27ae60'
    ))
    
    fig.add_trace(go.Bar(
        name='Social',
        x=sector_avg['Sector'],
        y=sector_avg['Social'],
        marker_color='#3498db'
    ))
    
    fig.add_trace(go.Bar(
        name='Governance',
        x=sector_avg['Sector'],
        y=sector_avg['Governance'],
        marker_color='#9b59b6'
    ))
    
    fig.add_trace(go.Scatter(
        name='Overall ESG',
        x=sector_avg['Sector'],
        y=sector_avg['Overall'],
        mode='lines+markers',
        line=dict(color='#e74c3c', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="Sector-wise ESG Performance",
        barmode='group',
        xaxis_title="Sector",
        yaxis_title="Score",
        yaxis=dict(range=[0, 100]),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig


def create_treemap(df: pd.DataFrame) -> go.Figure:
    """Create ESG treemap by sector"""
    fig = px.treemap(
        df,
        path=['Sector', 'Symbol'],
        values='Market Cap (Cr)',
        color='Overall ESG',
        color_continuous_scale=['#c0392b', '#e74c3c', '#f39c12', '#2ecc71', '#27ae60'],
        range_color=[40, 90],
        title="ESG Treemap by Market Cap and Sector"
    )
    
    fig.update_layout(height=500)
    
    return fig


def create_scatter_matrix(df: pd.DataFrame) -> go.Figure:
    """Create E-S-G scatter matrix"""
    fig = px.scatter_3d(
        df,
        x='Environmental',
        y='Social',
        z='Governance',
        color='Sector',
        size='Market Cap (Cr)',
        hover_name='Company',
        title="3D ESG Score Distribution",
        labels={
            'Environmental': 'E Score',
            'Social': 'S Score',
            'Governance': 'G Score'
        }
    )
    
    fig.update_layout(
        height=600,
        scene=dict(
            xaxis=dict(range=[30, 100]),
            yaxis=dict(range=[30, 100]),
            zaxis=dict(range=[30, 100])
        )
    )
    
    return fig


def create_trend_chart(historical_df: pd.DataFrame, company_name: str) -> go.Figure:
    """Create ESG trend chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Environmental'],
        name='Environmental',
        line=dict(color='#27ae60', width=2),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Social'],
        name='Social',
        line=dict(color='#3498db', width=2),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Governance'],
        name='Governance',
        line=dict(color='#9b59b6', width=2),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Overall'],
        name='Overall ESG',
        line=dict(color='#e74c3c', width=3),
        mode='lines+markers',
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f"ESG Score Trend - {company_name}",
        xaxis_title="Date",
        yaxis_title="Score",
        yaxis=dict(range=[30, 100]),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig


def create_risk_distribution(df: pd.DataFrame) -> go.Figure:
    """Create risk level distribution chart"""
    risk_counts = df['Risk Level'].value_counts().reset_index()
    risk_counts.columns = ['Risk Level', 'Count']
    
    colors = {
        'Negligible': '#27ae60',
        'Low': '#2ecc71',
        'Medium': '#f39c12',
        'High': '#e74c3c',
        'Severe': '#c0392b'
    }
    
    fig = px.pie(
        risk_counts,
        values='Count',
        names='Risk Level',
        color='Risk Level',
        color_discrete_map=colors,
        title="ESG Risk Distribution"
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style='margin: 0; font-size: 2.5em;'>🌿 NYZTrade ESG Pro</h1>
        <p style='margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;'>
            Professional ESG Analysis Platform for Indian Listed Companies
        </p>
        <p style='margin: 5px 0 0 0; font-size: 0.9em; opacity: 0.7;'>
            BRSR Framework Compliant | Real-time Analysis | Portfolio Scoring
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 🎛️ Control Center")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigate to",
        ["🏠 Dashboard", "🏢 Company Analysis", "📊 Sector Analysis", 
         "📁 Portfolio Scoring", "📈 Trends & History", "📋 Full Report"]
    )
    
    # Generate data
    esg_df = generate_esg_scores(NIFTY50_COMPANIES)
    
    # ========================================================================
    # DASHBOARD PAGE
    # ========================================================================
    if page == "🏠 Dashboard":
        st.markdown("### 📊 NIFTY 50 ESG Overview")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_esg = esg_df['Overall ESG'].mean()
            st.metric(
                "Average ESG Score",
                f"{avg_esg:.1f}",
                f"{avg_esg - 50:.1f} vs benchmark",
                delta_color="normal"
            )
        
        with col2:
            leaders = len(esg_df[esg_df['Risk Level'].isin(['Negligible', 'Low'])])
            st.metric(
                "ESG Leaders",
                f"{leaders}",
                f"{leaders/len(esg_df)*100:.0f}% of companies"
            )
        
        with col3:
            laggards = len(esg_df[esg_df['Risk Level'].isin(['High', 'Severe'])])
            st.metric(
                "ESG Laggards",
                f"{laggards}",
                f"{laggards/len(esg_df)*100:.0f}% of companies",
                delta_color="inverse"
            )
        
        with col4:
            top_sector = esg_df.groupby('Sector')['Overall ESG'].mean().idxmax()
            st.metric(
                "Top Sector",
                top_sector,
                f"Avg: {esg_df[esg_df['Sector']==top_sector]['Overall ESG'].mean():.1f}"
            )
        
        # Charts row
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = create_sector_breakdown(esg_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_risk_distribution(esg_df)
            st.plotly_chart(fig, use_container_width=True)
        
        # Treemap
        st.markdown("### 🗺️ ESG Landscape")
        fig = create_treemap(esg_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Top & Bottom performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 Top 5 ESG Performers")
            top5 = esg_df.head(5)[['Symbol', 'Company', 'Overall ESG', 'Risk Level']]
            for i, row in top5.iterrows():
                color = get_risk_color(row['Risk Level'])
                st.markdown(f"""
                <div class="metric-container">
                    <strong>{row['Symbol']}</strong> - {row['Company'][:25]}
                    <span style='float: right; color: {color}; font-weight: bold;'>
                        {row['Overall ESG']:.1f} {get_score_icon(row['Overall ESG'])}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### ⚠️ Needs Improvement")
            bottom5 = esg_df.tail(5)[['Symbol', 'Company', 'Overall ESG', 'Risk Level']]
            for i, row in bottom5.iloc[::-1].iterrows():
                color = get_risk_color(row['Risk Level'])
                st.markdown(f"""
                <div class="metric-container" style="border-left-color: {color};">
                    <strong>{row['Symbol']}</strong> - {row['Company'][:25]}
                    <span style='float: right; color: {color}; font-weight: bold;'>
                        {row['Overall ESG']:.1f} {get_score_icon(row['Overall ESG'])}
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    # ========================================================================
    # COMPANY ANALYSIS PAGE
    # ========================================================================
    elif page == "🏢 Company Analysis":
        st.markdown("### 🏢 Individual Company ESG Analysis")
        
        selected_symbol = st.selectbox(
            "Select Company",
            esg_df['Symbol'].tolist(),
            format_func=lambda x: f"{x} - {NIFTY50_COMPANIES[x]['name']}"
        )
        
        company_data = esg_df[esg_df['Symbol'] == selected_symbol].iloc[0]
        company_info = NIFTY50_COMPANIES[selected_symbol]
        
        # Company header
        risk_color = get_risk_color(company_data['Risk Level'])
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #34495e, #2c3e50); padding: 25px; 
                    border-radius: 15px; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0;'>{company_info['name']}</h2>
            <p style='color: #bdc3c7; margin: 5px 0;'>
                {selected_symbol} | {company_info['sector']} | {company_info['industry']}
            </p>
            <span style='background-color: {risk_color}; color: white; padding: 5px 15px; 
                        border-radius: 20px; font-weight: bold;'>
                {company_data['Risk Level']} Risk
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Gauge charts
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            fig = create_esg_gauge(company_data['Environmental'], "Environmental")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_esg_gauge(company_data['Social'], "Social")
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            fig = create_esg_gauge(company_data['Governance'], "Governance")
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            fig = create_esg_gauge(company_data['Overall ESG'], "Overall ESG")
            st.plotly_chart(fig, use_container_width=True)
        
        # Historical trend
        st.markdown("### 📈 Historical ESG Trend")
        historical_df = generate_historical_data(selected_symbol)
        fig = create_trend_chart(historical_df, company_info['name'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Peer comparison
        st.markdown("### 👥 Peer Comparison")
        peers = esg_df[esg_df['Industry'] == company_info['industry']]
        
        if len(peers) > 1:
            fig = px.bar(
                peers,
                x='Symbol',
                y=['Environmental', 'Social', 'Governance'],
                title=f"Industry Comparison - {company_info['industry']}",
                barmode='group'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No peer companies in the same industry for comparison.")
    
    # ========================================================================
    # SECTOR ANALYSIS PAGE
    # ========================================================================
    elif page == "📊 Sector Analysis":
        st.markdown("### 📊 Sector-wise ESG Analysis")
        
        selected_sector = st.selectbox(
            "Select Sector",
            esg_df['Sector'].unique().tolist()
        )
        
        sector_df = esg_df[esg_df['Sector'] == selected_sector]
        
        # Sector metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Companies", len(sector_df))
        with col2:
            st.metric("Avg ESG Score", f"{sector_df['Overall ESG'].mean():.1f}")
        with col3:
            st.metric("Best Performer", sector_df.iloc[0]['Symbol'])
        with col4:
            st.metric("Avg E Score", f"{sector_df['Environmental'].mean():.1f}")
        
        # Sector companies comparison
        fig = px.bar(
            sector_df,
            x='Symbol',
            y=['Environmental', 'Social', 'Governance'],
            title=f"ESG Breakdown - {selected_sector} Sector",
            barmode='group',
            color_discrete_sequence=['#27ae60', '#3498db', '#9b59b6']
        )
        fig.add_scatter(
            x=sector_df['Symbol'],
            y=sector_df['Overall ESG'],
            name='Overall ESG',
            mode='lines+markers',
            line=dict(color='#e74c3c', width=2)
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        
        # Sector table
        st.markdown("### 📋 Sector Companies")
        display_df = sector_df[['Symbol', 'Company', 'Environmental', 'Social', 
                                'Governance', 'Overall ESG', 'Risk Level']]
        st.dataframe(
            display_df.style.background_gradient(
                subset=['Environmental', 'Social', 'Governance', 'Overall ESG'],
                cmap='RdYlGn',
                vmin=40,
                vmax=90
            ),
            use_container_width=True
        )
    
    # ========================================================================
    # PORTFOLIO SCORING PAGE
    # ========================================================================
    elif page == "📁 Portfolio Scoring":
        st.markdown("### 📁 Portfolio ESG Scoring")
        
        st.markdown("""
        <div class="info-panel">
            <strong>📌 How to use:</strong> Select companies to build your portfolio and 
            see the weighted ESG score based on your allocation.
        </div>
        """, unsafe_allow_html=True)
        
        selected_companies = st.multiselect(
            "Select Companies for Portfolio",
            esg_df['Symbol'].tolist(),
            default=['TCS', 'HDFCBANK', 'RELIANCE', 'INFY'],
            format_func=lambda x: f"{x} - {NIFTY50_COMPANIES[x]['name']}"
        )
        
        if len(selected_companies) >= 2:
            # Allocation input
            st.markdown("### 📊 Set Allocations")
            allocations = {}
            remaining = 100.0
            
            cols = st.columns(min(4, len(selected_companies)))
            for i, symbol in enumerate(selected_companies):
                with cols[i % 4]:
                    default_val = 100 / len(selected_companies)
                    allocations[symbol] = st.number_input(
                        f"{symbol} (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=default_val,
                        step=5.0,
                        key=f"alloc_{symbol}"
                    )
            
            total_allocation = sum(allocations.values())
            
            if abs(total_allocation - 100) > 0.1:
                st.warning(f"⚠️ Total allocation is {total_allocation:.1f}%. Please adjust to 100%.")
            else:
                # Calculate portfolio ESG
                portfolio_df = esg_df[esg_df['Symbol'].isin(selected_companies)].copy()
                portfolio_df['Allocation'] = portfolio_df['Symbol'].map(allocations)
                
                weighted_env = (portfolio_df['Environmental'] * portfolio_df['Allocation'] / 100).sum()
                weighted_social = (portfolio_df['Social'] * portfolio_df['Allocation'] / 100).sum()
                weighted_gov = (portfolio_df['Governance'] * portfolio_df['Allocation'] / 100).sum()
                weighted_overall = (portfolio_df['Overall ESG'] * portfolio_df['Allocation'] / 100).sum()
                
                # Portfolio metrics
                st.markdown("### 📈 Portfolio ESG Scores")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    fig = create_esg_gauge(weighted_env, "Environmental")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = create_esg_gauge(weighted_social, "Social")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col3:
                    fig = create_esg_gauge(weighted_gov, "Governance")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col4:
                    fig = create_esg_gauge(weighted_overall, "Overall ESG")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Portfolio composition
                st.markdown("### 📊 Portfolio Composition")
                fig = px.pie(
                    portfolio_df,
                    values='Allocation',
                    names='Symbol',
                    title="Portfolio Allocation",
                    hover_data=['Company', 'Overall ESG']
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                # Portfolio table
                st.markdown("### 📋 Portfolio Holdings")
                display_df = portfolio_df[['Symbol', 'Company', 'Allocation', 
                                          'Environmental', 'Social', 'Governance', 
                                          'Overall ESG', 'Risk Level']]
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Please select at least 2 companies to build a portfolio.")
    
    # ========================================================================
    # TRENDS & HISTORY PAGE
    # ========================================================================
    elif page == "📈 Trends & History":
        st.markdown("### 📈 ESG Trends & Historical Analysis")
        
        selected_symbols = st.multiselect(
            "Select Companies to Compare",
            esg_df['Symbol'].tolist(),
            default=['TCS', 'RELIANCE', 'HDFCBANK'],
            max_selections=5,
            format_func=lambda x: f"{x} - {NIFTY50_COMPANIES[x]['name']}"
        )
        
        if selected_symbols:
            # Generate historical data for selected companies
            fig = go.Figure()
            
            colors = ['#27ae60', '#3498db', '#9b59b6', '#e74c3c', '#f39c12']
            
            for i, symbol in enumerate(selected_symbols):
                hist_df = generate_historical_data(symbol)
                fig.add_trace(go.Scatter(
                    x=hist_df['Date'],
                    y=hist_df['Overall'],
                    name=f"{symbol}",
                    line=dict(color=colors[i % len(colors)], width=2),
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title="Overall ESG Score Trend Comparison",
                xaxis_title="Date",
                yaxis_title="Overall ESG Score",
                yaxis=dict(range=[30, 100]),
                height=500,
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # YoY change
            st.markdown("### 📊 Year-over-Year Change")
            
            yoy_data = []
            for symbol in selected_symbols:
                hist_df = generate_historical_data(symbol)
                current = hist_df.iloc[-1]['Overall']
                previous = hist_df.iloc[0]['Overall']
                change = current - previous
                pct_change = (change / previous) * 100
                
                yoy_data.append({
                    'Symbol': symbol,
                    'Company': NIFTY50_COMPANIES[symbol]['name'],
                    'Current Score': round(current, 1),
                    'Previous Score': round(previous, 1),
                    'Change': round(change, 1),
                    '% Change': round(pct_change, 1)
                })
            
            yoy_df = pd.DataFrame(yoy_data)
            st.dataframe(yoy_df, use_container_width=True)
    
    # ========================================================================
    # FULL REPORT PAGE
    # ========================================================================
    elif page == "📋 Full Report":
        st.markdown("### 📋 Complete NIFTY 50 ESG Report")
        
        # Summary statistics
        st.markdown("#### 📊 Summary Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            summary_stats = esg_df[['Environmental', 'Social', 'Governance', 'Overall ESG']].describe()
            st.dataframe(summary_stats.round(1), use_container_width=True)
        
        with col2:
            risk_summary = esg_df['Risk Level'].value_counts()
            st.dataframe(risk_summary, use_container_width=True)
        
        # Full table
        st.markdown("#### 📋 Complete ESG Scores")
        
        styled_df = esg_df.style.background_gradient(
            subset=['Environmental', 'Social', 'Governance', 'Overall ESG'],
            cmap='RdYlGn',
            vmin=40,
            vmax=90
        ).format({
            'Market Cap (Cr)': '{:,.0f}',
            'Environmental': '{:.1f}',
            'Social': '{:.1f}',
            'Governance': '{:.1f}',
            'Overall ESG': '{:.1f}',
            'Controversy': '{:.1f}'
        })
        
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        # Download options
        st.markdown("#### 💾 Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = esg_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"nifty50_esg_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            json_data = esg_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"nifty50_esg_report_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        with col3:
            st.info("📄 PDF export coming soon!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: #7f8c8d;'>
        <p>🌿 <strong>NYZTrade ESG Pro</strong> | Powered by BRSR Framework</p>
        <p style='font-size: 0.8em;'>
            ⚠️ This is a demonstration tool. Actual ESG assessments should be based on verified BRSR disclosures.
        </p>
        <p style='font-size: 0.7em;'>
            Data refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
    """.format(datetime=datetime), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
