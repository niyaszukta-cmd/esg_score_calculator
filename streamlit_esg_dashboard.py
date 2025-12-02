# ============================================================================
# NYZTRADE - ESG SUSTAINABILITY DASHBOARD (STREAMLIT)
# Comprehensive ESG Score Visualization for Indian Companies
# ============================================================================

"""
Streamlit Dashboard for ESG Analysis
Run: streamlit run streamlit_esg_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="NYZTrade ESG Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 1rem;
    }
    
    /* Headers */
    .stTitle {
        color: #1e8449;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    
    /* ESG Score gauge colors */
    .esg-negligible { color: #27ae60; }
    .esg-low { color: #2ecc71; }
    .esg-medium { color: #f39c12; }
    .esg-high { color: #e74c3c; }
    .esg-severe { color: #c0392b; }
    
    /* Score badge */
    .score-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    .score-excellent { background-color: #27ae60; color: white; }
    .score-good { background-color: #2ecc71; color: white; }
    .score-average { background-color: #f39c12; color: white; }
    .score-poor { background-color: #e74c3c; color: white; }
    .score-critical { background-color: #c0392b; color: white; }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #1e8449, #27ae60);
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        margin: 20px 0;
        font-size: 1.2em;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #f8f9fa;
        border-left: 5px solid #1e8449;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    /* Tables */
    .dataframe {
        font-size: 0.9em;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f0f4f0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA CLASSES AND ENUMS (Matching main module)
# ============================================================================

class ESGCategory(Enum):
    ENVIRONMENTAL = "Environmental"
    SOCIAL = "Social"
    GOVERNANCE = "Governance"


class RiskLevel(Enum):
    NEGLIGIBLE = "Negligible"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    SEVERE = "Severe"


# ============================================================================
# ESG WEIGHTS CONFIG (Matching main module)
# ============================================================================

CATEGORY_WEIGHTS = {
    'Environmental': 0.35,
    'Social': 0.35,
    'Governance': 0.30
}

ENVIRONMENTAL_WEIGHTS = {
    'carbon_emissions_intensity': 0.20,
    'energy_consumption_intensity': 0.15,
    'renewable_energy_percentage': 0.15,
    'water_consumption_intensity': 0.12,
    'waste_recycling_rate': 0.10,
    'hazardous_waste_management': 0.08,
    'biodiversity_initiatives': 0.05,
    'environmental_compliance': 0.10,
    'climate_risk_disclosure': 0.05
}

SOCIAL_WEIGHTS = {
    'employee_health_safety': 0.15,
    'employee_turnover_rate': 0.10,
    'diversity_inclusion': 0.12,
    'training_development': 0.10,
    'fair_wages': 0.10,
    'community_investment': 0.08,
    'human_rights_compliance': 0.10,
    'customer_satisfaction': 0.08,
    'data_privacy_security': 0.10,
    'labor_practices': 0.07
}

GOVERNANCE_WEIGHTS = {
    'board_independence': 0.15,
    'board_diversity': 0.12,
    'audit_committee_quality': 0.12,
    'executive_compensation': 0.10,
    'shareholder_rights': 0.10,
    'ethics_anti_corruption': 0.12,
    'risk_management': 0.10,
    'tax_transparency': 0.08,
    'related_party_transactions': 0.06,
    'sustainability_committee': 0.05
}

# Industry Adjustments
INDUSTRY_ADJUSTMENTS = {
    'Oil & Gas': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Mining': {'environmental': 1.3, 'social': 1.0, 'governance': 0.7},
    'Power': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Cement': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Banking': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'IT Services': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'Pharmaceuticals': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'FMCG': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Automobiles': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Real Estate': {'environmental': 1.1, 'social': 1.0, 'governance': 0.9},
    'Default': {'environmental': 1.0, 'social': 1.0, 'governance': 1.0}
}


# ============================================================================
# NSE DATA FETCHER
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_company_info(symbol: str) -> Dict:
    """Fetch company info from NSE"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nseindia.com/',
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=10)
        
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'symbol': symbol,
                'company_name': data.get('info', {}).get('companyName', symbol),
                'industry': data.get('metadata', {}).get('industry', 'Unknown'),
                'sector': data.get('metadata', {}).get('sector', 'Unknown'),
                'market_cap': data.get('securityInfo', {}).get('marketCap', 0),
                'last_price': data.get('priceInfo', {}).get('lastPrice', 0),
            }
    except Exception as e:
        st.warning(f"Could not fetch live data for {symbol}. Using sample data.")
    
    return {
        'symbol': symbol,
        'company_name': symbol,
        'industry': 'Default',
        'sector': 'Default',
        'market_cap': 0,
        'last_price': 0
    }


