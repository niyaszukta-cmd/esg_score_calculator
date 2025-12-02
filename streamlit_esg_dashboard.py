# ============================================================================
# NYZTRADE - COMPLETE ESG DASHBOARD (SELF-CONTAINED)
# Real-Time Data + PDF Annual Report Parser + ESG Scoring
# ============================================================================
# 
# INSTALLATION:
# pip install streamlit pandas numpy plotly requests beautifulsoup4 PyMuPDF pdfplumber
#
# RUN:
# streamlit run streamlit_esg_dashboard_complete.py
#
# ============================================================================
pip install PyMuPDF pdfplumber
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
import re
import requests
import hashlib
import pickle
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ============================================================================
# CHECK AVAILABLE LIBRARIES
# ============================================================================

# Check for PDF libraries
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

PDF_PARSER_AVAILABLE = PYMUPDF_AVAILABLE or PDFPLUMBER_AVAILABLE

# Check for BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


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
    
    .badge-live { background-color: #27ae60; color: white; }
    .badge-pdf { background-color: #3498db; color: white; }
    .badge-manual { background-color: #9b59b6; color: white; }
    .badge-simulated { background-color: #f39c12; color: white; }
    
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
    
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CompanyData:
    """Complete company data structure"""
    symbol: str
    company_name: str = ""
    isin: str = ""
    series: str = ""
    sector: str = ""
    industry: str = ""
    sub_industry: str = ""
    last_price: float = 0.0
    change: float = 0.0
    pchange: float = 0.0
    open_price: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    prev_close: float = 0.0
    volume: int = 0
    value: float = 0.0
    market_cap: float = 0.0
    face_value: float = 0.0
    book_value: float = 0.0
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    dividend_yield: float = 0.0
    eps: float = 0.0
    roe: float = 0.0
    roce: float = 0.0
    week_high_52: float = 0.0
    week_low_52: float = 0.0
    promoter_holding: float = 0.0
    public_holding: float = 0.0
    fii_holding: float = 0.0
    dii_holding: float = 0.0
    pledged_percentage: float = 0.0
    revenue: float = 0.0
    net_profit: float = 0.0
    total_assets: float = 0.0
    total_debt: float = 0.0
    employee_count: int = 0
    csr_spending: float = 0.0
    data_source: str = ""
    fetch_time: datetime = field(default_factory=datetime.now)
    data_quality: float = 0.0
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


class ReportType(Enum):
    """Types of sustainability reports"""
    BRSR = "BRSR Report"
    ANNUAL = "Annual Report"
    SUSTAINABILITY = "Sustainability Report"
    INTEGRATED = "Integrated Report"
    CSR = "CSR Report"
    UNKNOWN = "Unknown"


@dataclass
class EnvironmentalMetrics:
    """Environmental metrics extracted from report"""
    total_energy_consumption: float = 0.0
    renewable_energy: float = 0.0
    non_renewable_energy: float = 0.0
    renewable_energy_percentage: float = 0.0
    energy_intensity: float = 0.0
    scope1_emissions: float = 0.0
    scope2_emissions: float = 0.0
    scope3_emissions: float = 0.0
    total_ghg_emissions: float = 0.0
    emission_intensity: float = 0.0
    total_water_withdrawal: float = 0.0
    water_recycled: float = 0.0
    water_recycling_percentage: float = 0.0
    water_intensity: float = 0.0
    total_waste_generated: float = 0.0
    hazardous_waste: float = 0.0
    non_hazardous_waste: float = 0.0
    waste_recycled: float = 0.0
    waste_recycling_percentage: float = 0.0
    environmental_fines: float = 0.0
    environmental_incidents: int = 0
    eco_sensitive_operations: int = 0


@dataclass
class SocialMetrics:
    """Social metrics extracted from report"""
    total_employees: int = 0
    permanent_employees: int = 0
    contractual_employees: int = 0
    women_employees: int = 0
    women_percentage: float = 0.0
    pwd_employees: int = 0
    fatalities: int = 0
    ltifr: float = 0.0
    recordable_injuries: int = 0
    safety_training_hours: float = 0.0
    training_hours_per_employee: float = 0.0
    total_training_hours: float = 0.0
    employees_trained_percentage: float = 0.0
    new_hires: int = 0
    employee_turnover: int = 0
    turnover_rate: float = 0.0
    women_in_management: float = 0.0
    women_on_board: float = 0.0
    csr_spending: float = 0.0
    csr_percentage: float = 0.0
    beneficiaries_reached: int = 0
    child_labor_incidents: int = 0
    forced_labor_incidents: int = 0
    discrimination_incidents: int = 0
    customer_complaints: int = 0
    complaints_resolved: int = 0
    resolution_rate: float = 0.0
    data_breaches: int = 0


@dataclass
class GovernanceMetrics:
    """Governance metrics extracted from report"""
    board_size: int = 0
    independent_directors: int = 0
    independent_percentage: float = 0.0
    women_directors: int = 0
    women_board_percentage: float = 0.0
    board_meetings: int = 0
    average_attendance: float = 0.0
    audit_committee_meetings: int = 0
    nomination_committee_meetings: int = 0
    csr_committee_meetings: int = 0
    risk_committee_meetings: int = 0
    ethics_complaints: int = 0
    corruption_incidents: int = 0
    whistleblower_complaints: int = 0
    rpt_value: float = 0.0
    ceo_remuneration: float = 0.0
    median_remuneration: float = 0.0
    ceo_to_median_ratio: float = 0.0


@dataclass 
class BRSRExtractedData:
    """Complete BRSR extracted data structure"""
    company_name: str = ""
    cin: str = ""
    year: int = 0
    report_type: ReportType = ReportType.UNKNOWN
    sector: str = ""
    industry: str = ""
    registered_office: str = ""
    corporate_office: str = ""
    email: str = ""
    website: str = ""
    reporting_boundary: str = ""
    turnover: float = 0.0
    net_worth: float = 0.0
    environmental: EnvironmentalMetrics = field(default_factory=EnvironmentalMetrics)
    social: SocialMetrics = field(default_factory=SocialMetrics)
    governance: GovernanceMetrics = field(default_factory=GovernanceMetrics)
    extraction_time: datetime = field(default_factory=datetime.now)
    pages_processed: int = 0
    extraction_confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_esg_input(self) -> Dict:
        """Convert to ESG calculator input format"""
        return {
            'company_name': self.company_name,
            'industry': self.industry,
            'year': self.year,
            'carbon_emissions_intensity': self.environmental.emission_intensity if self.environmental.emission_intensity > 0 else 50,
            'total_ghg_emissions': self.environmental.total_ghg_emissions,
            'scope1_emissions': self.environmental.scope1_emissions,
            'scope2_emissions': self.environmental.scope2_emissions,
            'energy_consumption_intensity': self.environmental.energy_intensity if self.environmental.energy_intensity > 0 else 200,
            'renewable_energy_percentage': self.environmental.renewable_energy_percentage if self.environmental.renewable_energy_percentage > 0 else 25,
            'water_consumption_intensity': self.environmental.water_intensity if self.environmental.water_intensity > 0 else 300,
            'waste_recycling_rate': self.environmental.waste_recycling_percentage if self.environmental.waste_recycling_percentage > 0 else 65,
            'ltifr': self.social.ltifr if self.social.ltifr > 0 else 0.5,
            'employee_turnover_rate': self.social.turnover_rate if self.social.turnover_rate > 0 else 15,
            'women_workforce_percentage': self.social.women_percentage if self.social.women_percentage > 0 else 25,
            'training_hours_per_employee': self.social.training_hours_per_employee if self.social.training_hours_per_employee > 0 else 20,
            'csr_spending_percentage': self.social.csr_percentage if self.social.csr_percentage > 0 else 2,
            'customer_complaints_resolved': self.social.resolution_rate if self.social.resolution_rate > 0 else 95,
            'data_breaches': self.social.data_breaches,
            'independent_directors_percentage': self.governance.independent_percentage if self.governance.independent_percentage > 0 else 50,
            'women_directors_percentage': self.governance.women_board_percentage if self.governance.women_board_percentage > 0 else 17,
            'board_meetings': self.governance.board_meetings if self.governance.board_meetings > 0 else 6,
            'audit_committee_meetings': self.governance.audit_committee_meetings if self.governance.audit_committee_meetings > 0 else 4,
            'ceo_median_pay_ratio': self.governance.ceo_to_median_ratio if self.governance.ceo_to_median_ratio > 0 else 100,
        }


# ============================================================================
# CONSTANTS
# ============================================================================

CATEGORY_WEIGHTS = {'Environmental': 0.35, 'Social': 0.35, 'Governance': 0.30}

INDUSTRY_ADJUSTMENTS = {
    'Oil & Gas': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Oil Exploration': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Refineries': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Power': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Power Generation': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Iron & Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Cement': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Mining': {'environmental': 1.3, 'social': 1.0, 'governance': 0.7},
    'Coal': {'environmental': 1.3, 'social': 1.0, 'governance': 0.7},
    'Banks': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Private Banks': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Public Sector Banks': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Financial Services': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'NBFC': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'IT Services': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'IT - Software': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'Computers - Software': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'IT Consulting': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'Pharmaceuticals': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Healthcare': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'FMCG': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Consumer Goods': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Automobiles': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Auto': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Auto Components': {'environmental': 1.1, 'social': 0.9, 'governance': 1.0},
    'Telecom': {'environmental': 0.9, 'social': 1.0, 'governance': 1.1},
    'Telecommunications': {'environmental': 0.9, 'social': 1.0, 'governance': 1.1},
    'Real Estate': {'environmental': 1.1, 'social': 0.9, 'governance': 1.0},
    'Construction': {'environmental': 1.1, 'social': 1.0, 'governance': 0.9},
    'Infrastructure': {'environmental': 1.1, 'social': 1.0, 'governance': 0.9},
    'Default': {'environmental': 1.0, 'social': 1.0, 'governance': 1.0}
}

ENVIRONMENTAL_BENCHMARKS = {
    'Oil & Gas': {'carbon': 150, 'energy': 500, 'water': 1000, 'renewable': 10, 'waste': 60},
    'Oil Exploration': {'carbon': 150, 'energy': 500, 'water': 1000, 'renewable': 10, 'waste': 60},
    'Refineries': {'carbon': 180, 'energy': 600, 'water': 1200, 'renewable': 8, 'waste': 55},
    'Power': {'carbon': 200, 'energy': 800, 'water': 2000, 'renewable': 25, 'waste': 50},
    'Power Generation': {'carbon': 200, 'energy': 800, 'water': 2000, 'renewable': 25, 'waste': 50},
    'IT Services': {'carbon': 5, 'energy': 50, 'water': 50, 'renewable': 50, 'waste': 80},
    'IT - Software': {'carbon': 5, 'energy': 50, 'water': 50, 'renewable': 50, 'waste': 80},
    'Computers - Software': {'carbon': 5, 'energy': 50, 'water': 50, 'renewable': 50, 'waste': 80},
    'Banks': {'carbon': 2, 'energy': 30, 'water': 30, 'renewable': 40, 'waste': 85},
    'Private Banks': {'carbon': 2, 'energy': 30, 'water': 30, 'renewable': 40, 'waste': 85},
    'Financial Services': {'carbon': 2, 'energy': 30, 'water': 30, 'renewable': 40, 'waste': 85},
    'Pharmaceuticals': {'carbon': 30, 'energy': 150, 'water': 500, 'renewable': 30, 'waste': 70},
    'Healthcare': {'carbon': 25, 'energy': 120, 'water': 400, 'renewable': 30, 'waste': 70},
    'Steel': {'carbon': 180, 'energy': 700, 'water': 1500, 'renewable': 15, 'waste': 65},
    'Iron & Steel': {'carbon': 180, 'energy': 700, 'water': 1500, 'renewable': 15, 'waste': 65},
    'Cement': {'carbon': 150, 'energy': 500, 'water': 800, 'renewable': 20, 'waste': 70},
    'FMCG': {'carbon': 20, 'energy': 100, 'water': 300, 'renewable': 35, 'waste': 75},
    'Consumer Goods': {'carbon': 20, 'energy': 100, 'water': 300, 'renewable': 35, 'waste': 75},
    'Automobiles': {'carbon': 40, 'energy': 200, 'water': 400, 'renewable': 25, 'waste': 80},
    'Auto': {'carbon': 40, 'energy': 200, 'water': 400, 'renewable': 25, 'waste': 80},
    'Telecom': {'carbon': 10, 'energy': 80, 'water': 60, 'renewable': 40, 'waste': 75},
    'Construction': {'carbon': 50, 'energy': 250, 'water': 500, 'renewable': 20, 'waste': 60},
    'Default': {'carbon': 50, 'energy': 200, 'water': 300, 'renewable': 25, 'waste': 65}
}

# NIFTY 50 Companies with details
NIFTY50_COMPANIES = {
    'RELIANCE': {'name': 'Reliance Industries Ltd', 'sector': 'Energy', 'industry': 'Oil & Gas'},
    'TCS': {'name': 'Tata Consultancy Services Ltd', 'sector': 'IT', 'industry': 'IT Services'},
    'HDFCBANK': {'name': 'HDFC Bank Ltd', 'sector': 'Financial', 'industry': 'Private Banks'},
    'INFY': {'name': 'Infosys Ltd', 'sector': 'IT', 'industry': 'IT Services'},
    'ICICIBANK': {'name': 'ICICI Bank Ltd', 'sector': 'Financial', 'industry': 'Private Banks'},
    'HINDUNILVR': {'name': 'Hindustan Unilever Ltd', 'sector': 'Consumer', 'industry': 'FMCG'},
    'ITC': {'name': 'ITC Ltd', 'sector': 'Consumer', 'industry': 'FMCG'},
    'SBIN': {'name': 'State Bank of India', 'sector': 'Financial', 'industry': 'Public Sector Banks'},
    'BHARTIARTL': {'name': 'Bharti Airtel Ltd', 'sector': 'Telecom', 'industry': 'Telecom'},
    'KOTAKBANK': {'name': 'Kotak Mahindra Bank Ltd', 'sector': 'Financial', 'industry': 'Private Banks'},
    'WIPRO': {'name': 'Wipro Ltd', 'sector': 'IT', 'industry': 'IT Services'},
    'LT': {'name': 'Larsen & Toubro Ltd', 'sector': 'Infrastructure', 'industry': 'Construction'},
    'AXISBANK': {'name': 'Axis Bank Ltd', 'sector': 'Financial', 'industry': 'Private Banks'},
    'ASIANPAINT': {'name': 'Asian Paints Ltd', 'sector': 'Consumer', 'industry': 'Consumer Goods'},
    'MARUTI': {'name': 'Maruti Suzuki India Ltd', 'sector': 'Auto', 'industry': 'Automobiles'},
    'TATASTEEL': {'name': 'Tata Steel Ltd', 'sector': 'Materials', 'industry': 'Steel'},
    'NTPC': {'name': 'NTPC Ltd', 'sector': 'Utilities', 'industry': 'Power'},
    'POWERGRID': {'name': 'Power Grid Corporation', 'sector': 'Utilities', 'industry': 'Power'},
    'SUNPHARMA': {'name': 'Sun Pharmaceutical Industries', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals'},
    'DRREDDY': {'name': 'Dr. Reddys Laboratories', 'sector': 'Healthcare', 'industry': 'Pharmaceuticals'},
    'ONGC': {'name': 'Oil & Natural Gas Corporation', 'sector': 'Energy', 'industry': 'Oil Exploration'},
    'COALINDIA': {'name': 'Coal India Ltd', 'sector': 'Energy', 'industry': 'Mining'},
    'TATAMOTORS': {'name': 'Tata Motors Ltd', 'sector': 'Auto', 'industry': 'Automobiles'},
    'M&M': {'name': 'Mahindra & Mahindra Ltd', 'sector': 'Auto', 'industry': 'Automobiles'},
    'HCLTECH': {'name': 'HCL Technologies Ltd', 'sector': 'IT', 'industry': 'IT Services'},
    'TECHM': {'name': 'Tech Mahindra Ltd', 'sector': 'IT', 'industry': 'IT Services'},
    'BAJFINANCE': {'name': 'Bajaj Finance Ltd', 'sector': 'Financial', 'industry': 'NBFC'},
    'TITAN': {'name': 'Titan Company Ltd', 'sector': 'Consumer', 'industry': 'Consumer Goods'},
    'ULTRACEMCO': {'name': 'UltraTech Cement Ltd', 'sector': 'Materials', 'industry': 'Cement'},
    'NESTLEIND': {'name': 'Nestle India Ltd', 'sector': 'Consumer', 'industry': 'FMCG'},
}

NIFTY50_SYMBOLS = list(NIFTY50_COMPANIES.keys())


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
# REAL-TIME DATA FETCHER
# ============================================================================

class NSEDataFetcher:
    """Fetch real-time data from NSE India"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.nseindia.com"
        self.api_url = f"{self.base_url}/api"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/',
        }
        self.session.headers.update(self.headers)
        self._initialized = False
        self._rate_limit_delay = 0.5
        self._last_request_time = 0
    
    def _initialize_session(self):
        """Initialize session with NSE cookies"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                self._initialized = True
                return True
        except Exception as e:
            logger.warning(f"NSE session init warning: {e}")
        return False
    
    def _rate_limit(self):
        """Implement rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        self._rate_limit()
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 401:
                    self._initialize_session()
                    time.sleep(1)
                elif response.status_code == 429:
                    time.sleep(5 * (attempt + 1))
            except requests.exceptions.Timeout:
                time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error: {e}")
                time.sleep(1)
        
        return None
    
    def get_company_info(self, symbol: str) -> Optional[CompanyData]:
        """Fetch comprehensive company information"""
        if not self._initialized:
            self._initialize_session()
        
        try:
            url = f"{self.api_url}/quote-equity?symbol={symbol}"
            response = self._make_request(url)
            
            if not response:
                return None
            
            data = response.json()
            
            info = data.get('info', {})
            metadata = data.get('metadata', {})
            price_info = data.get('priceInfo', {})
            security_info = data.get('securityInfo', {})
            
            company = CompanyData(
                symbol=symbol,
                company_name=info.get('companyName', symbol),
                isin=metadata.get('isin', ''),
                series=metadata.get('series', 'EQ'),
                sector=metadata.get('sector', ''),
                industry=metadata.get('industry', ''),
                last_price=price_info.get('lastPrice', 0),
                change=price_info.get('change', 0),
                pchange=price_info.get('pChange', 0),
                open_price=price_info.get('open', 0),
                prev_close=price_info.get('previousClose', 0),
                market_cap=security_info.get('marketCap', 0),
                face_value=security_info.get('faceValue', 0),
                pe_ratio=metadata.get('pdSymbolPe', 0),
                data_source='NSE India',
                fetch_time=datetime.now()
            )
            
            week_hl = price_info.get('weekHighLow', {})
            company.week_high_52 = week_hl.get('max', 0)
            company.week_low_52 = week_hl.get('min', 0)
            
            intraday = price_info.get('intraDayHighLow', {})
            company.high = intraday.get('max', 0)
            company.low = intraday.get('min', 0)
            
            # Get trade info for shareholding
            trade_data = self.get_trade_info(symbol)
            if trade_data:
                company.promoter_holding = trade_data.get('promoter_holding', 0)
                company.public_holding = trade_data.get('public_holding', 0)
                company.fii_holding = trade_data.get('fii_holding', 0)
                company.dii_holding = trade_data.get('dii_holding', 0)
                company.pledged_percentage = trade_data.get('pledged', 0)
                company.volume = trade_data.get('volume', 0)
                company.value = trade_data.get('value', 0)
            
            # Calculate data quality
            filled_fields = sum(1 for v in company.to_dict().values() if v)
            total_fields = len(company.to_dict())
            company.data_quality = (filled_fields / total_fields) * 100
            
            return company
            
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None
    
    def get_trade_info(self, symbol: str) -> Optional[Dict]:
        """Fetch trade info and shareholding pattern"""
        try:
            url = f"{self.api_url}/quote-equity?symbol={symbol}&section=trade_info"
            response = self._make_request(url)
            
            if response:
                data = response.json()
                trade_info = data.get('tradeInfo', {})
                security_dp = data.get('securityWiseDP', {})
                
                return {
                    'volume': trade_info.get('totalTradedVolume', 0),
                    'value': trade_info.get('totalTradedValue', 0),
                    'market_cap': trade_info.get('totalMarketCap', 0),
                    'free_float_market_cap': trade_info.get('ffmc', 0),
                    'promoter_holding': security_dp.get('promoterAndPromoterGroup', 0),
                    'public_holding': security_dp.get('public', 0),
                    'pledged': security_dp.get('pledged', 0),
                    'fii_holding': security_dp.get('fii', 0),
                    'dii_holding': security_dp.get('dii', 0),
                }
            return None
        except Exception as e:
            logger.warning(f"Trade info error for {symbol}: {e}")
            return None


class YahooFinanceFetcher:
    """Fetch data from Yahoo Finance as backup"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.quote_url = "https://query1.finance.yahoo.com/v7/finance/quote"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        self.session.headers.update(self.headers)
    
    def _get_yahoo_symbol(self, symbol: str) -> str:
        return f"{symbol}.NS"
    
    def get_company_info(self, symbol: str) -> Optional[CompanyData]:
        """Fetch company data from Yahoo Finance"""
        yahoo_symbol = self._get_yahoo_symbol(symbol)
        
        try:
            url = f"{self.quote_url}?symbols={yahoo_symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            result = data.get('quoteResponse', {}).get('result', [])
            
            if not result:
                return None
            
            quote = result[0]
            
            company = CompanyData(
                symbol=symbol,
                company_name=quote.get('longName', symbol),
                sector=quote.get('sector', ''),
                industry=quote.get('industry', ''),
                last_price=quote.get('regularMarketPrice', 0),
                change=quote.get('regularMarketChange', 0),
                pchange=quote.get('regularMarketChangePercent', 0),
                prev_close=quote.get('regularMarketPreviousClose', 0),
                open_price=quote.get('regularMarketOpen', 0),
                high=quote.get('regularMarketDayHigh', 0),
                low=quote.get('regularMarketDayLow', 0),
                volume=quote.get('regularMarketVolume', 0),
                market_cap=quote.get('marketCap', 0) / 10000000 if quote.get('marketCap') else 0,
                week_high_52=quote.get('fiftyTwoWeekHigh', 0),
                week_low_52=quote.get('fiftyTwoWeekLow', 0),
                pe_ratio=quote.get('trailingPE', 0) or 0,
                pb_ratio=quote.get('priceToBook', 0) or 0,
                eps=quote.get('trailingEps', 0) or 0,
                dividend_yield=(quote.get('dividendYield', 0) or 0) * 100,
                book_value=quote.get('bookValue', 0) or 0,
                data_source='Yahoo Finance',
                fetch_time=datetime.now()
            )
            
            return company
            
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None


class RealTimeDataAggregator:
    """Unified interface to fetch data from multiple sources"""
    
    def __init__(self):
        self.nse = NSEDataFetcher()
        self.yahoo = YahooFinanceFetcher()
    
    def get_company_data(self, symbol: str, preferred_source: str = 'NSE') -> Optional[CompanyData]:
        """Fetch company data with automatic fallback"""
        # Try NSE first
        try:
            data = self.nse.get_company_info(symbol)
            if data and data.company_name:
                return data
        except Exception as e:
            logger.warning(f"NSE failed for {symbol}: {e}")
        
        # Fallback to Yahoo
        try:
            data = self.yahoo.get_company_info(symbol)
            if data and data.company_name:
                return data
        except Exception as e:
            logger.warning(f"Yahoo failed for {symbol}: {e}")
        
        return None


# ============================================================================
# PDF REPORT PARSER
# ============================================================================

class ExtractionPatterns:
    """Regex patterns for extracting ESG metrics"""
    
    NUMBER = r'[\d,]+\.?\d*'
    PERCENTAGE = r'[\d,]+\.?\d*\s*%'
    
    ENERGY_PATTERNS = {
        'total_energy': [
            rf'total\s+energy\s+(?:consumption|consumed)[:\s]*({NUMBER})\s*(?:GJ|TJ|MWh|kWh)',
            rf'energy\s+consumption[:\s]*({NUMBER})\s*(?:GJ|TJ|MWh)',
        ],
        'renewable_energy': [
            rf'renewable\s+energy[:\s]*({NUMBER})\s*(?:GJ|TJ|MWh|%)',
            rf'({NUMBER})\s*(?:GJ|%)?\s*(?:from\s+)?renewable',
        ],
    }
    
    EMISSION_PATTERNS = {
        'scope1': [
            rf'scope\s*1[:\s]*({NUMBER})\s*(?:tCO2e?|MT|tonnes)',
            rf'direct\s+emissions?[:\s]*({NUMBER})\s*(?:tCO2e?|MT)',
        ],
        'scope2': [
            rf'scope\s*2[:\s]*({NUMBER})\s*(?:tCO2e?|MT|tonnes)',
            rf'indirect\s+emissions?[:\s]*({NUMBER})\s*(?:tCO2e?|MT)',
        ],
        'total_ghg': [
            rf'total\s+(?:ghg|greenhouse\s+gas)\s+emissions?[:\s]*({NUMBER})',
        ],
    }
    
    WATER_PATTERNS = {
        'total_water': [
            rf'total\s+water\s+(?:withdrawal|consumption|usage)[:\s]*({NUMBER})\s*(?:KL|ML|m3|kilolitres)',
        ],
        'water_recycled': [
            rf'water\s+recycled[:\s]*({NUMBER})\s*(?:KL|ML|%)',
        ],
    }
    
    WASTE_PATTERNS = {
        'total_waste': [
            rf'total\s+waste\s+(?:generated|produced)[:\s]*({NUMBER})\s*(?:MT|tonnes|kg)',
        ],
        'waste_recycled': [
            rf'waste\s+(?:recycled|diverted)[:\s]*({NUMBER})\s*(?:MT|%)',
            rf'recycling\s+rate[:\s]*({NUMBER})\s*%',
        ],
    }
    
    EMPLOYEE_PATTERNS = {
        'total_employees': [
            rf'total\s+(?:number\s+of\s+)?employees?[:\s]*({NUMBER})',
            rf'total\s+workforce[:\s]*({NUMBER})',
            rf'headcount[:\s]*({NUMBER})',
        ],
        'women_percentage': [
            rf'women[:\s]*({NUMBER})\s*%',
            rf'female\s+representation[:\s]*({NUMBER})\s*%',
        ],
    }
    
    SAFETY_PATTERNS = {
        'ltifr': [
            rf'ltifr[:\s]*({NUMBER})',
            rf'lost\s+time\s+injury\s+frequency\s+rate[:\s]*({NUMBER})',
        ],
        'fatalities': [
            rf'fatalities?[:\s]*({NUMBER})',
            rf'zero\s+fatalities?',
        ],
    }
    
    TRAINING_PATTERNS = {
        'training_hours': [
            rf'training\s+hours?[:\s]*({NUMBER})',
            rf'average\s+training[:\s]*({NUMBER})\s*hours?',
        ],
    }
    
    CSR_PATTERNS = {
        'csr_spending': [
            rf'csr\s+(?:expenditure|spending|spend)[:\s]*(?:₹|Rs\.?)?\s*({NUMBER})\s*(?:Cr|Crore|Lakh)?',
        ],
    }
    
    BOARD_PATTERNS = {
        'board_size': [
            rf'(?:board\s+)?(?:comprises?|consists?\s+of)[:\s]*({NUMBER})\s*directors?',
            rf'board\s+(?:strength|size)[:\s]*({NUMBER})',
        ],
        'independent_directors': [
            rf'independent\s+directors?[:\s]*({NUMBER})',
        ],
        'board_meetings': [
            rf'board\s+(?:met|meetings?)[:\s]*({NUMBER})\s*times?',
            rf'({NUMBER})\s*board\s+meetings?',
        ],
    }
    
    COMPANY_PATTERNS = {
        'company_name': [
            r'(?:name\s+of\s+(?:the\s+)?(?:listed\s+)?entity|company\s+name)[:\s]*([A-Za-z][A-Za-z0-9\s&\.\-]+(?:Ltd|Limited|Corporation|Corp|Inc)?)',
        ],
        'cin': [
            r'(?:cin|corporate\s+identity\s+number)[:\s]*([A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})',
        ],
    }


class PDFTextExtractor:
    """Extract text from PDF files"""
    
    @staticmethod
    def extract_with_pymupdf(pdf_path: str) -> Tuple[str, int]:
        """Extract text using PyMuPDF"""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not installed")
        
        text_parts = []
        page_count = 0
        
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        
        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text("text")
            text_parts.append(f"\n[PAGE {page_num + 1}]\n{text}")
        
        doc.close()
        
        return "\n".join(text_parts), page_count
    
    @staticmethod
    def extract_with_pdfplumber(pdf_path: str) -> Tuple[str, int]:
        """Extract text using pdfplumber"""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not installed")
        
        text_parts = []
        page_count = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                text_parts.append(f"\n[PAGE {i + 1}]\n{text}")
                
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        table_text = "\n".join(["\t".join([str(cell or '') for cell in row]) for row in table])
                        text_parts.append(f"\n[TABLE]\n{table_text}")
        
        return "\n".join(text_parts), page_count
    
    @classmethod
    def extract(cls, pdf_path: str) -> Tuple[str, int]:
        """Extract text using best available method"""
        if PYMUPDF_AVAILABLE:
            try:
                return cls.extract_with_pymupdf(pdf_path)
            except Exception:
                pass
        
        if PDFPLUMBER_AVAILABLE:
            return cls.extract_with_pdfplumber(pdf_path)
        
        raise ImportError("No PDF library available. Install PyMuPDF or pdfplumber.")


class BRSRReportParser:
    """Parse BRSR and Annual Reports to extract ESG metrics"""
    
    def __init__(self):
        self.patterns = ExtractionPatterns()
        self.extracted_data = None
    
    def _clean_number(self, value: str) -> float:
        """Clean and convert extracted number string to float"""
        if not value:
            return 0.0
        
        if 'zero' in str(value).lower() or 'nil' in str(value).lower():
            return 0.0
        
        cleaned = re.sub(r'[,\s]', '', str(value))
        cleaned = cleaned.replace('%', '')
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def _extract_metric(self, text: str, patterns: List[str], 
                       metric_name: str, category: str) -> Optional[float]:
        """Extract a metric using multiple regex patterns"""
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    value_str = match.group(1) if match.groups() else match.group(0)
                    value = self._clean_number(value_str)
                    
                    if value > 0:
                        return value
            except Exception:
                continue
        
        return None
    
    def _identify_report_type(self, text: str) -> ReportType:
        """Identify the type of report"""
        text_lower = text.lower()
        
        if 'business responsibility and sustainability' in text_lower or 'brsr' in text_lower:
            return ReportType.BRSR
        elif 'sustainability report' in text_lower:
            return ReportType.SUSTAINABILITY
        elif 'integrated report' in text_lower:
            return ReportType.INTEGRATED
        elif 'csr report' in text_lower:
            return ReportType.CSR
        elif 'annual report' in text_lower:
            return ReportType.ANNUAL
        else:
            return ReportType.UNKNOWN
    
    def _extract_environmental_metrics(self, text: str) -> EnvironmentalMetrics:
        """Extract all environmental metrics"""
        metrics = EnvironmentalMetrics()
        
        # Energy
        for metric_name, patterns in self.patterns.ENERGY_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Environmental')
            if result:
                if metric_name == 'total_energy':
                    metrics.total_energy_consumption = result
                elif metric_name == 'renewable_energy':
                    if result <= 100:
                        metrics.renewable_energy_percentage = result
                    else:
                        metrics.renewable_energy = result
        
        if metrics.renewable_energy > 0 and metrics.total_energy_consumption > 0:
            metrics.renewable_energy_percentage = (metrics.renewable_energy / metrics.total_energy_consumption) * 100
        
        # Emissions
        for metric_name, patterns in self.patterns.EMISSION_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Environmental')
            if result:
                if metric_name == 'scope1':
                    metrics.scope1_emissions = result
                elif metric_name == 'scope2':
                    metrics.scope2_emissions = result
                elif metric_name == 'total_ghg':
                    metrics.total_ghg_emissions = result
        
        if metrics.total_ghg_emissions == 0:
            metrics.total_ghg_emissions = metrics.scope1_emissions + metrics.scope2_emissions
        
        # Water
        for metric_name, patterns in self.patterns.WATER_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Environmental')
            if result:
                if metric_name == 'total_water':
                    metrics.total_water_withdrawal = result
                elif metric_name == 'water_recycled':
                    if result <= 100:
                        metrics.water_recycling_percentage = result
                    else:
                        metrics.water_recycled = result
        
        # Waste
        for metric_name, patterns in self.patterns.WASTE_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Environmental')
            if result:
                if metric_name == 'total_waste':
                    metrics.total_waste_generated = result
                elif metric_name == 'waste_recycled':
                    if result <= 100:
                        metrics.waste_recycling_percentage = result
                    else:
                        metrics.waste_recycled = result
        
        return metrics
    
    def _extract_social_metrics(self, text: str) -> SocialMetrics:
        """Extract all social metrics"""
        metrics = SocialMetrics()
        
        # Employees
        for metric_name, patterns in self.patterns.EMPLOYEE_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Social')
            if result:
                if metric_name == 'total_employees':
                    metrics.total_employees = int(result)
                elif metric_name == 'women_percentage':
                    metrics.women_percentage = result
        
        # Safety
        for metric_name, patterns in self.patterns.SAFETY_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Social')
            if result:
                if metric_name == 'ltifr':
                    metrics.ltifr = result
                elif metric_name == 'fatalities':
                    metrics.fatalities = int(result)
        
        if 'zero fatalities' in text.lower() or 'no fatalities' in text.lower():
            metrics.fatalities = 0
        
        # Training
        for metric_name, patterns in self.patterns.TRAINING_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Social')
            if result:
                if result < 100:
                    metrics.training_hours_per_employee = result
                else:
                    metrics.total_training_hours = result
        
        if metrics.training_hours_per_employee == 0 and metrics.total_training_hours > 0 and metrics.total_employees > 0:
            metrics.training_hours_per_employee = metrics.total_training_hours / metrics.total_employees
        
        # CSR
        for metric_name, patterns in self.patterns.CSR_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Social')
            if result:
                metrics.csr_spending = result
        
        return metrics
    
    def _extract_governance_metrics(self, text: str) -> GovernanceMetrics:
        """Extract all governance metrics"""
        metrics = GovernanceMetrics()
        
        for metric_name, patterns in self.patterns.BOARD_PATTERNS.items():
            result = self._extract_metric(text, patterns, metric_name, 'Governance')
            if result:
                if metric_name == 'board_size':
                    metrics.board_size = int(result)
                elif metric_name == 'independent_directors':
                    metrics.independent_directors = int(result)
                elif metric_name == 'board_meetings':
                    metrics.board_meetings = int(result)
        
        if metrics.board_size > 0 and metrics.independent_directors > 0:
            metrics.independent_percentage = (metrics.independent_directors / metrics.board_size) * 100
        
        return metrics
    
    def parse(self, pdf_path: str) -> BRSRExtractedData:
        """Parse a PDF report and extract ESG metrics"""
        text, page_count = PDFTextExtractor.extract(pdf_path)
        
        result = BRSRExtractedData()
        result.pages_processed = page_count
        
        result.report_type = self._identify_report_type(text)
        
        # Extract company info
        for pattern in self.patterns.COMPANY_PATTERNS.get('company_name', []):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.company_name = match.group(1).strip() if match.groups() else ''
                break
        
        for pattern in self.patterns.COMPANY_PATTERNS.get('cin', []):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.cin = match.group(1).strip() if match.groups() else ''
                break
        
        # Extract year
        year_match = re.search(r'(?:FY|financial\s+year)[:\s]*(\d{4})[-–]?(\d{2,4})?', text, re.IGNORECASE)
        if year_match:
            result.year = int(year_match.group(1))
        else:
            result.year = datetime.now().year
        
        # Extract all metrics
        result.environmental = self._extract_environmental_metrics(text)
        result.social = self._extract_social_metrics(text)
        result.governance = self._extract_governance_metrics(text)
        
        # Calculate confidence
        total_fields = 0
        filled_fields = 0
        
        for obj in [result.environmental, result.social, result.governance]:
            for key, value in asdict(obj).items():
                total_fields += 1
                if value and value != 0:
                    filled_fields += 1
        
        result.extraction_confidence = (filled_fields / total_fields) * 100 if total_fields > 0 else 0
        result.extraction_time = datetime.now()
        
        self.extracted_data = result
        return result
    
    def parse_from_bytes(self, pdf_bytes: bytes, filename: str = "uploaded.pdf") -> BRSRExtractedData:
        """Parse PDF from bytes (for Streamlit file uploads)"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name
        
        try:
            result = self.parse(tmp_path)
            return result
        finally:
            os.unlink(tmp_path)


# ============================================================================
# ESG CALCULATION FUNCTIONS
# ============================================================================

def get_benchmarks(industry: str) -> Dict:
    """Get industry benchmarks"""
    for key in ENVIRONMENTAL_BENCHMARKS:
        if key.lower() in industry.lower() or industry.lower() in key.lower():
            return ENVIRONMENTAL_BENCHMARKS[key]
    return ENVIRONMENTAL_BENCHMARKS['Default']


def get_industry_adjustments(industry: str) -> Dict:
    """Get industry adjustment factors"""
    for key in INDUSTRY_ADJUSTMENTS:
        if key.lower() in industry.lower() or industry.lower() in key.lower():
            return INDUSTRY_ADJUSTMENTS[key]
    return INDUSTRY_ADJUSTMENTS['Default']


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
    
    # Biodiversity
    bio = data.get('biodiversity_initiatives', 50)
    metrics['Biodiversity'] = {'value': bio, 'score': min(100, bio), 'unit': 'score', 'weight': 0.05}
    
    # Hazardous Waste
    hazardous = data.get('hazardous_waste_compliance', 90)
    metrics['Hazardous Waste'] = {'value': hazardous, 'score': min(100, hazardous), 'unit': '%', 'weight': 0.05}
    
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
    
    # Fair Wages
    fair_wages = data.get('fair_wages_compliance', 90)
    metrics['Fair Wages'] = {'value': fair_wages, 'score': min(100, fair_wages), 'unit': '%', 'weight': 0.10}
    
    # CSR
    csr = data.get('csr_spending_percentage', 2)
    score_csr = min(100, csr * 40)
    metrics['CSR Spending'] = {'value': csr, 'score': score_csr, 'unit': '%', 'weight': 0.08}
    
    # Human Rights
    hr = data.get('human_rights_compliance', 90)
    metrics['Human Rights'] = {'value': hr, 'score': min(100, hr), 'unit': '%', 'weight': 0.10}
    
    # Customer
    customer = data.get('customer_complaints_resolved', 95)
    metrics['Customer Satisfaction'] = {'value': customer, 'score': min(100, customer), 'unit': '%', 'weight': 0.08}
    
    # Data Privacy
    breaches = data.get('data_breaches', 0)
    score_p = max(0, 100 - breaches * 20)
    metrics['Data Privacy'] = {'value': breaches, 'score': score_p, 'unit': 'incidents', 'weight': 0.10}
    
    # Labor Practices
    labor = data.get('labor_practices_compliance', 95)
    metrics['Labor Practices'] = {'value': labor, 'score': min(100, labor), 'unit': '%', 'weight': 0.07}
    
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
    
    # Shareholder Rights
    shareholder = data.get('shareholder_rights', 80)
    metrics['Shareholder Rights'] = {'value': shareholder, 'score': min(100, shareholder), 'unit': 'score', 'weight': 0.10}
    
    # Ethics
    ethics = data.get('ethics_anti_corruption', 90)
    metrics['Ethics'] = {'value': ethics, 'score': min(100, ethics), 'unit': '%', 'weight': 0.12}
    
    # Risk Management
    risk = data.get('risk_management', 80)
    metrics['Risk Management'] = {'value': risk, 'score': min(100, risk), 'unit': 'score', 'weight': 0.10}
    
    # Tax Transparency
    tax = data.get('tax_transparency', 70)
    metrics['Tax Transparency'] = {'value': tax, 'score': min(100, tax), 'unit': '%', 'weight': 0.08}
    
    # RPT Compliance
    rpt = data.get('rpt_compliance', 90)
    metrics['RPT Compliance'] = {'value': rpt, 'score': min(100, rpt), 'unit': '%', 'weight': 0.06}
    
    # Sustainability Committee
    sus = data.get('sustainability_committee', 50)
    metrics['Sustainability Committee'] = {'value': sus, 'score': min(100, sus), 'unit': 'score', 'weight': 0.05}
    
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    return total, metrics


def calculate_overall_esg(env: float, social: float, gov: float, industry: str = 'Default') -> float:
    """Calculate overall ESG score with industry adjustments"""
    adj = get_industry_adjustments(industry)
    
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


def generate_simulated_esg_data(symbol: str, industry: str = 'Default') -> Dict:
    """Generate simulated ESG data based on industry"""
    np.random.seed(hash(symbol) % 2**32)
    
    benchmarks = get_benchmarks(industry)
    
    return {
        'carbon_emissions_intensity': benchmarks['carbon'] * np.random.uniform(0.7, 1.3),
        'energy_consumption_intensity': benchmarks['energy'] * np.random.uniform(0.7, 1.3),
        'renewable_energy_percentage': min(100, benchmarks['renewable'] * np.random.uniform(0.5, 1.5)),
        'water_consumption_intensity': benchmarks['water'] * np.random.uniform(0.7, 1.3),
        'waste_recycling_rate': min(100, benchmarks['waste'] * np.random.uniform(0.8, 1.2)),
        'environmental_compliance': np.random.uniform(85, 100),
        'climate_risk_disclosure': np.random.uniform(40, 90),
        'biodiversity_initiatives': np.random.uniform(30, 80),
        'hazardous_waste_compliance': np.random.uniform(80, 100),
        'ltifr': np.random.uniform(0.2, 0.8),
        'employee_turnover_rate': np.random.uniform(8, 25),
        'women_workforce_percentage': np.random.uniform(15, 40),
        'training_hours_per_employee': np.random.uniform(15, 50),
        'fair_wages_compliance': np.random.uniform(85, 100),
        'csr_spending_percentage': np.random.uniform(1.5, 3.0),
        'human_rights_compliance': np.random.uniform(85, 100),
        'customer_complaints_resolved': np.random.uniform(85, 99),
        'data_breaches': np.random.choice([0, 0, 0, 1, 2]),
        'labor_practices_compliance': np.random.uniform(85, 100),
        'independent_directors_percentage': np.random.uniform(45, 70),
        'women_directors_percentage': np.random.uniform(15, 35),
        'audit_committee_meetings': np.random.randint(4, 8),
        'ceo_median_pay_ratio': np.random.uniform(50, 200),
        'shareholder_rights': np.random.uniform(60, 95),
        'ethics_anti_corruption': np.random.uniform(80, 100),
        'risk_management': np.random.uniform(60, 95),
        'tax_transparency': np.random.uniform(50, 90),
        'rpt_compliance': np.random.uniform(80, 100),
        'sustainability_committee': np.random.uniform(40, 90),
    }


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
        delta={'reference': 50, 'increasing': {'color': '#27ae60'}, 'decreasing': {'color': '#e74c3c'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.8},
            'steps': [
                {'range': [0, 35], 'color': 'rgba(192, 57, 43, 0.2)'},
                {'range': [35, 50], 'color': 'rgba(231, 76, 60, 0.2)'},
                {'range': [50, 65], 'color': 'rgba(243, 156, 18, 0.2)'},
                {'range': [65, 80], 'color': 'rgba(46, 204, 113, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(39, 174, 96, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 2},
                'thickness': 0.75,
                'value': 50
            }
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
        name='Benchmark (50)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 100], showticklabels=True, ticksuffix=''),
        ),
        showlegend=True,
        height=400,
        margin=dict(l=80, r=80, t=40, b=40)
    )
    
    return fig


def create_metrics_bar(metrics: Dict, title: str) -> go.Figure:
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
    
    fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="Benchmark")
    fig.add_vline(x=70, line_dash="dash", line_color="green", annotation_text="Good")
    
    fig.update_layout(
        title=title,
        xaxis_title="Score",
        xaxis=dict(range=[0, 110]),
        height=50 + len(names) * 40,
        margin=dict(l=150, r=50, t=50, b=30)
    )
    
    return fig


def create_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Create comparison bar chart"""
    fig = go.Figure()
    
    colors = {'Environmental': '#27ae60', 'Social': '#3498db', 'Governance': '#9b59b6'}
    
    for col in ['Environmental', 'Social', 'Governance']:
        if col in df.columns:
            fig.add_trace(go.Bar(
                name=col,
                x=df['Symbol'],
                y=df[col],
                marker_color=colors.get(col, '#95a5a6'),
                text=df[col].round(1),
                textposition='outside'
            ))
    
    if 'Overall' in df.columns:
        fig.add_trace(go.Scatter(
            name='Overall ESG',
            x=df['Symbol'],
            y=df['Overall'],
            mode='lines+markers',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=10)
        ))
    
    fig.update_layout(
        barmode='group',
        xaxis_title="Company",
        yaxis_title="Score",
        yaxis=dict(range=[0, 110]),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    return fig


# ============================================================================
# CACHED DATA FUNCTIONS
# ============================================================================

@st.cache_data(ttl=300)
def fetch_live_company_data(symbol: str) -> Optional[Dict]:
    """Fetch live data from NSE/Yahoo with caching"""
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
        logger.error(f"Error fetching data: {e}")
    
    return None


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
         "📝 Manual Input", "🔍 Compare Companies", "📋 Full Report"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 Data Sources")
    st.sidebar.markdown(f"""
    - **Real-Time API**: ✅ Available
    - **PDF Parser**: {'✅ Available' if PDF_PARSER_AVAILABLE else '❌ Install PyMuPDF/pdfplumber'}
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.markdown("""
    ESG scoring based on **SEBI BRSR Framework** with:
    - 29 ESG metrics
    - Industry-specific benchmarks
    - Real-time data integration
    - PDF report parsing
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
                <p>Real-time stock data from NSE/Yahoo including market cap, shareholding patterns, and corporate info.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>📄 Report Upload</h4>
                <p>Upload Annual Reports or BRSR PDFs to automatically extract ESG metrics using AI pattern matching.</p>
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
        st.markdown("### 🚀 Quick ESG Analysis")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            quick_symbol = st.selectbox(
                "Select a NIFTY 50 company",
                NIFTY50_SYMBOLS,
                index=0,
                format_func=lambda x: f"{x} - {NIFTY50_COMPANIES.get(x, {}).get('name', x)}"
            )
        
        with col2:
            st.markdown("")
            st.markdown("")
            analyze_btn = st.button("📊 Analyze", type="primary", use_container_width=True)
        
        if analyze_btn:
            company_info = NIFTY50_COMPANIES.get(quick_symbol, {})
            industry = company_info.get('industry', 'Default')
            
            with st.spinner(f"Analyzing {quick_symbol}..."):
                # Try to get live data
                live_data = fetch_live_company_data(quick_symbol)
                
                if live_data and live_data.get('industry'):
                    industry = live_data.get('industry')
                
                # Generate ESG data
                esg_data = generate_simulated_esg_data(quick_symbol, industry)
                
                # Calculate scores
                env_score, env_metrics = calculate_environmental_score(esg_data, industry)
                social_score, social_metrics = calculate_social_score(esg_data)
                gov_score, gov_metrics = calculate_governance_score(esg_data)
                overall = calculate_overall_esg(env_score, social_score, gov_score, industry)
                risk = get_risk_level(overall)
            
            st.markdown("---")
            
            # Company header
            if live_data:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 20px; border-radius: 12px;'>
                    <h2 style='margin: 0;'>{live_data.get('company_name', quick_symbol)}</h2>
                    <p style='margin: 5px 0; color: #bdc3c7;'>
                        {quick_symbol} | {company_info.get('sector', 'N/A')} | {industry}
                    </p>
                    <p style='margin: 5px 0; color: #bdc3c7;'>
                        Market Cap: ₹{live_data.get('market_cap', 0):,.0f} Cr | 
                        LTP: ₹{live_data.get('last_price', 0):,.2f} ({live_data.get('pchange', 0):+.2f}%)
                    </p>
                    <span class="data-source-badge badge-live">{live_data.get('data_source', 'LIVE')}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 20px; border-radius: 12px;'>
                    <h2 style='margin: 0;'>{company_info.get('name', quick_symbol)}</h2>
                    <p style='margin: 5px 0; color: #bdc3c7;'>
                        {quick_symbol} | {company_info.get('sector', 'N/A')} | {industry}
                    </p>
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
            
            # Risk level banner
            risk_color = get_risk_color(risk)
            st.markdown(f"""
            <div style='text-align: center; padding: 20px;'>
                <span class="risk-{risk.lower()}" style='font-size: 1.3em; padding: 10px 30px;'>
                    ESG Risk Level: {risk} ({overall:.1f}/100)
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Radar chart and details
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(create_radar_chart(env_score, social_score, gov_score, quick_symbol), use_container_width=True)
            
            with col2:
                st.markdown("#### 📊 Score Breakdown")
                st.markdown(f"""
                | Category | Score | Status |
                |----------|-------|--------|
                | Environmental | {env_score:.1f} | {'🟢' if env_score >= 70 else '🟡' if env_score >= 50 else '🔴'} |
                | Social | {social_score:.1f} | {'🟢' if social_score >= 70 else '🟡' if social_score >= 50 else '🔴'} |
                | Governance | {gov_score:.1f} | {'🟢' if gov_score >= 70 else '🟡' if gov_score >= 50 else '🔴'} |
                | **Overall ESG** | **{overall:.1f}** | {'🟢' if overall >= 70 else '🟡' if overall >= 50 else '🔴'} |
                """)
                
                st.markdown("#### 🎯 Industry Adjustments")
                adj = get_industry_adjustments(industry)
                st.markdown(f"""
                - Environmental weight: {adj['environmental']:.1f}x
                - Social weight: {adj['social']:.1f}x
                - Governance weight: {adj['governance']:.1f}x
                """)
            
            # Detailed metrics
            with st.expander("📊 View Detailed Metrics"):
                tab1, tab2, tab3 = st.tabs(["🌍 Environmental", "👥 Social", "🏛️ Governance"])
                
                with tab1:
                    st.plotly_chart(create_metrics_bar(env_metrics, "Environmental Metrics"), use_container_width=True)
                
                with tab2:
                    st.plotly_chart(create_metrics_bar(social_metrics, "Social Metrics"), use_container_width=True)
                
                with tab3:
                    st.plotly_chart(create_metrics_bar(gov_metrics, "Governance Metrics"), use_container_width=True)
    
    # ========================================================================
    # LIVE DATA ANALYSIS PAGE
    # ========================================================================
    elif page == "📊 Live Data Analysis":
        st.markdown("### 📊 Real-Time Data Analysis")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            symbol = st.selectbox(
                "Select Company",
                NIFTY50_SYMBOLS,
                index=0,
                format_func=lambda x: f"{x} - {NIFTY50_COMPANIES.get(x, {}).get('name', x)}"
            )
        
        with col2:
            st.markdown("")
            st.markdown("")
            fetch_btn = st.button("🔄 Fetch Live Data", type="primary", use_container_width=True)
        
        if fetch_btn:
            with st.spinner(f"Fetching live data for {symbol}..."):
                live_data = fetch_live_company_data(symbol)
                
                if live_data:
                    st.session_state.live_company_data = live_data
                    st.success(f"✅ Data fetched from {live_data.get('data_source', 'API')}")
                else:
                    st.error("Failed to fetch live data. Please try again.")
        
        if st.session_state.live_company_data:
            data = st.session_state.live_company_data
            
            st.markdown("---")
            
            # Company header
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #34495e, #2c3e50); padding: 20px; border-radius: 12px; color: white;'>
                <h2 style='margin: 0;'>{data.get('company_name', data.get('symbol'))}</h2>
                <p style='color: #bdc3c7; margin: 5px 0;'>
                    {data.get('sector', 'N/A')} | {data.get('industry', 'N/A')}
                </p>
                <span class="data-source-badge badge-live">{data.get('data_source', 'LIVE')}</span>
                <span style='color: #bdc3c7; margin-left: 10px;'>Quality: {data.get('data_quality', 0):.1f}%</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                pchange = data.get('pchange', 0)
                st.metric("Last Price", f"₹{data.get('last_price', 0):,.2f}", f"{pchange:+.2f}%")
            with col2:
                st.metric("Market Cap", f"₹{data.get('market_cap', 0):,.0f} Cr")
            with col3:
                st.metric("PE Ratio", f"{data.get('pe_ratio', 0):.2f}")
            with col4:
                st.metric("52W Range", f"₹{data.get('week_low_52', 0):,.0f} - ₹{data.get('week_high_52', 0):,.0f}")
            
            st.markdown("---")
            
            # Shareholding pattern
            st.markdown("### 📊 Shareholding Pattern (Governance Indicators)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                shareholding_data = {
                    'Category': ['Promoter', 'FII', 'DII', 'Public'],
                    'Holding': [
                        data.get('promoter_holding', 0),
                        data.get('fii_holding', 0),
                        data.get('dii_holding', 0),
                        max(0, 100 - data.get('promoter_holding', 0) - data.get('fii_holding', 0) - data.get('dii_holding', 0))
                    ]
                }
                
                fig = px.pie(
                    shareholding_data,
                    values='Holding',
                    names='Category',
                    title='Shareholding Distribution',
                    color_discrete_sequence=['#1e8449', '#3498db', '#9b59b6', '#e74c3c']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 📈 Key Governance Indicators from Live Data")
                st.markdown(f"""
                - **Promoter Holding:** {data.get('promoter_holding', 0):.1f}%
                - **FII Holding:** {data.get('fii_holding', 0):.1f}% *(Foreign confidence)*
                - **DII Holding:** {data.get('dii_holding', 0):.1f}% *(Domestic confidence)*
                - **Pledged Shares:** {data.get('pledged_percentage', 0):.1f}% *(Risk indicator)*
                """)
                
                # Governance score from shareholding
                promoter = data.get('promoter_holding', 0)
                pledged = data.get('pledged_percentage', 0)
                fii_dii = data.get('fii_holding', 0) + data.get('dii_holding', 0)
                
                gov_from_sh = 50
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
                
                gov_from_sh += min(10, fii_dii / 5)
                gov_from_sh = min(100, max(0, gov_from_sh))
                
                st.metric("📊 Governance Score (from Shareholding)", f"{gov_from_sh:.1f}/100")
    
    # ========================================================================
    # UPLOAD ANNUAL REPORT PAGE
    # ========================================================================
    elif page == "📄 Upload Annual Report":
        st.markdown("### 📄 Upload Annual Report / BRSR Report")
        
        if not PDF_PARSER_AVAILABLE:
            st.error("""
            **PDF parsing libraries not installed!**
            
            Please install the required libraries:
            ```bash
            pip install PyMuPDF pdfplumber
            ```
            
            Then restart the Streamlit app.
            """)
            return
        
        st.markdown("""
        <div class="upload-zone">
            <h3>📁 Upload PDF Document</h3>
            <p>Supported: Annual Report, BRSR Report, Sustainability Report, CSR Report</p>
            <p style='color: #7f8c8d; font-size: 0.9em;'>
                The parser will extract ESG metrics automatically using pattern matching
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose PDF file",
            type=['pdf'],
            help="Upload your company's Annual Report or BRSR document"
        )
        
        if uploaded_file:
            st.info(f"📄 **File:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                extract_btn = st.button("🔍 Extract ESG Data", type="primary", use_container_width=True)
            
            if extract_btn:
                with st.spinner("Analyzing report... This may take a few minutes..."):
                    uploaded_file.seek(0)
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
            
            st.markdown(f"""
            <div class="extraction-result">
                <h3>{data.company_name or 'Company Name Not Found'}</h3>
                <p><strong>Year:</strong> {data.year} | <strong>Report Type:</strong> {data.report_type.value}</p>
                <p><strong>Extraction Confidence:</strong> {data.extraction_confidence:.1f}%</p>
                <p><strong>Pages Processed:</strong> {data.pages_processed}</p>
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
            
            # Calculate ESG score
            if st.button("📊 Calculate ESG Score from Extracted Data", type="primary"):
                esg_input = data.to_esg_input()
                industry = data.industry or 'Default'
                
                env_score, env_metrics = calculate_environmental_score(esg_input, industry)
                social_score, social_metrics = calculate_social_score(esg_input)
                gov_score, gov_metrics = calculate_governance_score(esg_input)
                overall = calculate_overall_esg(env_score, social_score, gov_score, industry)
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
                
                # Export
                st.markdown("---")
                json_str = json.dumps(esg_input, indent=2, default=str)
                st.download_button(
                    "💾 Download Extracted Data as JSON",
                    json_str,
                    f"esg_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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
            company_name = st.text_input("Company Name", "My Company Ltd")
            industry = st.selectbox(
                "Industry",
                [k for k in INDUSTRY_ADJUSTMENTS.keys() if k != 'Default'],
                index=0
            )
        
        with col2:
            symbol = st.text_input("Symbol", "MYCO")
            year = st.number_input("Reporting Year", 2020, 2025, 2024)
        
        st.markdown("---")
        
        benchmarks = get_benchmarks(industry)
        
        # Environmental
        st.markdown("#### 🌍 Environmental Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            carbon = st.number_input("Carbon Emissions (tCO2e/Cr)", 0.0, 500.0, float(benchmarks['carbon']), help="tCO2e per crore revenue")
            renewable = st.number_input("Renewable Energy %", 0.0, 100.0, float(benchmarks['renewable']))
        
        with col2:
            energy = st.number_input("Energy Consumption (GJ/Cr)", 0.0, 1000.0, float(benchmarks['energy']))
            waste = st.number_input("Waste Recycling %", 0.0, 100.0, float(benchmarks['waste']))
        
        with col3:
            water = st.number_input("Water Consumption (KL/Cr)", 0.0, 5000.0, float(benchmarks['water']))
            env_compliance = st.number_input("Environmental Compliance %", 0.0, 100.0, 95.0)
        
        # Social
        st.markdown("#### 👥 Social Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ltifr = st.number_input("LTIFR", 0.0, 5.0, 0.5, help="Lost Time Injury Frequency Rate")
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
            ceo_ratio = st.number_input("CEO Pay Ratio (x median)", 1.0, 500.0, 100.0)
        
        st.markdown("---")
        
        if st.button("🔄 Calculate ESG Score", type="primary", use_container_width=True):
            manual_data = {
                'carbon_emissions_intensity': carbon,
                'energy_consumption_intensity': energy,
                'renewable_energy_percentage': renewable,
                'water_consumption_intensity': water,
                'waste_recycling_rate': waste,
                'environmental_compliance': env_compliance,
                'climate_risk_disclosure': 60,
                'biodiversity_initiatives': 50,
                'hazardous_waste_compliance': 90,
                'ltifr': ltifr,
                'employee_turnover_rate': turnover,
                'women_workforce_percentage': women_wf,
                'training_hours_per_employee': training,
                'fair_wages_compliance': 90,
                'csr_spending_percentage': csr,
                'human_rights_compliance': 90,
                'customer_complaints_resolved': customer,
                'data_breaches': 0,
                'labor_practices_compliance': 95,
                'independent_directors_percentage': independent,
                'women_directors_percentage': women_board,
                'audit_committee_meetings': audit,
                'ceo_median_pay_ratio': ceo_ratio,
                'shareholder_rights': 80,
                'ethics_anti_corruption': ethics,
                'risk_management': risk_mgmt,
                'tax_transparency': 70,
                'rpt_compliance': 90,
                'sustainability_committee': 50,
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
                <div style='background-color: {risk_color}; color: white; padding: 40px; 
                            border-radius: 15px; text-align: center; margin-top: 50px;'>
                    <h2 style='margin: 0;'>ESG Risk Level</h2>
                    <h1 style='margin: 10px 0;'>{risk}</h1>
                    <p style='margin: 0;'>Score: {overall:.1f}/100</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ========================================================================
    # COMPARE COMPANIES PAGE
    # ========================================================================
    elif page == "🔍 Compare Companies":
        st.markdown("### 🔍 Compare Multiple Companies")
        
        selected = st.multiselect(
            "Select companies to compare (2-10)",
            NIFTY50_SYMBOLS,
            default=['TCS', 'INFY', 'WIPRO'],
            format_func=lambda x: f"{x} - {NIFTY50_COMPANIES.get(x, {}).get('name', x)}"
        )
        
        if len(selected) < 2:
            st.warning("Please select at least 2 companies to compare.")
        elif len(selected) > 10:
            st.warning("Please select no more than 10 companies.")
        else:
            if st.button("📊 Compare", type="primary"):
                results = []
                
                progress = st.progress(0)
                
                for i, symbol in enumerate(selected):
                    company_info = NIFTY50_COMPANIES.get(symbol, {})
                    industry = company_info.get('industry', 'Default')
                    
                    esg_data = generate_simulated_esg_data(symbol, industry)
                    
                    env_score, _ = calculate_environmental_score(esg_data, industry)
                    social_score, _ = calculate_social_score(esg_data)
                    gov_score, _ = calculate_governance_score(esg_data)
                    overall = calculate_overall_esg(env_score, social_score, gov_score, industry)
                    risk = get_risk_level(overall)
                    
                    results.append({
                        'Symbol': symbol,
                        'Company': company_info.get('name', symbol),
                        'Industry': industry,
                        'Environmental': round(env_score, 1),
                        'Social': round(social_score, 1),
                        'Governance': round(gov_score, 1),
                        'Overall': round(overall, 1),
                        'Risk': risk
                    })
                    
                    progress.progress((i + 1) / len(selected))
                
                df = pd.DataFrame(results)
                
                st.markdown("---")
                
                # Comparison chart
                st.plotly_chart(create_comparison_chart(df), use_container_width=True)
                
                # Ranking
                st.markdown("### 🏆 Rankings")
                df_sorted = df.sort_values('Overall', ascending=False).reset_index(drop=True)
                
                for i, row in df_sorted.iterrows():
                    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                    risk_class = row['Risk'].lower()
                    st.markdown(f"""
                    <div class="metric-card">
                        <span style='font-size: 1.5em;'>{medal}</span>
                        <strong>{row['Symbol']}</strong> - {row['Company']}
                        <span class="risk-{risk_class}" style='float: right;'>{row['Risk']}</span>
                        <br><small>E: {row['Environmental']} | S: {row['Social']} | G: {row['Governance']} | <strong>Overall: {row['Overall']}</strong></small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Full table
                st.markdown("### 📊 Detailed Comparison Table")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Download
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download Comparison as CSV",
                    csv,
                    f"esg_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
    
    # ========================================================================
    # FULL REPORT PAGE
    # ========================================================================
    elif page == "📋 Full Report":
        st.markdown("### 📋 NIFTY 50 ESG Report")
        
        if st.button("🔄 Generate Full Report", type="primary"):
            results = []
            
            progress = st.progress(0)
            status = st.empty()
            
            for i, symbol in enumerate(NIFTY50_SYMBOLS):
                status.text(f"Analyzing {symbol}...")
                
                company_info = NIFTY50_COMPANIES.get(symbol, {})
                industry = company_info.get('industry', 'Default')
                
                esg_data = generate_simulated_esg_data(symbol, industry)
                
                env_score, _ = calculate_environmental_score(esg_data, industry)
                social_score, _ = calculate_social_score(esg_data)
                gov_score, _ = calculate_governance_score(esg_data)
                overall = calculate_overall_esg(env_score, social_score, gov_score, industry)
                risk = get_risk_level(overall)
                
                results.append({
                    'Symbol': symbol,
                    'Company': company_info.get('name', symbol),
                    'Sector': company_info.get('sector', 'N/A'),
                    'Industry': industry,
                    'Environmental': round(env_score, 1),
                    'Social': round(social_score, 1),
                    'Governance': round(gov_score, 1),
                    'Overall': round(overall, 1),
                    'Risk': risk
                })
                
                progress.progress((i + 1) / len(NIFTY50_SYMBOLS))
            
            status.text("Complete!")
            df = pd.DataFrame(results)
            
            st.markdown("---")
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Average ESG Score", f"{df['Overall'].mean():.1f}")
            with col2:
                st.metric("ESG Leaders (≥65)", len(df[df['Overall'] >= 65]))
            with col3:
                st.metric("Needs Improvement (<50)", len(df[df['Overall'] < 50]))
            with col4:
                best = df.loc[df['Overall'].idxmax()]
                st.metric("Top Performer", f"{best['Symbol']} ({best['Overall']:.1f})")
            
            # Risk distribution
            st.markdown("### 📊 Risk Distribution")
            risk_counts = df['Risk'].value_counts()
            fig = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title='ESG Risk Distribution',
                color=risk_counts.index,
                color_discrete_map={
                    'Negligible': '#27ae60', 'Low': '#2ecc71',
                    'Medium': '#f39c12', 'High': '#e74c3c', 'Severe': '#c0392b'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Sector analysis
            st.markdown("### 📊 Sector-wise Average ESG Scores")
            sector_avg = df.groupby('Sector')[['Environmental', 'Social', 'Governance', 'Overall']].mean().round(1)
            st.dataframe(sector_avg, use_container_width=True)
            
            # Full table
            st.markdown("### 📋 Complete NIFTY 50 ESG Scores")
            st.dataframe(
                df.sort_values('Overall', ascending=False),
                use_container_width=True,
                hide_index=True,
                height=600
            )
            
            # Download options
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download as CSV",
                    csv,
                    f"nifty50_esg_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            
            with col2:
                json_str = df.to_json(orient='records', indent=2)
                st.download_button(
                    "📥 Download as JSON",
                    json_str,
                    f"nifty50_esg_{datetime.now().strftime('%Y%m%d')}.json",
                    "application/json"
                )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>🌿 <strong>NYZTrade ESG Platform</strong> | Integrated Real-Time Data & Document Analysis</p>
        <p style='font-size: 0.85em; color: #95a5a6;'>
            Based on SEBI BRSR Framework | 29 ESG Metrics | Industry-Specific Benchmarks
        </p>
        <p style='font-size: 0.8em;'>
            ⚠️ ESG scores are for informational purposes only. Consult qualified professionals for investment decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
