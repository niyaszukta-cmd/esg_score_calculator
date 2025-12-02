# ============================================================================
# NYZTRADE - ESG/SUSTAINABILITY SCORE CALCULATOR FOR INDIAN COMPANIES
# API-Based System with BRSR Framework Compliance
# ============================================================================

"""
ESG (Environmental, Social, Governance) Score Calculator
Designed for Indian listed companies following SEBI's BRSR Framework

Author: NYZTrade
Version: 1.0
"""

import requests
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import warnings
import time
from dataclasses import dataclass, field
from enum import Enum
import re

warnings.filterwarnings('ignore')

print("=" * 80)
print("🌿 NYZTRADE - ESG/SUSTAINABILITY SCORE CALCULATOR")
print("📊 For Indian Listed Companies | BRSR Framework Compliant")
print("=" * 80)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class ESGCategory(Enum):
    """ESG Categories"""
    ENVIRONMENTAL = "Environmental"
    SOCIAL = "Social"
    GOVERNANCE = "Governance"


class RiskLevel(Enum):
    """ESG Risk Levels"""
    NEGLIGIBLE = "Negligible"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    SEVERE = "Severe"


@dataclass
class ESGMetric:
    """Individual ESG Metric"""
    name: str
    category: ESGCategory
    value: float
    weight: float
    score: float = 0.0
    benchmark: float = 0.0
    unit: str = ""
    source: str = ""
    year: int = 2024
    description: str = ""


@dataclass
class CompanyESGProfile:
    """Complete ESG Profile of a Company"""
    company_name: str
    symbol: str
    sector: str
    industry: str
    market_cap: float = 0.0
    
    # Scores
    environmental_score: float = 0.0
    social_score: float = 0.0
    governance_score: float = 0.0
    overall_esg_score: float = 0.0
    
    # Risk Assessment
    esg_risk_level: RiskLevel = RiskLevel.MEDIUM
    controversy_score: float = 0.0
    
    # Individual metrics
    metrics: List[ESGMetric] = field(default_factory=list)
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.now)
    data_year: int = 2024


# ============================================================================
# ESG WEIGHTS AND BENCHMARKS (BRSR ALIGNED)
# ============================================================================

class ESGWeightsConfig:
    """
    ESG Weights Configuration aligned with SEBI's BRSR Framework
    and Global Reporting Initiative (GRI) Standards
    """
    
    # Category Weights (Total = 100%)
    CATEGORY_WEIGHTS = {
        ESGCategory.ENVIRONMENTAL: 0.35,  # 35%
        ESGCategory.SOCIAL: 0.35,         # 35%
        ESGCategory.GOVERNANCE: 0.30      # 30%
    }
    
    # Environmental Metrics Weights (within E category)
    ENVIRONMENTAL_WEIGHTS = {
        'carbon_emissions_intensity': 0.20,      # Scope 1 + 2 emissions per revenue
        'energy_consumption_intensity': 0.15,    # Energy per unit output
        'renewable_energy_percentage': 0.15,     # % of renewable in total energy
        'water_consumption_intensity': 0.12,     # Water per unit output
        'waste_recycling_rate': 0.10,           # % waste recycled
        'hazardous_waste_management': 0.08,     # Proper disposal rate
        'biodiversity_initiatives': 0.05,       # Conservation efforts
        'environmental_compliance': 0.10,       # Regulatory compliance
        'climate_risk_disclosure': 0.05         # TCFD alignment
    }
    
    # Social Metrics Weights (within S category)
    SOCIAL_WEIGHTS = {
        'employee_health_safety': 0.15,         # LTIFR, safety incidents
        'employee_turnover_rate': 0.10,         # Retention metric
        'diversity_inclusion': 0.12,            # Gender diversity, PWD inclusion
        'training_development': 0.10,           # Training hours per employee
        'fair_wages': 0.10,                     # Living wage compliance
        'community_investment': 0.08,           # CSR spending
        'human_rights_compliance': 0.10,        # Supply chain human rights
        'customer_satisfaction': 0.08,          # NPS, complaints resolution
        'data_privacy_security': 0.10,          # Data breach incidents
        'labor_practices': 0.07                 # Child labor, forced labor checks
    }
    
    # Governance Metrics Weights (within G category)
    GOVERNANCE_WEIGHTS = {
        'board_independence': 0.15,             # % independent directors
        'board_diversity': 0.12,                # Gender diversity on board
        'audit_committee_quality': 0.12,        # Expertise, meetings
        'executive_compensation': 0.10,         # CEO-to-worker pay ratio
        'shareholder_rights': 0.10,             # Voting policies
        'ethics_anti_corruption': 0.12,         # Anti-bribery policies
        'risk_management': 0.10,                # ERM framework
        'tax_transparency': 0.08,               # Tax disclosure
        'related_party_transactions': 0.06,     # RPT policies
        'sustainability_committee': 0.05        # ESG oversight at board level
    }
    
    # Industry-specific weight adjustments
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
# SECTOR BENCHMARKS (INDIAN CONTEXT)
# ============================================================================