# ============================================================================
# ESG SCORE CALCULATOR
# ============================================================================

def calculate_environmental_score(data: Dict) -> tuple:
    """Calculate environmental score"""
    metrics = {}
    
    # Carbon Emissions
    carbon_intensity = data.get('carbon_emissions_intensity', 50)
    benchmark = data.get('benchmark_carbon', 50)
    metrics['Carbon Emissions Intensity'] = {
        'value': carbon_intensity,
        'score': max(0, min(100, 100 - (carbon_intensity / benchmark * 50))),
        'weight': ENVIRONMENTAL_WEIGHTS['carbon_emissions_intensity'],
        'unit': 'tCO2e/Cr'
    }
    
    # Energy Consumption
    energy_intensity = data.get('energy_consumption_intensity', 200)
    benchmark_energy = data.get('benchmark_energy', 200)
    metrics['Energy Consumption Intensity'] = {
        'value': energy_intensity,
        'score': max(0, min(100, 100 - (energy_intensity / benchmark_energy * 50))),
        'weight': ENVIRONMENTAL_WEIGHTS['energy_consumption_intensity'],
        'unit': 'GJ/Cr'
    }
    
    # Renewable Energy
    renewable_pct = data.get('renewable_energy_percentage', 25)
    metrics['Renewable Energy Share'] = {
        'value': renewable_pct,
        'score': min(100, renewable_pct * 2),
        'weight': ENVIRONMENTAL_WEIGHTS['renewable_energy_percentage'],
        'unit': '%'
    }
    
    # Water Consumption
    water_intensity = data.get('water_consumption_intensity', 300)
    benchmark_water = data.get('benchmark_water', 300)
    metrics['Water Consumption Intensity'] = {
        'value': water_intensity,
        'score': max(0, min(100, 100 - (water_intensity / benchmark_water * 50))),
        'weight': ENVIRONMENTAL_WEIGHTS['water_consumption_intensity'],
        'unit': 'KL/Cr'
    }
    
    # Waste Recycling
    waste_recycling = data.get('waste_recycling_rate', 65)
    metrics['Waste Recycling Rate'] = {
        'value': waste_recycling,
        'score': min(100, waste_recycling * 1.25),
        'weight': ENVIRONMENTAL_WEIGHTS['waste_recycling_rate'],
        'unit': '%'
    }
    
    # Environmental Compliance
    env_compliance = data.get('environmental_compliance', 95)
    metrics['Environmental Compliance'] = {
        'value': env_compliance,
        'score': min(100, env_compliance),
        'weight': ENVIRONMENTAL_WEIGHTS['environmental_compliance'],
        'unit': '%'
    }
    
    # Climate Risk Disclosure
    climate_disclosure = data.get('climate_risk_disclosure', 60)
    metrics['Climate Risk Disclosure'] = {
        'value': climate_disclosure,
        'score': min(100, climate_disclosure),
        'weight': ENVIRONMENTAL_WEIGHTS['climate_risk_disclosure'],
        'unit': '%'
    }
    
    # Calculate weighted average
    total_score = sum(m['score'] * m['weight'] for m in metrics.values())
    
    return total_score, metrics


def calculate_social_score(data: Dict) -> tuple:
    """Calculate social score"""
    metrics = {}
    
    # Employee Safety
    ltifr = data.get('ltifr', 0.5)
    benchmark_ltifr = data.get('benchmark_ltifr', 0.5)
    metrics['Employee Health & Safety'] = {
        'value': ltifr,
        'score': max(0, min(100, 100 - (ltifr / benchmark_ltifr * 50))),
        'weight': SOCIAL_WEIGHTS['employee_health_safety'],
        'unit': 'LTIFR'
    }
    
    # Employee Turnover
    turnover = data.get('employee_turnover_rate', 15)
    metrics['Employee Retention'] = {
        'value': turnover,
        'score': max(0, min(100, 100 - (turnover * 2))),
        'weight': SOCIAL_WEIGHTS['employee_turnover_rate'],
        'unit': '%'
    }
    
    # Diversity
    women_workforce = data.get('women_workforce_percentage', 25)
    metrics['Diversity & Inclusion'] = {
        'value': women_workforce,
        'score': min(100, women_workforce * 2.5),
        'weight': SOCIAL_WEIGHTS['diversity_inclusion'],
        'unit': '% women'
    }
    
    # Training
    training_hours = data.get('training_hours_per_employee', 20)
    metrics['Training & Development'] = {
        'value': training_hours,
        'score': min(100, training_hours * 2.5),
        'weight': SOCIAL_WEIGHTS['training_development'],
        'unit': 'hrs/emp'
    }
    
    # CSR
    csr_spending = data.get('csr_spending_percentage', 2)
    metrics['Community Investment'] = {
        'value': csr_spending,
        'score': min(100, csr_spending * 40),
        'weight': SOCIAL_WEIGHTS['community_investment'],
        'unit': '% profit'
    }
    
    # Human Rights
    human_rights = data.get('human_rights_compliance', 90)
    metrics['Human Rights'] = {
        'value': human_rights,
        'score': min(100, human_rights),
        'weight': SOCIAL_WEIGHTS['human_rights_compliance'],
        'unit': '%'
    }
    
    # Customer Satisfaction
    customer_resolved = data.get('customer_complaints_resolved', 95)
    metrics['Customer Satisfaction'] = {
        'value': customer_resolved,
        'score': min(100, customer_resolved),
        'weight': SOCIAL_WEIGHTS['customer_satisfaction'],
        'unit': '% resolved'
    }
    
    total_score = sum(m['score'] * m['weight'] for m in metrics.values())
    
    return total_score, metrics


