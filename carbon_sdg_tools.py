# ============================================================================
# NYZTRADE - CARBON FOOTPRINT CALCULATOR & SDG ALIGNMENT MAPPER
# Environmental Impact Assessment Tools
# ============================================================================

"""
Carbon Footprint Calculator for Indian Companies
SDG (Sustainable Development Goals) Alignment Assessment
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import warnings

warnings.filterwarnings('ignore')


# ============================================================================
# CARBON FOOTPRINT CALCULATOR
# ============================================================================

class EmissionScope(Enum):
    """GHG Protocol Emission Scopes"""
    SCOPE_1 = "Scope 1 - Direct Emissions"
    SCOPE_2 = "Scope 2 - Indirect (Energy)"
    SCOPE_3 = "Scope 3 - Value Chain"


@dataclass
class EmissionFactors:
    """Emission factors for India (kg CO2e per unit)"""
    
    # Electricity (kg CO2e per kWh) - India Grid Average
    GRID_ELECTRICITY: float = 0.82  # CEA 2023 estimate
    RENEWABLE_ELECTRICITY: float = 0.0
    
    # Fuels (kg CO2e per liter)
    DIESEL: float = 2.68
    PETROL: float = 2.31
    LPG: float = 1.51
    CNG: float = 2.75  # per kg
    
    # Natural Gas (kg CO2e per SCM)
    NATURAL_GAS: float = 1.96
    
    # Coal (kg CO2e per kg)
    COAL: float = 2.42
    
    # Travel (kg CO2e per km)
    DOMESTIC_FLIGHT: float = 0.255
    INTERNATIONAL_FLIGHT: float = 0.195
    TRAIN: float = 0.041
    CAR_PETROL: float = 0.192
    CAR_DIESEL: float = 0.171
    TWO_WHEELER: float = 0.072
    
    # Others
    PAPER: float = 1.84  # per kg
    WATER: float = 0.344  # per kL
    WASTE_LANDFILL: float = 0.58  # per kg


class CarbonFootprintCalculator:
    """Calculate corporate carbon footprint following GHG Protocol"""
    
    def __init__(self):
        self.factors = EmissionFactors()
    
    def calculate_scope1_emissions(self, data: Dict) -> Tuple[float, Dict]:
        """
        Calculate Scope 1 (Direct) Emissions
        
        Args:
            data: Dictionary with fuel consumption data
        
        Returns:
            Total emissions (tCO2e) and breakdown
        """
        breakdown = {}
        
        # Stationary combustion
        diesel_litres = data.get('diesel_litres', 0)
        petrol_litres = data.get('petrol_litres', 0)
        lpg_litres = data.get('lpg_litres', 0)
        natural_gas_scm = data.get('natural_gas_scm', 0)
        coal_kg = data.get('coal_kg', 0)
        
        breakdown['diesel'] = diesel_litres * self.factors.DIESEL / 1000
        breakdown['petrol'] = petrol_litres * self.factors.PETROL / 1000
        breakdown['lpg'] = lpg_litres * self.factors.LPG / 1000
        breakdown['natural_gas'] = natural_gas_scm * self.factors.NATURAL_GAS / 1000
        breakdown['coal'] = coal_kg * self.factors.COAL / 1000
        
        # Mobile combustion (company vehicles)
        fleet_diesel = data.get('fleet_diesel_litres', 0)
        fleet_petrol = data.get('fleet_petrol_litres', 0)
        
        breakdown['fleet_diesel'] = fleet_diesel * self.factors.DIESEL / 1000
        breakdown['fleet_petrol'] = fleet_petrol * self.factors.PETROL / 1000
        
        # Fugitive emissions (refrigerants, etc.)
        refrigerant_kg = data.get('refrigerant_kg', 0)
        refrigerant_gwp = data.get('refrigerant_gwp', 1430)  # Default R-410A
        
        breakdown['refrigerants'] = refrigerant_kg * refrigerant_gwp / 1000
        
        total = sum(breakdown.values())
        
        return total, breakdown
    
    def calculate_scope2_emissions(self, data: Dict) -> Tuple[float, Dict]:
        """
        Calculate Scope 2 (Energy Indirect) Emissions
        
        Args:
            data: Dictionary with energy consumption data
        
        Returns:
            Total emissions (tCO2e) and breakdown
        """
        breakdown = {}
        
        # Grid electricity
        grid_kwh = data.get('grid_electricity_kwh', 0)
        renewable_kwh = data.get('renewable_electricity_kwh', 0)
        
        # Location-based method
        breakdown['grid_electricity'] = grid_kwh * self.factors.GRID_ELECTRICITY / 1000
        breakdown['renewable_electricity'] = renewable_kwh * self.factors.RENEWABLE_ELECTRICITY / 1000
        
        # Purchased steam/heating/cooling
        purchased_steam_gj = data.get('purchased_steam_gj', 0)
        steam_factor = 66.5  # kg CO2e per GJ (approximate)
        breakdown['purchased_steam'] = purchased_steam_gj * steam_factor / 1000
        
        total = sum(breakdown.values())
        
        return total, breakdown
    
    def calculate_scope3_emissions(self, data: Dict) -> Tuple[float, Dict]:
        """
        Calculate Scope 3 (Value Chain) Emissions
        
        Args:
            data: Dictionary with value chain data
        
        Returns:
            Total emissions (tCO2e) and breakdown
        """
        breakdown = {}
        
        # Category 1: Purchased goods and services (simplified)
        procurement_spend_cr = data.get('procurement_spend_cr', 0)
        avg_emission_factor = data.get('procurement_ef', 50)  # tCO2e per Cr
        breakdown['purchased_goods'] = procurement_spend_cr * avg_emission_factor
        
        # Category 3: Fuel and energy related (not in Scope 1/2)
        upstream_fuel = data.get('fuel_upstream_factor', 0.15)
        scope1_emissions = data.get('scope1_emissions', 0)
        breakdown['upstream_fuel'] = scope1_emissions * upstream_fuel
        
        # Category 4: Upstream transportation
        freight_tkm = data.get('freight_tonne_km', 0)
        freight_ef = 0.1  # kg CO2e per tonne-km (road average)
        breakdown['upstream_transport'] = freight_tkm * freight_ef / 1000
        
        # Category 5: Waste generated
        waste_kg = data.get('waste_to_landfill_kg', 0)
        breakdown['waste'] = waste_kg * self.factors.WASTE_LANDFILL / 1000
        
        # Category 6: Business travel
        domestic_flight_km = data.get('domestic_flight_km', 0)
        intl_flight_km = data.get('international_flight_km', 0)
        train_km = data.get('train_km', 0)
        
        breakdown['domestic_flights'] = domestic_flight_km * self.factors.DOMESTIC_FLIGHT / 1000
        breakdown['international_flights'] = intl_flight_km * self.factors.INTERNATIONAL_FLIGHT / 1000
        breakdown['train_travel'] = train_km * self.factors.TRAIN / 1000
        
        # Category 7: Employee commuting
        employees = data.get('total_employees', 0)
        avg_commute_km = data.get('avg_commute_km', 15)
        working_days = data.get('working_days', 250)
        car_pct = data.get('car_commute_pct', 30) / 100
        two_wheeler_pct = data.get('two_wheeler_commute_pct', 40) / 100
        
        total_commute_km = employees * avg_commute_km * 2 * working_days
        breakdown['commute_car'] = total_commute_km * car_pct * self.factors.CAR_PETROL / 1000
        breakdown['commute_two_wheeler'] = total_commute_km * two_wheeler_pct * self.factors.TWO_WHEELER / 1000
        
        # Category 9: Downstream transportation
        downstream_freight_tkm = data.get('downstream_freight_tkm', 0)
        breakdown['downstream_transport'] = downstream_freight_tkm * freight_ef / 1000
        
        total = sum(breakdown.values())
        
        return total, breakdown
    
    def calculate_total_footprint(self, data: Dict) -> Dict:
        """
        Calculate complete carbon footprint
        
        Args:
            data: Comprehensive company data
        
        Returns:
            Complete footprint analysis
        """
        scope1_total, scope1_breakdown = self.calculate_scope1_emissions(data)
        scope2_total, scope2_breakdown = self.calculate_scope2_emissions(data)
        
        # Add scope1 for upstream calculation
        data['scope1_emissions'] = scope1_total
        scope3_total, scope3_breakdown = self.calculate_scope3_emissions(data)
        
        total_emissions = scope1_total + scope2_total + scope3_total
        
        # Calculate intensity metrics
        revenue_cr = data.get('revenue_cr', 1)
        employees = data.get('total_employees', 1)
        
        return {
            'total_emissions_tco2e': round(total_emissions, 2),
            'scope1_tco2e': round(scope1_total, 2),
            'scope2_tco2e': round(scope2_total, 2),
            'scope3_tco2e': round(scope3_total, 2),
            'scope1_breakdown': scope1_breakdown,
            'scope2_breakdown': scope2_breakdown,
            'scope3_breakdown': scope3_breakdown,
            'intensity_per_cr': round(total_emissions / revenue_cr, 2),
            'intensity_per_employee': round(total_emissions / employees, 4),
            'scope1_pct': round(scope1_total / total_emissions * 100, 1) if total_emissions > 0 else 0,
            'scope2_pct': round(scope2_total / total_emissions * 100, 1) if total_emissions > 0 else 0,
            'scope3_pct': round(scope3_total / total_emissions * 100, 1) if total_emissions > 0 else 0,
        }
    
    def calculate_reduction_potential(self, footprint: Dict, targets: Dict) -> Dict:
        """Calculate emission reduction potential"""
        
        current = footprint['total_emissions_tco2e']
        scope2 = footprint['scope2_tco2e']
        
        # Renewable energy potential
        renewable_target_pct = targets.get('renewable_energy_pct', 50) / 100
        renewable_reduction = scope2 * renewable_target_pct
        
        # Energy efficiency potential
        efficiency_target_pct = targets.get('energy_efficiency_pct', 20) / 100
        efficiency_reduction = (footprint['scope1_tco2e'] + scope2) * efficiency_target_pct
        
        # Fleet electrification
        fleet_emissions = footprint['scope1_breakdown'].get('fleet_diesel', 0) + \
                         footprint['scope1_breakdown'].get('fleet_petrol', 0)
        fleet_electrification = targets.get('fleet_electrification_pct', 30) / 100
        fleet_reduction = fleet_emissions * fleet_electrification * 0.7  # 70% reduction with EVs
        
        total_reduction = renewable_reduction + efficiency_reduction + fleet_reduction
        
        return {
            'current_emissions': current,
            'renewable_reduction': round(renewable_reduction, 2),
            'efficiency_reduction': round(efficiency_reduction, 2),
            'fleet_reduction': round(fleet_reduction, 2),
            'total_reduction_potential': round(total_reduction, 2),
            'reduction_percentage': round(total_reduction / current * 100, 1) if current > 0 else 0,
            'remaining_emissions': round(current - total_reduction, 2)
        }


# ============================================================================
# SDG ALIGNMENT MAPPER
# ============================================================================

class SDGGoal(Enum):
    """UN Sustainable Development Goals"""
    SDG1 = "No Poverty"
    SDG2 = "Zero Hunger"
    SDG3 = "Good Health and Well-being"
    SDG4 = "Quality Education"
    SDG5 = "Gender Equality"
    SDG6 = "Clean Water and Sanitation"
    SDG7 = "Affordable and Clean Energy"
    SDG8 = "Decent Work and Economic Growth"
    SDG9 = "Industry, Innovation and Infrastructure"
    SDG10 = "Reduced Inequalities"
    SDG11 = "Sustainable Cities and Communities"
    SDG12 = "Responsible Consumption and Production"
    SDG13 = "Climate Action"
    SDG14 = "Life Below Water"
    SDG15 = "Life on Land"
    SDG16 = "Peace, Justice and Strong Institutions"
    SDG17 = "Partnerships for the Goals"


@dataclass
class SDGMetricMapping:
    """Mapping of ESG metrics to SDG goals"""
    
    # Environmental metrics SDG mapping
    ENVIRONMENTAL_SDG_MAP = {
        'carbon_emissions': [SDGGoal.SDG13, SDGGoal.SDG7],
        'renewable_energy': [SDGGoal.SDG7, SDGGoal.SDG13],
        'energy_efficiency': [SDGGoal.SDG7, SDGGoal.SDG12],
        'water_consumption': [SDGGoal.SDG6, SDGGoal.SDG12],
        'water_recycling': [SDGGoal.SDG6, SDGGoal.SDG12],
        'waste_management': [SDGGoal.SDG12, SDGGoal.SDG11],
        'biodiversity': [SDGGoal.SDG15, SDGGoal.SDG14],
        'pollution_control': [SDGGoal.SDG3, SDGGoal.SDG11, SDGGoal.SDG12],
    }
    
    # Social metrics SDG mapping
    SOCIAL_SDG_MAP = {
        'employee_health_safety': [SDGGoal.SDG3, SDGGoal.SDG8],
        'diversity_inclusion': [SDGGoal.SDG5, SDGGoal.SDG10],
        'fair_wages': [SDGGoal.SDG1, SDGGoal.SDG8, SDGGoal.SDG10],
        'training_development': [SDGGoal.SDG4, SDGGoal.SDG8],
        'community_investment': [SDGGoal.SDG1, SDGGoal.SDG11],
        'human_rights': [SDGGoal.SDG8, SDGGoal.SDG16],
        'healthcare_access': [SDGGoal.SDG3],
        'education_initiatives': [SDGGoal.SDG4],
    }
    
    # Governance metrics SDG mapping
    GOVERNANCE_SDG_MAP = {
        'ethics_compliance': [SDGGoal.SDG16],
        'anti_corruption': [SDGGoal.SDG16],
        'transparency': [SDGGoal.SDG16],
        'stakeholder_engagement': [SDGGoal.SDG17],
        'responsible_tax': [SDGGoal.SDG1, SDGGoal.SDG17],
    }


class SDGAlignmentMapper:
    """Map company activities to UN SDGs"""
    
    def __init__(self):
        self.mapping = SDGMetricMapping()
        
        # SDG targets and indicators (simplified)
        self.sdg_targets = {
            SDGGoal.SDG1: {'description': 'End poverty in all its forms everywhere'},
            SDGGoal.SDG3: {'description': 'Ensure healthy lives and promote well-being'},
            SDGGoal.SDG4: {'description': 'Ensure inclusive and equitable quality education'},
            SDGGoal.SDG5: {'description': 'Achieve gender equality and empower all women and girls'},
            SDGGoal.SDG6: {'description': 'Ensure availability and sustainable management of water'},
            SDGGoal.SDG7: {'description': 'Ensure access to affordable, reliable, sustainable energy'},
            SDGGoal.SDG8: {'description': 'Promote sustained, inclusive and sustainable economic growth'},
            SDGGoal.SDG9: {'description': 'Build resilient infrastructure, promote sustainable industrialization'},
            SDGGoal.SDG10: {'description': 'Reduce inequality within and among countries'},
            SDGGoal.SDG11: {'description': 'Make cities and human settlements inclusive, safe, sustainable'},
            SDGGoal.SDG12: {'description': 'Ensure sustainable consumption and production patterns'},
            SDGGoal.SDG13: {'description': 'Take urgent action to combat climate change and its impacts'},
            SDGGoal.SDG14: {'description': 'Conserve and sustainably use the oceans, seas and marine resources'},
            SDGGoal.SDG15: {'description': 'Protect, restore and promote sustainable use of terrestrial ecosystems'},
            SDGGoal.SDG16: {'description': 'Promote peaceful and inclusive societies for sustainable development'},
            SDGGoal.SDG17: {'description': 'Strengthen the means of implementation and revitalize partnerships'},
        }
    
    def assess_sdg_alignment(self, esg_data: Dict) -> Dict:
        """
        Assess company's alignment with SDGs based on ESG data
        
        Args:
            esg_data: Dictionary with ESG metrics
        
        Returns:
            SDG alignment assessment
        """
        sdg_scores = {goal: 0.0 for goal in SDGGoal}
        sdg_contributions = {goal: [] for goal in SDGGoal}
        
        # Assess Environmental contributions
        for metric, sdgs in self.mapping.ENVIRONMENTAL_SDG_MAP.items():
            metric_score = esg_data.get(metric, 50) / 100  # Normalize to 0-1
            for sdg in sdgs:
                sdg_scores[sdg] += metric_score * 20  # Weight contribution
                sdg_contributions[sdg].append(metric)
        
        # Assess Social contributions
        for metric, sdgs in self.mapping.SOCIAL_SDG_MAP.items():
            metric_score = esg_data.get(metric, 50) / 100
            for sdg in sdgs:
                sdg_scores[sdg] += metric_score * 20
                sdg_contributions[sdg].append(metric)
        
        # Assess Governance contributions
        for metric, sdgs in self.mapping.GOVERNANCE_SDG_MAP.items():
            metric_score = esg_data.get(metric, 50) / 100
            for sdg in sdgs:
                sdg_scores[sdg] += metric_score * 20
                sdg_contributions[sdg].append(metric)
        
        # Normalize scores
        max_score = max(sdg_scores.values()) if max(sdg_scores.values()) > 0 else 1
        sdg_scores = {k: min(100, v / max_score * 100) for k, v in sdg_scores.items()}
        
        # Determine primary and secondary SDG focus
        sorted_sdgs = sorted(sdg_scores.items(), key=lambda x: x[1], reverse=True)
        primary_sdgs = [sdg for sdg, score in sorted_sdgs[:3] if score > 50]
        secondary_sdgs = [sdg for sdg, score in sorted_sdgs[3:8] if score > 30]
        
        return {
            'sdg_scores': sdg_scores,
            'sdg_contributions': sdg_contributions,
            'primary_sdgs': primary_sdgs,
            'secondary_sdgs': secondary_sdgs,
            'total_sdgs_aligned': len([s for s, v in sdg_scores.items() if v > 30]),
            'average_alignment': np.mean(list(sdg_scores.values()))
        }
    
    def generate_sdg_report(self, company_name: str, alignment: Dict) -> str:
        """Generate SDG alignment report"""
        
        report = []
        report.append("=" * 80)
        report.append(f"🎯 SDG ALIGNMENT REPORT - {company_name}")
        report.append("=" * 80)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        report.append("")
        
        report.append("-" * 80)
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total SDGs Aligned (>30 score): {alignment['total_sdgs_aligned']}")
        report.append(f"Average Alignment Score: {alignment['average_alignment']:.1f}")
        report.append("")
        
        report.append("-" * 80)
        report.append("PRIMARY SDG FOCUS (Top 3)")
        report.append("-" * 80)
        for sdg in alignment['primary_sdgs']:
            score = alignment['sdg_scores'][sdg]
            report.append(f"  {sdg.name}: {sdg.value}")
            report.append(f"    Score: {score:.1f}")
            report.append(f"    Description: {self.sdg_targets[sdg]['description']}")
            report.append("")
        
        report.append("-" * 80)
        report.append("SECONDARY SDG ALIGNMENT")
        report.append("-" * 80)
        for sdg in alignment['secondary_sdgs']:
            score = alignment['sdg_scores'][sdg]
            report.append(f"  {sdg.name}: {sdg.value} - Score: {score:.1f}")
        report.append("")
        
        report.append("-" * 80)
        report.append("ALL SDG SCORES")
        report.append("-" * 80)
        for sdg, score in sorted(alignment['sdg_scores'].items(), 
                                  key=lambda x: x[1], reverse=True):
            bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            report.append(f"  {sdg.name:6} {bar} {score:5.1f}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def get_improvement_recommendations(self, alignment: Dict) -> List[Dict]:
        """Get recommendations to improve SDG alignment"""
        
        recommendations = []
        
        # Find SDGs with low scores that have high potential
        low_score_sdgs = [sdg for sdg, score in alignment['sdg_scores'].items() 
                         if score < 40 and sdg in [
                             SDGGoal.SDG7, SDGGoal.SDG12, SDGGoal.SDG13,
                             SDGGoal.SDG5, SDGGoal.SDG8
                         ]]
        
        recommendation_map = {
            SDGGoal.SDG7: {
                'action': 'Increase renewable energy adoption',
                'metrics': ['renewable_energy', 'energy_efficiency'],
                'impact': 'High'
            },
            SDGGoal.SDG12: {
                'action': 'Implement circular economy practices',
                'metrics': ['waste_management', 'water_recycling'],
                'impact': 'Medium'
            },
            SDGGoal.SDG13: {
                'action': 'Set science-based carbon reduction targets',
                'metrics': ['carbon_emissions', 'renewable_energy'],
                'impact': 'High'
            },
            SDGGoal.SDG5: {
                'action': 'Enhance gender diversity programs',
                'metrics': ['diversity_inclusion'],
                'impact': 'Medium'
            },
            SDGGoal.SDG8: {
                'action': 'Improve worker welfare and safety programs',
                'metrics': ['employee_health_safety', 'fair_wages'],
                'impact': 'High'
            },
        }
        
        for sdg in low_score_sdgs:
            if sdg in recommendation_map:
                rec = recommendation_map[sdg]
                recommendations.append({
                    'sdg': sdg.value,
                    'current_score': alignment['sdg_scores'][sdg],
                    'action': rec['action'],
                    'focus_metrics': rec['metrics'],
                    'impact': rec['impact']
                })
        
        return recommendations


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def demo_carbon_calculator():
    """Demonstrate carbon footprint calculation"""
    
    print("=" * 80)
    print("🌍 CARBON FOOTPRINT CALCULATOR DEMO")
    print("=" * 80)
    
    calculator = CarbonFootprintCalculator()
    
    # Sample company data
    company_data = {
        # Scope 1 data
        'diesel_litres': 50000,
        'petrol_litres': 20000,
        'natural_gas_scm': 100000,
        'fleet_diesel_litres': 30000,
        'fleet_petrol_litres': 15000,
        'refrigerant_kg': 100,
        
        # Scope 2 data
        'grid_electricity_kwh': 5000000,
        'renewable_electricity_kwh': 1000000,
        
        # Scope 3 data
        'procurement_spend_cr': 500,
        'freight_tonne_km': 1000000,
        'waste_to_landfill_kg': 50000,
        'domestic_flight_km': 500000,
        'international_flight_km': 200000,
        'train_km': 100000,
        'total_employees': 5000,
        'avg_commute_km': 15,
        'working_days': 250,
        'car_commute_pct': 30,
        'two_wheeler_commute_pct': 40,
        'downstream_freight_tkm': 500000,
        
        # Company info
        'revenue_cr': 1000,
    }
    
    footprint = calculator.calculate_total_footprint(company_data)
    
    print("\n📊 CARBON FOOTPRINT SUMMARY")
    print("-" * 60)
    print(f"Total Emissions: {footprint['total_emissions_tco2e']:,.2f} tCO2e")
    print(f"  Scope 1: {footprint['scope1_tco2e']:,.2f} tCO2e ({footprint['scope1_pct']}%)")
    print(f"  Scope 2: {footprint['scope2_tco2e']:,.2f} tCO2e ({footprint['scope2_pct']}%)")
    print(f"  Scope 3: {footprint['scope3_tco2e']:,.2f} tCO2e ({footprint['scope3_pct']}%)")
    print(f"\nIntensity Metrics:")
    print(f"  Per Cr Revenue: {footprint['intensity_per_cr']:.2f} tCO2e")
    print(f"  Per Employee: {footprint['intensity_per_employee']:.4f} tCO2e")
    
    # Calculate reduction potential
    targets = {
        'renewable_energy_pct': 50,
        'energy_efficiency_pct': 20,
        'fleet_electrification_pct': 30
    }
    
    reduction = calculator.calculate_reduction_potential(footprint, targets)
    
    print("\n🎯 EMISSION REDUCTION POTENTIAL")
    print("-" * 60)
    print(f"Current Emissions: {reduction['current_emissions']:,.2f} tCO2e")
    print(f"Renewable Energy Transition: -{reduction['renewable_reduction']:,.2f} tCO2e")
    print(f"Energy Efficiency: -{reduction['efficiency_reduction']:,.2f} tCO2e")
    print(f"Fleet Electrification: -{reduction['fleet_reduction']:,.2f} tCO2e")
    print(f"\nTotal Reduction Potential: {reduction['reduction_percentage']:.1f}%")
    print(f"Remaining Emissions: {reduction['remaining_emissions']:,.2f} tCO2e")
    
    return footprint, reduction


def demo_sdg_alignment():
    """Demonstrate SDG alignment assessment"""
    
    print("\n" + "=" * 80)
    print("🎯 SDG ALIGNMENT ASSESSMENT DEMO")
    print("=" * 80)
    
    mapper = SDGAlignmentMapper()
    
    # Sample ESG data
    esg_data = {
        # Environmental
        'carbon_emissions': 65,  # Score out of 100
        'renewable_energy': 70,
        'energy_efficiency': 75,
        'water_consumption': 60,
        'water_recycling': 55,
        'waste_management': 70,
        'biodiversity': 45,
        'pollution_control': 80,
        
        # Social
        'employee_health_safety': 85,
        'diversity_inclusion': 60,
        'fair_wages': 90,
        'training_development': 75,
        'community_investment': 65,
        'human_rights': 80,
        'healthcare_access': 70,
        'education_initiatives': 55,
        
        # Governance
        'ethics_compliance': 85,
        'anti_corruption': 90,
        'transparency': 75,
        'stakeholder_engagement': 70,
        'responsible_tax': 80,
    }
    
    alignment = mapper.assess_sdg_alignment(esg_data)
    
    report = mapper.generate_sdg_report("Sample Company Ltd", alignment)
    print(report)
    
    # Get recommendations
    recommendations = mapper.get_improvement_recommendations(alignment)
    
    if recommendations:
        print("\n💡 IMPROVEMENT RECOMMENDATIONS")
        print("-" * 60)
        for rec in recommendations:
            print(f"\n📌 {rec['sdg']}")
            print(f"   Current Score: {rec['current_score']:.1f}")
            print(f"   Action: {rec['action']}")
            print(f"   Focus Metrics: {', '.join(rec['focus_metrics'])}")
            print(f"   Impact: {rec['impact']}")
    
    return alignment, recommendations


if __name__ == "__main__":
    footprint, reduction = demo_carbon_calculator()
    alignment, recommendations = demo_sdg_alignment()
    
    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETE!")
    print("=" * 80)
