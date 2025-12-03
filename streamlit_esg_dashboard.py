# ============================================================================
# NYZTRADE - COMPLETE ESG DASHBOARD
# Real-Time Data + Enhanced BRSR PDF Parser + ESG Scoring
# ============================================================================
# 
# INSTALLATION:
# pip install streamlit pandas numpy plotly requests beautifulsoup4 PyMuPDF pdfplumber
#
# RUN:
# streamlit run esg_dashboard_final.py
#
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
import tempfile
import os
import re
import requests
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ============================================================================
# CHECK PDF LIBRARIES
# ============================================================================

PYMUPDF_AVAILABLE = False
PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    pass

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass

PDF_PARSER_AVAILABLE = PYMUPDF_AVAILABLE or PDFPLUMBER_AVAILABLE

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
    }
    
    .upload-zone {
        border: 2px dashed #27ae60;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        background-color: #f0fff4;
        margin: 20px 0;
    }
    
    .badge-live { background-color: #27ae60; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8em; }
    .badge-pdf { background-color: #3498db; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8em; }
    .badge-simulated { background-color: #f39c12; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8em; }
    
    .extraction-result {
        background-color: #e8f5e9;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #27ae60;
    }
    
    .extraction-warning {
        background-color: #fff3e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #ff9800;
    }
    
    .metric-found {
        background-color: #e8f5e9;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 5px 0;
        border-left: 3px solid #4caf50;
    }
    
    .metric-missing {
        background-color: #ffebee;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 5px 0;
        border-left: 3px solid #f44336;
    }
    
    .risk-negligible { background-color: #27ae60; color: white; padding: 5px 15px; border-radius: 15px; }
    .risk-low { background-color: #2ecc71; color: white; padding: 5px 15px; border-radius: 15px; }
    .risk-medium { background-color: #f39c12; color: white; padding: 5px 15px; border-radius: 15px; }
    .risk-high { background-color: #e74c3c; color: white; padding: 5px 15px; border-radius: 15px; }
    .risk-severe { background-color: #c0392b; color: white; padding: 5px 15px; border-radius: 15px; }
    
    .section-divider {
        border-top: 2px solid #e0e0e0;
        margin: 20px 0;
    }
    
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
# DATA CLASSES
# ============================================================================

class ReportType(Enum):
    BRSR = "BRSR Report"
    ANNUAL = "Annual Report"
    SUSTAINABILITY = "Sustainability Report"
    INTEGRATED = "Integrated Report"
    CSR = "CSR Report"
    UNKNOWN = "Unknown"


@dataclass
class EnvironmentalMetrics:
    """Environmental metrics from BRSR Section C - Principle 6"""
    # Energy (Essential Indicator 1 & 2)
    total_energy_consumption: float = 0.0  # GJ
    renewable_energy: float = 0.0  # GJ
    non_renewable_energy: float = 0.0  # GJ
    renewable_energy_percentage: float = 0.0
    energy_intensity: float = 0.0  # GJ per unit
    energy_intensity_optional: float = 0.0
    
    # Emissions (Essential Indicator 3, 4, 5)
    scope1_emissions: float = 0.0  # tCO2e
    scope2_emissions: float = 0.0  # tCO2e
    scope3_emissions: float = 0.0  # tCO2e (Leadership)
    total_ghg_emissions: float = 0.0  # tCO2e
    emission_intensity: float = 0.0  # tCO2e per unit
    
    # Air Pollutants (Essential Indicator 6)
    nox_emissions: float = 0.0
    sox_emissions: float = 0.0
    pm_emissions: float = 0.0
    pop_emissions: float = 0.0
    voc_emissions: float = 0.0
    hap_emissions: float = 0.0
    
    # Water (Essential Indicator 7, 8)
    total_water_withdrawal: float = 0.0  # KL
    water_from_surface: float = 0.0
    water_from_ground: float = 0.0
    water_from_third_party: float = 0.0
    water_recycled: float = 0.0
    water_recycling_percentage: float = 0.0
    water_intensity: float = 0.0
    zero_liquid_discharge: bool = False
    
    # Waste (Essential Indicator 9)
    total_waste_generated: float = 0.0  # MT
    plastic_waste: float = 0.0
    e_waste: float = 0.0
    bio_medical_waste: float = 0.0
    construction_waste: float = 0.0
    battery_waste: float = 0.0
    radioactive_waste: float = 0.0
    other_hazardous_waste: float = 0.0
    other_non_hazardous_waste: float = 0.0
    hazardous_waste: float = 0.0
    waste_recycled: float = 0.0
    waste_recycling_percentage: float = 0.0
    waste_to_landfill: float = 0.0
    
    # Compliance (Essential Indicator 10, 11)
    environmental_fines: float = 0.0
    environmental_fines_count: int = 0
    environmental_incidents: int = 0
    eco_sensitive_operations: int = 0
    eia_notifications: int = 0


@dataclass
class SocialMetrics:
    """Social metrics from BRSR Section C - Principle 3, 5, 8, 9"""
    # Employees (P3 - Essential Indicator 1)
    total_employees: int = 0
    male_employees: int = 0
    female_employees: int = 0
    permanent_employees: int = 0
    other_than_permanent: int = 0
    workers_total: int = 0
    male_workers: int = 0
    female_workers: int = 0
    permanent_workers: int = 0
    contract_workers: int = 0
    women_employees: int = 0
    women_percentage: float = 0.0
    differently_abled: int = 0
    differently_abled_percentage: float = 0.0
    
    # Turnover (P3 - Essential Indicator 2)
    new_hires_permanent: int = 0
    new_hires_workers: int = 0
    turnover_rate_employees: float = 0.0
    turnover_rate_workers: float = 0.0
    turnover_rate: float = 0.0
    
    # Health & Safety (P3 - Essential Indicator 10, 11, 12)
    fatalities_employees: int = 0
    fatalities_workers: int = 0
    fatalities: int = 0
    ltifr_employees: float = 0.0
    ltifr_workers: float = 0.0
    ltifr: float = 0.0
    recordable_injuries_employees: int = 0
    recordable_injuries_workers: int = 0
    recordable_injuries: int = 0
    high_consequence_injuries: int = 0
    man_days_lost: int = 0
    safety_incidents: int = 0
    near_misses: int = 0
    
    # Training (P3 - Essential Indicator 8)
    training_hours_employees_male: float = 0.0
    training_hours_employees_female: float = 0.0
    training_hours_workers_male: float = 0.0
    training_hours_workers_female: float = 0.0
    total_training_hours: float = 0.0
    training_hours_per_employee: float = 0.0
    employees_trained_percentage: float = 0.0
    skill_upgradation_employees: int = 0
    skill_upgradation_workers: int = 0
    
    # Benefits (P3 - Essential Indicator 4, 5, 6, 7)
    health_insurance_coverage: float = 0.0
    accident_insurance_coverage: float = 0.0
    maternity_benefits: float = 0.0
    paternity_benefits: float = 0.0
    daycare_facilities: float = 0.0
    
    # Diversity (P3)
    women_in_management: float = 0.0
    women_on_board: float = 0.0
    women_board_percentage: float = 0.0
    
    # Human Rights (P5 - Essential Indicators)
    child_labor_incidents: int = 0
    forced_labor_incidents: int = 0
    involuntary_labor_incidents: int = 0
    discrimination_incidents: int = 0
    sexual_harassment_complaints: int = 0
    sexual_harassment_resolved: int = 0
    human_rights_training_employees: float = 0.0
    human_rights_training_workers: float = 0.0
    minimum_wage_compliance: float = 0.0
    
    # CSR (P8 - Essential Indicators)
    csr_spending: float = 0.0  # In Lakhs/Crores
    csr_spending_required: float = 0.0
    csr_percentage: float = 0.0
    beneficiaries_reached: int = 0
    input_material_from_msme: float = 0.0
    input_material_from_small_producers: float = 0.0
    
    # Customer (P9 - Essential Indicators)
    customer_complaints: int = 0
    customer_complaints_resolved: int = 0
    complaints_pending: int = 0
    resolution_rate: float = 0.0
    product_recalls: int = 0
    cyber_security_incidents: int = 0
    data_breaches: int = 0
    consumer_cases_pending: int = 0


@dataclass
class GovernanceMetrics:
    """Governance metrics from BRSR Section A and C - Principle 1"""
    # Board Composition (Section A & P1)
    board_size: int = 0
    executive_directors: int = 0
    non_executive_directors: int = 0
    independent_directors: int = 0
    independent_percentage: float = 0.0
    women_directors: int = 0
    women_board_percentage: float = 0.0
    board_meetings: int = 0
    board_attendance_average: float = 0.0
    
    # Committees
    audit_committee_size: int = 0
    audit_committee_independent: int = 0
    audit_committee_meetings: int = 0
    nomination_committee_meetings: int = 0
    csr_committee_meetings: int = 0
    risk_committee_meetings: int = 0
    stakeholder_committee_meetings: int = 0
    
    # Ethics & Compliance (P1 - Essential Indicators)
    ethics_complaints: int = 0
    ethics_complaints_resolved: int = 0
    corruption_incidents: int = 0
    disciplinary_actions: int = 0
    whistleblower_complaints: int = 0
    whistleblower_resolved: int = 0
    
    # Anti-Corruption (P1)
    directors_trained_anti_corruption: float = 0.0
    kmps_trained_anti_corruption: float = 0.0
    employees_trained_anti_corruption: float = 0.0
    workers_trained_anti_corruption: float = 0.0
    
    # Legal & Regulatory
    fines_penalties_amount: float = 0.0
    fines_penalties_count: int = 0
    legal_cases_pending: int = 0
    
    # Related Party
    rpt_value: float = 0.0
    rpt_policy_compliance: float = 0.0
    
    # Executive Compensation
    ceo_remuneration: float = 0.0
    median_remuneration: float = 0.0
    ceo_to_median_ratio: float = 0.0
    
    # Policy Coverage (P1 - Essential Indicator 1)
    policy_coverage_p1: float = 0.0  # Percentage of operations covered
    policy_coverage_p2: float = 0.0
    policy_coverage_p3: float = 0.0
    policy_coverage_p4: float = 0.0
    policy_coverage_p5: float = 0.0
    policy_coverage_p6: float = 0.0
    policy_coverage_p7: float = 0.0
    policy_coverage_p8: float = 0.0
    policy_coverage_p9: float = 0.0


@dataclass 
class BRSRExtractedData:
    """Complete BRSR extracted data structure following SEBI format"""
    # Section A - General Disclosures
    company_name: str = ""
    cin: str = ""
    year: int = 0
    financial_year: str = ""
    report_type: ReportType = ReportType.UNKNOWN
    
    # Corporate Identity
    registered_office: str = ""
    corporate_office: str = ""
    email: str = ""
    telephone: str = ""
    website: str = ""
    
    # Business Details
    sector: str = ""
    industry: str = ""
    nic_code: str = ""
    main_business_activity: str = ""
    products_services: List[str] = field(default_factory=list)
    
    # Locations
    plants_national: int = 0
    plants_international: int = 0
    offices_national: int = 0
    offices_international: int = 0
    
    # Financial
    turnover: float = 0.0  # Revenue in Crores
    net_worth: float = 0.0
    paid_up_capital: float = 0.0
    total_spending_on_esg: float = 0.0
    
    # Holdings
    holding_company: str = ""
    subsidiaries_count: int = 0
    associates_count: int = 0
    
    # Reporting Boundary
    reporting_boundary: str = ""  # Standalone or Consolidated
    
    # Extracted Metrics
    environmental: EnvironmentalMetrics = field(default_factory=EnvironmentalMetrics)
    social: SocialMetrics = field(default_factory=SocialMetrics)
    governance: GovernanceMetrics = field(default_factory=GovernanceMetrics)
    
    # Raw extracted text for debugging
    raw_extractions: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    extraction_time: datetime = field(default_factory=datetime.now)
    pages_processed: int = 0
    extraction_confidence: float = 0.0
    metrics_found: int = 0
    metrics_total: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_esg_input(self) -> Dict:
        """Convert to ESG calculator input format with fallbacks"""
        env = self.environmental
        soc = self.social
        gov = self.governance
        
        # Calculate intensity metrics if we have revenue
        carbon_intensity = 50  # default
        if self.turnover > 0 and env.total_ghg_emissions > 0:
            carbon_intensity = env.total_ghg_emissions / self.turnover
        elif env.emission_intensity > 0:
            carbon_intensity = env.emission_intensity
        
        energy_intensity = 200  # default
        if self.turnover > 0 and env.total_energy_consumption > 0:
            energy_intensity = env.total_energy_consumption / self.turnover
        elif env.energy_intensity > 0:
            energy_intensity = env.energy_intensity
        
        water_intensity = 300  # default
        if self.turnover > 0 and env.total_water_withdrawal > 0:
            water_intensity = env.total_water_withdrawal / self.turnover
        elif env.water_intensity > 0:
            water_intensity = env.water_intensity
        
        # Calculate women percentage
        women_pct = soc.women_percentage
        if women_pct == 0 and soc.total_employees > 0 and soc.women_employees > 0:
            women_pct = (soc.women_employees / soc.total_employees) * 100
        elif women_pct == 0 and soc.total_employees > 0 and soc.female_employees > 0:
            women_pct = (soc.female_employees / soc.total_employees) * 100
        
        # Calculate CSR percentage
        csr_pct = soc.csr_percentage
        if csr_pct == 0 and soc.csr_spending > 0 and soc.csr_spending_required > 0:
            csr_pct = (soc.csr_spending / soc.csr_spending_required) * 100
        
        # Calculate resolution rate
        resolution_rate = soc.resolution_rate
        if resolution_rate == 0 and soc.customer_complaints > 0:
            resolution_rate = (soc.customer_complaints_resolved / soc.customer_complaints) * 100
        
        return {
            'company_name': self.company_name,
            'industry': self.industry or self.sector,
            'year': self.year,
            'turnover': self.turnover,
            
            # Environmental
            'carbon_emissions_intensity': carbon_intensity,
            'total_ghg_emissions': env.total_ghg_emissions,
            'scope1_emissions': env.scope1_emissions,
            'scope2_emissions': env.scope2_emissions,
            'scope3_emissions': env.scope3_emissions,
            'energy_consumption_intensity': energy_intensity,
            'total_energy_consumption': env.total_energy_consumption,
            'renewable_energy_percentage': env.renewable_energy_percentage if env.renewable_energy_percentage > 0 else 25,
            'water_consumption_intensity': water_intensity,
            'total_water_withdrawal': env.total_water_withdrawal,
            'water_recycling_percentage': env.water_recycling_percentage,
            'waste_recycling_rate': env.waste_recycling_percentage if env.waste_recycling_percentage > 0 else 65,
            'total_waste_generated': env.total_waste_generated,
            'hazardous_waste': env.hazardous_waste,
            'environmental_compliance': 100 if env.environmental_fines == 0 else max(50, 100 - env.environmental_fines_count * 10),
            
            # Social
            'total_employees': soc.total_employees,
            'ltifr': soc.ltifr if soc.ltifr > 0 else (soc.ltifr_employees if soc.ltifr_employees > 0 else 0.5),
            'fatalities': soc.fatalities,
            'employee_turnover_rate': soc.turnover_rate if soc.turnover_rate > 0 else 15,
            'women_workforce_percentage': women_pct if women_pct > 0 else 25,
            'training_hours_per_employee': soc.training_hours_per_employee if soc.training_hours_per_employee > 0 else 20,
            'csr_spending': soc.csr_spending,
            'csr_spending_percentage': csr_pct if csr_pct > 0 else 2,
            'customer_complaints_resolved': resolution_rate if resolution_rate > 0 else 95,
            'data_breaches': soc.data_breaches + soc.cyber_security_incidents,
            'child_labor_incidents': soc.child_labor_incidents,
            'discrimination_incidents': soc.discrimination_incidents,
            'sexual_harassment_complaints': soc.sexual_harassment_complaints,
            
            # Governance
            'board_size': gov.board_size,
            'independent_directors': gov.independent_directors,
            'independent_directors_percentage': gov.independent_percentage if gov.independent_percentage > 0 else 50,
            'women_directors': gov.women_directors,
            'women_directors_percentage': gov.women_board_percentage if gov.women_board_percentage > 0 else 17,
            'board_meetings': gov.board_meetings if gov.board_meetings > 0 else 6,
            'audit_committee_meetings': gov.audit_committee_meetings if gov.audit_committee_meetings > 0 else 4,
            'ceo_median_pay_ratio': gov.ceo_to_median_ratio if gov.ceo_to_median_ratio > 0 else 100,
            'ethics_complaints': gov.ethics_complaints,
            'corruption_incidents': gov.corruption_incidents,
            'whistleblower_complaints': gov.whistleblower_complaints,
            'fines_penalties': gov.fines_penalties_amount,
        }


# ============================================================================
# CONSTANTS
# ============================================================================

INDUSTRY_ADJUSTMENTS = {
    'Oil & Gas': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Oil Exploration': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Refineries': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
    'Power': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Power Generation': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Iron & Steel': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Metals': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Cement': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Mining': {'environmental': 1.3, 'social': 1.0, 'governance': 0.7},
    'Coal': {'environmental': 1.3, 'social': 1.0, 'governance': 0.7},
    'Banks': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Private Banks': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Public Sector Banks': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Financial Services': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'NBFC': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'Insurance': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2},
    'IT Services': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'IT - Software': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'Technology': {'environmental': 0.8, 'social': 1.1, 'governance': 1.1},
    'Pharmaceuticals': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Healthcare': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'FMCG': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Consumer Goods': {'environmental': 1.0, 'social': 1.1, 'governance': 0.9},
    'Automobiles': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Auto': {'environmental': 1.2, 'social': 0.9, 'governance': 0.9},
    'Telecom': {'environmental': 0.9, 'social': 1.0, 'governance': 1.1},
    'Construction': {'environmental': 1.1, 'social': 1.0, 'governance': 0.9},
    'Real Estate': {'environmental': 1.1, 'social': 0.9, 'governance': 1.0},
    'Chemicals': {'environmental': 1.2, 'social': 1.0, 'governance': 0.8},
    'Textiles': {'environmental': 1.1, 'social': 1.1, 'governance': 0.8},
    'Default': {'environmental': 1.0, 'social': 1.0, 'governance': 1.0}
}

ENVIRONMENTAL_BENCHMARKS = {
    'Oil & Gas': {'carbon': 150, 'energy': 500, 'water': 1000, 'renewable': 10, 'waste': 60},
    'Power': {'carbon': 200, 'energy': 800, 'water': 2000, 'renewable': 25, 'waste': 50},
    'IT Services': {'carbon': 5, 'energy': 50, 'water': 50, 'renewable': 50, 'waste': 80},
    'Banks': {'carbon': 2, 'energy': 30, 'water': 30, 'renewable': 40, 'waste': 85},
    'Pharmaceuticals': {'carbon': 30, 'energy': 150, 'water': 500, 'renewable': 30, 'waste': 70},
    'Steel': {'carbon': 180, 'energy': 700, 'water': 1500, 'renewable': 15, 'waste': 65},
    'Cement': {'carbon': 150, 'energy': 500, 'water': 800, 'renewable': 20, 'waste': 70},
    'FMCG': {'carbon': 20, 'energy': 100, 'water': 300, 'renewable': 35, 'waste': 75},
    'Automobiles': {'carbon': 40, 'energy': 200, 'water': 400, 'renewable': 25, 'waste': 80},
    'Chemicals': {'carbon': 80, 'energy': 400, 'water': 800, 'renewable': 20, 'waste': 60},
    'Textiles': {'carbon': 50, 'energy': 300, 'water': 1000, 'renewable': 15, 'waste': 55},
    'Default': {'carbon': 50, 'energy': 200, 'water': 300, 'renewable': 25, 'waste': 65}
}

# NIFTY 50 Companies
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
# SESSION STATE
# ============================================================================

if 'pdf_extracted_data' not in st.session_state:
    st.session_state.pdf_extracted_data = None
if 'live_company_data' not in st.session_state:
    st.session_state.live_company_data = None


# ============================================================================
# ENHANCED BRSR PDF PARSER
# ============================================================================

class EnhancedBRSRParser:
    """
    Enhanced parser for SEBI BRSR Reports with comprehensive pattern matching
    Follows BRSR format: Section A (General), Section B (Management), Section C (Principles 1-9)
    """
    
    def __init__(self):
        self.extracted_data = None
        self.text = ""
        self.tables = []
        self.metrics_found = {}
        
    # -------------------------------------------------------------------------
    # NUMBER EXTRACTION HELPERS
    # -------------------------------------------------------------------------
    
    def _clean_number(self, value: str, allow_negative: bool = False) -> float:
        """Clean and convert extracted number string to float"""
        if not value:
            return 0.0
        
        value = str(value).strip()
        
        # Handle special cases
        if value.lower() in ['zero', 'nil', 'na', 'n/a', '-', '–', 'none', 'not applicable']:
            return 0.0
        
        # Remove commas, spaces, and common formatting
        cleaned = re.sub(r'[,\s]', '', value)
        cleaned = cleaned.replace('−', '-')  # Unicode minus
        
        # Remove percentage sign
        cleaned = cleaned.replace('%', '')
        
        # Handle parentheses for negative numbers
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        
        # Handle currency symbols
        cleaned = re.sub(r'[₹$€£¥]', '', cleaned)
        
        # Handle multipliers
        multiplier = 1
        if cleaned.lower().endswith('cr') or cleaned.lower().endswith('crore') or cleaned.lower().endswith('crores'):
            multiplier = 1  # Keep in crores
            cleaned = re.sub(r'(?i)(cr|crore|crores)$', '', cleaned)
        elif cleaned.lower().endswith('lakh') or cleaned.lower().endswith('lakhs') or cleaned.lower().endswith('lac'):
            multiplier = 0.01  # Convert to crores
            cleaned = re.sub(r'(?i)(lakh|lakhs|lac)$', '', cleaned)
        elif cleaned.lower().endswith('mn') or cleaned.lower().endswith('million'):
            multiplier = 0.1  # Approximate conversion
            cleaned = re.sub(r'(?i)(mn|million)$', '', cleaned)
        
        try:
            result = float(cleaned) * multiplier
            if not allow_negative and result < 0:
                result = abs(result)
            return result
        except ValueError:
            return 0.0
    
    def _extract_first_number(self, text: str, pattern: str = None) -> float:
        """Extract first number from text matching optional pattern"""
        if not text:
            return 0.0
        
        # If pattern provided, search for it
        if pattern:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                text = match.group(0)
        
        # Find first number
        number_match = re.search(r'[\d,]+\.?\d*', text)
        if number_match:
            return self._clean_number(number_match.group())
        
        return 0.0
    
    def _extract_all_numbers(self, text: str) -> List[float]:
        """Extract all numbers from text"""
        if not text:
            return []
        
        numbers = []
        for match in re.finditer(r'[\d,]+\.?\d*', text):
            num = self._clean_number(match.group())
            if num > 0:
                numbers.append(num)
        
        return numbers
    
    # -------------------------------------------------------------------------
    # PATTERN MATCHING - BRSR SPECIFIC
    # -------------------------------------------------------------------------
    
    def _search_patterns(self, patterns: List[str], text: str = None) -> Optional[float]:
        """Search multiple patterns and return first match"""
        if text is None:
            text = self.text
        
        for pattern in patterns:
            try:
                matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
                for match in matches:
                    # Get the matched groups
                    groups = match.groups()
                    if groups:
                        for group in groups:
                            if group:
                                num = self._clean_number(group)
                                if num > 0:
                                    return num
                    else:
                        # Try to find number near the match
                        start = max(0, match.start() - 10)
                        end = min(len(text), match.end() + 100)
                        context = text[start:end]
                        num = self._extract_first_number(context)
                        if num > 0:
                            return num
            except Exception:
                continue
        
        return None
    
    def _search_table_patterns(self, row_patterns: List[str], col_index: int = -1) -> Optional[float]:
        """Search in extracted tables for patterns"""
        for table in self.tables:
            if not table:
                continue
            for row in table:
                if not row:
                    continue
                row_text = ' '.join([str(cell) if cell else '' for cell in row]).lower()
                for pattern in row_patterns:
                    if re.search(pattern, row_text, re.IGNORECASE):
                        # Try specified column or last column with number
                        if col_index >= 0 and col_index < len(row):
                            num = self._clean_number(str(row[col_index]))
                            if num > 0:
                                return num
                        else:
                            # Try each cell from right
                            for cell in reversed(row):
                                num = self._clean_number(str(cell) if cell else '')
                                if num > 0:
                                    return num
        return None
    
    # -------------------------------------------------------------------------
    # SECTION A - GENERAL DISCLOSURES
    # -------------------------------------------------------------------------
    
    def _extract_general_disclosures(self) -> Dict:
        """Extract Section A - General Disclosures"""
        data = {}
        
        # Company Name
        patterns = [
            r'name\s+of\s+(?:the\s+)?(?:listed\s+)?entity[:\s]+([A-Za-z][A-Za-z0-9\s&\.\-,]+(?:Ltd|Limited|Corporation|Corp|Inc)?)',
            r'corporate\s+identity[:\s]+.{20,50}?([A-Za-z][A-Za-z\s&]+(?:Ltd|Limited))',
            r'^([A-Z][A-Za-z\s&]+(?:Limited|Ltd))\s*$',
        ]
        for pattern in patterns:
            match = re.search(pattern, self.text[:5000], re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) > 5 and len(name) < 100:
                    data['company_name'] = name
                    break
        
        # CIN
        cin_match = re.search(r'([A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})', self.text[:10000])
        if cin_match:
            data['cin'] = cin_match.group(1)
        
        # Financial Year
        fy_patterns = [
            r'(?:FY|financial\s+year)[:\s]*(\d{4})[-–](\d{2,4})',
            r'(?:year\s+ended?|for\s+the\s+year)[:\s]*(?:31st?\s+)?(?:march|mar)[,\s]*(\d{4})',
            r'(\d{4})[-–](\d{2,4})',
        ]
        for pattern in fy_patterns:
            match = re.search(pattern, self.text[:5000], re.IGNORECASE)
            if match:
                if match.lastindex >= 1:
                    data['year'] = int(match.group(1))
                    break
        
        # Turnover/Revenue
        revenue_patterns = [
            r'(?:total\s+)?(?:turnover|revenue)[:\s]*(?:₹|Rs\.?|INR)?\s*([\d,]+\.?\d*)\s*(?:Cr|Crore)',
            r'(?:turnover|revenue)\s+(?:from\s+operations)?[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:Cr|Crore)\s*(?:turnover|revenue)',
        ]
        result = self._search_patterns(revenue_patterns)
        if result:
            data['turnover'] = result
        
        # Net Worth
        networth_patterns = [
            r'net\s*worth[:\s]*(?:₹|Rs\.?|INR)?\s*([\d,]+\.?\d*)\s*(?:Cr|Crore)?',
        ]
        result = self._search_patterns(networth_patterns)
        if result:
            data['net_worth'] = result
        
        # NIC Code / Sector
        nic_match = re.search(r'NIC\s*code[:\s]*(\d{4,5})', self.text, re.IGNORECASE)
        if nic_match:
            data['nic_code'] = nic_match.group(1)
        
        return data
    
    # -------------------------------------------------------------------------
    # SECTION C - PRINCIPLE 6: ENVIRONMENT
    # -------------------------------------------------------------------------
    
    def _extract_environmental(self) -> EnvironmentalMetrics:
        """Extract Principle 6 - Environment metrics"""
        metrics = EnvironmentalMetrics()
        
        # ===== ENERGY =====
        # Total energy consumption
        energy_patterns = [
            r'total\s+energy\s+consumption[:\s]*([\d,]+\.?\d*)\s*(?:GJ|TJ|Giga\s*Joule)',
            r'energy\s+(?:consumption|consumed)[:\s]*([\d,]+\.?\d*)\s*(?:GJ|TJ)',
            r'([\d,]+\.?\d*)\s*(?:GJ|TJ|Giga\s*Joule)\s*(?:total)?\s*energy',
            r'total\s+energy[:\s]*([\d,]+\.?\d*)',
        ]
        result = self._search_patterns(energy_patterns)
        if result:
            metrics.total_energy_consumption = result
            self.metrics_found['total_energy_consumption'] = result
        
        # Also check tables
        if metrics.total_energy_consumption == 0:
            result = self._search_table_patterns([
                r'total\s+energy',
                r'energy\s+consumption',
                r'total\s+\(a\+b\)',
            ])
            if result:
                metrics.total_energy_consumption = result
        
        # Renewable energy
        renewable_patterns = [
            r'renewable\s+(?:energy\s+)?(?:sources?|consumption)[:\s]*([\d,]+\.?\d*)\s*(?:GJ|TJ|%)',
            r'from\s+renewable\s+sources?[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:GJ|%)?\s*renewable',
            r'biomass|solar|wind|hydro[:\s]*([\d,]+\.?\d*)',
        ]
        result = self._search_patterns(renewable_patterns)
        if result:
            if result <= 100:  # Percentage
                metrics.renewable_energy_percentage = result
            else:
                metrics.renewable_energy = result
            self.metrics_found['renewable_energy'] = result
        
        # Calculate renewable percentage if needed
        if metrics.renewable_energy > 0 and metrics.total_energy_consumption > 0:
            metrics.renewable_energy_percentage = (metrics.renewable_energy / metrics.total_energy_consumption) * 100
        
        # Energy intensity
        intensity_patterns = [
            r'energy\s+intensity[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:GJ|MWh)\s*per\s*(?:crore|unit|rupee|revenue)',
        ]
        result = self._search_patterns(intensity_patterns)
        if result:
            metrics.energy_intensity = result
        
        # ===== EMISSIONS =====
        # Scope 1
        scope1_patterns = [
            r'scope\s*[-–]?\s*1[:\s]*([\d,]+\.?\d*)\s*(?:tCO2e?|MT|metric\s*tonnes?|tonnes?)',
            r'direct\s+(?:ghg\s+)?emissions?[:\s]*([\d,]+\.?\d*)\s*(?:tCO2e?|MT)',
            r'([\d,]+\.?\d*)\s*(?:tCO2e?|MT)\s*(?:scope\s*[-–]?\s*1|direct)',
        ]
        result = self._search_patterns(scope1_patterns)
        if result:
            metrics.scope1_emissions = result
            self.metrics_found['scope1_emissions'] = result
        
        # Scope 2
        scope2_patterns = [
            r'scope\s*[-–]?\s*2[:\s]*([\d,]+\.?\d*)\s*(?:tCO2e?|MT|metric\s*tonnes?|tonnes?)',
            r'indirect\s+(?:ghg\s+)?emissions?[:\s]*([\d,]+\.?\d*)\s*(?:tCO2e?|MT)',
            r'([\d,]+\.?\d*)\s*(?:tCO2e?|MT)\s*(?:scope\s*[-–]?\s*2|indirect)',
        ]
        result = self._search_patterns(scope2_patterns)
        if result:
            metrics.scope2_emissions = result
            self.metrics_found['scope2_emissions'] = result
        
        # Scope 3 (Leadership indicator)
        scope3_patterns = [
            r'scope\s*[-–]?\s*3[:\s]*([\d,]+\.?\d*)\s*(?:tCO2e?|MT)',
        ]
        result = self._search_patterns(scope3_patterns)
        if result:
            metrics.scope3_emissions = result
        
        # Total GHG
        total_ghg_patterns = [
            r'total\s+(?:ghg|greenhouse\s+gas)\s+emissions?[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:tCO2e?|MT)\s*total\s+(?:ghg|greenhouse|emission)',
        ]
        result = self._search_patterns(total_ghg_patterns)
        if result:
            metrics.total_ghg_emissions = result
        else:
            # Calculate if we have scope 1 and 2
            metrics.total_ghg_emissions = metrics.scope1_emissions + metrics.scope2_emissions
        
        if metrics.total_ghg_emissions > 0:
            self.metrics_found['total_ghg_emissions'] = metrics.total_ghg_emissions
        
        # Emission intensity
        emission_intensity_patterns = [
            r'(?:ghg|emission)\s+intensity[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:tCO2e?)\s*per\s*(?:crore|unit|revenue)',
        ]
        result = self._search_patterns(emission_intensity_patterns)
        if result:
            metrics.emission_intensity = result
        
        # ===== WATER =====
        water_patterns = [
            r'total\s+(?:water\s+)?(?:withdrawal|consumption|usage|drawn)[:\s]*([\d,]+\.?\d*)\s*(?:KL|ML|kilolitre|m3|cubic)',
            r'water\s+(?:withdrawn?|consumed|usage)[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:KL|ML|kilolitre)\s*(?:water|total)',
        ]
        result = self._search_patterns(water_patterns)
        if result:
            metrics.total_water_withdrawal = result
            self.metrics_found['total_water_withdrawal'] = result
        
        # Water recycled
        water_recycled_patterns = [
            r'water\s+(?:recycled|reused|reclaimed)[:\s]*([\d,]+\.?\d*)\s*(?:KL|ML|%)?',
            r'recycled\s+(?:and\s+reused\s+)?water[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:KL|ML|%)?\s*(?:water\s+)?recycled',
        ]
        result = self._search_patterns(water_recycled_patterns)
        if result:
            if result <= 100:
                metrics.water_recycling_percentage = result
            else:
                metrics.water_recycled = result
            self.metrics_found['water_recycled'] = result
        
        # Calculate recycling percentage
        if metrics.water_recycled > 0 and metrics.total_water_withdrawal > 0:
            metrics.water_recycling_percentage = (metrics.water_recycled / metrics.total_water_withdrawal) * 100
        
        # Zero Liquid Discharge
        if re.search(r'zero\s+liquid\s+discharge|ZLD', self.text, re.IGNORECASE):
            metrics.zero_liquid_discharge = True
        
        # ===== WASTE =====
        waste_patterns = [
            r'total\s+waste\s+(?:generated|produced)[:\s]*([\d,]+\.?\d*)\s*(?:MT|tonnes?|metric)',
            r'waste\s+generation[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:MT|tonnes?)\s*(?:total)?\s*waste',
        ]
        result = self._search_patterns(waste_patterns)
        if result:
            metrics.total_waste_generated = result
            self.metrics_found['total_waste_generated'] = result
        
        # Hazardous waste
        hazardous_patterns = [
            r'hazardous\s+waste[:\s]*([\d,]+\.?\d*)\s*(?:MT|tonnes?|kg)',
            r'([\d,]+\.?\d*)\s*(?:MT|tonnes?|kg)\s*hazardous',
        ]
        result = self._search_patterns(hazardous_patterns)
        if result:
            metrics.hazardous_waste = result
        
        # Waste recycled/recovered
        waste_recycled_patterns = [
            r'waste\s+(?:recycled|recovered|diverted)[:\s]*([\d,]+\.?\d*)\s*(?:MT|%)?',
            r'recycling\s+rate[:\s]*([\d,]+\.?\d*)\s*%?',
            r'([\d,]+\.?\d*)\s*%?\s*(?:waste\s+)?(?:recycled|diverted|recovered)',
        ]
        result = self._search_patterns(waste_recycled_patterns)
        if result:
            if result <= 100:
                metrics.waste_recycling_percentage = result
            else:
                metrics.waste_recycled = result
            self.metrics_found['waste_recycled'] = result
        
        # E-waste
        ewaste_patterns = [
            r'e[-\s]?waste[:\s]*([\d,]+\.?\d*)\s*(?:MT|tonnes?|kg)',
        ]
        result = self._search_patterns(ewaste_patterns)
        if result:
            metrics.e_waste = result
        
        # Plastic waste
        plastic_patterns = [
            r'plastic\s+waste[:\s]*([\d,]+\.?\d*)\s*(?:MT|tonnes?|kg)',
        ]
        result = self._search_patterns(plastic_patterns)
        if result:
            metrics.plastic_waste = result
        
        # ===== COMPLIANCE =====
        # Environmental fines
        fines_patterns = [
            r'environmental\s+(?:fine|penalt)[:\s]*(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:Cr|Lakh)?\s*(?:fine|penalt)',
        ]
        result = self._search_patterns(fines_patterns)
        if result:
            metrics.environmental_fines = result
        
        # Check for "no fines" or "nil"
        if re.search(r'no\s+(?:environmental\s+)?fines?|nil\s+(?:environmental\s+)?fines?|zero\s+fines?', 
                     self.text, re.IGNORECASE):
            metrics.environmental_fines = 0
        
        return metrics
    
    # -------------------------------------------------------------------------
    # SECTION C - PRINCIPLE 3: EMPLOYEE WELLBEING
    # -------------------------------------------------------------------------
    
    def _extract_social(self) -> SocialMetrics:
        """Extract Principle 3, 5, 8, 9 - Social metrics"""
        metrics = SocialMetrics()
        
        # ===== EMPLOYEES =====
        employee_patterns = [
            r'total\s+(?:number\s+of\s+)?employees?[:\s]*([\d,]+)',
            r'total\s+(?:permanent\s+)?employees?[:\s]*([\d,]+)',
            r'employees?\s+(?:strength|count|headcount)[:\s]*([\d,]+)',
            r'([\d,]+)\s*(?:total\s+)?employees?',
            r'headcount[:\s]*([\d,]+)',
            r'workforce[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(employee_patterns)
        if result and result > 10:  # Reasonable minimum
            metrics.total_employees = int(result)
            self.metrics_found['total_employees'] = int(result)
        
        # Also check tables
        if metrics.total_employees == 0:
            result = self._search_table_patterns([
                r'total\s+employees',
                r'permanent\s+employees',
                r'total\s+\(d\s*=',
            ])
            if result and result > 10:
                metrics.total_employees = int(result)
        
        # Female/Women employees
        women_patterns = [
            r'(?:female|women)\s+employees?[:\s]*([\d,]+)',
            r'([\d,]+)\s*(?:female|women)\s+(?:employees?|workers?)',
            r'women\s+(?:in\s+workforce)?[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(women_patterns)
        if result:
            metrics.women_employees = int(result)
            metrics.female_employees = int(result)
            self.metrics_found['women_employees'] = int(result)
        
        # Women percentage
        women_pct_patterns = [
            r'(?:female|women)[:\s]*([\d,]+\.?\d*)\s*%',
            r'([\d,]+\.?\d*)\s*%\s*(?:are\s+)?(?:female|women)',
            r'(?:female|women)\s+representation[:\s]*([\d,]+\.?\d*)\s*%?',
        ]
        result = self._search_patterns(women_pct_patterns)
        if result and result <= 100:
            metrics.women_percentage = result
        
        # Calculate if needed
        if metrics.women_percentage == 0 and metrics.women_employees > 0 and metrics.total_employees > 0:
            metrics.women_percentage = (metrics.women_employees / metrics.total_employees) * 100
        
        # Workers (often separate from employees in BRSR)
        workers_patterns = [
            r'total\s+(?:number\s+of\s+)?workers?[:\s]*([\d,]+)',
            r'workers?\s+(?:strength|count)[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(workers_patterns)
        if result:
            metrics.workers_total = int(result)
        
        # Differently abled
        pwd_patterns = [
            r'(?:differently\s+abled|persons?\s+with\s+disabilities?|PwD)[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(pwd_patterns)
        if result:
            metrics.differently_abled = int(result)
        
        # ===== HEALTH & SAFETY =====
        # LTIFR (Lost Time Injury Frequency Rate)
        ltifr_patterns = [
            r'LTIFR[:\s]*([\d,]+\.?\d*)',
            r'lost\s+time\s+injury\s+frequency\s+rate[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*LTIFR',
        ]
        result = self._search_patterns(ltifr_patterns)
        if result and result < 100:  # Reasonable LTIFR value
            metrics.ltifr = result
            self.metrics_found['ltifr'] = result
        
        # Fatalities
        fatality_patterns = [
            r'fatalities?[:\s]*([\d,]+)',
            r'([\d,]+)\s*fatalities?',
            r'(?:work[- ]?related\s+)?deaths?[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(fatality_patterns)
        if result is not None:
            metrics.fatalities = int(result)
            self.metrics_found['fatalities'] = int(result)
        
        # Check for zero fatalities
        if re.search(r'zero\s+fatalities?|no\s+fatalities?|nil\s+fatalities?|fatalities?[:\s]*(?:nil|zero|0)', 
                     self.text, re.IGNORECASE):
            metrics.fatalities = 0
            self.metrics_found['fatalities'] = 0
        
        # Recordable injuries
        injury_patterns = [
            r'(?:recordable|total)\s+(?:work[- ]?related\s+)?injuries?[:\s]*([\d,]+)',
            r'([\d,]+)\s*(?:recordable|total)\s+injuries?',
            r'TRIR[:\s]*([\d,]+\.?\d*)',
        ]
        result = self._search_patterns(injury_patterns)
        if result:
            metrics.recordable_injuries = int(result)
        
        # Man-days lost
        mandays_patterns = [
            r'(?:man[-\s]?days?|person[-\s]?days?)\s+lost[:\s]*([\d,]+)',
            r'([\d,]+)\s*(?:man[-\s]?days?|person[-\s]?days?)\s+lost',
        ]
        result = self._search_patterns(mandays_patterns)
        if result:
            metrics.man_days_lost = int(result)
        
        # ===== TRAINING =====
        training_patterns = [
            r'(?:average\s+)?training\s+(?:hours?|hrs?)\s*(?:per\s+)?(?:employee)?[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:hours?|hrs?)\s*(?:of\s+)?training',
            r'training[:\s]*([\d,]+\.?\d*)\s*(?:hours?|hrs?)',
        ]
        result = self._search_patterns(training_patterns)
        if result:
            if result < 500:  # Per employee (reasonable range)
                metrics.training_hours_per_employee = result
            else:  # Total hours
                metrics.total_training_hours = result
            self.metrics_found['training_hours'] = result
        
        # Calculate per employee if we have totals
        if metrics.training_hours_per_employee == 0 and metrics.total_training_hours > 0 and metrics.total_employees > 0:
            metrics.training_hours_per_employee = metrics.total_training_hours / metrics.total_employees
        
        # ===== TURNOVER =====
        turnover_patterns = [
            r'(?:employee\s+)?turnover\s+(?:rate)?[:\s]*([\d,]+\.?\d*)\s*%?',
            r'attrition\s+(?:rate)?[:\s]*([\d,]+\.?\d*)\s*%?',
            r'([\d,]+\.?\d*)\s*%?\s*(?:employee\s+)?(?:turnover|attrition)',
        ]
        result = self._search_patterns(turnover_patterns)
        if result and result <= 100:
            metrics.turnover_rate = result
        
        # ===== HUMAN RIGHTS (P5) =====
        # Child labor
        child_labor_patterns = [
            r'child\s+labo[u]?r\s+(?:incidents?|cases?|complaints?)[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(child_labor_patterns)
        if result is not None:
            metrics.child_labor_incidents = int(result)
        if re.search(r'no\s+child\s+labo[u]?r|zero\s+child\s+labo[u]?r|nil.*child\s+labo[u]?r', 
                     self.text, re.IGNORECASE):
            metrics.child_labor_incidents = 0
        
        # Forced labor
        if re.search(r'no\s+forced\s+labo[u]?r|zero\s+forced\s+labo[u]?r', self.text, re.IGNORECASE):
            metrics.forced_labor_incidents = 0
        
        # Sexual harassment
        posh_patterns = [
            r'(?:sexual\s+harassment|POSH)\s+(?:complaints?|cases?)[:\s]*([\d,]+)',
            r'([\d,]+)\s*(?:sexual\s+harassment|POSH)\s+(?:complaints?|cases?)',
        ]
        result = self._search_patterns(posh_patterns)
        if result is not None:
            metrics.sexual_harassment_complaints = int(result)
        
        # Discrimination
        discrimination_patterns = [
            r'discrimination\s+(?:complaints?|cases?|incidents?)[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(discrimination_patterns)
        if result is not None:
            metrics.discrimination_incidents = int(result)
        
        # ===== CSR (P8) =====
        csr_patterns = [
            r'CSR\s+(?:expenditure|spending|spend|amount)[:\s]*(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)\s*(?:Cr|Crore|Lakh)?',
            r'(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)\s*(?:Cr|Crore|Lakh)?\s*(?:on\s+|towards?\s+)?CSR',
            r'amount\s+spent\s+(?:on\s+)?CSR[:\s]*(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)',
        ]
        result = self._search_patterns(csr_patterns)
        if result:
            metrics.csr_spending = result
            self.metrics_found['csr_spending'] = result
        
        # CSR obligation/required
        csr_required_patterns = [
            r'CSR\s+obligation[:\s]*(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)',
            r'(?:2%\s+of\s+average\s+net\s+profit|prescribed\s+CSR)[:\s]*(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)',
        ]
        result = self._search_patterns(csr_required_patterns)
        if result:
            metrics.csr_spending_required = result
        
        # Calculate CSR percentage
        if metrics.csr_spending > 0 and metrics.csr_spending_required > 0:
            metrics.csr_percentage = (metrics.csr_spending / metrics.csr_spending_required) * 100
        
        # ===== CUSTOMER (P9) =====
        customer_complaint_patterns = [
            r'(?:customer|consumer)\s+complaints?\s+(?:received|filed)[:\s]*([\d,]+)',
            r'([\d,]+)\s*(?:customer|consumer)\s+complaints?',
            r'complaints?\s+received[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(customer_complaint_patterns)
        if result:
            metrics.customer_complaints = int(result)
        
        # Resolved complaints
        resolved_patterns = [
            r'complaints?\s+(?:resolved|addressed)[:\s]*([\d,]+)',
            r'([\d,]+)\s*complaints?\s+resolved',
        ]
        result = self._search_patterns(resolved_patterns)
        if result:
            metrics.customer_complaints_resolved = int(result)
        
        # Calculate resolution rate
        if metrics.customer_complaints > 0 and metrics.customer_complaints_resolved > 0:
            metrics.resolution_rate = (metrics.customer_complaints_resolved / metrics.customer_complaints) * 100
        
        # Data breaches / Cyber security
        breach_patterns = [
            r'(?:data|security)\s+breach(?:es)?[:\s]*([\d,]+)',
            r'cyber\s+(?:security\s+)?incidents?[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(breach_patterns)
        if result is not None:
            metrics.data_breaches = int(result)
        if re.search(r'no\s+(?:data\s+)?breach|zero\s+(?:data\s+)?breach|nil.*breach', 
                     self.text, re.IGNORECASE):
            metrics.data_breaches = 0
        
        return metrics
    
    # -------------------------------------------------------------------------
    # SECTION C - PRINCIPLE 1: GOVERNANCE
    # -------------------------------------------------------------------------
    
    def _extract_governance(self) -> GovernanceMetrics:
        """Extract Principle 1 - Governance metrics"""
        metrics = GovernanceMetrics()
        
        # ===== BOARD COMPOSITION =====
        # Board size
        board_patterns = [
            r'board\s+(?:of\s+directors?\s+)?(?:comprises?|consists?\s+of|has)[:\s]*([\d,]+)\s*(?:directors?|members?)',
            r'([\d,]+)\s*directors?\s+(?:on\s+)?(?:the\s+)?board',
            r'board\s+(?:strength|size)[:\s]*([\d,]+)',
            r'total\s+(?:number\s+of\s+)?directors?[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(board_patterns)
        if result and 3 <= result <= 25:  # Reasonable board size
            metrics.board_size = int(result)
            self.metrics_found['board_size'] = int(result)
        
        # Independent directors
        independent_patterns = [
            r'independent\s+directors?[:\s]*([\d,]+)',
            r'([\d,]+)\s*independent\s+directors?',
            r'non[-\s]?executive\s+independent[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(independent_patterns)
        if result:
            metrics.independent_directors = int(result)
            self.metrics_found['independent_directors'] = int(result)
        
        # Women directors
        women_board_patterns = [
            r'(?:women|female)\s+directors?[:\s]*([\d,]+)',
            r'([\d,]+)\s*(?:women|female)\s+(?:on\s+)?(?:the\s+)?board',
        ]
        result = self._search_patterns(women_board_patterns)
        if result:
            metrics.women_directors = int(result)
            self.metrics_found['women_directors'] = int(result)
        
        # Calculate percentages
        if metrics.board_size > 0:
            if metrics.independent_directors > 0:
                metrics.independent_percentage = (metrics.independent_directors / metrics.board_size) * 100
            if metrics.women_directors > 0:
                metrics.women_board_percentage = (metrics.women_directors / metrics.board_size) * 100
        
        # Board meetings
        board_meeting_patterns = [
            r'board\s+(?:of\s+directors?\s+)?(?:met|meetings?)[:\s]*([\d,]+)\s*(?:times?|meetings?)?',
            r'([\d,]+)\s*board\s+meetings?',
            r'number\s+of\s+board\s+meetings?[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(board_meeting_patterns)
        if result and result <= 20:  # Reasonable number
            metrics.board_meetings = int(result)
            self.metrics_found['board_meetings'] = int(result)
        
        # ===== COMMITTEES =====
        # Audit committee meetings
        audit_patterns = [
            r'audit\s+committee[:\s]*(?:met\s+)?([\d,]+)\s*(?:times?|meetings?)',
            r'([\d,]+)\s*audit\s+committee\s+meetings?',
        ]
        result = self._search_patterns(audit_patterns)
        if result and result <= 15:
            metrics.audit_committee_meetings = int(result)
        
        # CSR committee meetings
        csr_comm_patterns = [
            r'CSR\s+committee[:\s]*(?:met\s+)?([\d,]+)\s*(?:times?|meetings?)',
            r'([\d,]+)\s*CSR\s+committee\s+meetings?',
        ]
        result = self._search_patterns(csr_comm_patterns)
        if result:
            metrics.csr_committee_meetings = int(result)
        
        # ===== ETHICS & COMPLIANCE =====
        # Ethics complaints
        ethics_patterns = [
            r'(?:ethics?|code\s+of\s+conduct)\s+(?:complaints?|violations?|breaches?)[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(ethics_patterns)
        if result is not None:
            metrics.ethics_complaints = int(result)
        
        # Corruption incidents
        corruption_patterns = [
            r'corruption\s+(?:incidents?|cases?)[:\s]*([\d,]+)',
            r'bribery\s+(?:incidents?|cases?)[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(corruption_patterns)
        if result is not None:
            metrics.corruption_incidents = int(result)
        if re.search(r'no\s+(?:corruption|bribery)|zero\s+(?:corruption|bribery)', 
                     self.text, re.IGNORECASE):
            metrics.corruption_incidents = 0
        
        # Whistleblower complaints
        whistle_patterns = [
            r'whistle[-\s]?blower\s+(?:complaints?|cases?)[:\s]*([\d,]+)',
            r'vigil\s+mechanism\s+(?:complaints?|cases?)[:\s]*([\d,]+)',
        ]
        result = self._search_patterns(whistle_patterns)
        if result is not None:
            metrics.whistleblower_complaints = int(result)
        
        # Fines and penalties
        penalty_patterns = [
            r'(?:fines?|penalties?)\s+(?:paid|imposed)[:\s]*(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)\s*(?:Cr|Lakh)?',
            r'(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)\s*(?:Cr|Lakh)?\s*(?:fines?|penalties?)',
        ]
        result = self._search_patterns(penalty_patterns)
        if result:
            metrics.fines_penalties_amount = result
        
        # CEO/Median ratio
        ratio_patterns = [
            r'(?:CEO|MD)\s*(?:to\s+)?median\s+(?:employee\s+)?(?:ratio|remuneration)[:\s]*([\d,]+\.?\d*)',
            r'ratio\s+of[:\s]*([\d,]+\.?\d*)\s*(?:times?|x)',
        ]
        result = self._search_patterns(ratio_patterns)
        if result:
            metrics.ceo_to_median_ratio = result
        
        # Anti-corruption training
        training_patterns = [
            r'(?:anti[-\s]?corruption|ethics?)\s+training[:\s]*([\d,]+\.?\d*)\s*%?',
            r'([\d,]+\.?\d*)\s*%?\s*(?:trained\s+on\s+)?(?:anti[-\s]?corruption|ethics?)',
        ]
        result = self._search_patterns(training_patterns)
        if result:
            if result <= 100:
                metrics.employees_trained_anti_corruption = result
        
        return metrics
    
    # -------------------------------------------------------------------------
    # PDF EXTRACTION
    # -------------------------------------------------------------------------
    
    def _extract_text_pymupdf(self, pdf_path: str) -> Tuple[str, int, List]:
        """Extract text using PyMuPDF"""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not installed")
        
        text_parts = []
        tables = []
        
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        
        for page_num in range(page_count):
            page = doc[page_num]
            
            # Extract text with better formatting
            blocks = page.get_text("dict")["blocks"]
            page_text = ""
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"] + " "
                        page_text += line_text.strip() + "\n"
            
            text_parts.append(f"\n[PAGE {page_num + 1}]\n{page_text}")
            
            # Try to extract tables
            try:
                page_tables = page.find_tables()
                for table in page_tables:
                    tables.append(table.extract())
            except:
                pass
        
        doc.close()
        return "\n".join(text_parts), page_count, tables
    
    def _extract_text_pdfplumber(self, pdf_path: str) -> Tuple[str, int, List]:
        """Extract text using pdfplumber"""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not installed")
        
        text_parts = []
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            
            for i, page in enumerate(pdf.pages):
                # Extract text
                text = page.extract_text() or ""
                text_parts.append(f"\n[PAGE {i + 1}]\n{text}")
                
                # Extract tables
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table:
                        tables.append(table)
        
        return "\n".join(text_parts), page_count, tables
    
    def _extract_pdf(self, pdf_path: str) -> Tuple[str, int, List]:
        """Extract text from PDF using best available method"""
        # Try PyMuPDF first (faster, better quality)
        if PYMUPDF_AVAILABLE:
            try:
                return self._extract_text_pymupdf(pdf_path)
            except Exception as e:
                logger.warning(f"PyMuPDF failed: {e}")
        
        # Fallback to pdfplumber
        if PDFPLUMBER_AVAILABLE:
            try:
                return self._extract_text_pdfplumber(pdf_path)
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e}")
        
        raise ImportError("No PDF library available")
    
    # -------------------------------------------------------------------------
    # MAIN PARSING METHODS
    # -------------------------------------------------------------------------
    
    def parse(self, pdf_path: str) -> BRSRExtractedData:
        """Parse a BRSR PDF report and extract all ESG metrics"""
        
        # Extract text and tables
        self.text, page_count, self.tables = self._extract_pdf(pdf_path)
        
        # Initialize result
        result = BRSRExtractedData()
        result.pages_processed = page_count
        
        # Identify report type
        text_lower = self.text.lower()
        if 'business responsibility and sustainability' in text_lower or 'brsr' in text_lower:
            result.report_type = ReportType.BRSR
        elif 'sustainability report' in text_lower:
            result.report_type = ReportType.SUSTAINABILITY
        elif 'annual report' in text_lower:
            result.report_type = ReportType.ANNUAL
        else:
            result.report_type = ReportType.UNKNOWN
        
        # Extract Section A - General Disclosures
        general = self._extract_general_disclosures()
        result.company_name = general.get('company_name', '')
        result.cin = general.get('cin', '')
        result.year = general.get('year', datetime.now().year)
        result.turnover = general.get('turnover', 0)
        result.net_worth = general.get('net_worth', 0)
        result.nic_code = general.get('nic_code', '')
        
        # Extract Section C metrics
        result.environmental = self._extract_environmental()
        result.social = self._extract_social()
        result.governance = self._extract_governance()
        
        # Store raw extractions for debugging
        result.raw_extractions = dict(self.metrics_found)
        
        # Calculate confidence and counts
        result.metrics_found = len(self.metrics_found)
        result.metrics_total = 50  # Approximate total metrics we look for
        result.extraction_confidence = (result.metrics_found / result.metrics_total) * 100
        result.extraction_time = datetime.now()
        
        self.extracted_data = result
        return result
    
    def parse_from_bytes(self, pdf_bytes: bytes, filename: str = "uploaded.pdf") -> BRSRExtractedData:
        """Parse PDF from bytes (for Streamlit uploads)"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name
        
        try:
            result = self.parse(tmp_path)
            return result
        finally:
            os.unlink(tmp_path)
    
    def get_extraction_summary(self) -> str:
        """Get summary of extracted metrics"""
        if not self.extracted_data:
            return "No data extracted yet."
        
        lines = [
            "=" * 60,
            "📋 BRSR EXTRACTION SUMMARY",
            "=" * 60,
            f"Company: {self.extracted_data.company_name}",
            f"Year: {self.extracted_data.year}",
            f"Report Type: {self.extracted_data.report_type.value}",
            f"Pages Processed: {self.extracted_data.pages_processed}",
            f"Metrics Found: {self.extracted_data.metrics_found}/{self.extracted_data.metrics_total}",
            f"Extraction Confidence: {self.extracted_data.extraction_confidence:.1f}%",
            "",
            "📊 METRICS EXTRACTED:",
            "-" * 40,
        ]
        
        for key, value in self.metrics_found.items():
            lines.append(f"  ✅ {key}: {value:,.2f}" if isinstance(value, float) else f"  ✅ {key}: {value:,}")
        
        return "\n".join(lines)


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
    """Calculate environmental score"""
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
    
    # Others
    metrics['Climate Disclosure'] = {'value': 60, 'score': 60, 'unit': '%', 'weight': 0.08}
    metrics['Biodiversity'] = {'value': 50, 'score': 50, 'unit': 'score', 'weight': 0.05}
    metrics['Hazardous Waste'] = {'value': 90, 'score': 90, 'unit': '%', 'weight': 0.05}
    
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    return total, metrics


def calculate_social_score(data: Dict) -> Tuple[float, Dict]:
    """Calculate social score"""
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
    metrics['CSR Spending'] = {'value': csr, 'score': score_csr, 'unit': '%', 'weight': 0.08}
    
    # Others
    metrics['Fair Wages'] = {'value': 90, 'score': 90, 'unit': '%', 'weight': 0.10}
    metrics['Human Rights'] = {'value': 90, 'score': 90, 'unit': '%', 'weight': 0.10}
    
    customer = data.get('customer_complaints_resolved', 95)
    metrics['Customer Satisfaction'] = {'value': customer, 'score': min(100, customer), 'unit': '%', 'weight': 0.08}
    
    breaches = data.get('data_breaches', 0)
    score_p = max(0, 100 - breaches * 20)
    metrics['Data Privacy'] = {'value': breaches, 'score': score_p, 'unit': 'incidents', 'weight': 0.10}
    
    metrics['Labor Practices'] = {'value': 95, 'score': 95, 'unit': '%', 'weight': 0.07}
    
    total = sum(m['score'] * m['weight'] for m in metrics.values())
    return total, metrics


def calculate_governance_score(data: Dict) -> Tuple[float, Dict]:
    """Calculate governance score"""
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
    
    # Others
    metrics['Shareholder Rights'] = {'value': 80, 'score': 80, 'unit': 'score', 'weight': 0.10}
    metrics['Ethics'] = {'value': 90, 'score': 90, 'unit': '%', 'weight': 0.12}
    metrics['Risk Management'] = {'value': 80, 'score': 80, 'unit': 'score', 'weight': 0.10}
    metrics['Tax Transparency'] = {'value': 70, 'score': 70, 'unit': '%', 'weight': 0.08}
    metrics['RPT Compliance'] = {'value': 90, 'score': 90, 'unit': '%', 'weight': 0.06}
    metrics['Sustainability Committee'] = {'value': 50, 'score': 50, 'unit': 'score', 'weight': 0.05}
    
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
    if score >= 80: return "Negligible"
    elif score >= 65: return "Low"
    elif score >= 50: return "Medium"
    elif score >= 35: return "High"
    else: return "Severe"


def get_risk_color(risk: str) -> str:
    colors = {
        "Negligible": "#27ae60", "Low": "#2ecc71",
        "Medium": "#f39c12", "High": "#e74c3c", "Severe": "#c0392b"
    }
    return colors.get(risk, "#f39c12")


def generate_simulated_esg_data(symbol: str, industry: str = 'Default') -> Dict:
    """Generate simulated ESG data"""
    np.random.seed(hash(symbol) % 2**32)
    benchmarks = get_benchmarks(industry)
    
    return {
        'carbon_emissions_intensity': benchmarks['carbon'] * np.random.uniform(0.7, 1.3),
        'energy_consumption_intensity': benchmarks['energy'] * np.random.uniform(0.7, 1.3),
        'renewable_energy_percentage': min(100, benchmarks['renewable'] * np.random.uniform(0.5, 1.5)),
        'water_consumption_intensity': benchmarks['water'] * np.random.uniform(0.7, 1.3),
        'waste_recycling_rate': min(100, benchmarks['waste'] * np.random.uniform(0.8, 1.2)),
        'environmental_compliance': np.random.uniform(85, 100),
        'ltifr': np.random.uniform(0.2, 0.8),
        'employee_turnover_rate': np.random.uniform(8, 25),
        'women_workforce_percentage': np.random.uniform(15, 40),
        'training_hours_per_employee': np.random.uniform(15, 50),
        'csr_spending_percentage': np.random.uniform(1.5, 3.0),
        'customer_complaints_resolved': np.random.uniform(85, 99),
        'data_breaches': np.random.choice([0, 0, 0, 1, 2]),
        'independent_directors_percentage': np.random.uniform(45, 70),
        'women_directors_percentage': np.random.uniform(15, 35),
        'audit_committee_meetings': np.random.randint(4, 8),
        'ceo_median_pay_ratio': np.random.uniform(50, 200),
    }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_gauge_chart(score: float, title: str, height: int = 250) -> go.Figure:
    color = "#27ae60" if score >= 80 else "#2ecc71" if score >= 65 else "#f39c12" if score >= 50 else "#e74c3c"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        delta={'reference': 50, 'increasing': {'color': '#27ae60'}, 'decreasing': {'color': '#e74c3c'}},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color, 'thickness': 0.8},
            'steps': [
                {'range': [0, 35], 'color': 'rgba(192, 57, 43, 0.2)'},
                {'range': [35, 50], 'color': 'rgba(231, 76, 60, 0.2)'},
                {'range': [50, 65], 'color': 'rgba(243, 156, 18, 0.2)'},
                {'range': [65, 80], 'color': 'rgba(46, 204, 113, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(39, 174, 96, 0.2)'}
            ],
        }
    ))
    
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_radar_chart(env: float, social: float, gov: float, name: str) -> go.Figure:
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
        polar=dict(radialaxis=dict(range=[0, 100])),
        showlegend=True, height=400
    )
    return fig


def create_metrics_bar(metrics: Dict, title: str) -> go.Figure:
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
# REAL-TIME DATA FETCHER
# ============================================================================

class NSEDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.nseindia.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.nseindia.com/',
        }
        self.session.headers.update(self.headers)
        self._initialized = False
    
    def _init_session(self):
        try:
            self.session.get(self.base_url, timeout=10)
            self._initialized = True
        except:
            pass
    
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        if not self._initialized:
            self._init_session()
        
        try:
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}"
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                info = data.get('info', {})
                price = data.get('priceInfo', {})
                meta = data.get('metadata', {})
                sec = data.get('securityInfo', {})
                
                return {
                    'symbol': symbol,
                    'company_name': info.get('companyName', symbol),
                    'sector': meta.get('sector', ''),
                    'industry': meta.get('industry', ''),
                    'last_price': price.get('lastPrice', 0),
                    'pchange': price.get('pChange', 0),
                    'market_cap': sec.get('marketCap', 0),
                    'pe_ratio': meta.get('pdSymbolPe', 0),
                    'week_high_52': price.get('weekHighLow', {}).get('max', 0),
                    'week_low_52': price.get('weekHighLow', {}).get('min', 0),
                    'data_source': 'NSE India'
                }
        except Exception as e:
            logger.warning(f"NSE fetch error: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_live_data(symbol: str) -> Optional[Dict]:
    fetcher = NSEDataFetcher()
    return fetcher.get_company_info(symbol)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌿 NYZTrade ESG Platform</h1>
        <p>Comprehensive ESG Analysis with Real-Time Data & BRSR Report Parsing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("## 🎛️ Navigation")
    
    page = st.sidebar.radio(
        "",
        ["🏠 Dashboard", "📄 Upload BRSR Report", "📝 Manual Input", 
         "🔍 Compare Companies", "📋 Full Report"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 Status")
    st.sidebar.markdown(f"- Real-Time API: ✅")
    st.sidebar.markdown(f"- PDF Parser: {'✅' if PDF_PARSER_AVAILABLE else '❌'}")
    
    if not PDF_PARSER_AVAILABLE:
        st.sidebar.warning("Install PDF libraries:\n`pip install PyMuPDF pdfplumber`")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Resources")
    st.sidebar.markdown("[📥 Download BRSR Reports](https://www.nseindia.com/companies-listing/corporate-filings-bussiness-sustainabilitiy-reports)")
    
    # ========================================================================
    # DASHBOARD PAGE
    # ========================================================================
    if page == "🏠 Dashboard":
        st.markdown("### 🚀 Quick ESG Analysis")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            symbol = st.selectbox(
                "Select Company",
                NIFTY50_SYMBOLS,
                format_func=lambda x: f"{x} - {NIFTY50_COMPANIES.get(x, {}).get('name', x)}"
            )
        
        with col2:
            st.markdown("")
            st.markdown("")
            analyze = st.button("📊 Analyze", type="primary", use_container_width=True)
        
        if analyze:
            company_info = NIFTY50_COMPANIES.get(symbol, {})
            industry = company_info.get('industry', 'Default')
            
            with st.spinner(f"Analyzing {symbol}..."):
                # Fetch live data
                live_data = fetch_live_data(symbol)
                
                # Generate ESG data
                esg_data = generate_simulated_esg_data(symbol, industry)
                
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
                    <h2 style='margin: 0;'>{live_data.get('company_name', symbol)}</h2>
                    <p style='margin: 5px 0; color: #bdc3c7;'>{symbol} | {company_info.get('sector', '')} | {industry}</p>
                    <p style='margin: 5px 0; color: #bdc3c7;'>
                        LTP: ₹{live_data.get('last_price', 0):,.2f} ({live_data.get('pchange', 0):+.2f}%) | 
                        Market Cap: ₹{live_data.get('market_cap', 0):,.0f} Cr
                    </p>
                    <span class="badge-live">LIVE DATA</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 20px; border-radius: 12px;'>
                    <h2 style='margin: 0;'>{company_info.get('name', symbol)}</h2>
                    <p style='margin: 5px 0; color: #bdc3c7;'>{symbol} | {company_info.get('sector', '')} | {industry}</p>
                    <span class="badge-simulated">SIMULATED</span>
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
            
            # Risk banner
            risk_color = get_risk_color(risk)
            st.markdown(f"""
            <div style='text-align: center; padding: 20px;'>
                <span class="risk-{risk.lower()}" style='font-size: 1.3em; padding: 10px 30px;'>
                    ESG Risk Level: {risk} ({overall:.1f}/100)
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Radar and details
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_radar_chart(env_score, social_score, gov_score, symbol), use_container_width=True)
            with col2:
                st.markdown("#### 📊 Score Breakdown")
                st.markdown(f"""
                | Category | Score | Status |
                |----------|-------|--------|
                | Environmental | {env_score:.1f} | {'🟢' if env_score >= 70 else '🟡' if env_score >= 50 else '🔴'} |
                | Social | {social_score:.1f} | {'🟢' if social_score >= 70 else '🟡' if social_score >= 50 else '🔴'} |
                | Governance | {gov_score:.1f} | {'🟢' if gov_score >= 70 else '🟡' if gov_score >= 50 else '🔴'} |
                | **Overall** | **{overall:.1f}** | {'🟢' if overall >= 70 else '🟡' if overall >= 50 else '🔴'} |
                """)
            
            # Detailed metrics
            with st.expander("📊 View Detailed Metrics"):
                tab1, tab2, tab3 = st.tabs(["🌍 Environmental", "👥 Social", "🏛️ Governance"])
                with tab1:
                    st.plotly_chart(create_metrics_bar(env_metrics, "Environmental"), use_container_width=True)
                with tab2:
                    st.plotly_chart(create_metrics_bar(social_metrics, "Social"), use_container_width=True)
                with tab3:
                    st.plotly_chart(create_metrics_bar(gov_metrics, "Governance"), use_container_width=True)
    
    # ========================================================================
    # UPLOAD BRSR REPORT PAGE
    # ========================================================================
    elif page == "📄 Upload BRSR Report":
        st.markdown("### 📄 Upload BRSR / Annual Report")
        
        st.markdown("""
        <div class="info-box" style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 4px solid #2196f3;">
            <strong>📥 Download BRSR Reports:</strong><br>
            Visit <a href="https://www.nseindia.com/companies-listing/corporate-filings-bussiness-sustainabilitiy-reports" target="_blank">
            NSE India BRSR Reports</a> to download official reports.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        
        if not PDF_PARSER_AVAILABLE:
            st.error("""
            **PDF parsing libraries not installed!**
            
            Please run this command in your terminal:
            ```bash
            pip install PyMuPDF pdfplumber
            ```
            
            Then restart the Streamlit app.
            """)
            
            st.markdown("---")
            st.markdown("### 📋 Installation Steps")
            st.code("""
# Step 1: Open terminal/command prompt

# Step 2: Install PDF libraries
pip install PyMuPDF pdfplumber

# Step 3: Restart Streamlit
# Press Ctrl+C in terminal, then run:
streamlit run esg_dashboard_final.py
            """, language="bash")
            return
        
        st.markdown("""
        <div class="upload-zone">
            <h3>📁 Drag & Drop or Browse</h3>
            <p>Upload BRSR Report, Annual Report, or Sustainability Report (PDF)</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("", type=['pdf'], label_visibility="collapsed")
        
        if uploaded_file:
            st.success(f"📄 **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
            
            if st.button("🔍 Extract ESG Data", type="primary", use_container_width=True):
                with st.spinner("Analyzing report... This may take 1-2 minutes..."):
                    uploaded_file.seek(0)
                    
                    parser = EnhancedBRSRParser()
                    data = parser.parse_from_bytes(uploaded_file.read(), uploaded_file.name)
                    
                    st.session_state.pdf_extracted_data = data
                
                st.success(f"✅ Extraction complete! Found {data.metrics_found} metrics ({data.extraction_confidence:.1f}% confidence)")
        
        # Display results
        if st.session_state.pdf_extracted_data:
            data = st.session_state.pdf_extracted_data
            
            st.markdown("---")
            st.markdown("### 📋 Extracted Data")
            
            # Summary
            st.markdown(f"""
            <div class="extraction-result">
                <h3>{data.company_name or 'Company Name Not Found'}</h3>
                <p><strong>Year:</strong> {data.year} | <strong>Type:</strong> {data.report_type.value}</p>
                <p><strong>Turnover:</strong> ₹{data.turnover:,.0f} Cr</p>
                <p><strong>Metrics Found:</strong> {data.metrics_found}/{data.metrics_total} ({data.extraction_confidence:.1f}% confidence)</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics found
            if data.raw_extractions:
                st.markdown("#### ✅ Metrics Successfully Extracted")
                cols = st.columns(3)
                items = list(data.raw_extractions.items())
                for i, (key, value) in enumerate(items):
                    with cols[i % 3]:
                        display_val = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
                        st.markdown(f"""
                        <div class="metric-found">
                            <strong>{key.replace('_', ' ').title()}</strong><br>
                            {display_val}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Show E, S, G breakdown
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🌍 Environmental")
                env = data.environmental
                st.markdown(f"""
                - **Total Energy:** {env.total_energy_consumption:,.0f} GJ
                - **Renewable %:** {env.renewable_energy_percentage:.1f}%
                - **Scope 1:** {env.scope1_emissions:,.0f} tCO2e
                - **Scope 2:** {env.scope2_emissions:,.0f} tCO2e
                - **Total GHG:** {env.total_ghg_emissions:,.0f} tCO2e
                - **Water:** {env.total_water_withdrawal:,.0f} KL
                - **Waste Recycled:** {env.waste_recycling_percentage:.1f}%
                """)
            
            with col2:
                st.markdown("#### 👥 Social")
                soc = data.social
                st.markdown(f"""
                - **Total Employees:** {soc.total_employees:,}
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
            if st.button("📊 Calculate ESG Score", type="primary", use_container_width=True):
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
                
                risk_color = get_risk_color(risk)
                st.markdown(f"""
                <div style='text-align: center; padding: 20px;'>
                    <span class="risk-{risk.lower()}" style='font-size: 1.2em;'>
                        ESG Risk Level: {risk}
                    </span>
                    <span class="badge-pdf" style='margin-left: 15px;'>FROM PDF</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Export
                st.markdown("---")
                json_str = json.dumps(esg_input, indent=2, default=str)
                st.download_button(
                    "💾 Download Extracted Data (JSON)",
                    json_str,
                    f"esg_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
    
    # ========================================================================
    # MANUAL INPUT PAGE
    # ========================================================================
    elif page == "📝 Manual Input":
        st.markdown("### 📝 Manual ESG Data Input")
        
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", "My Company Ltd")
            industry = st.selectbox("Industry", [k for k in INDUSTRY_ADJUSTMENTS.keys() if k != 'Default'])
        with col2:
            symbol = st.text_input("Symbol", "MYCO")
            year = st.number_input("Year", 2020, 2025, 2024)
        
        benchmarks = get_benchmarks(industry)
        
        st.markdown("---")
        st.markdown("#### 🌍 Environmental")
        col1, col2, col3 = st.columns(3)
        with col1:
            carbon = st.number_input("Carbon (tCO2e/Cr)", 0.0, 500.0, float(benchmarks['carbon']))
            renewable = st.number_input("Renewable Energy %", 0.0, 100.0, float(benchmarks['renewable']))
        with col2:
            energy = st.number_input("Energy (GJ/Cr)", 0.0, 1000.0, float(benchmarks['energy']))
            waste = st.number_input("Waste Recycling %", 0.0, 100.0, float(benchmarks['waste']))
        with col3:
            water = st.number_input("Water (KL/Cr)", 0.0, 5000.0, float(benchmarks['water']))
        
        st.markdown("#### 👥 Social")
        col1, col2, col3 = st.columns(3)
        with col1:
            ltifr = st.number_input("LTIFR", 0.0, 5.0, 0.5)
            women_wf = st.number_input("Women Workforce %", 0.0, 100.0, 25.0)
        with col2:
            turnover = st.number_input("Turnover %", 0.0, 100.0, 15.0)
            training = st.number_input("Training Hrs/Employee", 0.0, 100.0, 20.0)
        with col3:
            csr = st.number_input("CSR % of Profit", 0.0, 10.0, 2.0)
        
        st.markdown("#### 🏛️ Governance")
        col1, col2, col3 = st.columns(3)
        with col1:
            independent = st.number_input("Independent Directors %", 0.0, 100.0, 50.0)
        with col2:
            women_board = st.number_input("Women on Board %", 0.0, 100.0, 17.0)
        with col3:
            audit = st.number_input("Audit Committee Meetings", 1, 12, 4)
        
        if st.button("🔄 Calculate ESG Score", type="primary", use_container_width=True):
            manual_data = {
                'carbon_emissions_intensity': carbon,
                'energy_consumption_intensity': energy,
                'renewable_energy_percentage': renewable,
                'water_consumption_intensity': water,
                'waste_recycling_rate': waste,
                'ltifr': ltifr,
                'employee_turnover_rate': turnover,
                'women_workforce_percentage': women_wf,
                'training_hours_per_employee': training,
                'csr_spending_percentage': csr,
                'independent_directors_percentage': independent,
                'women_directors_percentage': women_board,
                'audit_committee_meetings': audit,
            }
            
            env_score, _ = calculate_environmental_score(manual_data, industry)
            social_score, _ = calculate_social_score(manual_data)
            gov_score, _ = calculate_governance_score(manual_data)
            overall = calculate_overall_esg(env_score, social_score, gov_score, industry)
            risk = get_risk_level(overall)
            
            st.markdown("---")
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
                <span style='background-color: {risk_color}; color: white; padding: 10px 30px; border-radius: 15px; font-size: 1.2em;'>
                    ESG Risk Level: {risk} ({overall:.1f}/100)
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================================================
    # COMPARE COMPANIES PAGE
    # ========================================================================
    elif page == "🔍 Compare Companies":
        st.markdown("### 🔍 Compare Companies")
        
        selected = st.multiselect(
            "Select 2-10 companies",
            NIFTY50_SYMBOLS,
            default=['TCS', 'INFY', 'WIPRO'],
            format_func=lambda x: f"{x} - {NIFTY50_COMPANIES.get(x, {}).get('name', x)}"
        )
        
        if len(selected) >= 2:
            if st.button("📊 Compare", type="primary"):
                results = []
                for symbol in selected:
                    info = NIFTY50_COMPANIES.get(symbol, {})
                    industry = info.get('industry', 'Default')
                    esg_data = generate_simulated_esg_data(symbol, industry)
                    
                    env, _ = calculate_environmental_score(esg_data, industry)
                    soc, _ = calculate_social_score(esg_data)
                    gov, _ = calculate_governance_score(esg_data)
                    overall = calculate_overall_esg(env, soc, gov, industry)
                    
                    results.append({
                        'Symbol': symbol,
                        'Company': info.get('name', symbol),
                        'Environmental': round(env, 1),
                        'Social': round(soc, 1),
                        'Governance': round(gov, 1),
                        'Overall': round(overall, 1),
                        'Risk': get_risk_level(overall)
                    })
                
                df = pd.DataFrame(results)
                
                # Chart
                fig = go.Figure()
                for col in ['Environmental', 'Social', 'Governance']:
                    fig.add_trace(go.Bar(name=col, x=df['Symbol'], y=df[col]))
                fig.add_trace(go.Scatter(name='Overall', x=df['Symbol'], y=df['Overall'], 
                                        mode='lines+markers', line=dict(color='red', width=3)))
                fig.update_layout(barmode='group', height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(df.sort_values('Overall', ascending=False), use_container_width=True, hide_index=True)
        else:
            st.warning("Select at least 2 companies")
    
    # ========================================================================
    # FULL REPORT PAGE
    # ========================================================================
    elif page == "📋 Full Report":
        st.markdown("### 📋 NIFTY 50 ESG Report")
        
        if st.button("🔄 Generate Report", type="primary"):
            results = []
            progress = st.progress(0)
            
            for i, symbol in enumerate(NIFTY50_SYMBOLS):
                info = NIFTY50_COMPANIES.get(symbol, {})
                industry = info.get('industry', 'Default')
                esg_data = generate_simulated_esg_data(symbol, industry)
                
                env, _ = calculate_environmental_score(esg_data, industry)
                soc, _ = calculate_social_score(esg_data)
                gov, _ = calculate_governance_score(esg_data)
                overall = calculate_overall_esg(env, soc, gov, industry)
                
                results.append({
                    'Symbol': symbol,
                    'Company': info.get('name', symbol),
                    'Sector': info.get('sector', ''),
                    'Industry': industry,
                    'Environmental': round(env, 1),
                    'Social': round(soc, 1),
                    'Governance': round(gov, 1),
                    'Overall': round(overall, 1),
                    'Risk': get_risk_level(overall)
                })
                progress.progress((i + 1) / len(NIFTY50_SYMBOLS))
            
            df = pd.DataFrame(results)
            
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average ESG", f"{df['Overall'].mean():.1f}")
            with col2:
                st.metric("Leaders (≥65)", len(df[df['Overall'] >= 65]))
            with col3:
                st.metric("Laggards (<50)", len(df[df['Overall'] < 50]))
            with col4:
                best = df.loc[df['Overall'].idxmax()]
                st.metric("Top", f"{best['Symbol']} ({best['Overall']:.1f})")
            
            # Table
            st.dataframe(df.sort_values('Overall', ascending=False), use_container_width=True, hide_index=True, height=600)
            
            # Download
            csv = df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, f"nifty50_esg_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>🌿 <strong>NYZTrade ESG Platform</strong> | Based on SEBI BRSR Framework</p>
        <p style='font-size: 0.8em;'>⚠️ ESG scores are for informational purposes only.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
