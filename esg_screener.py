# ============================================================================
# NYZTRADE - ESG SCREENER & FILTERING TOOL
# Advanced Stock Screening Based on ESG Criteria
# ============================================================================

"""
ESG Screener for Indian Companies
Features:
- Multi-criteria ESG filtering
- Exclusion screening (negative screening)
- Thematic screening (e.g., clean energy, diversity)
- Best-in-class selection
- ESG momentum screening
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import warnings

warnings.filterwarnings('ignore')


# ============================================================================
# SCREENING ENUMS AND DATA CLASSES
# ============================================================================

class ScreeningType(Enum):
    """Types of ESG Screening"""
    NEGATIVE = "Negative Screening"      # Exclude certain sectors/practices
    POSITIVE = "Positive Screening"      # Include only ESG leaders
    BEST_IN_CLASS = "Best-in-Class"      # Top performers within each sector
    THEMATIC = "Thematic"                # Specific ESG themes
    NORMS_BASED = "Norms-Based"          # UN Global Compact, etc.
    ESG_INTEGRATION = "ESG Integration"  # Factor ESG into analysis


class ThematicFocus(Enum):
    """Thematic Investment Focus Areas"""
    CLEAN_ENERGY = "Clean Energy"
    WATER = "Water & Sanitation"
    CLIMATE = "Climate Action"
    GENDER_DIVERSITY = "Gender Diversity"
    CIRCULAR_ECONOMY = "Circular Economy"
    SUSTAINABLE_AGRICULTURE = "Sustainable Agriculture"
    HEALTHCARE_ACCESS = "Healthcare Access"
    FINANCIAL_INCLUSION = "Financial Inclusion"
    DIGITAL_INCLUSION = "Digital Inclusion"


@dataclass
class ScreeningCriteria:
    """Screening criteria configuration"""
    min_esg_score: float = 0.0
    max_controversy_score: float = 100.0
    min_environmental: float = 0.0
    min_social: float = 0.0
    min_governance: float = 0.0
    excluded_sectors: List[str] = None
    excluded_industries: List[str] = None
    required_certifications: List[str] = None
    min_market_cap: float = 0.0
    max_carbon_intensity: float = float('inf')
    min_renewable_energy_pct: float = 0.0
    min_women_workforce_pct: float = 0.0
    min_board_independence_pct: float = 0.0
    
    def __post_init__(self):
        if self.excluded_sectors is None:
            self.excluded_sectors = []
        if self.excluded_industries is None:
            self.excluded_industries = []
        if self.required_certifications is None:
            self.required_certifications = []


# ============================================================================
# EXCLUSION LISTS (NEGATIVE SCREENING)
# ============================================================================

class ExclusionLists:
    """Pre-defined exclusion lists for negative screening"""
    
    # Controversial sectors
    CONTROVERSIAL_SECTORS = [
        'Tobacco',
        'Gambling',
        'Adult Entertainment',
        'Weapons & Defense',
        'Thermal Coal',
        'Oil Sands',
    ]
    
    # Fossil fuel industries
    FOSSIL_FUEL_INDUSTRIES = [
        'Coal Mining',
        'Oil & Gas Exploration',
        'Oil Refining',
        'Thermal Power (Coal)',
    ]
    
    # UN Global Compact violators criteria
    UNGC_VIOLATION_CRITERIA = {
        'human_rights_violations': True,
        'labor_rights_violations': True,
        'environmental_violations': True,
        'corruption_cases': True,
    }
    
    # High carbon intensity industries
    HIGH_CARBON_INDUSTRIES = [
        'Coal Mining',
        'Steel',
        'Cement',
        'Aluminum',
        'Oil & Gas',
        'Thermal Power',
        'Shipping',
        'Aviation',
    ]
    
    # Deforestation risk industries
    DEFORESTATION_RISK = [
        'Palm Oil',
        'Soy',
        'Cattle/Beef',
        'Timber',
        'Rubber',
        'Cocoa',
        'Coffee',
    ]


# ============================================================================
# THEMATIC CRITERIA
# ============================================================================

class ThematicCriteria:
    """Criteria for thematic ESG screening"""
    
    CLEAN_ENERGY = {
        'included_industries': [
            'Solar Energy', 'Wind Energy', 'Hydro Power',
            'Energy Storage', 'Smart Grid', 'EV Infrastructure',
            'Green Hydrogen', 'Renewable Energy Equipment'
        ],
        'min_renewable_revenue_pct': 50,
        'excluded_industries': ['Coal', 'Oil & Gas'],
    }
    
    WATER_SUSTAINABILITY = {
        'included_industries': [
            'Water Utilities', 'Water Treatment',
            'Water Infrastructure', 'Desalination',
            'Water Efficiency Technology'
        ],
        'metrics': {
            'water_recycling_rate': 50,  # minimum %
            'water_intensity_reduction': 10,  # YoY %
        }
    }
    
    GENDER_DIVERSITY = {
        'min_women_workforce': 30,  # %
        'min_women_management': 25,  # %
        'min_women_board': 25,  # %
        'equal_pay_policy': True,
        'parental_leave_policy': True,
    }
    
    CIRCULAR_ECONOMY = {
        'min_recycled_inputs': 30,  # %
        'min_waste_recycling': 70,  # %
        'product_recyclability': 50,  # %
        'extended_producer_responsibility': True,
    }
    
    CLIMATE_ACTION = {
        'has_sbti_targets': True,
        'net_zero_commitment': True,
        'tcfd_disclosure': True,
        'max_carbon_intensity': 100,  # tCO2e/Cr
        'renewable_energy_target': 50,  # %
    }


# ============================================================================
# ESG SCREENER CLASS
# ============================================================================

class ESGScreener:
    """Advanced ESG Screener for Indian Companies"""
    
    def __init__(self):
        self.exclusion_lists = ExclusionLists()
        self.thematic_criteria = ThematicCriteria()
    
    def apply_negative_screening(self, 
                                  df: pd.DataFrame,
                                  exclude_controversial: bool = True,
                                  exclude_fossil_fuels: bool = False,
                                  exclude_high_carbon: bool = False,
                                  custom_exclusions: List[str] = None) -> pd.DataFrame:
        """
        Apply negative screening to exclude certain companies
        
        Args:
            df: DataFrame with company ESG data
            exclude_controversial: Exclude tobacco, gambling, etc.
            exclude_fossil_fuels: Exclude fossil fuel companies
            exclude_high_carbon: Exclude high carbon intensity industries
            custom_exclusions: Custom list of industries to exclude
        
        Returns:
            Filtered DataFrame
        """
        result_df = df.copy()
        exclusions_applied = []
        
        if exclude_controversial:
            result_df = result_df[~result_df['Industry'].isin(
                self.exclusion_lists.CONTROVERSIAL_SECTORS
            )]
            exclusions_applied.append("Controversial Sectors")
        
        if exclude_fossil_fuels:
            result_df = result_df[~result_df['Industry'].isin(
                self.exclusion_lists.FOSSIL_FUEL_INDUSTRIES
            )]
            exclusions_applied.append("Fossil Fuels")
        
        if exclude_high_carbon:
            result_df = result_df[~result_df['Industry'].isin(
                self.exclusion_lists.HIGH_CARBON_INDUSTRIES
            )]
            exclusions_applied.append("High Carbon Industries")
        
        if custom_exclusions:
            result_df = result_df[~result_df['Industry'].isin(custom_exclusions)]
            exclusions_applied.append("Custom Exclusions")
        
        print(f"✅ Negative Screening Applied: {', '.join(exclusions_applied)}")
        print(f"   Companies remaining: {len(result_df)} / {len(df)}")
        
        return result_df
    
    def apply_positive_screening(self,
                                  df: pd.DataFrame,
                                  criteria: ScreeningCriteria) -> pd.DataFrame:
        """
        Apply positive screening to select ESG leaders
        
        Args:
            df: DataFrame with company ESG data
            criteria: ScreeningCriteria object with thresholds
        
        Returns:
            Filtered DataFrame
        """
        result_df = df.copy()
        
        # Apply minimum ESG score
        if criteria.min_esg_score > 0:
            result_df = result_df[result_df['Overall ESG'] >= criteria.min_esg_score]
        
        # Apply maximum controversy score
        if criteria.max_controversy_score < 100:
            if 'Controversy' in result_df.columns:
                result_df = result_df[result_df['Controversy'] <= criteria.max_controversy_score]
        
        # Apply E, S, G minimums
        if criteria.min_environmental > 0:
            result_df = result_df[result_df['Environmental'] >= criteria.min_environmental]
        
        if criteria.min_social > 0:
            result_df = result_df[result_df['Social'] >= criteria.min_social]
        
        if criteria.min_governance > 0:
            result_df = result_df[result_df['Governance'] >= criteria.min_governance]
        
        # Apply sector exclusions
        if criteria.excluded_sectors:
            result_df = result_df[~result_df['Sector'].isin(criteria.excluded_sectors)]
        
        # Apply industry exclusions
        if criteria.excluded_industries:
            result_df = result_df[~result_df['Industry'].isin(criteria.excluded_industries)]
        
        # Apply market cap filter
        if criteria.min_market_cap > 0 and 'Market Cap (Cr)' in result_df.columns:
            result_df = result_df[result_df['Market Cap (Cr)'] >= criteria.min_market_cap]
        
        print(f"✅ Positive Screening Applied")
        print(f"   Min ESG Score: {criteria.min_esg_score}")
        print(f"   Max Controversy: {criteria.max_controversy_score}")
        print(f"   Companies remaining: {len(result_df)} / {len(df)}")
        
        return result_df
    
    def apply_best_in_class(self,
                            df: pd.DataFrame,
                            top_pct: float = 25.0,
                            metric: str = 'Overall ESG') -> pd.DataFrame:
        """
        Select top ESG performers within each sector
        
        Args:
            df: DataFrame with company ESG data
            top_pct: Top percentage to select from each sector
            metric: Metric to rank by
        
        Returns:
            DataFrame with best-in-class companies
        """
        result_dfs = []
        
        for sector in df['Sector'].unique():
            sector_df = df[df['Sector'] == sector].copy()
            n_select = max(1, int(len(sector_df) * top_pct / 100))
            
            top_companies = sector_df.nlargest(n_select, metric)
            result_dfs.append(top_companies)
        
        result_df = pd.concat(result_dfs, ignore_index=True)
        result_df = result_df.sort_values(metric, ascending=False)
        
        print(f"✅ Best-in-Class Screening Applied")
        print(f"   Top {top_pct}% from each sector")
        print(f"   Companies selected: {len(result_df)} / {len(df)}")
        
        return result_df
    
    def apply_thematic_screening(self,
                                  df: pd.DataFrame,
                                  theme: ThematicFocus,
                                  strict: bool = False) -> pd.DataFrame:
        """
        Apply thematic ESG screening
        
        Args:
            df: DataFrame with company ESG data
            theme: ThematicFocus enum value
            strict: If True, apply stricter criteria
        
        Returns:
            Filtered DataFrame
        """
        result_df = df.copy()
        
        if theme == ThematicFocus.CLEAN_ENERGY:
            criteria = self.thematic_criteria.CLEAN_ENERGY
            # Filter by included industries
            result_df = result_df[result_df['Industry'].isin(
                criteria['included_industries'] + ['Default']  # Include Default for demo
            )]
            # Exclude fossil fuels
            result_df = result_df[~result_df['Industry'].isin(
                criteria['excluded_industries']
            )]
        
        elif theme == ThematicFocus.GENDER_DIVERSITY:
            criteria = self.thematic_criteria.GENDER_DIVERSITY
            # For demo, filter by Social score as proxy
            if strict:
                result_df = result_df[result_df['Social'] >= 70]
            else:
                result_df = result_df[result_df['Social'] >= 60]
        
        elif theme == ThematicFocus.CLIMATE:
            criteria = self.thematic_criteria.CLIMATE_ACTION
            # For demo, filter by Environmental score
            if strict:
                result_df = result_df[result_df['Environmental'] >= 70]
            else:
                result_df = result_df[result_df['Environmental'] >= 60]
        
        elif theme == ThematicFocus.CIRCULAR_ECONOMY:
            criteria = self.thematic_criteria.CIRCULAR_ECONOMY
            # For demo, filter by Environmental score
            if strict:
                result_df = result_df[result_df['Environmental'] >= 65]
            else:
                result_df = result_df[result_df['Environmental'] >= 55]
        
        print(f"✅ Thematic Screening Applied: {theme.value}")
        print(f"   Strict Mode: {strict}")
        print(f"   Companies remaining: {len(result_df)} / {len(df)}")
        
        return result_df
    
    def calculate_esg_momentum(self,
                               current_scores: pd.DataFrame,
                               previous_scores: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate ESG momentum (score improvement over time)
        
        Args:
            current_scores: Current period ESG scores
            previous_scores: Previous period ESG scores
        
        Returns:
            DataFrame with momentum metrics
        """
        merged = current_scores.merge(
            previous_scores[['Symbol', 'Overall ESG', 'Environmental', 'Social', 'Governance']],
            on='Symbol',
            suffixes=('', '_prev')
        )
        
        merged['ESG_Momentum'] = merged['Overall ESG'] - merged['Overall ESG_prev']
        merged['E_Momentum'] = merged['Environmental'] - merged['Environmental_prev']
        merged['S_Momentum'] = merged['Social'] - merged['Social_prev']
        merged['G_Momentum'] = merged['Governance'] - merged['Governance_prev']
        
        return merged.sort_values('ESG_Momentum', ascending=False)
    
    def screen_by_risk_level(self,
                             df: pd.DataFrame,
                             max_risk: str = 'Medium') -> pd.DataFrame:
        """
        Screen companies by ESG risk level
        
        Args:
            df: DataFrame with company ESG data
            max_risk: Maximum acceptable risk level
        
        Returns:
            Filtered DataFrame
        """
        risk_hierarchy = ['Negligible', 'Low', 'Medium', 'High', 'Severe']
        
        if max_risk not in risk_hierarchy:
            max_risk = 'Medium'
        
        acceptable_risks = risk_hierarchy[:risk_hierarchy.index(max_risk) + 1]
        
        result_df = df[df['Risk Level'].isin(acceptable_risks)]
        
        print(f"✅ Risk-based Screening Applied")
        print(f"   Max Risk Level: {max_risk}")
        print(f"   Acceptable: {acceptable_risks}")
        print(f"   Companies remaining: {len(result_df)} / {len(df)}")
        
        return result_df
    
    def generate_screening_report(self,
                                   original_df: pd.DataFrame,
                                   screened_df: pd.DataFrame,
                                   screening_type: str) -> str:
        """Generate screening summary report"""
        
        report = []
        report.append("=" * 80)
        report.append("📊 ESG SCREENING REPORT")
        report.append("=" * 80)
        report.append(f"Screening Type: {screening_type}")
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("-" * 80)
        report.append("SCREENING SUMMARY")
        report.append("-" * 80)
        report.append(f"Original Universe: {len(original_df)} companies")
        report.append(f"After Screening: {len(screened_df)} companies")
        report.append(f"Companies Excluded: {len(original_df) - len(screened_df)}")
        report.append(f"Retention Rate: {len(screened_df)/len(original_df)*100:.1f}%")
        report.append("")
        
        report.append("-" * 80)
        report.append("SCREENED UNIVERSE STATISTICS")
        report.append("-" * 80)
        report.append(f"Average ESG Score: {screened_df['Overall ESG'].mean():.1f}")
        report.append(f"Median ESG Score: {screened_df['Overall ESG'].median():.1f}")
        report.append(f"Min ESG Score: {screened_df['Overall ESG'].min():.1f}")
        report.append(f"Max ESG Score: {screened_df['Overall ESG'].max():.1f}")
        report.append("")
        
        report.append("-" * 80)
        report.append("SECTOR BREAKDOWN")
        report.append("-" * 80)
        sector_counts = screened_df['Sector'].value_counts()
        for sector, count in sector_counts.items():
            report.append(f"  {sector}: {count} companies")
        report.append("")
        
        report.append("-" * 80)
        report.append("RISK LEVEL DISTRIBUTION")
        report.append("-" * 80)
        risk_counts = screened_df['Risk Level'].value_counts()
        for risk, count in risk_counts.items():
            report.append(f"  {risk}: {count} companies")
        report.append("")
        
        report.append("-" * 80)
        report.append("TOP 10 SELECTED COMPANIES")
        report.append("-" * 80)
        for i, row in screened_df.head(10).iterrows():
            report.append(f"  {row['Symbol']:12} | {row['Company'][:25]:25} | ESG: {row['Overall ESG']:.1f}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


# ============================================================================
# PORTFOLIO OPTIMIZER BASED ON ESG
# ============================================================================

class ESGPortfolioOptimizer:
    """Optimize portfolio based on ESG criteria"""
    
    def __init__(self):
        self.screener = ESGScreener()
    
    def optimize_esg_portfolio(self,
                               df: pd.DataFrame,
                               target_esg: float = 70.0,
                               max_companies: int = 20,
                               sector_diversification: bool = True,
                               max_sector_weight: float = 30.0) -> pd.DataFrame:
        """
        Create an ESG-optimized portfolio
        
        Args:
            df: DataFrame with company ESG data
            target_esg: Target portfolio ESG score
            max_companies: Maximum number of companies
            sector_diversification: Enforce sector diversification
            max_sector_weight: Maximum weight per sector (%)
        
        Returns:
            DataFrame with optimized portfolio
        """
        # Start with ESG leaders
        candidates = df.sort_values('Overall ESG', ascending=False).copy()
        
        portfolio = []
        sectors_count = {}
        
        for _, company in candidates.iterrows():
            if len(portfolio) >= max_companies:
                break
            
            sector = company['Sector']
            
            # Check sector diversification
            if sector_diversification:
                current_sector_count = sectors_count.get(sector, 0)
                max_per_sector = max(1, int(max_companies * max_sector_weight / 100))
                
                if current_sector_count >= max_per_sector:
                    continue
            
            portfolio.append(company)
            sectors_count[sector] = sectors_count.get(sector, 0) + 1
        
        portfolio_df = pd.DataFrame(portfolio)
        
        # Calculate equal weights
        portfolio_df['Weight'] = 100 / len(portfolio_df)
        
        # Calculate portfolio ESG
        portfolio_esg = (portfolio_df['Overall ESG'] * portfolio_df['Weight'] / 100).sum()
        
        print(f"\n✅ ESG Portfolio Optimized")
        print(f"   Companies: {len(portfolio_df)}")
        print(f"   Portfolio ESG Score: {portfolio_esg:.1f}")
        print(f"   Target ESG: {target_esg}")
        print(f"   Sectors: {len(sectors_count)}")
        
        return portfolio_df
    
    def tilt_portfolio_esg(self,
                           df: pd.DataFrame,
                           base_weights: Dict[str, float],
                           esg_tilt_strength: float = 0.5) -> Dict[str, float]:
        """
        Tilt existing portfolio weights based on ESG scores
        
        Args:
            df: DataFrame with company ESG data
            base_weights: Original portfolio weights {symbol: weight}
            esg_tilt_strength: Strength of ESG tilt (0-1)
        
        Returns:
            Dictionary with tilted weights
        """
        tilted_weights = {}
        
        # Get ESG scores for portfolio companies
        portfolio_symbols = list(base_weights.keys())
        portfolio_df = df[df['Symbol'].isin(portfolio_symbols)].copy()
        
        # Calculate ESG z-scores
        portfolio_df['ESG_zscore'] = (
            portfolio_df['Overall ESG'] - portfolio_df['Overall ESG'].mean()
        ) / portfolio_df['Overall ESG'].std()
        
        # Apply tilt
        for symbol in portfolio_symbols:
            base_weight = base_weights[symbol]
            
            if symbol in portfolio_df['Symbol'].values:
                zscore = portfolio_df[portfolio_df['Symbol'] == symbol]['ESG_zscore'].values[0]
                tilt_factor = 1 + (zscore * esg_tilt_strength * 0.2)  # Max 20% tilt
                tilted_weights[symbol] = base_weight * tilt_factor
            else:
                tilted_weights[symbol] = base_weight
        
        # Normalize to 100%
        total = sum(tilted_weights.values())
        tilted_weights = {k: v / total * 100 for k, v in tilted_weights.items()}
        
        return tilted_weights


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def demo_screening():
    """Demonstrate ESG screening capabilities"""
    
    print("=" * 80)
    print("🌿 NYZTRADE - ESG SCREENER DEMONSTRATION")
    print("=" * 80)
    
    # Create sample data
    np.random.seed(42)
    
    companies_data = []
    sectors = ['Technology', 'Financial Services', 'Energy', 'Healthcare', 
               'Consumer Goods', 'Materials', 'Utilities', 'Automobile']
    industries = ['IT Services', 'Banking', 'Oil & Gas', 'Pharmaceuticals',
                  'FMCG', 'Steel', 'Power', 'Automobiles']
    
    for i in range(50):
        sector = sectors[i % len(sectors)]
        industry = industries[i % len(industries)]
        
        env = np.random.uniform(40, 90)
        social = np.random.uniform(45, 90)
        gov = np.random.uniform(50, 90)
        overall = env * 0.35 + social * 0.35 + gov * 0.30
        
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
        
        companies_data.append({
            'Symbol': f'COMP{i+1:02d}',
            'Company': f'Company {i+1}',
            'Sector': sector,
            'Industry': industry,
            'Market Cap (Cr)': np.random.uniform(10000, 500000),
            'Environmental': round(env, 1),
            'Social': round(social, 1),
            'Governance': round(gov, 1),
            'Overall ESG': round(overall, 1),
            'Risk Level': risk,
            'Controversy': round(np.random.uniform(0, 30), 1)
        })
    
    df = pd.DataFrame(companies_data)
    
    # Initialize screener
    screener = ESGScreener()
    
    # Demo 1: Negative Screening
    print("\n" + "=" * 80)
    print("DEMO 1: NEGATIVE SCREENING")
    print("=" * 80)
    
    negative_screened = screener.apply_negative_screening(
        df,
        exclude_controversial=True,
        exclude_fossil_fuels=True,
        exclude_high_carbon=True
    )
    
    # Demo 2: Positive Screening
    print("\n" + "=" * 80)
    print("DEMO 2: POSITIVE SCREENING")
    print("=" * 80)
    
    criteria = ScreeningCriteria(
        min_esg_score=60,
        max_controversy_score=20,
        min_environmental=55,
        min_social=55,
        min_governance=55
    )
    
    positive_screened = screener.apply_positive_screening(df, criteria)
    
    # Demo 3: Best-in-Class
    print("\n" + "=" * 80)
    print("DEMO 3: BEST-IN-CLASS SCREENING")
    print("=" * 80)
    
    best_in_class = screener.apply_best_in_class(df, top_pct=25)
    
    # Demo 4: Thematic Screening
    print("\n" + "=" * 80)
    print("DEMO 4: THEMATIC SCREENING (CLIMATE ACTION)")
    print("=" * 80)
    
    climate_screened = screener.apply_thematic_screening(
        df,
        theme=ThematicFocus.CLIMATE,
        strict=False
    )
    
    # Demo 5: Risk-based Screening
    print("\n" + "=" * 80)
    print("DEMO 5: RISK-BASED SCREENING")
    print("=" * 80)
    
    low_risk = screener.screen_by_risk_level(df, max_risk='Low')
    
    # Generate report
    print("\n" + "=" * 80)
    print("GENERATING SCREENING REPORT")
    print("=" * 80)
    
    report = screener.generate_screening_report(
        df,
        best_in_class,
        "Best-in-Class (Top 25%)"
    )
    print(report)
    
    # Demo Portfolio Optimization
    print("\n" + "=" * 80)
    print("DEMO 6: ESG PORTFOLIO OPTIMIZATION")
    print("=" * 80)
    
    optimizer = ESGPortfolioOptimizer()
    optimal_portfolio = optimizer.optimize_esg_portfolio(
        df,
        target_esg=70,
        max_companies=15,
        sector_diversification=True,
        max_sector_weight=25
    )
    
    print("\n📊 Optimized Portfolio:")
    print(optimal_portfolio[['Symbol', 'Company', 'Sector', 'Overall ESG', 'Weight']].to_string(index=False))
    
    return df, screener, optimizer


if __name__ == "__main__":
    df, screener, optimizer = demo_screening()
    print("\n✅ ESG Screener Demo Complete!")
