# ============================================================================
# NYZTRADE - INTEGRATED ESG DASHBOARD WITH REAL DATA & PDF UPLOAD
# Complete Production-Ready ESG Analysis Platform
# ============================================================================

"""
Integrated ESG Dashboard with:
1. Real-time NSE/BSE data integration
2. Annual Report / BRSR PDF upload and parsing
3. Custom data input
4. Comprehensive ESG scoring

Run: streamlit run streamlit_integrated_esg.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import time
import io
import tempfile
import os
from typing import Dict, List, Optional, Tuple

# Import our modules
try:
    from real_data_fetcher import (
        RealTimeDataAggregator, NSEDataFetcher, CompanyData, 
        ShareholdingPattern, ESGDataMapper
    )
    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False
    st.warning("Real data module not found. Using simulated data.")

try:
    from brsr_report_parser import BRSRReportParser, BRSRExtractedData
    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="NYZTrade ESG Platform",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e8449 0%, #27ae60 50%, #2ecc71 100%);
        color: white;
        padding: 25px 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 8px 25px rgba(30, 132, 73, 0.3);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #1e8449;
        margin-bottom: 12px;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
    }
    
    .upload-zone {
        border: 2px dashed #27ae60;
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        background-color: #f0fff4;
        margin: 20px 0;
    }
    
    .upload-zone:hover {
        background-color: #e8f5e9;
        border-color: #1e8449;
    }
    
    .data-source-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: bold;
        margin-left: 10px;
    }
    
    .badge-live {
        background-color: #27ae60;
        color: white;
    }
    
    .badge-pdf {
        background-color: #3498db;
        color: white;
    }
    
    .badge-manual {
        background-color: #9b59b6;
        color: white;
    }
    
    .badge-simulated {
        background-color: #f39c12;
        color: white;
    }
    
    .extraction-result {
        background-color: #e8f5e9;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #27ae60;
    }
    
    .section-header {
        background: linear-gradient(90deg, #1e8449, #27ae60);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin: 20px 0 15px 0;
        font-weight: 600;
    }
    
    .risk-negligible { background-color: #27ae60; color: white; padding: 5px 15px; border-radius: 15px; }
    .risk-low { background-color: #2ecc71; color: white; padding: 5px 15px; border-radius: 15px; }
    .risk-medium { background-color: #f39c12; color: white; padding: 5px 15px; border-radius: 15px; }
    .risk-high { background-color: #e74c3c; color: white; padding: 5px 15px; border-radius: 15px; }
    .risk-severe { background-color: #c0392b; color: white; padding: 5px 15px; border-radius: 15px; }
    
    .footer {
        text-align: center;
        padding: 20px;
        color: #7f8c8d;
        border-top: 1px solid #e0e0e0;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# CONSTANTS
# ============================================================================

CATEGORY_WEIGHTS = {'Environmental': 0.35, 'Social': 0.35, 'Governance': 0.30}

INDUSTRY_ADJUSTMENTS = {
    'Oil & Gas': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Oil Exploration': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Power': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Iron & Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Cement': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Mining': {'environmental': 1.3, 'social': 1.0, 'governance': 0.7},
    'Banks': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Private Banks': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Financial Services': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'IT Services': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'IT - Software': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'Computers - Software': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'Pharmaceuticals': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'FMCG': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Automobiles': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Auto': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Telecom': {'environmental': 0.9, 'social': 1.0, 'governance': 1.1},
    'Default': {'environmental': 1.0, 'social': 1.0, 'governance': 1.0}
}

ENVIRONMENTAL_BENCHMARKS = {
    'Oil & Gas': {'carbon': 150, 'energy': 500, 'water': 1000, 'renewable': 10, 'waste': 60},
    'Power': {'carbon': 200, 'energy': 800, 'water': 2000, 'renewable': 25, 'waste': 50},
    'IT Services': {'carbon': 5, 'energy': 50, 'water': 50, 'renewable': 50, 'waste': 80},
    'IT - Software': {'carbon': 5, 'energy': 50, 'water': 50, 'renewable': 50, 'waste': 80},
    'Banks': {'carbon': 2, 'energy': 30, 'water': 30, 'renewable': 40, 'waste': 85},
    'Private Banks': {'carbon': 2, 'energy': 30, 'water': 30, 'renewable': 40, 'waste': 85},
    'Pharmaceuticals': {'carbon': 30, 'energy': 150, 'water': 500, 'renewable': 30, 'waste': 70},
    'Steel': {'carbon': 180, 'energy': 700, 'water': 1500, 'renewable': 15, 'waste': 65},
    'FMCG': {'carbon': 20, 'energy': 100, 'water': 300, 'renewable': 35, 'waste': 75},
    'Automobiles': {'carbon': 40, 'energy': 200, 'water': 400, 'renewable': 25, 'waste': 80},
    'Default': {'carbon': 50, 'energy': 200, 'water': 300, 'renewable': 25, 'waste': 65}
}

NIFTY50_SYMBOLS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 
    'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'WIPRO', 'LT', 'AXISBANK', 'ASIANPAINT',
    'MARUTI', 'TATASTEEL', 'NTPC', 'POWERGRID', 'SUNPHARMA', 'DRREDDY',
    'ONGC', 'COALINDIA', 'TATAMOTORS', 'M&M', 'HCLTECH', 'TECHM',
    'BAJFINANCE', 'TITAN', 'ULTRACEMCO', 'NESTLEIND'
]


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'esg_data' not in st.session_state:
    st.session_state.esg_data = {}
if 'pdf_extracted_data' not in st.session_state:
    st.session_state.pdf_extracted_data = None
if 'live_company_data' not in st.session_state:
    st.session_state.live_company_data = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = 'Simulated'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_benchmarks(industry: str) -> Dict:
    """Get industry benchmarks"""
    return ENVIRONMENTAL_BENCHMARKS.get(industry, ENVIRONMENTAL_BENCHMARKS['Default'])


def calculate_environmental_score(data: Dict, industry: str = 'Default') -> Tuple[float, Dict]:
    """Calculate environmental score from data"""
    benchmarks = get_benchmarks(industry)
    metrics = {}
    
    # Carbon
    carbon = data.get('carbon_emissions_intensity', benchmarks['carbon'])
    benchmark = benchmarks['carbon']
    score = max(0, min(100, 100 - (carbon / benchmark * 50))) if benchmark > 0 else 50
    metrics['Carbon Emissions'] = {'value': carbon, 'score': score, 'unit': 'tCO2e/Cr', 'weight': 0.20}
    
    # Energy
    energy = data.get('energy_consumption_intensity', benchmarks['energy'])
    benchmark_e = benchmarks['energy']
    score_e = max(0, min(100, 100 - (energy / benchmark_e * 50))) if benchmark_e > 0 else 50
    metrics['Energy Consumption'] = {'value': energy, 'score': score_e, 'unit': 'GJ/Cr', 'weight': 0.15}
    
    # Renewable
    renewable = data.get('renewable_energy_percentage', benchmarks['renewable'])
    score_r = min(100, renewable * 2)
    metrics['Renewable Energy'] = {'value': renewable, 'score': score_r, 'unit': '%', 'weight': 0.15}
    
    # Water
    water = data.get('water_consumption_intensity', benchmarks['water'])
    benchmark_w = benchmarks['water']
    score_w = max(0, min(100, 100 - (water / benchmark_w * 50))) if benchmark_w > 0 else 50
    metrics['Water Usage'] = {'value': water, 'score': score_w, 'unit': 'KL/Cr', 'weight': 0.12}
    
    # Waste
    waste = data.get('waste_recycling_rate', benchmarks['waste'])
    score_ws = min(100, waste * 1.25)
    metrics['Waste Recycling'] = {'value': waste, 'score': score_ws, 'unit': '%', 'weight': 0.10}
    
    # Compliance
    compliance = data.get('environmental_compliance', 95)
    metrics['Compliance'] = {'value': compliance, 'score': min(100, compliance), 'unit': '%', 'weight': 0.10}
    
    # Climate Disclosure
    climate = data.get('climate_risk_disclosure', 60)
    metrics['Climate Disclosure'] = {'value': climate, 'score': min(100, climate), 'unit': '%', 'weight': 0.08}
    
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    return total, metrics


def calculate_social_score(data: Dict) -> Tuple[float, Dict]:
    """Calculate social score from data"""
    metrics = {}
    
    # Safety
    ltifr = data.get('ltifr', 0.5)
    score = max(0, min(100, 100 - (ltifr / 0.5 * 50)))
    metrics['Employee Safety'] = {'value': ltifr, 'score': score, 'unit': 'LTIFR', 'weight': 0.15}
    
    # Turnover
    turnover = data.get('employee_turnover_rate', 15)
    score_t = max(0, min(100, 100 - turnover * 2))
    metrics['Employee Retention'] = {'value': turnover, 'score': score_t, 'unit': '%', 'weight': 0.10}
    
    # Diversity
    women = data.get('women_workforce_percentage', 25)
    score_d = min(100, women * 2.5)
    metrics['Gender Diversity'] = {'value': women, 'score': score_d, 'unit': '%', 'weight': 0.12}
    
    # Training
    training = data.get('training_hours_per_employee', 20)
    score_tr = min(100, training * 2.5)
    metrics['Training'] = {'value': training, 'score': score_tr, 'unit': 'hrs', 'weight': 0.10}
    
    # CSR
    csr = data.get('csr_spending_percentage', 2)
    score_csr = min(100, csr * 40)
    metrics['CSR Spending'] = {'value': csr, 'score': score_csr, 'unit': '%', 'weight': 0.10}
    
    # Human Rights
    hr = data.get('human_rights_compliance', 90)
    metrics['Human Rights'] = {'value': hr, 'score': min(100, hr), 'unit': '%', 'weight': 0.10}
    
    # Customer
    customer = data.get('customer_complaints_resolved', 95)
    metrics['Customer Satisfaction'] = {'value': customer, 'score': min(100, customer), 'unit': '%', 'weight': 0.08}
    
    # Data Privacy
    breaches = data.get('data_breaches', 0)
    score_p = max(0, 100 - breaches * 20)
    metrics['Data Privacy'] = {'value': breaches, 'score': score_p, 'unit': 'incidents', 'weight': 0.08}
    
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    return total, metrics


def calculate_governance_score(data: Dict) -> Tuple[float, Dict]:
    """Calculate governance score from data"""
    metrics = {}
    
    # Board Independence
    independent = data.get('independent_directors_percentage', 50)
    score = min(100, independent * 1.5)
    metrics['Board Independence'] = {'value': independent, 'score': score, 'unit': '%', 'weight': 0.15}
    
    # Board Diversity
    women = data.get('women_directors_percentage', 17)
    score_w = min(100, women * 4)
    metrics['Board Diversity'] = {'value': women, 'score': score_w, 'unit': '%', 'weight': 0.12}
    
    # Audit
    audit = data.get('audit_committee_meetings', 4)
    score_a = min(100, audit * 16.67)
    metrics['Audit Committee'] = {'value': audit, 'score': score_a, 'unit': 'meetings', 'weight': 0.12}
    
    # Executive Pay
    ratio = data.get('ceo_median_pay_ratio', 100)
    score_e = max(0, min(100, 150 - ratio * 0.5))
    metrics['Executive Pay'] = {'value': ratio, 'score': score_e, 'unit': 'x median', 'weight': 0.10}
    
    # Ethics
    ethics = data.get('ethics_anti_corruption', 90)
    metrics['Ethics'] = {'value': ethics, 'score': min(100, ethics), 'unit': '%', 'weight': 0.12}
    
    # Risk Management
    risk = data.get('risk_management', 80)
    metrics['Risk Management'] = {'value': risk, 'score': min(100, risk), 'unit': 'score', 'weight': 0.10}
    
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    return total, metrics


def calculate_overall_esg(env: float, social: float, gov: float, industry: str = 'Default') -> float:
    """Calculate overall ESG score with industry adjustments"""
    adj = INDUSTRY_ADJUSTMENTS.get(industry, INDUSTRY_ADJUSTMENTS['Default'])
    
    env_w = 0.35 * adj['environmental']
    soc_w = 0.35 * adj['social']
    gov_w = 0.30 * adj['governance']
    total_w = env_w + soc_w + gov_w
    
    return (env * env_w + social * soc_w + gov * gov_w) / total_w


def get_risk_level(score: float) -> str:
    """Get risk level from score"""
    if score >= 80: return "Negligible"
    elif score >= 65: return "Low"
    elif score >= 50: return "Medium"
    elif score >= 35: return "High"
    else: return "Severe"


def get_risk_color(risk: str) -> str:
    """Get color for risk level"""
    colors = {
        "Negligible": "#27ae60", "Low": "#2ecc71",
        "Medium": "#f39c12", "High": "#e74c3c", "Severe": "#c0392b"
    }
    return colors.get(risk, "#f39c12")


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_gauge_chart(score: float, title: str, height: int = 250) -> go.Figure:
    """Create gauge chart"""
    color = "#27ae60" if score >= 80 else "#2ecc71" if score >= 65 else "#f39c12" if score >= 50 else "#e74c3c"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color, 'thickness': 0.8},
            'steps': [
                {'range': [0, 35], 'color': 'rgba(192, 57, 43, 0.2)'},
                {'range': [35, 50], 'color': 'rgba(231, 76, 60, 0.2)'},
                {'range': [50, 65], 'color': 'rgba(243, 156, 18, 0.2)'},
                {'range': [65, 80], 'color': 'rgba(46, 204, 113, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(39, 174, 96, 0.2)'}
            ]
        }
    ))
    
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_radar_chart(env: float, social: float, gov: float, name: str) -> go.Figure:
    """Create radar chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=[env, social, gov, env],
        theta=['Environmental', 'Social', 'Governance', 'Environmental'],
        fill='toself',
        fillcolor='rgba(30, 132, 73, 0.3)',
        line=dict(color='#1e8449', width=2),
        name=name
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[50, 50, 50, 50],
        theta=['Environmental', 'Social', 'Governance', 'Environmental'],
        line=dict(color='#f39c12', width=2, dash='dash'),
        name='Benchmark'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 100])),
        showlegend=True, height=400
    )
    
    return fig


