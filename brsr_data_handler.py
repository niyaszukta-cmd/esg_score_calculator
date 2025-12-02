# ============================================================================
# NYZTRADE - BRSR DATA HANDLER
# Business Responsibility and Sustainability Report Data Processor
# ============================================================================

"""
BRSR Data Handler for Indian Companies
Fetches ESG data from multiple sources:
- NSE India
- BSE India
- Company Annual Reports
- BRSR Disclosures
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import re
from bs4 import BeautifulSoup
import time
import warnings

warnings.filterwarnings('ignore')


# ============================================================================
# BRSR METRICS MAPPING
# ============================================================================

class BRSRMetricsMapping:
    """
    SEBI BRSR Framework Metrics Mapping
    Based on SEBI Circular SEBI/HO/CFD/CMD-2/P/CIR/2021/562
    """
    
    # Section A: General Disclosures
    GENERAL_METRICS = {
        'A1': 'Corporate Identity Number (CIN)',
        'A2': 'Name of Listed Entity',
        'A3': 'Year of Incorporation',
        'A4': 'Registered Office Address',
        'A5': 'Corporate Address',
        'A6': 'Email',
        'A7': 'Telephone',
        'A8': 'Website',
        'A9': 'Financial Year',
        'A10': 'Stock Exchange Listing',
        'A11': 'Paid-up Capital',
        'A12': 'Name of Auditors',
        'A13': 'Turnover',
        'A14': 'Net Worth',
    }
    
    # Section B: Management and Process Disclosures
    MANAGEMENT_METRICS = {
        'B1': 'Policy Framework',
        'B2': 'Policy Coverage',
        'B3': 'Policy Translation',
        'B4': 'Stakeholder Engagement',
        'B5': 'Materiality Assessment',
        'B6': 'Human Rights Due Diligence',
        'B7': 'Grievance Mechanism',
    }
    
    # Section C: Principle-wise Performance Disclosures
    # Principle 1: Businesses should conduct and govern themselves with Ethics
    PRINCIPLE_1_METRICS = {
        'P1_1': 'Training on ethics and anti-corruption',
        'P1_2': 'Disciplinary actions for unethical practices',
        'P1_3': 'Conflicts of interest complaints',
        'P1_4': 'Anti-corruption policy',
        'P1_5': 'Whistle-blower mechanism',
    }
    
    # Principle 2: Businesses should provide goods and services that are sustainable
    PRINCIPLE_2_METRICS = {
        'P2_1': 'R&D spend on sustainable products',
        'P2_2': 'LCA for products',
        'P2_3': 'Sustainable packaging',
        'P2_4': 'Recycled inputs',
        'P2_5': 'EPR compliance',
    }
    
    # Principle 3: Businesses should respect and promote the well-being of employees
    PRINCIPLE_3_METRICS = {
        'P3_1': 'Employee count (permanent/temporary)',
        'P3_2': 'Women employees percentage',
        'P3_3': 'Employee turnover rate',
        'P3_4': 'Training hours per employee',
        'P3_5': 'Health and safety incidents (LTIFR)',
        'P3_6': 'Return to work rate',
        'P3_7': 'Employee grievances',
        'P3_8': 'Minimum wage compliance',
        'P3_9': 'POSH complaints',
    }
    
    # Principle 4: Businesses should respect the interests of stakeholders
    PRINCIPLE_4_METRICS = {
        'P4_1': 'Stakeholder identification',
        'P4_2': 'Stakeholder engagement frequency',
        'P4_3': 'Material issues from engagement',
    }
    
    # Principle 5: Businesses should respect and promote human rights
    PRINCIPLE_5_METRICS = {
        'P5_1': 'Human rights training',
        'P5_2': 'Minimum wage compliance',
        'P5_3': 'Sexual harassment complaints',
        'P5_4': 'Child labor complaints',
        'P5_5': 'Forced labor complaints',
        'P5_6': 'Wages discrimination complaints',
    }
    
    # Principle 6: Businesses should respect and make efforts to protect the environment
    PRINCIPLE_6_METRICS = {
        'P6_1': 'Energy consumption (total and intensity)',
        'P6_2': 'Renewable energy percentage',
        'P6_3': 'Water consumption (total and intensity)',
        'P6_4': 'Air emissions (SOx, NOx, PM)',
        'P6_5': 'GHG emissions (Scope 1, 2, 3)',
        'P6_6': 'Waste generation and management',
        'P6_7': 'Hazardous waste disposal',
        'P6_8': 'Water discharge',
        'P6_9': 'Environmental compliance',
        'P6_10': 'EIA undertaken',
        'P6_11': 'Biodiversity impact',
    }
    
    # Principle 7: Businesses should engage in influencing public and regulatory policy
    PRINCIPLE_7_METRICS = {
        'P7_1': 'Trade association memberships',
        'P7_2': 'Anti-competitive conduct cases',
    }
    
    # Principle 8: Businesses should promote inclusive growth and equitable development
    PRINCIPLE_8_METRICS = {
        'P8_1': 'CSR spending',
        'P8_2': 'Community development projects',
        'P8_3': 'Beneficiaries of CSR',
        'P8_4': 'Input from local communities',
        'P8_5': 'Rehabilitation and resettlement',
        'P8_6': 'Social impact assessment',
    }
    
    # Principle 9: Businesses should engage with and provide value to their customers
    PRINCIPLE_9_METRICS = {
        'P9_1': 'Consumer complaints received',
        'P9_2': 'Consumer complaints resolved',
        'P9_3': 'Product recalls',
        'P9_4': 'Data privacy complaints',
        'P9_5': 'Advertising complaints',
        'P9_6': 'Cyber security incidents',
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
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session with NSE cookies"""
        try:
            self.session.get(self.base_url, timeout=10)
            print("✅ NSE session initialized")
        except Exception as e:
            print(f"⚠️ NSE session warning: {e}")
    
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
                    'series': data.get('metadata', {}).get('series', ''),
                    'market_cap': data.get('securityInfo', {}).get('marketCap', 0),
                    'last_price': data.get('priceInfo', {}).get('lastPrice', 0),
                    'change': data.get('priceInfo', {}).get('change', 0),
                    'pchange': data.get('priceInfo', {}).get('pChange', 0),
                    'pe_ratio': data.get('metadata', {}).get('pdSymbolPe', 0),
                    'isin': data.get('metadata', {}).get('isin', ''),
                    'face_value': data.get('securityInfo', {}).get('faceValue', 0),
                }
            return None
        except Exception as e:
            print(f"❌ Error fetching company info: {e}")
            return None
    
    def get_corporate_actions(self, symbol: str) -> Optional[List[Dict]]:
        """Fetch corporate actions for ESG-related activities"""
        try:
            url = f"{self.base_url}/api/corporates-corporateActions?index=equities&symbol={symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Error fetching corporate actions: {e}")
            return None
    
    def get_shareholding_pattern(self, symbol: str) -> Optional[Dict]:
        """Fetch shareholding pattern for governance analysis"""
        try:
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}&section=trade_info"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                shareholding = data.get('securityWiseDP', {})
                
                return {
                    'promoter_holding': shareholding.get('promoterHolding', 0),
                    'public_holding': shareholding.get('publicHolding', 0),
                    'fii_holding': shareholding.get('fii', 0),
                    'dii_holding': shareholding.get('dii', 0),
                }
            return None
        except Exception as e:
            print(f"❌ Error fetching shareholding pattern: {e}")
            return None
    
    def get_board_meetings(self, symbol: str) -> Optional[List[Dict]]:
        """Fetch board meeting information"""
        try:
            url = f"{self.base_url}/api/corporates-boardMeetings?index=equities&symbol={symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Error fetching board meetings: {e}")
            return None
    
    def get_financial_results(self, symbol: str) -> Optional[Dict]:
        """Fetch financial results for ESG context"""
        try:
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}&section=trade_info"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('tradeInfo', {})
            return None
        except Exception as e:
            print(f"❌ Error fetching financial results: {e}")
            return None


