# ============================================================================
# NYZTRADE - COMPLETE ESG DASHBOARD (STREAMLIT)
# Production-Ready ESG Analysis Platform for Indian Companies
# ============================================================================

"""
Complete Streamlit Dashboard for ESG Analysis
Features:
- Real NSE/BSE data integration
- Single company deep-dive
- Multi-company comparison
- Sector analysis
- Portfolio ESG scoring
- Custom data input
- Historical trends
- Export options

Run: streamlit run streamlit_esg_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
import requests
import time
import io
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="NYZTrade ESG Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/nyztrade/esg',
        'About': 'NYZTrade ESG Dashboard - Professional ESG Analysis for Indian Markets'
    }
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0.5rem 1rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e8449 0%, #27ae60 50%, #2ecc71 100%);
        color: white;
        padding: 25px 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 8px 25px rgba(30, 132, 73, 0.3);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.2em;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 8px 0 0 0;
        opacity: 0.9;
        font-size: 1.1em;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #1e8449;
        margin-bottom: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
    }
    
    /* Score indicators */
    .score-excellent { color: #27ae60; font-weight: bold; }
    .score-good { color: #2ecc71; font-weight: bold; }
    .score-average { color: #f39c12; font-weight: bold; }
    .score-poor { color: #e74c3c; font-weight: bold; }
    .score-critical { color: #c0392b; font-weight: bold; }
    
    /* Risk badges */
    .risk-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
        text-transform: uppercase;
    }
    
    .risk-negligible { background-color: #27ae60; color: white; }
    .risk-low { background-color: #2ecc71; color: white; }
    .risk-medium { background-color: #f39c12; color: white; }
    .risk-high { background-color: #e74c3c; color: white; }
    .risk-severe { background-color: #c0392b; color: white; }
    
    /* Info panels */
    .info-panel {
        background-color: #e8f5e9;
        border-radius: 10px;
        padding: 15px 20px;
        margin: 12px 0;
        border-left: 4px solid #27ae60;
    }
    
    .warning-panel {
        background-color: #fff3e0;
        border-radius: 10px;
        padding: 15px 20px;
        margin: 12px 0;
        border-left: 4px solid #f39c12;
    }
    
    .error-panel {
        background-color: #ffebee;
        border-radius: 10px;
        padding: 15px 20px;
        margin: 12px 0;
        border-left: 4px solid #e74c3c;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #1e8449, #27ae60);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin: 20px 0 15px 0;
        font-size: 1.1em;
        font-weight: 600;
    }
    
    /* Tables */
    .dataframe {
        font-size: 0.88em;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0f4f0 0%, #e8f5e9 100%);
    }
    
    section[data-testid="stSidebar"] .stRadio > label {
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1e8449, #27ae60);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(30, 132, 73, 0.3);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f4f0;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e8449 !important;
        color: white !important;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #1e8449, #2ecc71);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1e8449;
    }
    
    /* Footer */
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
# CONSTANTS AND CONFIGURATION
# ============================================================================

# ESG Weights
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
    'environmental_compliance': 0.10,
    'climate_risk_disclosure': 0.05,
    'biodiversity_initiatives': 0.05
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
    'Oil Exploration': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Refineries': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Mining': {'environmental': 1.3, 'social': 1.0, 'governance': 0.7},
    'Power': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Power Generation': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Cement': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Iron & Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
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
    'Real Estate': {'environmental': 1.1, 'social': 1.0, 'governance': 0.9},
    'Default': {'environmental': 1.0, 'social': 1.0, 'governance': 1.0}
}

# Industry Benchmarks
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
    'Telecom': {'carbon': 8, 'energy': 80, 'water': 40, 'renewable': 35, 'waste': 75},
    'Default': {'carbon': 50, 'energy': 200, 'water': 300, 'renewable': 25, 'waste': 65}
}

# Sample companies data
NIFTY50_COMPANIES = {
    'RELIANCE': {'name': 'Reliance Industries Ltd', 'sector': 'Energy', 'industry': 'Oil & Gas', 'market_cap': 1800000},
    'TCS': {'name': 'Tata Consultancy Services', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 1400000},
    'HDFCBANK': {'name': 'HDFC Bank Ltd', 'sector': 'Financial Services', 'industry': 'Private Banks', 'market_cap': 1100000},
    'INFY': {'name': 'Infosys Ltd', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 700000},
    'ICICIBANK': {'name': 'ICICI Bank Ltd', 'sector': 'Financial Services', 'industry': 'Private Banks', 'market_cap': 650000},
    'HINDUNILVR': {'name': 'Hindustan Unilever Ltd', 'sector': 'Consumer Goods', 'industry': 'FMCG', 'market_cap': 600000},
    'ITC': {'name': 'ITC Limited', 'sector': 'Consumer Goods', 'industry': 'FMCG', 'market_cap': 550000},
    'SBIN': {'name': 'State Bank of India', 'sector': 'Financial Services', 'industry': 'Banks', 'market_cap': 500000},
    'BHARTIARTL': {'name': 'Bharti Airtel Ltd', 'sector': 'Telecom', 'industry': 'Telecom', 'market_cap': 480000},
    'KOTAKBANK': {'name': 'Kotak Mahindra Bank', 'sector': 'Financial Services', 'industry': 'Private Banks', 'market_cap': 350000},
    'WIPRO': {'name': 'Wipro Ltd', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 300000},
    'LT': {'name': 'Larsen & Toubro Ltd', 'sector': 'Infrastructure', 'industry': 'Construction', 'market_cap': 400000},
    'AXISBANK': {'name': 'Axis Bank Ltd', 'sector': 'Financial Services', 'industry': 'Private Banks', 'market_cap': 280000},
    'ASIANPAINT': {'name': 'Asian Paints Ltd', 'sector': 'Consumer Goods', 'industry': 'Paints', 'market_cap': 320000},
    'MARUTI': {'name': 'Maruti Suzuki India Ltd', 'sector': 'Automobile', 'industry': 'Automobiles', 'market_cap': 350000},
    'TATASTEEL': {'name': 'Tata Steel Ltd', 'sector': 'Materials', 'industry': 'Steel', 'market_cap': 180000},
    'NTPC': {'name': 'NTPC Ltd', 'sector': 'Utilities', 'industry': 'Power', 'market_cap': 250000},
    'POWERGRID': {'name': 'Power Grid Corporation', 'sector': 'Utilities', 'industry': 'Power', 'market_cap': 200000},
    'SUNPHARMA': {'name': 'Sun Pharmaceutical', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals', 'market_cap': 320000},
    'DRREDDY': {'name': "Dr. Reddy's Laboratories", 'sector': 'Healthcare', 'industry': 'Pharmaceuticals', 'market_cap': 100000},
    'ONGC': {'name': 'Oil & Natural Gas Corp', 'sector': 'Energy', 'industry': 'Oil & Gas', 'market_cap': 200000},
    'COALINDIA': {'name': 'Coal India Ltd', 'sector': 'Energy', 'industry': 'Mining', 'market_cap': 150000},
    'TATAMOTORS': {'name': 'Tata Motors Ltd', 'sector': 'Automobile', 'industry': 'Automobiles', 'market_cap': 250000},
    'M&M': {'name': 'Mahindra & Mahindra Ltd', 'sector': 'Automobile', 'industry': 'Automobiles', 'market_cap': 280000},
    'HCLTECH': {'name': 'HCL Technologies Ltd', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 350000},
    'TECHM': {'name': 'Tech Mahindra Ltd', 'sector': 'Technology', 'industry': 'IT Services', 'market_cap': 120000},
    'BAJFINANCE': {'name': 'Bajaj Finance Ltd', 'sector': 'Financial Services', 'industry': 'NBFC', 'market_cap': 400000},
    'TITAN': {'name': 'Titan Company Ltd', 'sector': 'Consumer Goods', 'industry': 'Jewellery', 'market_cap': 280000},
    'ULTRACEMCO': {'name': 'UltraTech Cement Ltd', 'sector': 'Materials', 'industry': 'Cement', 'market_cap': 200000},
    'NESTLEIND': {'name': 'Nestle India Ltd', 'sector': 'Consumer Goods', 'industry': 'FMCG', 'market_cap': 220000},
}


# ============================================================================
# NSE DATA FETCHER (Real Data)
# ============================================================================

class NSEDataFetcher:
    """Fetch real company data from NSE India"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.base_url = "https://www.nseindia.com"
        self._initialized = False
    
    def _initialize_session(self):
        """Initialize session with NSE cookies"""
        if not self._initialized:
            try:
                self.session.get(self.base_url, timeout=10)
                self._initialized = True
            except:
                pass
    
    @st.cache_data(ttl=300)
    def get_company_info(_self, symbol: str) -> Optional[Dict]:
        """Fetch company info from NSE (cached for 5 minutes)"""
        _self._initialize_session()
        try:
            url = f"{_self.base_url}/api/quote-equity?symbol={symbol}"
            response = _self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'company_name': data.get('info', {}).get('companyName', symbol),
                    'industry': data.get('metadata', {}).get('industry', 'Unknown'),
                    'sector': data.get('metadata', {}).get('sector', 'Unknown'),
                    'market_cap': data.get('securityInfo', {}).get('marketCap', 0),
                    'last_price': data.get('priceInfo', {}).get('lastPrice', 0),
                    'change': data.get('priceInfo', {}).get('change', 0),
                    'pchange': data.get('priceInfo', {}).get('pChange', 0),
                    'isin': data.get('metadata', {}).get('isin', ''),
                }
        except Exception as e:
            st.warning(f"Could not fetch live data for {symbol}")
        
        return None
    
    @st.cache_data(ttl=300)
    def get_shareholding(_self, symbol: str) -> Optional[Dict]:
        """Fetch shareholding pattern"""
        _self._initialize_session()
        try:
            url = f"{_self.base_url}/api/quote-equity?symbol={symbol}&section=trade_info"
            response = _self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                dp = data.get('securityWiseDP', {})
                return {
                    'promoter_holding': dp.get('promoterAndPromoterGroup', 0),
                    'public_holding': dp.get('public', 0),
                    'fii_holding': dp.get('fii', 0),
                    'dii_holding': dp.get('dii', 0),
                }
        except:
            pass
        return None