class IndianSectorBenchmarks:
    """
    Industry benchmarks for ESG metrics in Indian context
    Based on BRSR disclosures and industry reports
    """
    
    # Environmental Benchmarks (per crore revenue unless specified)
    ENVIRONMENTAL_BENCHMARKS = {
        'Oil & Gas': {
            'carbon_emissions_intensity': 150,      # tCO2e per crore
            'energy_consumption_intensity': 500,    # GJ per crore
            'renewable_energy_percentage': 10,      # %
            'water_consumption_intensity': 1000,    # KL per crore
            'waste_recycling_rate': 60,            # %
        },
        'Power': {
            'carbon_emissions_intensity': 200,
            'energy_consumption_intensity': 800,
            'renewable_energy_percentage': 25,
            'water_consumption_intensity': 2000,
            'waste_recycling_rate': 50,
        },
        'IT Services': {
            'carbon_emissions_intensity': 5,
            'energy_consumption_intensity': 50,
            'renewable_energy_percentage': 50,
            'water_consumption_intensity': 50,
            'waste_recycling_rate': 80,
        },
        'Banking': {
            'carbon_emissions_intensity': 2,
            'energy_consumption_intensity': 30,
            'renewable_energy_percentage': 40,
            'water_consumption_intensity': 30,
            'waste_recycling_rate': 85,
        },
        'Pharmaceuticals': {
            'carbon_emissions_intensity': 30,
            'energy_consumption_intensity': 150,
            'renewable_energy_percentage': 30,
            'water_consumption_intensity': 500,
            'waste_recycling_rate': 70,
        },
        'Default': {
            'carbon_emissions_intensity': 50,
            'energy_consumption_intensity': 200,
            'renewable_energy_percentage': 25,
            'water_consumption_intensity': 300,
            'waste_recycling_rate': 65,
        }
    }
    
    # Social Benchmarks
    SOCIAL_BENCHMARKS = {
        'Default': {
            'employee_turnover_rate': 15,           # % (lower is better)
            'ltifr': 0.5,                           # Lost Time Injury Frequency Rate
            'training_hours_per_employee': 20,      # hours
            'women_workforce_percentage': 25,       # %
            'pwd_employment_percentage': 1,         # %
            'csr_spending_percentage': 2,           # % of avg net profit
            'customer_complaints_resolved': 95,     # %
        }
    }
    
    # Governance Benchmarks
    GOVERNANCE_BENCHMARKS = {
        'Default': {
            'independent_directors_percentage': 50,  # %
            'women_directors_percentage': 17,        # % (SEBI mandate)
            'board_meetings_per_year': 6,           # minimum
            'audit_committee_meetings': 4,          # minimum
            'ceo_median_pay_ratio': 100,            # x times (lower is better)
            'promoter_holding': 50,                 # %
        }
    }


# ============================================================================
# NSE DATA FETCHER
# ============================================================================