# ============================================================================
# BSE DATA FETCHER
# ============================================================================

class BSEDataFetcher:
    """Fetch company data from BSE India"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.base_url = "https://api.bseindia.com/BseIndiaAPI/api"
    
    def get_company_info(self, scrip_code: str) -> Optional[Dict]:
        """Fetch company information from BSE"""
        try:
            url = f"{self.base_url}/StockReachGraph/w?scripcode={scrip_code}&flag=0&fromdate=&todate=&seriesid="
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Error fetching BSE data: {e}")
            return None


# ============================================================================
# BRSR REPORT PARSER
# ============================================================================

class BRSRReportParser:
    """Parse BRSR reports and extract ESG metrics"""
    
    def __init__(self):
        self.metrics_mapping = BRSRMetricsMapping()
    
    def extract_environmental_metrics(self, report_data: Dict) -> Dict:
        """Extract environmental metrics from BRSR report"""
        env_metrics = {}
        
        # Energy metrics
        env_metrics['total_energy_consumption'] = report_data.get('energy_consumption_gj', 0)
        env_metrics['renewable_energy_consumption'] = report_data.get('renewable_energy_gj', 0)
        env_metrics['energy_intensity'] = report_data.get('energy_intensity', 0)
        
        # Water metrics
        env_metrics['total_water_withdrawal'] = report_data.get('water_withdrawal_kl', 0)
        env_metrics['water_intensity'] = report_data.get('water_intensity', 0)
        env_metrics['water_recycled'] = report_data.get('water_recycled_kl', 0)
        
        # Emissions metrics
        env_metrics['scope1_emissions'] = report_data.get('scope1_tco2e', 0)
        env_metrics['scope2_emissions'] = report_data.get('scope2_tco2e', 0)
        env_metrics['scope3_emissions'] = report_data.get('scope3_tco2e', 0)
        env_metrics['emission_intensity'] = report_data.get('emission_intensity', 0)
        
        # Waste metrics
        env_metrics['total_waste_generated'] = report_data.get('waste_generated_mt', 0)
        env_metrics['waste_recycled'] = report_data.get('waste_recycled_mt', 0)
        env_metrics['hazardous_waste'] = report_data.get('hazardous_waste_mt', 0)
        
        # Compliance
        env_metrics['environmental_fines'] = report_data.get('env_fines', 0)
        env_metrics['eia_undertaken'] = report_data.get('eia_count', 0)
        
        return env_metrics
    
    def extract_social_metrics(self, report_data: Dict) -> Dict:
        """Extract social metrics from BRSR report"""
        social_metrics = {}
        
        # Employee metrics
        social_metrics['total_employees'] = report_data.get('total_employees', 0)
        social_metrics['permanent_employees'] = report_data.get('permanent_employees', 0)
        social_metrics['contractual_employees'] = report_data.get('contractual_employees', 0)
        social_metrics['women_employees'] = report_data.get('women_employees', 0)
        social_metrics['women_percentage'] = report_data.get('women_percentage', 0)
        
        # Diversity
        social_metrics['pwd_employees'] = report_data.get('pwd_employees', 0)
        social_metrics['sc_st_employees'] = report_data.get('sc_st_employees', 0)
        
        # Training
        social_metrics['training_hours_male'] = report_data.get('training_hours_male', 0)
        social_metrics['training_hours_female'] = report_data.get('training_hours_female', 0)
        social_metrics['avg_training_hours'] = report_data.get('avg_training_hours', 0)
        
        # Health & Safety
        social_metrics['ltifr'] = report_data.get('ltifr', 0)
        social_metrics['fatalities'] = report_data.get('fatalities', 0)
        social_metrics['recordable_injuries'] = report_data.get('recordable_injuries', 0)
        
        # Grievances
        social_metrics['employee_grievances'] = report_data.get('employee_grievances', 0)
        social_metrics['grievances_resolved'] = report_data.get('grievances_resolved', 0)
        social_metrics['posh_complaints'] = report_data.get('posh_complaints', 0)
        
        # Turnover
        social_metrics['employee_turnover'] = report_data.get('employee_turnover', 0)
        social_metrics['new_hires'] = report_data.get('new_hires', 0)
        
        # CSR
        social_metrics['csr_spend'] = report_data.get('csr_spend_cr', 0)
        social_metrics['csr_beneficiaries'] = report_data.get('csr_beneficiaries', 0)
        
        return social_metrics
    
    def extract_governance_metrics(self, report_data: Dict) -> Dict:
        """Extract governance metrics from BRSR report"""
        gov_metrics = {}
        
        # Board composition
        gov_metrics['board_size'] = report_data.get('board_size', 0)
        gov_metrics['independent_directors'] = report_data.get('independent_directors', 0)
        gov_metrics['women_directors'] = report_data.get('women_directors', 0)
        gov_metrics['executive_directors'] = report_data.get('executive_directors', 0)
        
        # Board meetings
        gov_metrics['board_meetings'] = report_data.get('board_meetings', 0)
        gov_metrics['avg_attendance'] = report_data.get('avg_attendance', 0)
        
        # Committees
        gov_metrics['audit_committee_meetings'] = report_data.get('audit_meetings', 0)
        gov_metrics['csr_committee_meetings'] = report_data.get('csr_meetings', 0)
        gov_metrics['risk_committee_meetings'] = report_data.get('risk_meetings', 0)
        
        # Ethics & Compliance
        gov_metrics['ethics_training'] = report_data.get('ethics_training_pct', 0)
        gov_metrics['whistleblower_complaints'] = report_data.get('whistleblower_complaints', 0)
        gov_metrics['anti_corruption_training'] = report_data.get('anti_corruption_training', 0)
        
        # Compensation
        gov_metrics['ceo_compensation'] = report_data.get('ceo_compensation_cr', 0)
        gov_metrics['median_employee_compensation'] = report_data.get('median_comp_lakhs', 0)
        
        # Related Party Transactions
        gov_metrics['rpt_value'] = report_data.get('rpt_value_cr', 0)
        gov_metrics['rpt_count'] = report_data.get('rpt_count', 0)
        
        return gov_metrics


# ============================================================================
# ESG DATA AGGREGATOR
# ============================================================================

class ESGDataAggregator:
    """Aggregate ESG data from multiple sources"""
    
    def __init__(self):
        self.nse_fetcher = NSEDataFetcher()
        self.bse_fetcher = BSEDataFetcher()
        self.brsr_parser = BRSRReportParser()
    
    def fetch_company_esg_data(self, symbol: str, 
                               brsr_data: Optional[Dict] = None) -> Dict:
        """
        Fetch and aggregate ESG data for a company
        
        Args:
            symbol: NSE symbol
            brsr_data: Optional BRSR report data (if available)
        
        Returns:
            Aggregated ESG data dictionary
        """
        print(f"\n🔄 Fetching ESG data for {symbol}...")
        
        # Fetch company info from NSE
        company_info = self.nse_fetcher.get_company_info(symbol)
        if company_info is None:
            company_info = {'symbol': symbol, 'company_name': symbol}
        
        # Fetch shareholding for governance metrics
        shareholding = self.nse_fetcher.get_shareholding_pattern(symbol)
        
        # Fetch board meetings for governance metrics
        board_meetings = self.nse_fetcher.get_board_meetings(symbol)
        
        # Process BRSR data if available
        env_metrics = {}
        social_metrics = {}
        gov_metrics = {}
        
        if brsr_data:
            env_metrics = self.brsr_parser.extract_environmental_metrics(brsr_data)
            social_metrics = self.brsr_parser.extract_social_metrics(brsr_data)
            gov_metrics = self.brsr_parser.extract_governance_metrics(brsr_data)
        
        # Aggregate data
        aggregated_data = {
            'company_info': company_info,
            'shareholding': shareholding or {},
            'board_meetings_count': len(board_meetings) if board_meetings else 0,
            'environmental': env_metrics,
            'social': social_metrics,
            'governance': gov_metrics,
            'data_source': 'NSE + BRSR' if brsr_data else 'NSE Only',
            'fetch_timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ ESG data aggregated for {symbol}")
        
        return aggregated_data
    
    def fetch_multiple_companies(self, symbols: List[str]) -> pd.DataFrame:
        """Fetch ESG data for multiple companies"""
        results = []
        
        for symbol in symbols:
            try:
                data = self.fetch_company_esg_data(symbol)
                
                company_info = data.get('company_info', {})
                shareholding = data.get('shareholding', {})
                
                results.append({
                    'Symbol': symbol,
                    'Company': company_info.get('company_name', symbol),
                    'Industry': company_info.get('industry', 'Unknown'),
                    'Sector': company_info.get('sector', 'Unknown'),
                    'Market Cap': company_info.get('market_cap', 0),
                    'Promoter Holding': shareholding.get('promoter_holding', 0),
                    'Public Holding': shareholding.get('public_holding', 0),
                    'FII Holding': shareholding.get('fii_holding', 0),
                    'DII Holding': shareholding.get('dii_holding', 0),
                    'Board Meetings': data.get('board_meetings_count', 0),
                    'Data Source': data.get('data_source', ''),
                })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
        
        return pd.DataFrame(results)


# ============================================================================
# INDUSTRY CLASSIFICATION
# ============================================================================

class IndustryClassifier:
    """Classify companies by industry for sector-specific ESG analysis"""
    
    # High-impact industries (environmentally sensitive)
    HIGH_IMPACT_INDUSTRIES = [
        'Oil & Gas',
        'Mining',
        'Metals & Mining',
        'Power',
        'Cement',
        'Steel',
        'Chemicals',
        'Fertilizers',
        'Paper',
        'Textiles',
    ]
    
    # Medium-impact industries
    MEDIUM_IMPACT_INDUSTRIES = [
        'Automobiles',
        'Auto Components',
        'Pharmaceuticals',
        'FMCG',
        'Consumer Durables',
        'Real Estate',
        'Construction',
        'Infrastructure',
    ]
    
    # Low-impact industries
    LOW_IMPACT_INDUSTRIES = [
        'IT Services',
        'Banking',
        'Financial Services',
        'Insurance',
        'Media & Entertainment',
        'Healthcare Services',
        'Education',
        'Telecom',
    ]
    
    @staticmethod
    def get_impact_level(industry: str) -> str:
        """Get environmental impact level for an industry"""
        if industry in IndustryClassifier.HIGH_IMPACT_INDUSTRIES:
            return 'High'
        elif industry in IndustryClassifier.MEDIUM_IMPACT_INDUSTRIES:
            return 'Medium'
        elif industry in IndustryClassifier.LOW_IMPACT_INDUSTRIES:
            return 'Low'
        else:
            return 'Medium'  # Default
    
    @staticmethod
    def get_esg_weight_adjustment(industry: str) -> Dict:
        """Get ESG weight adjustments based on industry"""
        impact_level = IndustryClassifier.get_impact_level(industry)
        
        adjustments = {
            'High': {'environmental': 1.3, 'social': 0.9, 'governance': 0.8},
            'Medium': {'environmental': 1.0, 'social': 1.0, 'governance': 1.0},
            'Low': {'environmental': 0.7, 'social': 1.1, 'governance': 1.2}
        }
        
        return adjustments.get(impact_level, adjustments['Medium'])


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("=" * 80)
    print("🌿 NYZTRADE - BRSR DATA HANDLER")
    print("=" * 80)
    
    # Initialize aggregator
    aggregator = ESGDataAggregator()
    
    # Sample companies
    symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
    
    # Fetch data
    df = aggregator.fetch_multiple_companies(symbols)
    
    if not df.empty:
        print("\n📊 Fetched ESG Data:")
        print(df.to_string(index=False))
        
        # Save to CSV
        filename = f"esg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Data saved to: {filename}")
    
    return df


if __name__ == "__main__":
    df = main()