def calculate_governance_score(data: Dict) -> tuple:
    """Calculate governance score"""
    metrics = {}
    
    # Board Independence
    independent_pct = data.get('independent_directors_percentage', 50)
    metrics['Board Independence'] = {
        'value': independent_pct,
        'score': min(100, independent_pct * 1.5),
        'weight': GOVERNANCE_WEIGHTS['board_independence'],
        'unit': '%'
    }
    
    # Board Diversity
    women_board = data.get('women_directors_percentage', 17)
    metrics['Board Diversity'] = {
        'value': women_board,
        'score': min(100, women_board * 4),
        'weight': GOVERNANCE_WEIGHTS['board_diversity'],
        'unit': '% women'
    }
    
    # Audit Committee
    audit_meetings = data.get('audit_committee_meetings', 4)
    metrics['Audit Committee'] = {
        'value': audit_meetings,
        'score': min(100, audit_meetings * 16.67),
        'weight': GOVERNANCE_WEIGHTS['audit_committee_quality'],
        'unit': 'meetings'
    }
    
    # Executive Compensation
    ceo_ratio = data.get('ceo_median_pay_ratio', 100)
    metrics['Executive Compensation'] = {
        'value': ceo_ratio,
        'score': max(0, min(100, 150 - (ceo_ratio * 0.5))),
        'weight': GOVERNANCE_WEIGHTS['executive_compensation'],
        'unit': 'x median'
    }
    
    # Ethics
    ethics_compliance = data.get('ethics_anti_corruption', 90)
    metrics['Ethics & Anti-Corruption'] = {
        'value': ethics_compliance,
        'score': min(100, ethics_compliance),
        'weight': GOVERNANCE_WEIGHTS['ethics_anti_corruption'],
        'unit': '%'
    }
    
    # Risk Management
    risk_mgmt = data.get('risk_management', 80)
    metrics['Risk Management'] = {
        'value': risk_mgmt,
        'score': min(100, risk_mgmt),
        'weight': GOVERNANCE_WEIGHTS['risk_management'],
        'unit': 'score'
    }
    
    total_score = sum(m['score'] * m['weight'] for m in metrics.values())
    
    return total_score, metrics


def get_risk_level(score: float) -> str:
    """Get risk level based on score"""
    if score >= 80:
        return "Negligible"
    elif score >= 65:
        return "Low"
    elif score >= 50:
        return "Medium"
    elif score >= 35:
        return "High"
    else:
        return "Severe"


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