class NSEDataFetcher:
    """Fetch company data from NSE India"""
    
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
        
        # Initialize session
        try:
            self.session.get(self.base_url, timeout=10)
            print("✅ Connected to NSE India")
        except Exception as e:
            print(f"⚠️ NSE connection warning: {e}")
    
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Fetch basic company information"""
        try:
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'company_name': data.get('info', {}).get('companyName', symbol),
                    'industry': data.get('metadata', {}).get('industry', 'Unknown'),
                    'sector': data.get('metadata', {}).get('sector', 'Unknown'),
                    'market_cap': data.get('securityInfo', {}).get('marketCap', 0),
                    'last_price': data.get('priceInfo', {}).get('lastPrice', 0),
                    'pe_ratio': data.get('metadata', {}).get('pdSymbolPe', 0),
                    'pb_ratio': data.get('metadata', {}).get('pdSectorPe', 0),
                    'isin': data.get('metadata', {}).get('isin', ''),
                }
            return None
        except Exception as e:
            print(f"❌ Error fetching company info for {symbol}: {e}")
            return None
    
    def get_corporate_governance_data(self, symbol: str) -> Optional[Dict]:
        """Fetch corporate governance data from NSE"""
        try:
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}&section=trade_info"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Error fetching governance data: {e}")
            return None
    
    def get_shareholding_pattern(self, symbol: str) -> Optional[Dict]:
        """Fetch shareholding pattern for governance analysis"""
        try:
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}&section=trade_info"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('shareholdingPatterns', {})
            return None
        except Exception as e:
            print(f"❌ Error fetching shareholding pattern: {e}")
            return None


# ============================================================================
# BRSR DATA PROCESSOR
# ============================================================================

class BRSRDataProcessor:
    """
    Process Business Responsibility and Sustainability Report (BRSR) data
    Following SEBI's mandatory disclosure framework
    """
    
    # BRSR Principle Mapping
    PRINCIPLES = {
        'P1': 'Ethics, Transparency and Accountability',
        'P2': 'Product Sustainability',
        'P3': 'Employee Well-being',
        'P4': 'Stakeholder Engagement',
        'P5': 'Human Rights',
        'P6': 'Environment',
        'P7': 'Policy Advocacy',
        'P8': 'Inclusive Growth',
        'P9': 'Customer Value'
    }
    
    @staticmethod
    def calculate_environmental_score(data: Dict) -> Tuple[float, List[ESGMetric]]:
        """Calculate Environmental Score from BRSR data"""
        metrics = []
        weights = ESGWeightsConfig.ENVIRONMENTAL_WEIGHTS
        
        # Carbon Emissions Intensity
        carbon_intensity = data.get('carbon_emissions_intensity', 50)
        benchmark = data.get('benchmark_carbon', 50)
        carbon_score = max(0, min(100, 100 - (carbon_intensity / benchmark * 50)))
        metrics.append(ESGMetric(
            name='Carbon Emissions Intensity',
            category=ESGCategory.ENVIRONMENTAL,
            value=carbon_intensity,
            weight=weights['carbon_emissions_intensity'],
            score=carbon_score,
            benchmark=benchmark,
            unit='tCO2e/Cr',
            source='BRSR - Principle 6',
            description='Scope 1 + Scope 2 emissions per crore revenue'
        ))
        
        # Energy Consumption Intensity
        energy_intensity = data.get('energy_consumption_intensity', 200)
        benchmark_energy = data.get('benchmark_energy', 200)
        energy_score = max(0, min(100, 100 - (energy_intensity / benchmark_energy * 50)))
        metrics.append(ESGMetric(
            name='Energy Consumption Intensity',
            category=ESGCategory.ENVIRONMENTAL,
            value=energy_intensity,
            weight=weights['energy_consumption_intensity'],
            score=energy_score,
            benchmark=benchmark_energy,
            unit='GJ/Cr',
            source='BRSR - Principle 6',
            description='Total energy consumption per crore revenue'
        ))
        
        # Renewable Energy Percentage
        renewable_pct = data.get('renewable_energy_percentage', 25)
        renewable_score = min(100, renewable_pct * 2)  # 50% renewable = 100 score
        metrics.append(ESGMetric(
            name='Renewable Energy Share',
            category=ESGCategory.ENVIRONMENTAL,
            value=renewable_pct,
            weight=weights['renewable_energy_percentage'],
            score=renewable_score,
            benchmark=50,
            unit='%',
            source='BRSR - Principle 6',
            description='Percentage of renewable energy in total consumption'
        ))
        
        # Water Consumption Intensity
        water_intensity = data.get('water_consumption_intensity', 300)
        benchmark_water = data.get('benchmark_water', 300)
        water_score = max(0, min(100, 100 - (water_intensity / benchmark_water * 50)))
        metrics.append(ESGMetric(
            name='Water Consumption Intensity',
            category=ESGCategory.ENVIRONMENTAL,
            value=water_intensity,
            weight=weights['water_consumption_intensity'],
            score=water_score,
            benchmark=benchmark_water,
            unit='KL/Cr',
            source='BRSR - Principle 6',
            description='Water withdrawal per crore revenue'
        ))
        
        # Waste Recycling Rate
        waste_recycling = data.get('waste_recycling_rate', 65)
        waste_score = min(100, waste_recycling * 1.25)  # 80% = 100 score
        metrics.append(ESGMetric(
            name='Waste Recycling Rate',
            category=ESGCategory.ENVIRONMENTAL,
            value=waste_recycling,
            weight=weights['waste_recycling_rate'],
            score=waste_score,
            benchmark=80,
            unit='%',
            source='BRSR - Principle 6',
            description='Percentage of waste recycled or reused'
        ))
        
        # Hazardous Waste Management
        hazardous_mgmt = data.get('hazardous_waste_management', 90)
        hazardous_score = min(100, hazardous_mgmt)
        metrics.append(ESGMetric(
            name='Hazardous Waste Management',
            category=ESGCategory.ENVIRONMENTAL,
            value=hazardous_mgmt,
            weight=weights['hazardous_waste_management'],
            score=hazardous_score,
            benchmark=100,
            unit='% compliance',
            source='BRSR - Principle 6',
            description='Proper disposal of hazardous waste'
        ))
        
        # Environmental Compliance
        env_compliance = data.get('environmental_compliance', 95)
        compliance_score = min(100, env_compliance)
        metrics.append(ESGMetric(
            name='Environmental Compliance',
            category=ESGCategory.ENVIRONMENTAL,
            value=env_compliance,
            weight=weights['environmental_compliance'],
            score=compliance_score,
            benchmark=100,
            unit='% compliance',
            source='BRSR - Principle 6',
            description='Compliance with environmental regulations'
        ))
        
        # Climate Risk Disclosure (TCFD alignment)
        climate_disclosure = data.get('climate_risk_disclosure', 60)
        disclosure_score = min(100, climate_disclosure)
        metrics.append(ESGMetric(
            name='Climate Risk Disclosure',
            category=ESGCategory.ENVIRONMENTAL,
            value=climate_disclosure,
            weight=weights['climate_risk_disclosure'],
            score=disclosure_score,
            benchmark=100,
            unit='% disclosure',
            source='TCFD Framework',
            description='TCFD-aligned climate risk disclosure'
        ))
        
        # Biodiversity Initiatives
        biodiversity = data.get('biodiversity_initiatives', 50)
        biodiversity_score = min(100, biodiversity)
        metrics.append(ESGMetric(
            name='Biodiversity Initiatives',
            category=ESGCategory.ENVIRONMENTAL,
            value=biodiversity,
            weight=weights['biodiversity_initiatives'],
            score=biodiversity_score,
            benchmark=100,
            unit='score',
            source='BRSR - Principle 6',
            description='Conservation and biodiversity efforts'
        ))
        
        # Calculate weighted average
        total_score = sum(m.score * m.weight for m in metrics)
        
        return total_score, metrics
    
    @staticmethod
    def calculate_social_score(data: Dict) -> Tuple[float, List[ESGMetric]]:
        """Calculate Social Score from BRSR data"""
        metrics = []
        weights = ESGWeightsConfig.SOCIAL_WEIGHTS
        
        # Employee Health & Safety (LTIFR)
        ltifr = data.get('ltifr', 0.5)
        benchmark_ltifr = data.get('benchmark_ltifr', 0.5)
        safety_score = max(0, min(100, 100 - (ltifr / benchmark_ltifr * 50)))
        metrics.append(ESGMetric(
            name='Employee Health & Safety',
            category=ESGCategory.SOCIAL,
            value=ltifr,
            weight=weights['employee_health_safety'],
            score=safety_score,
            benchmark=benchmark_ltifr,
            unit='LTIFR',
            source='BRSR - Principle 3',
            description='Lost Time Injury Frequency Rate'
        ))
        
        # Employee Turnover Rate
        turnover = data.get('employee_turnover_rate', 15)
        turnover_score = max(0, min(100, 100 - (turnover * 2)))  # 50% turnover = 0
        metrics.append(ESGMetric(
            name='Employee Retention',
            category=ESGCategory.SOCIAL,
            value=turnover,
            weight=weights['employee_turnover_rate'],
            score=turnover_score,
            benchmark=10,
            unit='%',
            source='BRSR - Principle 3',
            description='Annual employee turnover rate'
        ))
        
        # Diversity & Inclusion
        women_workforce = data.get('women_workforce_percentage', 25)
        diversity_score = min(100, women_workforce * 2.5)  # 40% = 100
        metrics.append(ESGMetric(
            name='Diversity & Inclusion',
            category=ESGCategory.SOCIAL,
            value=women_workforce,
            weight=weights['diversity_inclusion'],
            score=diversity_score,
            benchmark=40,
            unit='% women',
            source='BRSR - Principle 3',
            description='Women in workforce'
        ))
        
        # Training & Development
        training_hours = data.get('training_hours_per_employee', 20)
        training_score = min(100, training_hours * 2.5)  # 40 hours = 100
        metrics.append(ESGMetric(
            name='Training & Development',
            category=ESGCategory.SOCIAL,
            value=training_hours,
            weight=weights['training_development'],
            score=training_score,
            benchmark=40,
            unit='hours/employee',
            source='BRSR - Principle 3',
            description='Average training hours per employee'
        ))
        
        # Fair Wages
        fair_wage_compliance = data.get('fair_wages', 100)
        fair_wage_score = min(100, fair_wage_compliance)
        metrics.append(ESGMetric(
            name='Fair Wages',
            category=ESGCategory.SOCIAL,
            value=fair_wage_compliance,
            weight=weights['fair_wages'],
            score=fair_wage_score,
            benchmark=100,
            unit='% compliance',
            source='BRSR - Principle 3',
            description='Minimum wage compliance'
        ))
        
        # Community Investment (CSR)
        csr_spending = data.get('csr_spending_percentage', 2)
        csr_score = min(100, csr_spending * 40)  # 2.5% = 100
        metrics.append(ESGMetric(
            name='Community Investment',
            category=ESGCategory.SOCIAL,
            value=csr_spending,
            weight=weights['community_investment'],
            score=csr_score,
            benchmark=2.5,
            unit='% of profit',
            source='BRSR - Principle 8',
            description='CSR spending as % of average net profit'
        ))
        
        # Human Rights Compliance
        human_rights = data.get('human_rights_compliance', 90)
        hr_score = min(100, human_rights)
        metrics.append(ESGMetric(
            name='Human Rights',
            category=ESGCategory.SOCIAL,
            value=human_rights,
            weight=weights['human_rights_compliance'],
            score=hr_score,
            benchmark=100,
            unit='% compliance',
            source='BRSR - Principle 5',
            description='Human rights policy compliance'
        ))
        
        # Customer Satisfaction
        customer_complaints_resolved = data.get('customer_complaints_resolved', 95)
        customer_score = min(100, customer_complaints_resolved)
        metrics.append(ESGMetric(
            name='Customer Satisfaction',
            category=ESGCategory.SOCIAL,
            value=customer_complaints_resolved,
            weight=weights['customer_satisfaction'],
            score=customer_score,
            benchmark=100,
            unit='% resolved',
            source='BRSR - Principle 9',
            description='Customer complaints resolution rate'
        ))
        
        # Data Privacy & Security
        data_breaches = data.get('data_breaches', 0)
        privacy_score = max(0, 100 - (data_breaches * 20))  # Each breach -20 points
        metrics.append(ESGMetric(
            name='Data Privacy & Security',
            category=ESGCategory.SOCIAL,
            value=data_breaches,
            weight=weights['data_privacy_security'],
            score=privacy_score,
            benchmark=0,
            unit='breaches',
            source='BRSR - Principle 9',
            description='Number of data breach incidents'
        ))
        
        # Labor Practices
        labor_compliance = data.get('labor_practices', 100)
        labor_score = min(100, labor_compliance)
        metrics.append(ESGMetric(
            name='Labor Practices',
            category=ESGCategory.SOCIAL,
            value=labor_compliance,
            weight=weights['labor_practices'],
            score=labor_score,
            benchmark=100,
            unit='% compliance',
            source='BRSR - Principle 5',
            description='Child labor and forced labor compliance'
        ))
        
        # Calculate weighted average
        total_score = sum(m.score * m.weight for m in metrics)
        
        return total_score, metrics
    
    @staticmethod
    def calculate_governance_score(data: Dict) -> Tuple[float, List[ESGMetric]]:
        """Calculate Governance Score from BRSR data"""
        metrics = []
        weights = ESGWeightsConfig.GOVERNANCE_WEIGHTS
        
        # Board Independence
        independent_pct = data.get('independent_directors_percentage', 50)
        independence_score = min(100, independent_pct * 1.5)  # 67% = 100
        metrics.append(ESGMetric(
            name='Board Independence',
            category=ESGCategory.GOVERNANCE,
            value=independent_pct,
            weight=weights['board_independence'],
            score=independence_score,
            benchmark=67,
            unit='%',
            source='SEBI LODR',
            description='Independent directors percentage'
        ))
        
        # Board Diversity
        women_board = data.get('women_directors_percentage', 17)
        board_diversity_score = min(100, women_board * 4)  # 25% = 100
        metrics.append(ESGMetric(
            name='Board Diversity',
            category=ESGCategory.GOVERNANCE,
            value=women_board,
            weight=weights['board_diversity'],
            score=board_diversity_score,
            benchmark=25,
            unit='% women',
            source='SEBI LODR',
            description='Women on board'
        ))
        
        # Audit Committee Quality
        audit_meetings = data.get('audit_committee_meetings', 4)
        audit_score = min(100, audit_meetings * 16.67)  # 6 meetings = 100
        metrics.append(ESGMetric(
            name='Audit Committee',
            category=ESGCategory.GOVERNANCE,
            value=audit_meetings,
            weight=weights['audit_committee_quality'],
            score=audit_score,
            benchmark=6,
            unit='meetings/year',
            source='SEBI LODR',
            description='Audit committee meetings'
        ))
        
        # Executive Compensation (CEO Pay Ratio)
        ceo_ratio = data.get('ceo_median_pay_ratio', 100)
        # Lower ratio is better
        exec_score = max(0, min(100, 150 - (ceo_ratio * 0.5)))
        metrics.append(ESGMetric(
            name='Executive Compensation',
            category=ESGCategory.GOVERNANCE,
            value=ceo_ratio,
            weight=weights['executive_compensation'],
            score=exec_score,
            benchmark=100,
            unit='x median',
            source='BRSR - Principle 1',
            description='CEO to median employee pay ratio'
        ))
        
        # Shareholder Rights
        shareholder_rights = data.get('shareholder_rights', 80)
        rights_score = min(100, shareholder_rights)
        metrics.append(ESGMetric(
            name='Shareholder Rights',
            category=ESGCategory.GOVERNANCE,
            value=shareholder_rights,
            weight=weights['shareholder_rights'],
            score=rights_score,
            benchmark=100,
            unit='score',
            source='SEBI LODR',
            description='Shareholder rights protection'
        ))
        
        # Ethics & Anti-Corruption
        ethics_compliance = data.get('ethics_anti_corruption', 90)
        ethics_score = min(100, ethics_compliance)
        metrics.append(ESGMetric(
            name='Ethics & Anti-Corruption',
            category=ESGCategory.GOVERNANCE,
            value=ethics_compliance,
            weight=weights['ethics_anti_corruption'],
            score=ethics_score,
            benchmark=100,
            unit='% compliance',
            source='BRSR - Principle 1',
            description='Anti-bribery and ethics compliance'
        ))
        
        # Risk Management
        risk_mgmt = data.get('risk_management', 80)
        risk_score = min(100, risk_mgmt)
        metrics.append(ESGMetric(
            name='Risk Management',
            category=ESGCategory.GOVERNANCE,
            value=risk_mgmt,
            weight=weights['risk_management'],
            score=risk_score,
            benchmark=100,
            unit='score',
            source='SEBI LODR',
            description='Enterprise risk management maturity'
        ))
        
        # Tax Transparency
        tax_disclosure = data.get('tax_transparency', 70)
        tax_score = min(100, tax_disclosure)
        metrics.append(ESGMetric(
            name='Tax Transparency',
            category=ESGCategory.GOVERNANCE,
            value=tax_disclosure,
            weight=weights['tax_transparency'],
            score=tax_score,
            benchmark=100,
            unit='% disclosure',
            source='BRSR - Principle 1',
            description='Tax disclosure and transparency'
        ))
        
        # Related Party Transactions
        rpt_compliance = data.get('related_party_transactions', 100)
        rpt_score = min(100, rpt_compliance)
        metrics.append(ESGMetric(
            name='Related Party Transactions',
            category=ESGCategory.GOVERNANCE,
            value=rpt_compliance,
            weight=weights['related_party_transactions'],
            score=rpt_score,
            benchmark=100,
            unit='% compliance',
            source='SEBI LODR',
            description='RPT policy compliance'
        ))
        
        # Sustainability Committee
        sustainability_committee = data.get('sustainability_committee', 1)
        committee_score = 100 if sustainability_committee >= 1 else 0
        metrics.append(ESGMetric(
            name='Sustainability Committee',
            category=ESGCategory.GOVERNANCE,
            value=sustainability_committee,
            weight=weights['sustainability_committee'],
            score=committee_score,
            benchmark=1,
            unit='exists',
            source='BRSR',
            description='Board-level ESG oversight'
        ))
        
        # Calculate weighted average
        total_score = sum(m.score * m.weight for m in metrics)
        
        return total_score, metrics


# ============================================================================
# ESG SCORE CALCULATOR
# ============================================================================

class ESGScoreCalculator:
    """Main ESG Score Calculator"""
    
    def __init__(self):
        self.nse_fetcher = NSEDataFetcher()
        self.brsr_processor = BRSRDataProcessor()
        self.weights_config = ESGWeightsConfig()
        self.benchmarks = IndianSectorBenchmarks()
    
    def get_risk_level(self, score: float) -> RiskLevel:
        """Determine ESG risk level based on score"""
        if score >= 80:
            return RiskLevel.NEGLIGIBLE
        elif score >= 65:
            return RiskLevel.LOW
        elif score >= 50:
            return RiskLevel.MEDIUM
        elif score >= 35:
            return RiskLevel.HIGH
        else:
            return RiskLevel.SEVERE
    
    def get_risk_color(self, risk_level: RiskLevel) -> str:
        """Get color for risk level"""
        colors = {
            RiskLevel.NEGLIGIBLE: '#27ae60',  # Green
            RiskLevel.LOW: '#2ecc71',          # Light Green
            RiskLevel.MEDIUM: '#f39c12',       # Orange
            RiskLevel.HIGH: '#e74c3c',         # Red
            RiskLevel.SEVERE: '#c0392b'        # Dark Red
        }
        return colors.get(risk_level, '#f39c12')
    
    def calculate_company_esg(self, symbol: str, 
                              custom_data: Optional[Dict] = None) -> CompanyESGProfile:
        """
        Calculate comprehensive ESG score for a company
        
        Args:
            symbol: NSE symbol of the company
            custom_data: Optional custom BRSR data (if available)
        
        Returns:
            CompanyESGProfile with complete ESG analysis
        """
        print(f"\n🔄 Calculating ESG Score for {symbol}...")
        
        # Fetch company info from NSE
        company_info = self.nse_fetcher.get_company_info(symbol)
        
        if company_info is None:
            company_info = {
                'symbol': symbol,
                'company_name': symbol,
                'industry': 'Unknown',
                'sector': 'Unknown',
                'market_cap': 0
            }
        
        # Get industry-specific benchmarks
        industry = company_info.get('industry', 'Default')
        sector = company_info.get('sector', 'Default')
        
        env_benchmarks = self.benchmarks.ENVIRONMENTAL_BENCHMARKS.get(
            industry, self.benchmarks.ENVIRONMENTAL_BENCHMARKS['Default']
        )
        
        # Prepare data for calculation
        # Use custom data if provided, otherwise use default/simulated data
        if custom_data is None:
            # Generate sample data based on industry benchmarks
            custom_data = self._generate_sample_data(industry, env_benchmarks)
        
        # Add benchmarks to data
        custom_data.update({
            'benchmark_carbon': env_benchmarks.get('carbon_emissions_intensity', 50),
            'benchmark_energy': env_benchmarks.get('energy_consumption_intensity', 200),
            'benchmark_water': env_benchmarks.get('water_consumption_intensity', 300),
            'benchmark_ltifr': 0.5
        })
        
        # Calculate E, S, G scores
        env_score, env_metrics = self.brsr_processor.calculate_environmental_score(custom_data)
        social_score, social_metrics = self.brsr_processor.calculate_social_score(custom_data)
        gov_score, gov_metrics = self.brsr_processor.calculate_governance_score(custom_data)
        
        # Apply industry weight adjustments
        industry_adj = self.weights_config.INDUSTRY_ADJUSTMENTS.get(
            industry, self.weights_config.INDUSTRY_ADJUSTMENTS['Default']
        )
        
        # Calculate overall ESG score
        category_weights = self.weights_config.CATEGORY_WEIGHTS
        
        adjusted_env_weight = category_weights[ESGCategory.ENVIRONMENTAL] * industry_adj['environmental']
        adjusted_social_weight = category_weights[ESGCategory.SOCIAL] * industry_adj['social']
        adjusted_gov_weight = category_weights[ESGCategory.GOVERNANCE] * industry_adj['governance']
        
        # Normalize weights
        total_weight = adjusted_env_weight + adjusted_social_weight + adjusted_gov_weight
        adjusted_env_weight /= total_weight
        adjusted_social_weight /= total_weight
        adjusted_gov_weight /= total_weight
        
        overall_score = (
            env_score * adjusted_env_weight +
            social_score * adjusted_social_weight +
            gov_score * adjusted_gov_weight
        )
        
        # Combine all metrics
        all_metrics = env_metrics + social_metrics + gov_metrics
        
        # Determine risk level
        risk_level = self.get_risk_level(overall_score)
        
        # Create profile
        profile = CompanyESGProfile(
            company_name=company_info.get('company_name', symbol),
            symbol=symbol,
            sector=sector,
            industry=industry,
            market_cap=company_info.get('market_cap', 0),
            environmental_score=round(env_score, 2),
            social_score=round(social_score, 2),
            governance_score=round(gov_score, 2),
            overall_esg_score=round(overall_score, 2),
            esg_risk_level=risk_level,
            controversy_score=custom_data.get('controversy_score', 0),
            metrics=all_metrics,
            last_updated=datetime.now(),
            data_year=custom_data.get('data_year', 2024)
        )
        
        return profile
    
    def _generate_sample_data(self, industry: str, benchmarks: Dict) -> Dict:
        """Generate sample ESG data for demonstration"""
        np.random.seed(hash(industry) % 2**32)
        
        return {
            # Environmental
            'carbon_emissions_intensity': benchmarks.get('carbon_emissions_intensity', 50) * np.random.uniform(0.7, 1.3),
            'energy_consumption_intensity': benchmarks.get('energy_consumption_intensity', 200) * np.random.uniform(0.7, 1.3),
            'renewable_energy_percentage': benchmarks.get('renewable_energy_percentage', 25) * np.random.uniform(0.8, 1.5),
            'water_consumption_intensity': benchmarks.get('water_consumption_intensity', 300) * np.random.uniform(0.7, 1.3),
            'waste_recycling_rate': benchmarks.get('waste_recycling_rate', 65) * np.random.uniform(0.8, 1.2),
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
            'data_breaches': np.random.randint(0, 3),
            'labor_practices': np.random.uniform(95, 100),
            
            # Governance
            'independent_directors_percentage': np.random.uniform(45, 70),
            'women_directors_percentage': np.random.uniform(15, 35),
            'audit_committee_meetings': np.random.randint(4, 8),
            'ceo_median_pay_ratio': np.random.uniform(50, 200),
            'shareholder_rights': np.random.uniform(70, 95),
            'ethics_anti_corruption': np.random.uniform(80, 100),
            'risk_management': np.random.uniform(60, 95),
            'tax_transparency': np.random.uniform(50, 90),
            'related_party_transactions': np.random.uniform(90, 100),
            'sustainability_committee': np.random.choice([0, 1], p=[0.3, 0.7]),
            
            # Other
            'controversy_score': np.random.uniform(0, 30),
            'data_year': 2024
        }
    
    def compare_companies(self, symbols: List[str]) -> pd.DataFrame:
        """Compare ESG scores across multiple companies"""
        results = []
        
        for symbol in symbols:
            try:
                profile = self.calculate_company_esg(symbol)
                results.append({
                    'Symbol': profile.symbol,
                    'Company': profile.company_name,
                    'Sector': profile.sector,
                    'Industry': profile.industry,
                    'Environmental': profile.environmental_score,
                    'Social': profile.social_score,
                    'Governance': profile.governance_score,
                    'Overall ESG': profile.overall_esg_score,
                    'Risk Level': profile.esg_risk_level.value,
                    'Controversy': profile.controversy_score
                })
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
        
        return pd.DataFrame(results)
    
    def generate_esg_report(self, profile: CompanyESGProfile) -> str:
        """Generate detailed ESG report"""
        report = []
        report.append("=" * 80)
        report.append(f"🌿 ESG SUSTAINABILITY REPORT - {profile.company_name}")
        report.append("=" * 80)
        report.append(f"Symbol: {profile.symbol}")
        report.append(f"Sector: {profile.sector} | Industry: {profile.industry}")
        report.append(f"Report Date: {profile.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Data Year: {profile.data_year}")
        report.append("")
        
        # Overall Score
        report.append("-" * 80)
        report.append("📊 OVERALL ESG SCORE")
        report.append("-" * 80)
        report.append(f"{'Overall ESG Score:':<30} {profile.overall_esg_score:>10.2f} / 100")
        report.append(f"{'ESG Risk Level:':<30} {profile.esg_risk_level.value:>10}")
        report.append(f"{'Controversy Score:':<30} {profile.controversy_score:>10.2f}")
        report.append("")
        
        # Category Scores
        report.append("-" * 80)
        report.append("📈 CATEGORY SCORES")
        report.append("-" * 80)
        report.append(f"{'🌍 Environmental:':<30} {profile.environmental_score:>10.2f} / 100")
        report.append(f"{'👥 Social:':<30} {profile.social_score:>10.2f} / 100")
        report.append(f"{'🏛️ Governance:':<30} {profile.governance_score:>10.2f} / 100")
        report.append("")
        
        # Detailed Metrics
        for category in ESGCategory:
            category_metrics = [m for m in profile.metrics if m.category == category]
            if category_metrics:
                report.append("-" * 80)
                report.append(f"📋 {category.value.upper()} METRICS")
                report.append("-" * 80)
                for metric in category_metrics:
                    score_indicator = "🟢" if metric.score >= 70 else "🟡" if metric.score >= 50 else "🔴"
                    report.append(f"{score_indicator} {metric.name:<35} Score: {metric.score:>6.2f} | Value: {metric.value:>8.2f} {metric.unit}")
                report.append("")
        
        report.append("=" * 80)
        report.append("⚠️ DISCLAIMER: This ESG score is for informational purposes only.")
        report.append("   Actual ESG assessments should be based on verified BRSR disclosures.")
        report.append("=" * 80)
        
        return "\n".join(report)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_esg_analysis(symbols: List[str] = None):
    """Run ESG analysis for given symbols"""
    
    if symbols is None:
        # Default NIFTY 50 sample
        symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 
                   'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK']
    
    print("\n" + "=" * 80)
    print("🌿 NYZTRADE - ESG SCORE ANALYSIS")
    print("=" * 80)
    
    calculator = ESGScoreCalculator()
    
    # Analyze companies
    comparison_df = calculator.compare_companies(symbols)
    
    if not comparison_df.empty:
        # Sort by Overall ESG score
        comparison_df = comparison_df.sort_values('Overall ESG', ascending=False)
        
        print("\n📊 ESG SCORE COMPARISON:")
        print("-" * 100)
        print(comparison_df.to_string(index=False))
        
        # Generate detailed report for top company
        top_symbol = comparison_df.iloc[0]['Symbol']
        profile = calculator.calculate_company_esg(top_symbol)
        report = calculator.generate_esg_report(profile)
        print(f"\n{report}")
        
        return comparison_df, profile
    
    return None, None


if __name__ == "__main__":
    # Run analysis
    df, profile = run_esg_analysis()
    
    print("\n✅ ESG Analysis Complete!")