# Initialize NSE fetcher
nse_fetcher = NSEDataFetcher()


# ============================================================================
# ESG CALCULATION FUNCTIONS
# ============================================================================

def get_industry_benchmarks(industry: str) -> Dict:
    """Get benchmarks for an industry"""
    return ENVIRONMENTAL_BENCHMARKS.get(industry, ENVIRONMENTAL_BENCHMARKS['Default'])


def generate_esg_data(industry: str, seed: int = None) -> Dict:
    """Generate ESG data based on industry benchmarks"""
    if seed:
        np.random.seed(seed)
    
    benchmarks = get_industry_benchmarks(industry)
    
    def vary(val, pct=0.3):
        return val * np.random.uniform(1-pct, 1+pct)
    
    return {
        # Environmental
        'carbon_emissions_intensity': vary(benchmarks['carbon']),
        'energy_consumption_intensity': vary(benchmarks['energy']),
        'renewable_energy_percentage': min(100, vary(benchmarks['renewable'], 0.5)),
        'water_consumption_intensity': vary(benchmarks['water']),
        'waste_recycling_rate': min(100, vary(benchmarks['waste'], 0.2)),
        'hazardous_waste_management': np.random.uniform(80, 100),
        'environmental_compliance': np.random.uniform(85, 100),
        'climate_risk_disclosure': np.random.uniform(40, 90),
        'biodiversity_initiatives': np.random.uniform(30, 80),
        
        # Social
        'ltifr': np.random.uniform(0.2, 1.0),
        'employee_turnover_rate': np.random.uniform(8, 25),
        'women_workforce_percentage': np.random.uniform(15, 40),
        'training_hours_per_employee': np.random.uniform(15, 50),
        'fair_wages': np.random.uniform(95, 100),
        'csr_spending_percentage': np.random.uniform(1.5, 3.0),
        'human_rights_compliance': np.random.uniform(85, 100),
        'customer_complaints_resolved': np.random.uniform(85, 99),
        'data_breaches': np.random.choice([0, 0, 0, 1, 2], p=[0.6, 0.2, 0.1, 0.07, 0.03]),
        'labor_practices': np.random.uniform(95, 100),
        
        # Governance
        'independent_directors_percentage': np.random.uniform(45, 70),
        'women_directors_percentage': np.random.uniform(15, 35),
        'audit_committee_meetings': np.random.randint(4, 8),
        'ceo_median_pay_ratio': np.random.uniform(50, 200),
        'ethics_anti_corruption': np.random.uniform(80, 100),
        'risk_management': np.random.uniform(60, 95),
        'tax_transparency': np.random.uniform(50, 90),
        'related_party_transactions': np.random.uniform(90, 100),
        'sustainability_committee': np.random.choice([0, 1], p=[0.2, 0.8]),
        
        # Benchmarks
        'benchmark_carbon': benchmarks['carbon'],
        'benchmark_energy': benchmarks['energy'],
        'benchmark_water': benchmarks['water'],
        'benchmark_ltifr': 0.5,
        
        # Other
        'controversy_score': np.random.uniform(0, 30),
    }