def generate_sample_data(industry: str) -> Dict:
    """Generate sample ESG data based on industry"""
    np.random.seed(hash(industry) % 2**32)
    
    # Industry-specific benchmarks
    benchmarks = {
        'IT Services': {'carbon': 5, 'energy': 50, 'water': 50},
        'Banking': {'carbon': 2, 'energy': 30, 'water': 30},
        'Oil & Gas': {'carbon': 150, 'energy': 500, 'water': 1000},
        'Power': {'carbon': 200, 'energy': 800, 'water': 2000},
        'Default': {'carbon': 50, 'energy': 200, 'water': 300}
    }
    
    bench = benchmarks.get(industry, benchmarks['Default'])
    
    return {
        # Environmental
        'carbon_emissions_intensity': bench['carbon'] * np.random.uniform(0.7, 1.3),
        'energy_consumption_intensity': bench['energy'] * np.random.uniform(0.7, 1.3),
        'renewable_energy_percentage': np.random.uniform(15, 60),
        'water_consumption_intensity': bench['water'] * np.random.uniform(0.7, 1.3),
        'waste_recycling_rate': np.random.uniform(50, 90),
        'environmental_compliance': np.random.uniform(85, 100),
        'climate_risk_disclosure': np.random.uniform(40, 90),
        
        # Benchmarks
        'benchmark_carbon': bench['carbon'],
        'benchmark_energy': bench['energy'],
        'benchmark_water': bench['water'],
        'benchmark_ltifr': 0.5,
        
        # Social
        'ltifr': np.random.uniform(0.2, 1.0),
        'employee_turnover_rate': np.random.uniform(8, 25),
        'women_workforce_percentage': np.random.uniform(15, 40),
        'training_hours_per_employee': np.random.uniform(15, 50),
        'csr_spending_percentage': np.random.uniform(1.5, 3.0),
        'human_rights_compliance': np.random.uniform(85, 100),
        'customer_complaints_resolved': np.random.uniform(85, 99),
        
        # Governance
        'independent_directors_percentage': np.random.uniform(45, 70),
        'women_directors_percentage': np.random.uniform(15, 35),
        'audit_committee_meetings': np.random.randint(4, 8),
        'ceo_median_pay_ratio': np.random.uniform(50, 200),
        'ethics_anti_corruption': np.random.uniform(80, 100),
        'risk_management': np.random.uniform(60, 95),
        
        # Other
        'controversy_score': np.random.uniform(0, 30)
    }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_gauge_chart(score: float, title: str, height: int = 250) -> go.Figure:
    """Create a gauge chart for ESG score"""
    
    # Determine color based on score
    if score >= 80:
        color = "#27ae60"
    elif score >= 65:
        color = "#2ecc71"
    elif score >= 50:
        color = "#f39c12"
    elif score >= 35:
        color = "#e74c3c"
    else:
        color = "#c0392b"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        delta={'reference': 50, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 35], 'color': 'rgba(192, 57, 43, 0.3)'},
                {'range': [35, 50], 'color': 'rgba(231, 76, 60, 0.3)'},
                {'range': [50, 65], 'color': 'rgba(243, 156, 18, 0.3)'},
                {'range': [65, 80], 'color': 'rgba(46, 204, 113, 0.3)'},
                {'range': [80, 100], 'color': 'rgba(39, 174, 96, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': "Arial"}
    )
    
    return fig