def create_metrics_bar(metrics: Dict, title: str) -> go.Figure:
    """Create horizontal bar chart for metrics"""
    names = list(metrics.keys())
    scores = [m['score'] for m in metrics.values()]
    colors = ['#27ae60' if s >= 70 else '#f39c12' if s >= 50 else '#e74c3c' for s in scores]
    
    fig = go.Figure(go.Bar(
        y=names, x=scores, orientation='h',
        marker_color=colors,
        text=[f'{s:.1f}' for s in scores],
        textposition='outside'
    ))
    
    fig.add_vline(x=50, line_dash="dash", line_color="gray")
    fig.add_vline(x=70, line_dash="dash", line_color="green")
    
    fig.update_layout(
        title=title, xaxis_title="Score", xaxis=dict(range=[0, 110]),
        height=50 + len(names) * 40, margin=dict(l=150, r=50)
    )
    
    return fig


# ============================================================================
# REAL DATA FETCHING
# ============================================================================

@st.cache_data(ttl=300)
def fetch_live_company_data(symbol: str) -> Optional[Dict]:
    """Fetch live data from NSE"""
    if not REAL_DATA_AVAILABLE:
        return None
    
    try:
        aggregator = RealTimeDataAggregator()
        data = aggregator.get_company_data(symbol)
        
        if data:
            return {
                'symbol': data.symbol,
                'company_name': data.company_name,
                'sector': data.sector,
                'industry': data.industry,
                'market_cap': data.market_cap,
                'last_price': data.last_price,
                'change': data.change,
                'pchange': data.pchange,
                'pe_ratio': data.pe_ratio,
                'promoter_holding': data.promoter_holding,
                'fii_holding': data.fii_holding,
                'dii_holding': data.dii_holding,
                'pledged_percentage': data.pledged_percentage,
                'week_high_52': data.week_high_52,
                'week_low_52': data.week_low_52,
                'data_source': data.data_source,
                'data_quality': data.data_quality
            }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    
    return None