def calculate_environmental_score(data: Dict) -> Tuple[float, Dict]:
    """Calculate environmental score"""
    metrics = {}
    
    # Carbon Emissions
    carbon = data.get('carbon_emissions_intensity', 50)
    benchmark = data.get('benchmark_carbon', 50)
    score = max(0, min(100, 100 - (carbon / benchmark * 50))) if benchmark > 0 else 50
    metrics['Carbon Emissions Intensity'] = {
        'value': carbon, 'score': score, 
        'weight': ENVIRONMENTAL_WEIGHTS['carbon_emissions_intensity'], 
        'unit': 'tCO2e/Cr', 'benchmark': benchmark
    }
    
    # Energy Consumption
    energy = data.get('energy_consumption_intensity', 200)
    benchmark_e = data.get('benchmark_energy', 200)
    score_e = max(0, min(100, 100 - (energy / benchmark_e * 50))) if benchmark_e > 0 else 50
    metrics['Energy Consumption'] = {
        'value': energy, 'score': score_e,
        'weight': ENVIRONMENTAL_WEIGHTS['energy_consumption_intensity'],
        'unit': 'GJ/Cr', 'benchmark': benchmark_e
    }
    
    # Renewable Energy
    renewable = data.get('renewable_energy_percentage', 25)
    score_r = min(100, renewable * 2)
    metrics['Renewable Energy'] = {
        'value': renewable, 'score': score_r,
        'weight': ENVIRONMENTAL_WEIGHTS['renewable_energy_percentage'],
        'unit': '%', 'benchmark': 50
    }
    
    # Water Consumption
    water = data.get('water_consumption_intensity', 300)
    benchmark_w = data.get('benchmark_water', 300)
    score_w = max(0, min(100, 100 - (water / benchmark_w * 50))) if benchmark_w > 0 else 50
    metrics['Water Consumption'] = {
        'value': water, 'score': score_w,
        'weight': ENVIRONMENTAL_WEIGHTS['water_consumption_intensity'],
        'unit': 'KL/Cr', 'benchmark': benchmark_w
    }
    
    # Waste Recycling
    waste = data.get('waste_recycling_rate', 65)
    score_ws = min(100, waste * 1.25)
    metrics['Waste Recycling'] = {
        'value': waste, 'score': score_ws,
        'weight': ENVIRONMENTAL_WEIGHTS['waste_recycling_rate'],
        'unit': '%', 'benchmark': 80
    }
    
    # Environmental Compliance
    compliance = data.get('environmental_compliance', 95)
    metrics['Env Compliance'] = {
        'value': compliance, 'score': min(100, compliance),
        'weight': ENVIRONMENTAL_WEIGHTS['environmental_compliance'],
        'unit': '%', 'benchmark': 100
    }
    
    # Climate Disclosure
    climate = data.get('climate_risk_disclosure', 60)
    metrics['Climate Disclosure'] = {
        'value': climate, 'score': min(100, climate),
        'weight': ENVIRONMENTAL_WEIGHTS['climate_risk_disclosure'],
        'unit': '%', 'benchmark': 100
    }
    
    # Calculate total
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    
    return total, metrics


def calculate_social_score(data: Dict) -> Tuple[float, Dict]:
    """Calculate social score"""
    metrics = {}
    
    # Employee Safety
    ltifr = data.get('ltifr', 0.5)
    benchmark = data.get('benchmark_ltifr', 0.5)
    score = max(0, min(100, 100 - (ltifr / benchmark * 50))) if benchmark > 0 else 50
    metrics['Employee Safety'] = {
        'value': ltifr, 'score': score,
        'weight': SOCIAL_WEIGHTS['employee_health_safety'],
        'unit': 'LTIFR', 'benchmark': benchmark
    }
    
    # Employee Retention
    turnover = data.get('employee_turnover_rate', 15)
    score_t = max(0, min(100, 100 - turnover * 2))
    metrics['Employee Retention'] = {
        'value': turnover, 'score': score_t,
        'weight': SOCIAL_WEIGHTS['employee_turnover_rate'],
        'unit': '%', 'benchmark': 10
    }
    
    # Diversity
    women = data.get('women_workforce_percentage', 25)
    score_d = min(100, women * 2.5)
    metrics['Diversity'] = {
        'value': women, 'score': score_d,
        'weight': SOCIAL_WEIGHTS['diversity_inclusion'],
        'unit': '% women', 'benchmark': 40
    }
    
    # Training
    training = data.get('training_hours_per_employee', 20)
    score_tr = min(100, training * 2.5)
    metrics['Training'] = {
        'value': training, 'score': score_tr,
        'weight': SOCIAL_WEIGHTS['training_development'],
        'unit': 'hrs/emp', 'benchmark': 40
    }
    
    # CSR
    csr = data.get('csr_spending_percentage', 2)
    score_csr = min(100, csr * 40)
    metrics['CSR Spending'] = {
        'value': csr, 'score': score_csr,
        'weight': SOCIAL_WEIGHTS['community_investment'],
        'unit': '% profit', 'benchmark': 2.5
    }
    
    # Human Rights
    hr = data.get('human_rights_compliance', 90)
    metrics['Human Rights'] = {
        'value': hr, 'score': min(100, hr),
        'weight': SOCIAL_WEIGHTS['human_rights_compliance'],
        'unit': '%', 'benchmark': 100
    }
    
    # Customer Satisfaction
    customer = data.get('customer_complaints_resolved', 95)
    metrics['Customer Satisfaction'] = {
        'value': customer, 'score': min(100, customer),
        'weight': SOCIAL_WEIGHTS['customer_satisfaction'],
        'unit': '% resolved', 'benchmark': 100
    }
    
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    
    return total, metrics