def create_radar_chart(env_score: float, social_score: float, gov_score: float, 
                       company_name: str) -> go.Figure:
    """Create radar chart for E, S, G scores"""
    
    categories = ['Environmental', 'Social', 'Governance', 'Environmental']
    values = [env_score, social_score, gov_score, env_score]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(30, 132, 73, 0.3)',
        line=dict(color='#1e8449', width=2),
        name=company_name
    ))
    
    # Add benchmark line
    benchmark = [50, 50, 50, 50]
    fig.add_trace(go.Scatterpolar(
        r=benchmark,
        theta=categories,
        fill='toself',
        fillcolor='rgba(243, 156, 18, 0.1)',
        line=dict(color='#f39c12', width=2, dash='dash'),
        name='Benchmark'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title=f"ESG Profile - {company_name}",
        height=400,
        margin=dict(l=60, r=60, t=60, b=60)
    )
    
    return fig


def create_metrics_bar_chart(metrics: Dict, category: str) -> go.Figure:
    """Create bar chart for individual metrics"""
    
    names = list(metrics.keys())
    scores = [m['score'] for m in metrics.values()]
    
    colors = ['#27ae60' if s >= 70 else '#f39c12' if s >= 50 else '#e74c3c' for s in scores]
    
    fig = go.Figure(go.Bar(
        y=names,
        x=scores,
        orientation='h',
        marker_color=colors,
        text=[f'{s:.1f}' for s in scores],
        textposition='outside'
    ))
    
    fig.add_vline(x=50, line_dash="dash", line_color="gray", 
                  annotation_text="Threshold", annotation_position="top")
    fig.add_vline(x=70, line_dash="dash", line_color="green", 
                  annotation_text="Good", annotation_position="top")
    
    fig.update_layout(
        title=f"{category} Metrics Scores",
        xaxis_title="Score",
        yaxis_title="",
        xaxis=dict(range=[0, 110]),
        height=50 + len(names) * 40,
        margin=dict(l=200, r=50, t=50, b=50)
    )
    
    return fig


def create_comparison_chart(comparison_df: pd.DataFrame) -> go.Figure:
    """Create company comparison chart"""
    
    fig = go.Figure()
    
    x = comparison_df['Company']
    
    fig.add_trace(go.Bar(
        name='Environmental',
        x=x,
        y=comparison_df['Environmental'],
        marker_color='#27ae60'
    ))
    
    fig.add_trace(go.Bar(
        name='Social',
        x=x,
        y=comparison_df['Social'],
        marker_color='#3498db'
    ))
    
    fig.add_trace(go.Bar(
        name='Governance',
        x=x,
        y=comparison_df['Governance'],
        marker_color='#9b59b6'
    ))
    
    fig.add_trace(go.Scatter(
        name='Overall ESG',
        x=x,
        y=comparison_df['Overall ESG'],
        mode='lines+markers',
        line=dict(color='#e74c3c', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="Company ESG Score Comparison",
        barmode='group',
        xaxis_title="Company",
        yaxis_title="Score",
        yaxis=dict(range=[0, 100]),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_heatmap(comparison_df: pd.DataFrame) -> go.Figure:
    """Create ESG heatmap for multiple companies"""
    
    df = comparison_df[['Company', 'Environmental', 'Social', 'Governance', 'Overall ESG']]
    df = df.set_index('Company')
    
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns,
        y=df.index,
        colorscale=[
            [0, '#c0392b'],
            [0.35, '#e74c3c'],
            [0.5, '#f39c12'],
            [0.65, '#2ecc71'],
            [1, '#27ae60']
        ],
        text=np.round(df.values, 1),
        texttemplate="%{text}",
        textfont={"size": 12},
        colorbar=dict(title="Score")
    ))
    
    fig.update_layout(
        title="ESG Score Heatmap",
        height=100 + len(df) * 40,
        xaxis_title="Category",
        yaxis_title="Company"
    )
    
    return fig


def create_trend_chart(scores_history: List[Dict]) -> go.Figure:
    """Create ESG score trend chart"""
    
    df = pd.DataFrame(scores_history)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['environmental'],
        name='Environmental',
        line=dict(color='#27ae60', width=2),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['social'],
        name='Social',
        line=dict(color='#3498db', width=2),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['governance'],
        name='Governance',
        line=dict(color='#9b59b6', width=2),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['overall'],
        name='Overall ESG',
        line=dict(color='#e74c3c', width=3),
        mode='lines+markers'
    ))
    
    fig.update_layout(
        title="ESG Score Trend",
        xaxis_title="Date",
        yaxis_title="Score",
        yaxis=dict(range=[0, 100]),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig


# ============================================================================
# SAMPLE COMPANY DATA
# ============================================================================

SAMPLE_COMPANIES = {
    'RELIANCE': {'name': 'Reliance Industries Ltd', 'industry': 'Oil & Gas', 'sector': 'Energy'},
    'TCS': {'name': 'Tata Consultancy Services', 'industry': 'IT Services', 'sector': 'Technology'},
    'HDFCBANK': {'name': 'HDFC Bank Ltd', 'industry': 'Banking', 'sector': 'Financial Services'},
    'INFY': {'name': 'Infosys Ltd', 'industry': 'IT Services', 'sector': 'Technology'},
    'ICICIBANK': {'name': 'ICICI Bank Ltd', 'industry': 'Banking', 'sector': 'Financial Services'},
    'HINDUNILVR': {'name': 'Hindustan Unilever Ltd', 'industry': 'FMCG', 'sector': 'Consumer Goods'},
    'ITC': {'name': 'ITC Ltd', 'industry': 'FMCG', 'sector': 'Consumer Goods'},
    'SBIN': {'name': 'State Bank of India', 'industry': 'Banking', 'sector': 'Financial Services'},
    'BHARTIARTL': {'name': 'Bharti Airtel Ltd', 'industry': 'Telecom', 'sector': 'Communication'},
    'KOTAKBANK': {'name': 'Kotak Mahindra Bank', 'industry': 'Banking', 'sector': 'Financial Services'},
    'WIPRO': {'name': 'Wipro Ltd', 'industry': 'IT Services', 'sector': 'Technology'},
    'TATASTEEL': {'name': 'Tata Steel Ltd', 'industry': 'Steel', 'sector': 'Materials'},
    'MARUTI': {'name': 'Maruti Suzuki India', 'industry': 'Automobiles', 'sector': 'Auto'},
    'NTPC': {'name': 'NTPC Ltd', 'industry': 'Power', 'sector': 'Utilities'},
    'POWERGRID': {'name': 'Power Grid Corp', 'industry': 'Power', 'sector': 'Utilities'}
}


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #1e8449, #27ae60); 
                border-radius: 15px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0;'>🌿 NYZTrade ESG Dashboard</h1>
        <p style='color: white; margin: 10px 0 0 0;'>
            Sustainability Score Calculator for Indian Listed Companies
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 🎛️ Control Panel")
    
    # Analysis Mode Selection
    analysis_mode = st.sidebar.radio(
        "Select Analysis Mode",
        ["Single Company", "Multi-Company Comparison", "Custom Data Input"]
    )
    
    # ========================================================================
    # SINGLE COMPANY ANALYSIS
    # ========================================================================
    if analysis_mode == "Single Company":
        st.sidebar.markdown("### 📊 Company Selection")
        
        symbol = st.sidebar.selectbox(
            "Select Company",
            list(SAMPLE_COMPANIES.keys()),
            format_func=lambda x: f"{x} - {SAMPLE_COMPANIES[x]['name']}"
        )
        
        company_info = SAMPLE_COMPANIES[symbol]
        
        # Generate ESG data
        esg_data = generate_sample_data(company_info['industry'])
        
        # Calculate scores
        env_score, env_metrics = calculate_environmental_score(esg_data)
        social_score, social_metrics = calculate_social_score(esg_data)
        gov_score, gov_metrics = calculate_governance_score(esg_data)
        
        # Calculate overall score
        overall_score = (
            env_score * CATEGORY_WEIGHTS['Environmental'] +
            social_score * CATEGORY_WEIGHTS['Social'] +
            gov_score * CATEGORY_WEIGHTS['Governance']
        )
        
        risk_level = get_risk_level(overall_score)
        risk_color = get_risk_color(risk_level)
        
        # Company Header
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #34495e, #2c3e50); padding: 20px; 
                    border-radius: 15px; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0;'>{company_info['name']}</h2>
            <p style='color: #bdc3c7; margin: 5px 0;'>
                {symbol} | {company_info['sector']} | {company_info['industry']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Score Cards Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🌍 Environmental",
                value=f"{env_score:.1f}",
                delta=f"{env_score - 50:.1f} vs benchmark"
            )
        
        with col2:
            st.metric(
                label="👥 Social",
                value=f"{social_score:.1f}",
                delta=f"{social_score - 50:.1f} vs benchmark"
            )
        
        with col3:
            st.metric(
                label="🏛️ Governance",
                value=f"{gov_score:.1f}",
                delta=f"{gov_score - 50:.1f} vs benchmark"
            )
        
        with col4:
            st.metric(
                label="📊 Overall ESG",
                value=f"{overall_score:.1f}",
                delta=f"Risk: {risk_level}"
            )
        
        # Gauge Charts
        st.markdown("### 📈 ESG Score Gauges")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            fig = create_gauge_chart(env_score, "Environmental")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_gauge_chart(social_score, "Social")
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            fig = create_gauge_chart(gov_score, "Governance")
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            fig = create_gauge_chart(overall_score, "Overall ESG")
            st.plotly_chart(fig, use_container_width=True)
        
        # Radar Chart
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🎯 ESG Profile")
            fig = create_radar_chart(env_score, social_score, gov_score, symbol)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📋 Risk Assessment")
            st.markdown(f"""
            <div style='background-color: {risk_color}; color: white; padding: 30px; 
                        border-radius: 15px; text-align: center;'>
                <h2 style='margin: 0;'>ESG Risk Level</h2>
                <h1 style='margin: 10px 0; font-size: 3em;'>{risk_level}</h1>
                <p style='margin: 0;'>Overall Score: {overall_score:.1f}/100</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Controversy Score
            controversy = esg_data.get('controversy_score', 0)
            st.markdown(f"""
            <div style='background-color: #34495e; padding: 20px; border-radius: 10px;'>
                <h4 style='color: white; margin: 0;'>⚠️ Controversy Score</h4>
                <h2 style='color: {'#e74c3c' if controversy > 20 else '#f39c12' if controversy > 10 else '#27ae60'}; 
                          margin: 10px 0;'>{controversy:.1f}/100</h2>
                <p style='color: #bdc3c7; margin: 0;'>Based on media & regulatory incidents</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed Metrics
        st.markdown("---")
        st.markdown("### 📊 Detailed Metrics Analysis")
        
        tab1, tab2, tab3 = st.tabs(["🌍 Environmental", "👥 Social", "🏛️ Governance"])
        
        with tab1:
            fig = create_metrics_bar_chart(env_metrics, "Environmental")
            st.plotly_chart(fig, use_container_width=True)
            
            # Metrics table
            env_df = pd.DataFrame([
                {
                    'Metric': name,
                    'Value': f"{m['value']:.2f} {m['unit']}",
                    'Score': f"{m['score']:.1f}",
                    'Weight': f"{m['weight']*100:.0f}%",
                    'Status': '🟢' if m['score'] >= 70 else '🟡' if m['score'] >= 50 else '🔴'
                }
                for name, m in env_metrics.items()
            ])
            st.dataframe(env_df, use_container_width=True)
        
        with tab2:
            fig = create_metrics_bar_chart(social_metrics, "Social")
            st.plotly_chart(fig, use_container_width=True)
            
            social_df = pd.DataFrame([
                {
                    'Metric': name,
                    'Value': f"{m['value']:.2f} {m['unit']}",
                    'Score': f"{m['score']:.1f}",
                    'Weight': f"{m['weight']*100:.0f}%",
                    'Status': '🟢' if m['score'] >= 70 else '🟡' if m['score'] >= 50 else '🔴'
                }
                for name, m in social_metrics.items()
            ])
            st.dataframe(social_df, use_container_width=True)
        
        with tab3:
            fig = create_metrics_bar_chart(gov_metrics, "Governance")
            st.plotly_chart(fig, use_container_width=True)
            
            gov_df = pd.DataFrame([
                {
                    'Metric': name,
                    'Value': f"{m['value']:.2f} {m['unit']}",
                    'Score': f"{m['score']:.1f}",
                    'Weight': f"{m['weight']*100:.0f}%",
                    'Status': '🟢' if m['score'] >= 70 else '🟡' if m['score'] >= 50 else '🔴'
                }
                for name, m in gov_metrics.items()
            ])
            st.dataframe(gov_df, use_container_width=True)
    
    # ========================================================================
    # MULTI-COMPANY COMPARISON
    # ========================================================================
    elif analysis_mode == "Multi-Company Comparison":
        st.sidebar.markdown("### 📊 Company Selection")
        
        selected_companies = st.sidebar.multiselect(
            "Select Companies to Compare",
            list(SAMPLE_COMPANIES.keys()),
            default=['TCS', 'INFY', 'WIPRO', 'HDFCBANK', 'RELIANCE'],
            format_func=lambda x: f"{x} - {SAMPLE_COMPANIES[x]['name']}"
        )
        
        if len(selected_companies) < 2:
            st.warning("Please select at least 2 companies for comparison.")
            return
        
        # Calculate scores for all companies
        comparison_data = []
        
        for symbol in selected_companies:
            company_info = SAMPLE_COMPANIES[symbol]
            esg_data = generate_sample_data(company_info['industry'])
            
            env_score, _ = calculate_environmental_score(esg_data)
            social_score, _ = calculate_social_score(esg_data)
            gov_score, _ = calculate_governance_score(esg_data)
            
            overall_score = (
                env_score * CATEGORY_WEIGHTS['Environmental'] +
                social_score * CATEGORY_WEIGHTS['Social'] +
                gov_score * CATEGORY_WEIGHTS['Governance']
            )
            
            comparison_data.append({
                'Symbol': symbol,
                'Company': company_info['name'][:20] + '...' if len(company_info['name']) > 20 else company_info['name'],
                'Industry': company_info['industry'],
                'Environmental': round(env_score, 1),
                'Social': round(social_score, 1),
                'Governance': round(gov_score, 1),
                'Overall ESG': round(overall_score, 1),
                'Risk Level': get_risk_level(overall_score)
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.sort_values('Overall ESG', ascending=False)
        
        st.markdown("### 📊 Multi-Company ESG Comparison")
        
        # Comparison Bar Chart
        fig = create_comparison_chart(comparison_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = create_heatmap(comparison_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🏆 ESG Leaders")
            for i, row in comparison_df.head(5).iterrows():
                color = get_risk_color(row['Risk Level'])
                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 10px; margin: 5px 0; 
                            border-radius: 10px; border-left: 5px solid {color};'>
                    <strong>{row['Symbol']}</strong>: {row['Overall ESG']:.1f}
                    <span style='float: right; color: {color};'>{row['Risk Level']}</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Detailed Comparison Table
        st.markdown("### 📋 Detailed Comparison")
        
        styled_df = comparison_df.style.background_gradient(
            subset=['Environmental', 'Social', 'Governance', 'Overall ESG'],
            cmap='RdYlGn',
            vmin=0,
            vmax=100
        )
        st.dataframe(styled_df, use_container_width=True)
        
        # Download option
        csv = comparison_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Comparison Data",
            data=csv,
            file_name=f"esg_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # ========================================================================
    # CUSTOM DATA INPUT
    # ========================================================================
    elif analysis_mode == "Custom Data Input":
        st.markdown("### 📝 Custom ESG Data Input")
        st.markdown("Enter your company's ESG metrics to calculate sustainability score.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name", "My Company")
            industry = st.selectbox("Industry", list(INDUSTRY_ADJUSTMENTS.keys())[:-1])
        
        with col2:
            symbol = st.text_input("Symbol", "MYCO")
            sector = st.text_input("Sector", "Default")
        
        st.markdown("---")
        
        # Environmental Metrics Input
        st.markdown("#### 🌍 Environmental Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            carbon = st.number_input("Carbon Emissions Intensity (tCO2e/Cr)", 0.0, 500.0, 50.0)
            renewable = st.number_input("Renewable Energy %", 0.0, 100.0, 25.0)
        
        with col2:
            energy = st.number_input("Energy Consumption (GJ/Cr)", 0.0, 1000.0, 200.0)
            waste = st.number_input("Waste Recycling Rate %", 0.0, 100.0, 65.0)
        
        with col3:
            water = st.number_input("Water Consumption (KL/Cr)", 0.0, 5000.0, 300.0)
            env_compliance = st.number_input("Environmental Compliance %", 0.0, 100.0, 95.0)
        
        # Social Metrics Input
        st.markdown("#### 👥 Social Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ltifr = st.number_input("LTIFR", 0.0, 5.0, 0.5)
            women_workforce = st.number_input("Women Workforce %", 0.0, 100.0, 25.0)
        
        with col2:
            turnover = st.number_input("Employee Turnover %", 0.0, 100.0, 15.0)
            training = st.number_input("Training Hours/Employee", 0.0, 100.0, 20.0)
        
        with col3:
            csr = st.number_input("CSR Spending % of Profit", 0.0, 10.0, 2.0)
            customer = st.number_input("Customer Complaints Resolved %", 0.0, 100.0, 95.0)
        
        # Governance Metrics Input
        st.markdown("#### 🏛️ Governance Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            independent = st.number_input("Independent Directors %", 0.0, 100.0, 50.0)
            ethics = st.number_input("Ethics Compliance %", 0.0, 100.0, 90.0)
        
        with col2:
            women_board = st.number_input("Women on Board %", 0.0, 100.0, 17.0)
            risk_mgmt = st.number_input("Risk Management Score", 0.0, 100.0, 80.0)
        
        with col3:
            audit = st.number_input("Audit Committee Meetings", 1, 12, 4)
            ceo_ratio = st.number_input("CEO Pay Ratio (x median)", 1.0, 500.0, 100.0)
        
        if st.button("🔄 Calculate ESG Score", type="primary"):
            # Prepare custom data
            custom_data = {
                'carbon_emissions_intensity': carbon,
                'energy_consumption_intensity': energy,
                'renewable_energy_percentage': renewable,
                'water_consumption_intensity': water,
                'waste_recycling_rate': waste,
                'environmental_compliance': env_compliance,
                'climate_risk_disclosure': 60,
                'benchmark_carbon': 50,
                'benchmark_energy': 200,
                'benchmark_water': 300,
                'benchmark_ltifr': 0.5,
                'ltifr': ltifr,
                'employee_turnover_rate': turnover,
                'women_workforce_percentage': women_workforce,
                'training_hours_per_employee': training,
                'csr_spending_percentage': csr,
                'human_rights_compliance': 90,
                'customer_complaints_resolved': customer,
                'independent_directors_percentage': independent,
                'women_directors_percentage': women_board,
                'audit_committee_meetings': audit,
                'ceo_median_pay_ratio': ceo_ratio,
                'ethics_anti_corruption': ethics,
                'risk_management': risk_mgmt,
                'controversy_score': 10
            }
            
            # Calculate scores
            env_score, env_metrics = calculate_environmental_score(custom_data)
            social_score, social_metrics = calculate_social_score(custom_data)
            gov_score, gov_metrics = calculate_governance_score(custom_data)
            
            # Apply industry adjustments
            adj = INDUSTRY_ADJUSTMENTS.get(industry, INDUSTRY_ADJUSTMENTS['Default'])
            
            overall_score = (
                env_score * CATEGORY_WEIGHTS['Environmental'] +
                social_score * CATEGORY_WEIGHTS['Social'] +
                gov_score * CATEGORY_WEIGHTS['Governance']
            )
            
            risk_level = get_risk_level(overall_score)
            risk_color = get_risk_color(risk_level)
            
            st.markdown("---")
            st.markdown("### 📊 Your ESG Score Results")
            
            # Score Cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🌍 Environmental", f"{env_score:.1f}")
            with col2:
                st.metric("👥 Social", f"{social_score:.1f}")
            with col3:
                st.metric("🏛️ Governance", f"{gov_score:.1f}")
            with col4:
                st.metric("📊 Overall ESG", f"{overall_score:.1f}")
            
            # Gauges
            col1, col2 = st.columns(2)
            
            with col1:
                fig = create_gauge_chart(overall_score, "Overall ESG Score", 300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = create_radar_chart(env_score, social_score, gov_score, company_name)
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"""
            <div style='background-color: {risk_color}; color: white; padding: 20px; 
                        border-radius: 10px; text-align: center;'>
                <h3>ESG Risk Level: {risk_level}</h3>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: #7f8c8d;'>
        <p>🌿 <strong>NYZTrade ESG Dashboard</strong> | Powered by BRSR Framework</p>
        <p style='font-size: 0.8em;'>
            ⚠️ This is a demonstration tool. Actual ESG assessments should be based on verified BRSR disclosures.
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