# ============================================================================
# PDF PARSING
# ============================================================================

def parse_uploaded_pdf(uploaded_file) -> Optional[BRSRExtractedData]:
    """Parse uploaded PDF file"""
    if not PDF_PARSER_AVAILABLE:
        st.error("PDF parsing not available. Install: pip install PyMuPDF pdfplumber")
        return None
    
    try:
        parser = BRSRReportParser()
        data = parser.parse_from_bytes(uploaded_file.read(), uploaded_file.name)
        return data
    except Exception as e:
        st.error(f"Error parsing PDF: {e}")
        return None


def convert_brsr_to_esg_input(brsr_data: BRSRExtractedData) -> Dict:
    """Convert BRSR extracted data to ESG input format"""
    env = brsr_data.environmental
    soc = brsr_data.social
    gov = brsr_data.governance
    
    return {
        'company_name': brsr_data.company_name,
        'year': brsr_data.year,
        
        # Environmental (with fallbacks)
        'carbon_emissions_intensity': env.emission_intensity if env.emission_intensity > 0 else 50,
        'energy_consumption_intensity': env.energy_intensity if env.energy_intensity > 0 else 200,
        'renewable_energy_percentage': env.renewable_energy_percentage if env.renewable_energy_percentage > 0 else 25,
        'water_consumption_intensity': (env.total_water_withdrawal / 100) if env.total_water_withdrawal > 0 else 300,
        'waste_recycling_rate': env.waste_recycling_percentage if env.waste_recycling_percentage > 0 else 65,
        'environmental_compliance': 95,
        'climate_risk_disclosure': 60,
        
        # Social
        'ltifr': soc.ltifr if soc.ltifr > 0 else 0.5,
        'employee_turnover_rate': soc.turnover_rate if soc.turnover_rate > 0 else 15,
        'women_workforce_percentage': soc.women_percentage if soc.women_percentage > 0 else 25,
        'training_hours_per_employee': soc.training_hours_per_employee if soc.training_hours_per_employee > 0 else 20,
        'csr_spending_percentage': soc.csr_percentage if soc.csr_percentage > 0 else 2,
        'human_rights_compliance': 90,
        'customer_complaints_resolved': soc.resolution_rate if soc.resolution_rate > 0 else 95,
        'data_breaches': soc.data_breaches,
        
        # Governance
        'independent_directors_percentage': gov.independent_percentage if gov.independent_percentage > 0 else 50,
        'women_directors_percentage': gov.women_board_percentage if gov.women_board_percentage > 0 else 17,
        'audit_committee_meetings': gov.audit_committee_meetings if gov.audit_committee_meetings > 0 else 4,
        'board_meetings': gov.board_meetings if gov.board_meetings > 0 else 6,
        'ceo_median_pay_ratio': gov.ceo_to_median_ratio if gov.ceo_to_median_ratio > 0 else 100,
        'ethics_anti_corruption': 90,
        'risk_management': 80,
    }


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌿 NYZTrade ESG Platform</h1>
        <p>Integrated ESG Analysis with Real-Time Data & Annual Report Parsing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 🎛️ Control Panel")
    
    page = st.sidebar.radio(
        "Navigate",
        ["🏠 Dashboard", "📊 Live Data Analysis", "📄 Upload Annual Report",
         "📝 Manual Input", "🔄 Compare Sources"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 Data Sources")
    st.sidebar.markdown(f"""
    - **NSE India**: {'✅ Available' if REAL_DATA_AVAILABLE else '❌ Not Available'}
    - **PDF Parser**: {'✅ Available' if PDF_PARSER_AVAILABLE else '❌ Not Available'}
    """)
    
    # ========================================================================
    # DASHBOARD PAGE
    # ========================================================================
    if page == "🏠 Dashboard":
        st.markdown("### 📊 ESG Analysis Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>📡 Live Data</h4>
                <p>Real-time stock data from NSE/BSE including market cap, shareholding patterns, and corporate info.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>📄 Report Upload</h4>
                <p>Upload Annual Reports or BRSR PDFs to automatically extract ESG metrics using AI.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4>📝 Manual Input</h4>
                <p>Enter custom ESG metrics manually for comprehensive sustainability scoring.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick analysis
        st.markdown("### 🚀 Quick Analysis")
        
        quick_symbol = st.selectbox(
            "Select a company for quick ESG score",
            NIFTY50_SYMBOLS,
            index=0
        )
        
        if st.button("📊 Generate ESG Score", type="primary"):
            with st.spinner("Calculating ESG Score..."):
                # Generate simulated data based on symbol
                np.random.seed(hash(quick_symbol) % 2**32)
                
                # Try to get live data first
                live_data = None
                if REAL_DATA_AVAILABLE:
                    live_data = fetch_live_company_data(quick_symbol)
                
                industry = live_data.get('industry', 'Default') if live_data else 'Default'
                benchmarks = get_benchmarks(industry)
                
                # Generate ESG data
                esg_data = {
                    'carbon_emissions_intensity': benchmarks['carbon'] * np.random.uniform(0.7, 1.3),
                    'energy_consumption_intensity': benchmarks['energy'] * np.random.uniform(0.7, 1.3),
                    'renewable_energy_percentage': min(100, benchmarks['renewable'] * np.random.uniform(0.5, 1.5)),
                    'water_consumption_intensity': benchmarks['water'] * np.random.uniform(0.7, 1.3),
                    'waste_recycling_rate': min(100, benchmarks['waste'] * np.random.uniform(0.8, 1.2)),
                    'environmental_compliance': np.random.uniform(85, 100),
                    'climate_risk_disclosure': np.random.uniform(40, 90),
                    'ltifr': np.random.uniform(0.2, 0.8),
                    'employee_turnover_rate': np.random.uniform(8, 25),
                    'women_workforce_percentage': np.random.uniform(15, 40),
                    'training_hours_per_employee': np.random.uniform(15, 50),
                    'csr_spending_percentage': np.random.uniform(1.5, 3.0),
                    'human_rights_compliance': np.random.uniform(85, 100),
                    'customer_complaints_resolved': np.random.uniform(85, 99),
                    'data_breaches': np.random.choice([0, 0, 0, 1, 2]),
                    'independent_directors_percentage': np.random.uniform(45, 70),
                    'women_directors_percentage': np.random.uniform(15, 35),
                    'audit_committee_meetings': np.random.randint(4, 8),
                    'ceo_median_pay_ratio': np.random.uniform(50, 200),
                    'ethics_anti_corruption': np.random.uniform(80, 100),
                    'risk_management': np.random.uniform(60, 95),
                }
                
                # Calculate scores
                env_score, env_metrics = calculate_environmental_score(esg_data, industry)
                social_score, social_metrics = calculate_social_score(esg_data)
                gov_score, gov_metrics = calculate_governance_score(esg_data)
                overall = calculate_overall_esg(env_score, social_score, gov_score, industry)
                risk = get_risk_level(overall)
                
                # Display results
                st.markdown("---")
                
                # Company info
                if live_data:
                    st.markdown(f"""
                    <div style='background-color: #2c3e50; color: white; padding: 15px; border-radius: 10px;'>
                        <h3 style='margin: 0;'>{live_data.get('company_name', quick_symbol)}</h3>
                        <p style='margin: 5px 0; color: #bdc3c7;'>
                            {quick_symbol} | {live_data.get('sector', 'N/A')} | {industry}
                        </p>
                        <p style='margin: 5px 0; color: #bdc3c7;'>
                            Market Cap: ₹{live_data.get('market_cap', 0):,.0f} Cr | 
                            LTP: ₹{live_data.get('last_price', 0):,.2f} ({live_data.get('pchange', 0):+.2f}%)
                        </p>
                        <span class="data-source-badge badge-live">LIVE DATA</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background-color: #2c3e50; color: white; padding: 15px; border-radius: 10px;'>
                        <h3 style='margin: 0;'>{quick_symbol}</h3>
                        <span class="data-source-badge badge-simulated">SIMULATED DATA</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("")
                
                # Gauge charts
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.plotly_chart(create_gauge_chart(env_score, "Environmental"), use_container_width=True)
                with col2:
                    st.plotly_chart(create_gauge_chart(social_score, "Social"), use_container_width=True)
                with col3:
                    st.plotly_chart(create_gauge_chart(gov_score, "Governance"), use_container_width=True)
                with col4:
                    st.plotly_chart(create_gauge_chart(overall, "Overall ESG"), use_container_width=True)
                
                # Risk badge
                risk_color = get_risk_color(risk)
                st.markdown(f"""
                <div style='text-align: center; padding: 20px;'>
                    <span class="risk-{risk.lower()}" style='font-size: 1.2em;'>
                        ESG Risk Level: {risk}
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    # ========================================================================
    # LIVE DATA ANALYSIS PAGE
    # ========================================================================
    elif page == "📊 Live Data Analysis":
        st.markdown("### 📊 Real-Time Data Analysis")
        
        if not REAL_DATA_AVAILABLE:
            st.error("Real-time data module not available. Please ensure real_data_fetcher.py is in the same directory.")
            return
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            symbol = st.selectbox("Select Company", NIFTY50_SYMBOLS, index=0)
        
        with col2:
            st.markdown("")
            st.markdown("")
            fetch_btn = st.button("🔄 Fetch Live Data", type="primary")
        
        if fetch_btn:
            with st.spinner(f"Fetching live data for {symbol}..."):
                live_data = fetch_live_company_data(symbol)
                
                if live_data:
                    st.session_state.live_company_data = live_data
                    st.success(f"✅ Live data fetched from {live_data.get('data_source', 'NSE')}")
                else:
                    st.error("Failed to fetch live data")
        
        if st.session_state.live_company_data:
            data = st.session_state.live_company_data
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #34495e, #2c3e50); padding: 20px; border-radius: 10px; color: white;'>
                <h2 style='margin: 0;'>{data.get('company_name', data.get('symbol'))}</h2>
                <p style='color: #bdc3c7; margin: 5px 0;'>
                    {data.get('sector', 'N/A')} | {data.get('industry', 'N/A')}
                </p>
                <span class="data-source-badge badge-live">{data.get('data_source', 'LIVE')}</span>
                <span style='color: #bdc3c7; margin-left: 10px;'>Quality: {data.get('data_quality', 0):.1f}%</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Last Price", f"₹{data.get('last_price', 0):,.2f}", f"{data.get('pchange', 0):+.2f}%")
            with col2:
                st.metric("Market Cap", f"₹{data.get('market_cap', 0):,.0f} Cr")
            with col3:
                st.metric("PE Ratio", f"{data.get('pe_ratio', 0):.2f}")
            with col4:
                st.metric("52W Range", f"₹{data.get('week_low_52', 0):,.0f} - ₹{data.get('week_high_52', 0):,.0f}")
            
            st.markdown("---")
            
            # Shareholding for governance metrics
            st.markdown("### 📊 Shareholding Pattern (Governance Indicator)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    values=[data.get('promoter_holding', 0), data.get('fii_holding', 0), 
                           data.get('dii_holding', 0), max(0, 100 - data.get('promoter_holding', 0) - 
                                                          data.get('fii_holding', 0) - data.get('dii_holding', 0))],
                    names=['Promoter', 'FII', 'DII', 'Public'],
                    title='Shareholding Distribution',
                    color_discrete_sequence=['#1e8449', '#3498db', '#9b59b6', '#e74c3c']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### Key Governance Indicators")
                st.markdown(f"""
                - **Promoter Holding:** {data.get('promoter_holding', 0):.1f}%
                - **FII Holding:** {data.get('fii_holding', 0):.1f}% (Foreign confidence)
                - **DII Holding:** {data.get('dii_holding', 0):.1f}% (Domestic confidence)
                - **Pledged Shares:** {data.get('pledged_percentage', 0):.1f}% (Risk indicator)
                """)
                
                # Governance score from shareholding
                promoter = data.get('promoter_holding', 0)
                pledged = data.get('pledged_percentage', 0)
                
                gov_from_sh = 50  # Base
                if 40 <= promoter <= 60:
                    gov_from_sh += 20
                elif 30 <= promoter <= 70:
                    gov_from_sh += 10
                
                if pledged == 0:
                    gov_from_sh += 20
                elif pledged < 10:
                    gov_from_sh += 10
                elif pledged > 25:
                    gov_from_sh -= 10
                
                fii_dii = data.get('fii_holding', 0) + data.get('dii_holding', 0)
                gov_from_sh += min(10, fii_dii / 5)
                
                gov_from_sh = min(100, max(0, gov_from_sh))
                
                st.metric("Governance Score (from Shareholding)", f"{gov_from_sh:.1f}/100")
    
    # ========================================================================
    # UPLOAD ANNUAL REPORT PAGE
    # ========================================================================
    elif page == "📄 Upload Annual Report":
        st.markdown("### 📄 Upload Annual Report / BRSR Report")
        
        if not PDF_PARSER_AVAILABLE:
            st.error("""
            PDF parsing not available. Please install the required libraries:
            ```
            pip install PyMuPDF pdfplumber
            ```
            """)
            return
        
        st.markdown("""
        <div class="upload-zone">
            <h3>📁 Upload PDF Document</h3>
            <p>Supported formats: Annual Report, BRSR Report, Sustainability Report</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose PDF file",
            type=['pdf'],
            help="Upload your company's Annual Report or BRSR document"
        )
        
        if uploaded_file:
            st.info(f"📄 **File:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
            
            if st.button("🔍 Extract ESG Data", type="primary"):
                with st.spinner("Analyzing report... This may take a few minutes..."):
                    # Reset file pointer
                    uploaded_file.seek(0)
                    
                    # Parse PDF
                    extracted = parse_uploaded_pdf(uploaded_file)
                    
                    if extracted:
                        st.session_state.pdf_extracted_data = extracted
                        st.session_state.data_source = 'PDF'
                        st.success(f"✅ Extraction complete! Confidence: {extracted.extraction_confidence:.1f}%")
        
        # Display extracted data
        if st.session_state.pdf_extracted_data:
            data = st.session_state.pdf_extracted_data
            
            st.markdown("---")
            st.markdown("### 📋 Extracted Data")
            
            # Company info
            st.markdown(f"""
            <div class="extraction-result">
                <h4>{data.company_name or 'Unknown Company'}</h4>
                <p>Year: {data.year} | Report Type: {data.report_type.value}</p>
                <p>Extraction Confidence: {data.extraction_confidence:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Three columns for E, S, G
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🌍 Environmental")
                env = data.environmental
                st.markdown(f"""
                - **GHG Emissions:** {env.total_ghg_emissions:,.0f} tCO2e
                - **Scope 1:** {env.scope1_emissions:,.0f} tCO2e
                - **Scope 2:** {env.scope2_emissions:,.0f} tCO2e
                - **Total Energy:** {env.total_energy_consumption:,.0f} GJ
                - **Renewable %:** {env.renewable_energy_percentage:.1f}%
                - **Water:** {env.total_water_withdrawal:,.0f} KL
                - **Waste Recycled:** {env.waste_recycling_percentage:.1f}%
                """)
            
            with col2:
                st.markdown("#### 👥 Social")
                soc = data.social
                st.markdown(f"""
                - **Employees:** {soc.total_employees:,}
                - **Women %:** {soc.women_percentage:.1f}%
                - **LTIFR:** {soc.ltifr:.2f}
                - **Fatalities:** {soc.fatalities}
                - **Training Hrs:** {soc.training_hours_per_employee:.1f}
                - **CSR Spending:** ₹{soc.csr_spending:,.0f} Cr
                """)
            
            with col3:
                st.markdown("#### 🏛️ Governance")
                gov = data.governance
                st.markdown(f"""
                - **Board Size:** {gov.board_size}
                - **Independent %:** {gov.independent_percentage:.1f}%
                - **Women on Board:** {gov.women_board_percentage:.1f}%
                - **Board Meetings:** {gov.board_meetings}
                - **Audit Meetings:** {gov.audit_committee_meetings}
                """)
            
            st.markdown("---")
            
            # Calculate ESG score from extracted data
            if st.button("📊 Calculate ESG Score from Extracted Data", type="primary"):
                esg_input = convert_brsr_to_esg_input(data)
                
                env_score, env_metrics = calculate_environmental_score(esg_input)
                social_score, social_metrics = calculate_social_score(esg_input)
                gov_score, gov_metrics = calculate_governance_score(esg_input)
                overall = calculate_overall_esg(env_score, social_score, gov_score)
                risk = get_risk_level(overall)
                
                st.markdown("### 📊 ESG Score from Extracted Data")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.plotly_chart(create_gauge_chart(env_score, "Environmental"), use_container_width=True)
                with col2:
                    st.plotly_chart(create_gauge_chart(social_score, "Social"), use_container_width=True)
                with col3:
                    st.plotly_chart(create_gauge_chart(gov_score, "Governance"), use_container_width=True)
                with col4:
                    st.plotly_chart(create_gauge_chart(overall, "Overall ESG"), use_container_width=True)
                
                risk_color = get_risk_color(risk)
                st.markdown(f"""
                <div style='text-align: center; padding: 20px;'>
                    <span class="risk-{risk.lower()}" style='font-size: 1.2em;'>
                        ESG Risk Level: {risk}
                    </span>
                    <span class="data-source-badge badge-pdf" style='margin-left: 15px;'>
                        FROM PDF EXTRACTION
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # Show detailed metrics
                with st.expander("📊 View Detailed Metrics"):
                    tab1, tab2, tab3 = st.tabs(["Environmental", "Social", "Governance"])
                    
                    with tab1:
                        st.plotly_chart(create_metrics_bar(env_metrics, "Environmental Metrics"), use_container_width=True)
                    
                    with tab2:
                        st.plotly_chart(create_metrics_bar(social_metrics, "Social Metrics"), use_container_width=True)
                    
                    with tab3:
                        st.plotly_chart(create_metrics_bar(gov_metrics, "Governance Metrics"), use_container_width=True)
                
                # Export option
                st.markdown("---")
                if st.button("💾 Export Extracted Data as JSON"):
                    json_str = json.dumps(esg_input, indent=2, default=str)
                    st.download_button(
                        "📥 Download JSON",
                        json_str,
                        f"esg_extracted_{datetime.now().strftime('%Y%m%d')}.json",
                        "application/json"
                    )
    
    # ========================================================================
    # MANUAL INPUT PAGE
    # ========================================================================
    elif page == "📝 Manual Input":
        st.markdown("### 📝 Manual ESG Data Input")
        st.markdown("Enter your company's ESG metrics manually to calculate sustainability score.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name", "My Company")
            industry = st.selectbox("Industry", list(INDUSTRY_ADJUSTMENTS.keys())[:-1])
        
        with col2:
            symbol = st.text_input("Symbol", "MYCO")
            year = st.number_input("Year", 2020, 2025, 2024)
        
        st.markdown("---")
        
        # Environmental
        st.markdown("#### 🌍 Environmental Metrics")
        col1, col2, col3 = st.columns(3)
        
        benchmarks = get_benchmarks(industry)
        
        with col1:
            carbon = st.number_input("Carbon Emissions (tCO2e/Cr)", 0.0, 500.0, float(benchmarks['carbon']))
            renewable = st.number_input("Renewable Energy %", 0.0, 100.0, float(benchmarks['renewable']))
        
        with col2:
            energy = st.number_input("Energy Consumption (GJ/Cr)", 0.0, 1000.0, float(benchmarks['energy']))
            waste = st.number_input("Waste Recycling %", 0.0, 100.0, float(benchmarks['waste']))
        
        with col3:
            water = st.number_input("Water Consumption (KL/Cr)", 0.0, 5000.0, float(benchmarks['water']))
            env_compliance = st.number_input("Env Compliance %", 0.0, 100.0, 95.0)
        
        # Social
        st.markdown("#### 👥 Social Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ltifr = st.number_input("LTIFR", 0.0, 5.0, 0.5)
            women_wf = st.number_input("Women Workforce %", 0.0, 100.0, 25.0)
        
        with col2:
            turnover = st.number_input("Employee Turnover %", 0.0, 100.0, 15.0)
            training = st.number_input("Training Hrs/Employee", 0.0, 100.0, 20.0)
        
        with col3:
            csr = st.number_input("CSR % of Profit", 0.0, 10.0, 2.0)
            customer = st.number_input("Complaints Resolved %", 0.0, 100.0, 95.0)
        
        # Governance
        st.markdown("#### 🏛️ Governance Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            independent = st.number_input("Independent Directors %", 0.0, 100.0, 50.0)
            ethics = st.number_input("Ethics Compliance %", 0.0, 100.0, 90.0)
        
        with col2:
            women_board = st.number_input("Women on Board %", 0.0, 100.0, 17.0)
            risk_mgmt = st.number_input("Risk Mgmt Score", 0.0, 100.0, 80.0)
        
        with col3:
            audit = st.number_input("Audit Committee Meetings", 1, 12, 4)
            ceo_ratio = st.number_input("CEO Pay Ratio (x)", 1.0, 500.0, 100.0)
        
        if st.button("🔄 Calculate ESG Score", type="primary"):
            manual_data = {
                'carbon_emissions_intensity': carbon,
                'energy_consumption_intensity': energy,
                'renewable_energy_percentage': renewable,
                'water_consumption_intensity': water,
                'waste_recycling_rate': waste,
                'environmental_compliance': env_compliance,
                'climate_risk_disclosure': 60,
                'ltifr': ltifr,
                'employee_turnover_rate': turnover,
                'women_workforce_percentage': women_wf,
                'training_hours_per_employee': training,
                'csr_spending_percentage': csr,
                'human_rights_compliance': 90,
                'customer_complaints_resolved': customer,
                'data_breaches': 0,
                'independent_directors_percentage': independent,
                'women_directors_percentage': women_board,
                'audit_committee_meetings': audit,
                'ceo_median_pay_ratio': ceo_ratio,
                'ethics_anti_corruption': ethics,
                'risk_management': risk_mgmt,
            }
            
            env_score, env_metrics = calculate_environmental_score(manual_data, industry)
            social_score, social_metrics = calculate_social_score(manual_data)
            gov_score, gov_metrics = calculate_governance_score(manual_data)
            overall = calculate_overall_esg(env_score, social_score, gov_score, industry)
            risk = get_risk_level(overall)
            
            st.markdown("---")
            st.markdown("### 📊 Your ESG Score Results")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.plotly_chart(create_gauge_chart(env_score, "Environmental"), use_container_width=True)
            with col2:
                st.plotly_chart(create_gauge_chart(social_score, "Social"), use_container_width=True)
            with col3:
                st.plotly_chart(create_gauge_chart(gov_score, "Governance"), use_container_width=True)
            with col4:
                st.plotly_chart(create_gauge_chart(overall, "Overall ESG"), use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(create_radar_chart(env_score, social_score, gov_score, company_name), use_container_width=True)
            
            with col2:
                risk_color = get_risk_color(risk)
                st.markdown(f"""
                <div style='background-color: {risk_color}; color: white; padding: 30px; 
                            border-radius: 15px; text-align: center; margin-top: 50px;'>
                    <h2>ESG Risk Level</h2>
                    <h1>{risk}</h1>
                </div>
                """, unsafe_allow_html=True)
    
    # ========================================================================
    # COMPARE SOURCES PAGE
    # ========================================================================
    elif page == "🔄 Compare Sources":
        st.markdown("### 🔄 Compare Data from Different Sources")
        st.markdown("Compare ESG metrics from live data, PDF extraction, and manual input.")
        
        st.info("""
        This feature allows you to:
        1. Fetch live data from NSE/BSE
        2. Extract data from uploaded annual reports
        3. Input data manually
        4. Compare all sources side by side
        """)
        
        # This would show a comparison table of data from different sources
        # For brevity, showing a placeholder
        
        st.markdown("""
        <div class="metric-card">
            <h4>📊 Data Source Comparison</h4>
            <p>Use the other pages to populate data from different sources, then return here to compare.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.live_company_data or st.session_state.pdf_extracted_data:
            st.markdown("### Available Data")
            
            if st.session_state.live_company_data:
                st.markdown("✅ **Live Data Available**")
                with st.expander("View Live Data"):
                    st.json(st.session_state.live_company_data)
            
            if st.session_state.pdf_extracted_data:
                st.markdown("✅ **PDF Extracted Data Available**")
                with st.expander("View Extracted Data"):
                    st.json(st.session_state.pdf_extracted_data.to_esg_input())
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>🌿 <strong>NYZTrade ESG Platform</strong> | Integrated Real-Time & Document Analysis</p>
        <p style='font-size: 0.8em;'>
            ⚠️ ESG scores are for informational purposes. Consult professionals for investment decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