def calculate_governance_score(data: Dict) -> Tuple[float, Dict]:
    """Calculate governance score"""
    metrics = {}
    
    # Board Independence
    independent = data.get('independent_directors_percentage', 50)
    score = min(100, independent * 1.5)
    metrics['Board Independence'] = {
        'value': independent, 'score': score,
        'weight': GOVERNANCE_WEIGHTS['board_independence'],
        'unit': '%', 'benchmark': 67
    }
    
    # Board Diversity
    women = data.get('women_directors_percentage', 17)
    score_w = min(100, women * 4)
    metrics['Board Diversity'] = {
        'value': women, 'score': score_w,
        'weight': GOVERNANCE_WEIGHTS['board_diversity'],
        'unit': '% women', 'benchmark': 25
    }
    
    # Audit Committee
    audit = data.get('audit_committee_meetings', 4)
    score_a = min(100, audit * 16.67)
    metrics['Audit Committee'] = {
        'value': audit, 'score': score_a,
        'weight': GOVERNANCE_WEIGHTS['audit_committee_quality'],
        'unit': 'meetings', 'benchmark': 6
    }
    
    # Executive Compensation
    ratio = data.get('ceo_median_pay_ratio', 100)
    score_e = max(0, min(100, 150 - ratio * 0.5))
    metrics['Exec Compensation'] = {
        'value': ratio, 'score': score_e,
        'weight': GOVERNANCE_WEIGHTS['executive_compensation'],
        'unit': 'x median', 'benchmark': 100
    }
    
    # Ethics
    ethics = data.get('ethics_anti_corruption', 90)
    metrics['Ethics'] = {
        'value': ethics, 'score': min(100, ethics),
        'weight': GOVERNANCE_WEIGHTS['ethics_anti_corruption'],
        'unit': '%', 'benchmark': 100
    }
    
    # Risk Management
    risk = data.get('risk_management', 80)
    metrics['Risk Management'] = {
        'value': risk, 'score': min(100, risk),
        'weight': GOVERNANCE_WEIGHTS['risk_management'],
        'unit': 'score', 'benchmark': 100
    }
    
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    
    return total, metrics


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


def get_risk_color(risk: str) -> str:
    """Get color for risk level"""
    colors = {
        "Negligible": "#27ae60",
        "Low": "#2ecc71",
        "Medium": "#f39c12",
        "High": "#e74c3c",
        "Severe": "#c0392b"
    }
    return colors.get(risk, "#f39c12")


def get_score_icon(score: float) -> str:
    """Get icon for score"""
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

def create_gauge_chart(score: float, title: str, height: int = 250) -> go.Figure:
    """Create gauge chart for scores"""
    color = "#27ae60" if score >= 80 else "#2ecc71" if score >= 65 else "#f39c12" if score >= 50 else "#e74c3c"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16, 'family': 'Arial'}},
        delta={'reference': 50, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.8},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
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
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': "Arial"}
    )
    
    return fig


def create_radar_chart(env: float, social: float, gov: float, name: str) -> go.Figure:
    """Create radar chart for ESG profile"""
    categories = ['Environmental', 'Social', 'Governance', 'Environmental']
    values = [env, social, gov, env]
    benchmark = [50, 50, 50, 50]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(30, 132, 73, 0.3)',
        line=dict(color='#1e8449', width=2),
        name=name
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=benchmark,
        theta=categories,
        fill='toself',
        fillcolor='rgba(243, 156, 18, 0.1)',
        line=dict(color='#f39c12', width=2, dash='dash'),
        name='Benchmark'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title=f"ESG Profile - {name}",
        height=400,
        margin=dict(l=60, r=60, t=60, b=60)
    )
    
    return fig


def create_bar_chart(metrics: Dict, title: str) -> go.Figure:
    """Create horizontal bar chart for metrics"""
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
    
    fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="Threshold")
    fig.add_vline(x=70, line_dash="dash", line_color="green", annotation_text="Good")
    
    fig.update_layout(
        title=title,
        xaxis_title="Score",
        xaxis=dict(range=[0, 110]),
        height=50 + len(names) * 45,
        margin=dict(l=150, r=50, t=50, b=50)
    )
    
    return fig


def create_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Create company comparison chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(name='Environmental', x=df['Company'], y=df['Environmental'], marker_color='#27ae60'))
    fig.add_trace(go.Bar(name='Social', x=df['Company'], y=df['Social'], marker_color='#3498db'))
    fig.add_trace(go.Bar(name='Governance', x=df['Company'], y=df['Governance'], marker_color='#9b59b6'))
    
    fig.add_trace(go.Scatter(
        name='Overall ESG', x=df['Company'], y=df['Overall ESG'],
        mode='lines+markers', line=dict(color='#e74c3c', width=3), marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="Company ESG Score Comparison",
        barmode='group',
        xaxis_title="Company",
        yaxis_title="Score",
        yaxis=dict(range=[0, 100]),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig


def create_sector_chart(df: pd.DataFrame) -> go.Figure:
    """Create sector breakdown chart"""
    sector_avg = df.groupby('Sector').agg({
        'Environmental': 'mean',
        'Social': 'mean',
        'Governance': 'mean',
        'Overall ESG': 'mean'
    }).round(1).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(name='Environmental', x=sector_avg['Sector'], y=sector_avg['Environmental'], marker_color='#27ae60'))
    fig.add_trace(go.Bar(name='Social', x=sector_avg['Sector'], y=sector_avg['Social'], marker_color='#3498db'))
    fig.add_trace(go.Bar(name='Governance', x=sector_avg['Sector'], y=sector_avg['Governance'], marker_color='#9b59b6'))
    
    fig.add_trace(go.Scatter(
        name='Overall', x=sector_avg['Sector'], y=sector_avg['Overall ESG'],
        mode='lines+markers', line=dict(color='#e74c3c', width=3)
    ))
    
    fig.update_layout(
        title="Sector-wise ESG Performance",
        barmode='group',
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig


def create_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create ESG heatmap"""
    data = df[['Company', 'Environmental', 'Social', 'Governance', 'Overall ESG']].set_index('Company')
    
    fig = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns,
        y=data.index,
        colorscale=[[0, '#c0392b'], [0.35, '#e74c3c'], [0.5, '#f39c12'], [0.65, '#2ecc71'], [1, '#27ae60']],
        text=np.round(data.values, 1),
        texttemplate="%{text}",
        textfont={"size": 11},
        colorbar=dict(title="Score")
    ))
    
    fig.update_layout(
        title="ESG Score Heatmap",
        height=100 + len(data) * 35,
        xaxis_title="Category",
        yaxis_title="Company"
    )
    
    return fig


def create_historical_chart(symbol: str, periods: int = 12) -> go.Figure:
    """Create historical trend chart (simulated)"""
    np.random.seed(hash(symbol) % 2**32)
    
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='M')
    base_e, base_s, base_g = np.random.uniform(50, 70, 3)
    
    data = []
    for i, date in enumerate(dates):
        e = min(100, max(0, base_e + i * 0.5 + np.random.uniform(-3, 3)))
        s = min(100, max(0, base_s + i * 0.3 + np.random.uniform(-3, 3)))
        g = min(100, max(0, base_g + i * 0.2 + np.random.uniform(-2, 2)))
        o = e * 0.35 + s * 0.35 + g * 0.30
        data.append({'Date': date, 'Environmental': e, 'Social': s, 'Governance': g, 'Overall': o})
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Environmental'], name='Environmental', line=dict(color='#27ae60', width=2), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Social'], name='Social', line=dict(color='#3498db', width=2), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Governance'], name='Governance', line=dict(color='#9b59b6', width=2), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Overall'], name='Overall ESG', line=dict(color='#e74c3c', width=3), mode='lines+markers', marker=dict(size=8)))
    
    fig.update_layout(
        title=f"ESG Score Trend - {symbol}",
        xaxis_title="Date",
        yaxis_title="Score",
        yaxis=dict(range=[30, 100]),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig, df


# ============================================================================
# GENERATE ESG SCORES FOR ALL COMPANIES
# ============================================================================

@st.cache_data(ttl=600)
def generate_all_esg_scores() -> pd.DataFrame:
    """Generate ESG scores for all sample companies"""
    results = []
    
    for symbol, info in NIFTY50_COMPANIES.items():
        np.random.seed(hash(symbol) % 2**32)
        
        industry = info['industry']
        adj = INDUSTRY_ADJUSTMENTS.get(industry, INDUSTRY_ADJUSTMENTS['Default'])
        
        # Generate data
        data = generate_esg_data(industry, hash(symbol) % 2**32)
        
        # Calculate scores
        env_score, _ = calculate_environmental_score(data)
        social_score, _ = calculate_social_score(data)
        gov_score, _ = calculate_governance_score(data)
        
        # Calculate overall with adjustments
        env_w = 0.35 * adj['environmental']
        soc_w = 0.35 * adj['social']
        gov_w = 0.30 * adj['governance']
        total_w = env_w + soc_w + gov_w
        
        overall = (env_score * env_w + social_score * soc_w + gov_score * gov_w) / total_w
        
        results.append({
            'Symbol': symbol,
            'Company': info['name'][:25] + '...' if len(info['name']) > 25 else info['name'],
            'Full Name': info['name'],
            'Sector': info['sector'],
            'Industry': industry,
            'Market Cap (Cr)': info['market_cap'],
            'Environmental': round(env_score, 1),
            'Social': round(social_score, 1),
            'Governance': round(gov_score, 1),
            'Overall ESG': round(overall, 1),
            'Risk Level': get_risk_level(overall),
            'Controversy': round(data['controversy_score'], 1)
        })
    
    return pd.DataFrame(results).sort_values('Overall ESG', ascending=False).reset_index(drop=True)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌿 NYZTrade ESG Dashboard</h1>
        <p>Professional ESG Analysis Platform for Indian Listed Companies | BRSR Framework Compliant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 🎛️ Control Panel")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigate to",
        ["🏠 Dashboard", "🏢 Company Analysis", "📊 Compare Companies", 
         "🔍 Sector Analysis", "📁 Portfolio Scoring", "📝 Custom Input", 
         "📋 Full Report"],
        label_visibility="collapsed"
    )
    
    # Data settings
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Settings")
    use_real_data = st.sidebar.checkbox("Fetch Real NSE Data", value=False, 
                                        help="Enable to fetch live data from NSE (may be slow)")
    
    # Generate data
    esg_df = generate_all_esg_scores()
    
    # ========================================================================
    # DASHBOARD PAGE
    # ========================================================================
    if page == "🏠 Dashboard":
        st.markdown("### 📊 NIFTY 50 ESG Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_esg = esg_df['Overall ESG'].mean()
            st.metric("Average ESG Score", f"{avg_esg:.1f}", f"{avg_esg - 50:.1f} vs benchmark")
        
        with col2:
            leaders = len(esg_df[esg_df['Risk Level'].isin(['Negligible', 'Low'])])
            st.metric("ESG Leaders", f"{leaders}", f"{leaders/len(esg_df)*100:.0f}% of total")
        
        with col3:
            laggards = len(esg_df[esg_df['Risk Level'].isin(['High', 'Severe'])])
            st.metric("Needs Improvement", f"{laggards}", delta_color="inverse")
        
        with col4:
            top_sector = esg_df.groupby('Sector')['Overall ESG'].mean().idxmax()
            st.metric("Top Sector", top_sector)
        
        # Charts
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = create_sector_chart(esg_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Risk distribution
            risk_counts = esg_df['Risk Level'].value_counts()
            colors = {'Negligible': '#27ae60', 'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c', 'Severe': '#c0392b'}
            
            fig = px.pie(values=risk_counts.values, names=risk_counts.index, 
                        color=risk_counts.index, color_discrete_map=colors,
                        title="Risk Distribution")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Top & Bottom performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 Top 5 ESG Leaders")
            for _, row in esg_df.head(5).iterrows():
                color = get_risk_color(row['Risk Level'])
                st.markdown(f"""
                <div class="metric-card">
                    <strong>{row['Symbol']}</strong> - {row['Company']}
                    <span style='float: right; color: {color}; font-weight: bold;'>
                        {row['Overall ESG']:.1f} {get_score_icon(row['Overall ESG'])}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### ⚠️ Needs Improvement")
            for _, row in esg_df.tail(5).iloc[::-1].iterrows():
                color = get_risk_color(row['Risk Level'])
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: {color};">
                    <strong>{row['Symbol']}</strong> - {row['Company']}
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
        
        selected = st.selectbox(
            "Select Company",
            esg_df['Symbol'].tolist(),
            format_func=lambda x: f"{x} - {NIFTY50_COMPANIES.get(x, {}).get('name', x)}"
        )
        
        company_info = NIFTY50_COMPANIES.get(selected, {})
        company_row = esg_df[esg_df['Symbol'] == selected].iloc[0]
        
        # Fetch real data if enabled
        real_data = None
        if use_real_data:
            with st.spinner("Fetching live data from NSE..."):
                real_data = nse_fetcher.get_company_info(selected)
                shareholding = nse_fetcher.get_shareholding(selected)
                if real_data:
                    st.success(f"✅ Live data fetched for {selected}")
        
        # Company header
        risk_color = get_risk_color(company_row['Risk Level'])
        
        market_cap = real_data['market_cap'] if real_data and real_data.get('market_cap') else company_info.get('market_cap', 0)
        last_price = real_data.get('last_price', 0) if real_data else 0
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #34495e, #2c3e50); padding: 25px; border-radius: 15px; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0;'>{company_info.get('name', selected)}</h2>
            <p style='color: #bdc3c7; margin: 5px 0;'>
                {selected} | {company_info.get('sector', 'N/A')} | {company_info.get('industry', 'N/A')}
            </p>
            <p style='color: #bdc3c7; margin: 5px 0;'>
                Market Cap: ₹{market_cap:,.0f} Cr {f'| LTP: ₹{last_price:,.2f}' if last_price else ''}
            </p>
            <span class="risk-badge risk-{company_row['Risk Level'].lower()}">{company_row['Risk Level']} Risk</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Gauge charts
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            fig = create_gauge_chart(company_row['Environmental'], "Environmental")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_gauge_chart(company_row['Social'], "Social")
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            fig = create_gauge_chart(company_row['Governance'], "Governance")
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            fig = create_gauge_chart(company_row['Overall ESG'], "Overall ESG")
            st.plotly_chart(fig, use_container_width=True)
        
        # Radar & Details
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig = create_radar_chart(company_row['Environmental'], company_row['Social'], 
                                    company_row['Governance'], selected)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📋 Quick Summary")
            
            st.markdown(f"""
            <div class="info-panel">
                <strong>Overall ESG Score:</strong> {company_row['Overall ESG']:.1f} / 100<br>
                <strong>Risk Level:</strong> <span style="color: {risk_color}; font-weight: bold;">{company_row['Risk Level']}</span><br>
                <strong>Controversy Score:</strong> {company_row['Controversy']:.1f}
            </div>
            """, unsafe_allow_html=True)
            
            # Strengths & Weaknesses
            scores = {'Environmental': company_row['Environmental'], 
                     'Social': company_row['Social'], 
                     'Governance': company_row['Governance']}
            
            best = max(scores, key=scores.get)
            worst = min(scores, key=scores.get)
            
            st.markdown(f"""
            **💪 Strongest Area:** {best} ({scores[best]:.1f})
            
            **📈 Area for Improvement:** {worst} ({scores[worst]:.1f})
            """)
        
        # Historical Trend
        st.markdown("### 📈 Historical ESG Trend")
        fig, _ = create_historical_chart(selected)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Metrics
        st.markdown("### 📊 Detailed Metrics")
        
        # Generate detailed data
        esg_data = generate_esg_data(company_info.get('industry', 'Default'), hash(selected) % 2**32)
        env_score, env_metrics = calculate_environmental_score(esg_data)
        social_score, social_metrics = calculate_social_score(esg_data)
        gov_score, gov_metrics = calculate_governance_score(esg_data)
        
        tab1, tab2, tab3 = st.tabs(["🌍 Environmental", "👥 Social", "🏛️ Governance"])
        
        with tab1:
            fig = create_bar_chart(env_metrics, "Environmental Metrics")
            st.plotly_chart(fig, use_container_width=True)
            
            env_df = pd.DataFrame([
                {'Metric': k, 'Value': f"{v['value']:.2f} {v['unit']}", 
                 'Score': f"{v['score']:.1f}", 'Weight': f"{v['weight']*100:.0f}%",
                 'Status': '🟢' if v['score'] >= 70 else '🟡' if v['score'] >= 50 else '🔴'}
                for k, v in env_metrics.items()
            ])
            st.dataframe(env_df, use_container_width=True, hide_index=True)
        
        with tab2:
            fig = create_bar_chart(social_metrics, "Social Metrics")
            st.plotly_chart(fig, use_container_width=True)
            
            social_df = pd.DataFrame([
                {'Metric': k, 'Value': f"{v['value']:.2f} {v['unit']}", 
                 'Score': f"{v['score']:.1f}", 'Weight': f"{v['weight']*100:.0f}%",
                 'Status': '🟢' if v['score'] >= 70 else '🟡' if v['score'] >= 50 else '🔴'}
                for k, v in social_metrics.items()
            ])
            st.dataframe(social_df, use_container_width=True, hide_index=True)
        
        with tab3:
            fig = create_bar_chart(gov_metrics, "Governance Metrics")
            st.plotly_chart(fig, use_container_width=True)
            
            gov_df = pd.DataFrame([
                {'Metric': k, 'Value': f"{v['value']:.2f} {v['unit']}", 
                 'Score': f"{v['score']:.1f}", 'Weight': f"{v['weight']*100:.0f}%",
                 'Status': '🟢' if v['score'] >= 70 else '🟡' if v['score'] >= 50 else '🔴'}
                for k, v in gov_metrics.items()
            ])
            st.dataframe(gov_df, use_container_width=True, hide_index=True)
    
    # ========================================================================
    # COMPARE COMPANIES PAGE
    # ========================================================================
    elif page == "📊 Compare Companies":
        st.markdown("### 📊 Multi-Company ESG Comparison")
        
        selected = st.multiselect(
            "Select Companies to Compare (2-10)",
            esg_df['Symbol'].tolist(),
            default=['TCS', 'INFY', 'WIPRO', 'HDFCBANK', 'RELIANCE'],
            max_selections=10,
            format_func=lambda x: f"{x} - {NIFTY50_COMPANIES.get(x, {}).get('name', x)[:20]}"
        )
        
        if len(selected) >= 2:
            comp_df = esg_df[esg_df['Symbol'].isin(selected)].copy()
            
            # Comparison chart
            fig = create_comparison_chart(comp_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Heatmap
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = create_heatmap(comp_df)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 🏆 Ranking")
                for i, (_, row) in enumerate(comp_df.sort_values('Overall ESG', ascending=False).iterrows()):
                    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                    color = get_risk_color(row['Risk Level'])
                    st.markdown(f"""
                    <div class="metric-card">
                        {medal} <strong>{row['Symbol']}</strong>
                        <span style='float: right; color: {color};'>{row['Overall ESG']:.1f}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Table
            st.markdown("### 📋 Detailed Comparison")
            display_df = comp_df[['Symbol', 'Company', 'Sector', 'Environmental', 'Social', 'Governance', 'Overall ESG', 'Risk Level']]
            
            st.dataframe(
                display_df.style.background_gradient(
                    subset=['Environmental', 'Social', 'Governance', 'Overall ESG'],
                    cmap='RdYlGn', vmin=40, vmax=90
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Please select at least 2 companies to compare.")
    
    # ========================================================================
    # SECTOR ANALYSIS PAGE
    # ========================================================================
    elif page == "🔍 Sector Analysis":
        st.markdown("### 🔍 Sector-wise ESG Analysis")
        
        selected_sector = st.selectbox("Select Sector", esg_df['Sector'].unique().tolist())
        
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
        
        # Comparison chart
        fig = px.bar(
            sector_df,
            x='Symbol',
            y=['Environmental', 'Social', 'Governance'],
            title=f"ESG Breakdown - {selected_sector} Sector",
            barmode='group',
            color_discrete_sequence=['#27ae60', '#3498db', '#9b59b6']
        )
        fig.add_scatter(x=sector_df['Symbol'], y=sector_df['Overall ESG'], name='Overall ESG',
                       mode='lines+markers', line=dict(color='#e74c3c', width=2))
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        st.markdown("### 📋 Sector Companies")
        st.dataframe(
            sector_df[['Symbol', 'Company', 'Industry', 'Environmental', 'Social', 'Governance', 'Overall ESG', 'Risk Level']].style.background_gradient(
                subset=['Environmental', 'Social', 'Governance', 'Overall ESG'],
                cmap='RdYlGn', vmin=40, vmax=90
            ),
            use_container_width=True,
            hide_index=True
        )
    
    # ========================================================================
    # PORTFOLIO SCORING PAGE
    # ========================================================================
    elif page == "📁 Portfolio Scoring":
        st.markdown("### 📁 Portfolio ESG Scoring")
        
        st.markdown("""
        <div class="info-panel">
            <strong>📌 How to use:</strong> Select companies and set allocations to calculate your portfolio's ESG score.
        </div>
        """, unsafe_allow_html=True)
        
        selected = st.multiselect(
            "Select Portfolio Companies",
            esg_df['Symbol'].tolist(),
            default=['TCS', 'HDFCBANK', 'RELIANCE', 'INFY'],
            format_func=lambda x: f"{x} - {NIFTY50_COMPANIES.get(x, {}).get('name', x)[:20]}"
        )
        
        if len(selected) >= 2:
            st.markdown("### 📊 Set Allocations")
            
            allocations = {}
            cols = st.columns(min(4, len(selected)))
            
            for i, symbol in enumerate(selected):
                with cols[i % 4]:
                    allocations[symbol] = st.number_input(
                        f"{symbol} (%)", min_value=0.0, max_value=100.0,
                        value=100.0/len(selected), step=5.0, key=f"alloc_{symbol}"
                    )
            
            total_alloc = sum(allocations.values())
            
            if abs(total_alloc - 100) > 0.1:
                st.warning(f"⚠️ Total allocation is {total_alloc:.1f}%. Please adjust to 100%.")
            else:
                portfolio_df = esg_df[esg_df['Symbol'].isin(selected)].copy()
                portfolio_df['Allocation'] = portfolio_df['Symbol'].map(allocations)
                
                # Calculate weighted scores
                w_env = (portfolio_df['Environmental'] * portfolio_df['Allocation'] / 100).sum()
                w_soc = (portfolio_df['Social'] * portfolio_df['Allocation'] / 100).sum()
                w_gov = (portfolio_df['Governance'] * portfolio_df['Allocation'] / 100).sum()
                w_overall = (portfolio_df['Overall ESG'] * portfolio_df['Allocation'] / 100).sum()
                
                st.markdown("### 📈 Portfolio ESG Scores")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    fig = create_gauge_chart(w_env, "Environmental")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = create_gauge_chart(w_soc, "Social")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col3:
                    fig = create_gauge_chart(w_gov, "Governance")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col4:
                    fig = create_gauge_chart(w_overall, "Overall ESG")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Portfolio composition
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.pie(portfolio_df, values='Allocation', names='Symbol',
                                title="Portfolio Allocation", hover_data=['Company', 'Overall ESG'])
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = create_radar_chart(w_env, w_soc, w_gov, "Portfolio")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.markdown("### 📋 Portfolio Holdings")
                display_df = portfolio_df[['Symbol', 'Company', 'Allocation', 'Environmental', 'Social', 'Governance', 'Overall ESG', 'Risk Level']]
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Please select at least 2 companies to build a portfolio.")
    
    # ========================================================================
    # CUSTOM INPUT PAGE
    # ========================================================================
    elif page == "📝 Custom Input":
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
        
        # Environmental
        st.markdown("#### 🌍 Environmental Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            carbon = st.number_input("Carbon Emissions (tCO2e/Cr)", 0.0, 500.0, 50.0)
            renewable = st.number_input("Renewable Energy %", 0.0, 100.0, 25.0)
        
        with col2:
            energy = st.number_input("Energy Consumption (GJ/Cr)", 0.0, 1000.0, 200.0)
            waste = st.number_input("Waste Recycling %", 0.0, 100.0, 65.0)
        
        with col3:
            water = st.number_input("Water Consumption (KL/Cr)", 0.0, 5000.0, 300.0)
            env_compliance = st.number_input("Env Compliance %", 0.0, 100.0, 95.0)
        
        # Social
        st.markdown("#### 👥 Social Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ltifr = st.number_input("LTIFR", 0.0, 5.0, 0.5)
            women = st.number_input("Women Workforce %", 0.0, 100.0, 25.0)
        
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
            benchmarks = get_industry_benchmarks(industry)
            
            custom_data = {
                'carbon_emissions_intensity': carbon,
                'energy_consumption_intensity': energy,
                'renewable_energy_percentage': renewable,
                'water_consumption_intensity': water,
                'waste_recycling_rate': waste,
                'environmental_compliance': env_compliance,
                'climate_risk_disclosure': 60,
                'benchmark_carbon': benchmarks['carbon'],
                'benchmark_energy': benchmarks['energy'],
                'benchmark_water': benchmarks['water'],
                'benchmark_ltifr': 0.5,
                'ltifr': ltifr,
                'employee_turnover_rate': turnover,
                'women_workforce_percentage': women,
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
            }
            
            env_score, env_metrics = calculate_environmental_score(custom_data)
            social_score, social_metrics = calculate_social_score(custom_data)
            gov_score, gov_metrics = calculate_governance_score(custom_data)
            
            adj = INDUSTRY_ADJUSTMENTS.get(industry, INDUSTRY_ADJUSTMENTS['Default'])
            env_w = 0.35 * adj['environmental']
            soc_w = 0.35 * adj['social']
            gov_w = 0.30 * adj['governance']
            total_w = env_w + soc_w + gov_w
            
            overall = (env_score * env_w + social_score * soc_w + gov_score * gov_w) / total_w
            risk = get_risk_level(overall)
            risk_color = get_risk_color(risk)
            
            st.markdown("---")
            st.markdown("### 📊 Your ESG Score Results")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🌍 Environmental", f"{env_score:.1f}")
            with col2:
                st.metric("👥 Social", f"{social_score:.1f}")
            with col3:
                st.metric("🏛️ Governance", f"{gov_score:.1f}")
            with col4:
                st.metric("📊 Overall ESG", f"{overall:.1f}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = create_gauge_chart(overall, "Overall ESG Score", 300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = create_radar_chart(env_score, social_score, gov_score, company_name)
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"""
            <div style='background-color: {risk_color}; color: white; padding: 20px; 
                        border-radius: 10px; text-align: center;'>
                <h3>ESG Risk Level: {risk}</h3>
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================================================
    # FULL REPORT PAGE
    # ========================================================================
    elif page == "📋 Full Report":
        st.markdown("### 📋 Complete NIFTY 50 ESG Report")
        
        # Summary
        st.markdown("#### 📊 Summary Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            summary = esg_df[['Environmental', 'Social', 'Governance', 'Overall ESG']].describe()
            st.dataframe(summary.round(1), use_container_width=True)
        
        with col2:
            risk_summary = esg_df['Risk Level'].value_counts()
            st.dataframe(risk_summary, use_container_width=True)
        
        # Full table
        st.markdown("#### 📋 Complete ESG Scores")
        
        st.dataframe(
            esg_df.style.background_gradient(
                subset=['Environmental', 'Social', 'Governance', 'Overall ESG'],
                cmap='RdYlGn', vmin=40, vmax=90
            ).format({
                'Market Cap (Cr)': '{:,.0f}',
                'Environmental': '{:.1f}',
                'Social': '{:.1f}',
                'Governance': '{:.1f}',
                'Overall ESG': '{:.1f}',
                'Controversy': '{:.1f}'
            }),
            use_container_width=True,
            height=600,
            hide_index=True
        )
        
        # Export
        st.markdown("#### 💾 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = esg_df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                f"nifty50_esg_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        
        with col2:
            json_data = esg_df.to_json(orient='records', indent=2)
            st.download_button(
                "📥 Download JSON",
                json_data,
                f"nifty50_esg_{datetime.now().strftime('%Y%m%d')}.json",
                "application/json"
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>🌿 <strong>NYZTrade ESG Dashboard</strong> | Powered by BRSR Framework</p>
        <p style='font-size: 0.8em;'>
            ⚠️ This is a demonstration tool. Actual ESG assessments should be based on verified BRSR disclosures.
        </p>
        <p style='font-size: 0.7em;'>
            Last Updated: {timestamp}
        </p>
    </div>
    """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
