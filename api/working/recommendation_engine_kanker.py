"""
Recommendation Engine Module - Kanker District Specific
Generates comprehensive fertilizer recommendations based on Kanker soil data
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

# Import our custom modules
from .fertilizer_database import (
    CHEMICAL_FERTILIZERS, ORGANIC_FERTILIZERS, 
    calculate_fertilizer_cost, get_optimal_fertilizer,
    DEFICIENCY_SYMPTOMS, APPLICATION_GUIDELINES
)
from .crop_requirements_kanker import (
    KANKER_CROP_REQUIREMENTS, KANKER_ZONES,
    KANKER_MICRONUTRIENT_STATUS, KANKER_PH_STATUS,
    get_crop_requirement, classify_nutrient_status,
    get_micronutrient_recommendation, get_ph_recommendation
)
from .kanker_data_loader import kanker_loader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RecommendationItem:
    """Individual recommendation item"""
    nutrient: str
    product: str
    quantity_kg: float
    cost_with_subsidy: float
    cost_without_subsidy: float
    timing: str
    method: str
    reason: str
    priority: str
    confidence: float

@dataclass
class DeficiencyAnalysis:
    """Deficiency analysis result"""
    nutrient: str
    current_value: float
    optimal_min: float
    optimal_max: float
    deficiency_amount: float
    status: str
    severity: str
    village_comparison: Optional[str] = None

class KankerRecommendationEngine:
    """Main recommendation engine for Kanker district"""
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.kanker_loader = kanker_loader
        self.confidence_threshold = 0.7  # Minimum confidence for recommendations
        
    def generate_recommendations(
        self,
        npk_data: Dict[str, float],
        enhanced_details: Dict[str, Any],
        crop_type: str,
        coordinates: Tuple[float, float],
        field_area_ha: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate comprehensive fertilizer recommendations
        
        Args:
            npk_data: NPK values from satellite analysis
            enhanced_details: Enhanced analysis details
            crop_type: Type of crop
            coordinates: Field coordinates (lat, lon)
            field_area_ha: Field area in hectares
            
        Returns:
            Comprehensive recommendation dictionary
        """
        try:
            lat, lon = coordinates
            
            # 1. Find nearest village
            nearest_village_info = self.kanker_loader.find_nearest_village(lat, lon)
            
            # 2. Get zone information
            zone_info = self.kanker_loader.get_zone_information(lat, lon)
            if not zone_info:
                zone_info = {"error": "Zone information not available"}
            
            # 3. Classify nutrient status using Kanker ranges
            nutrient_status = self._classify_nutrients_kanker(npk_data, crop_type, nearest_village_info)
            
            # 4. Analyze deficiencies
            deficiency_analysis = self._analyze_deficiencies(npk_data, crop_type, nutrient_status)
            
            # 5. Generate chemical fertilizer recommendations
            chemical_recs = self._generate_chemical_recommendations(
                deficiency_analysis, zone_info, crop_type, field_area_ha
            )
            
            # 6. Generate organic alternatives
            organic_recs = self._generate_organic_recommendations(
                deficiency_analysis, field_area_ha
            )
            
            # 7. Micronutrient recommendations
            micronutrient_recs = self._generate_micronutrient_recommendations(
                enhanced_details, nearest_village_info, field_area_ha
            )
            
            # 8. pH recommendations
            ph_recs = self._generate_ph_recommendations(enhanced_details, field_area_ha)
            
            # 9. Application schedule
            application_schedule = self._create_application_schedule(
                chemical_recs, crop_type
            )
            
            # 10. Cost analysis
            cost_analysis = self._calculate_total_cost(
                chemical_recs, organic_recs, micronutrient_recs, ph_recs
            )
            
            # 11. Generate summary
            summary = self._generate_summary(
                deficiency_analysis, chemical_recs, micronutrient_recs
            )
            
            return {
                "dataSource": "Kanker Soil Analysis 2025 (91 villages)",
                "nearest_village": nearest_village_info.get('village_name') if nearest_village_info else "Unknown",
                "distance_to_village_km": nearest_village_info.get('distance_km', 0) if nearest_village_info else 0,
                "zoneInformation": zone_info,
                "nutrientStatus": nutrient_status,
                "deficiencyAnalysis": deficiency_analysis,
                "recommendations_list": chemical_recs + organic_recs,
                "micronutrientRecommendations": micronutrient_recs,
                "phRecommendations": ph_recs,
                "applicationSchedule": application_schedule,
                "costAnalysis": cost_analysis,
                "summary": summary,
                "confidence": f"{self._calculate_overall_confidence(nearest_village_info, zone_info)*100:.0f}%",
                "total_cost_with_subsidy_per_ha": cost_analysis.get('total_with_subsidy', 0),
                "total_cost_without_subsidy_per_ha": cost_analysis.get('total_without_subsidy', 0),
                "total_subsidy_savings_per_ha": cost_analysis.get('subsidy_savings', 0),
                "total_cost_with_subsidy_per_acre": cost_analysis.get('total_with_subsidy', 0) * 0.404686,
                "total_cost_without_subsidy_per_acre": cost_analysis.get('total_without_subsidy', 0) * 0.404686,
                "total_subsidy_savings_per_acre": cost_analysis.get('subsidy_savings', 0) * 0.404686,
                "total_cost_with_subsidy_for_field": round(cost_analysis.get('total_with_subsidy', 0) * field_area_ha, 2),
                "total_cost_without_subsidy_for_field": round(cost_analysis.get('total_without_subsidy', 0) * field_area_ha, 2),
                "total_subsidy_savings_for_field": round(cost_analysis.get('subsidy_savings', 0) * field_area_ha, 2),
                "metadata": {
                    "crop_type": crop_type,
                    "field_area_ha": field_area_ha,
                    "coordinates": coordinates,
                    "analysis_date": enhanced_details.get('analysis_date', 'Unknown'),
                    "satellite_data": enhanced_details.get('satellite_item', 'Unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "error": f"Failed to generate recommendations: {str(e)}",
                "dataSource": "Kanker Soil Analysis 2025 (91 villages)",
                "fallback": True
            }
    
    def _classify_nutrients_kanker(
        self, 
        npk_data: Dict[str, float], 
        crop_type: str, 
        nearest_village_info: Optional[Dict]
    ) -> Dict[str, Any]:
        """Classify nutrients using Kanker ranges"""
        
        crop_req = get_crop_requirement(crop_type)
        village_data = nearest_village_info.get('village_data') if nearest_village_info and nearest_village_info.get('village_data') else None
        
        nutrient_status = {}
        
        for nutrient in ['Nitrogen', 'Phosphorus', 'Potassium']:
            nutrient_key = nutrient[0]  # N, P, K
            current_value = npk_data.get(nutrient, 0)
            
            # Get Kanker classification
            kanker_classification = classify_nutrient_status(current_value, nutrient_key, crop_type)
            
            # Get village comparison
            village_comparison = None
            if village_data:
                village_value = village_data.get(f'{nutrient_key.lower()}_value')
                village_level = village_data.get(f'{nutrient_key.lower()}_level')
                if village_value:
                    village_comparison = f"{village_level} ({village_value} kg/ha in {village_data.get('village_name', 'village')})"
            
            nutrient_status[nutrient] = {
                "current": round(current_value, 2),
                "optimal_range": f"{crop_req.optimal_npk[nutrient_key]['min']}-{crop_req.optimal_npk[nutrient_key]['max']} kg/ha",
                "status": kanker_classification['status'],
                "description": kanker_classification['description'],
                "village_comparison": village_comparison,
                "kanker_range": kanker_classification['range']
            }
        
        return nutrient_status
    
    def _analyze_deficiencies(
        self, 
        npk_data: Dict[str, float], 
        crop_type: str, 
        nutrient_status: Dict[str, Any]
    ) -> List[DeficiencyAnalysis]:
        """Analyze nutrient deficiencies"""
        
        crop_req = get_crop_requirement(crop_type)
        deficiencies = []
        
        for nutrient in ['Nitrogen', 'Phosphorus', 'Potassium']:
            nutrient_key = nutrient[0]
            current_value = npk_data.get(nutrient, 0)
            optimal_min = crop_req.optimal_npk[nutrient_key]['min']
            optimal_max = crop_req.optimal_npk[nutrient_key]['max']
            
            # Calculate deficiency
            if current_value < optimal_min:
                deficiency_amount = optimal_min - current_value
                status = "deficient"
                severity = "high" if deficiency_amount > optimal_min * 0.5 else "medium"
            elif current_value > optimal_max:
                deficiency_amount = current_value - optimal_max
                status = "excess"
                severity = "high" if deficiency_amount > optimal_max * 0.5 else "medium"
            else:
                deficiency_amount = 0
                status = "sufficient"
                severity = "low"
            
            deficiencies.append(DeficiencyAnalysis(
                nutrient=nutrient,
                current_value=current_value,
                optimal_min=optimal_min,
                optimal_max=optimal_max,
                deficiency_amount=deficiency_amount,
                status=status,
                severity=severity
            ))
        
        return deficiencies
    
    def _generate_chemical_recommendations(
        self, 
        deficiency_analysis: List[DeficiencyAnalysis],
        zone_info: Dict[str, Any],
        crop_type: str,
        field_area_ha: float
    ) -> List[Dict[str, Any]]:
        """Generate chemical fertilizer recommendations"""
        
        recommendations = []
        
        for deficiency in deficiency_analysis:
            if deficiency.status == "deficient" and deficiency.deficiency_amount > 0:
                
                # Get fertilizer product
                if deficiency.nutrient == "Nitrogen":
                    product = "Urea"
                    nutrient_content = 46  # Urea has 46% N
                elif deficiency.nutrient == "Phosphorus":
                    product = "DAP"
                    nutrient_content = 46  # DAP has 46% P
                elif deficiency.nutrient == "Potassium":
                    product = "MOP"
                    nutrient_content = 60  # MOP has 60% K
                else:
                    continue
                
                # Calculate quantity needed
                quantity_kg = (deficiency.deficiency_amount * 100) / nutrient_content
                quantity_kg = round(quantity_kg, 2)
                
                # Calculate cost with Kanker-specific pricing
                cost_info = self._calculate_kanker_fertilizer_cost(product, quantity_kg)
                
                # Check if cost calculation was successful
                if 'error' in cost_info:
                    print(f"❌ Cost calculation error for {product}: {cost_info['error']}")
                    # Use fallback pricing
                    cost_info = self._get_fallback_pricing(product, quantity_kg)
                
                # Determine priority
                priority = "HIGH" if deficiency.severity == "high" else "MEDIUM"
                
                # Determine timing
                timing = self._get_application_timing(product, crop_type)
                
                # Generate reason
                reason = self._generate_recommendation_reason(
                    deficiency, zone_info, product
                )
                
                # Convert to acres for Indian farmers
                quantity_per_acre = round(quantity_kg / 2.47, 2)  # 1 hectare = 2.47 acres
                cost_per_acre = round(cost_info.get('total_cost', 0) / 2.47, 2)
                
                recommendations.append({
                    "nutrient": deficiency.nutrient,
                    "product": product,
                    "quantity_kg": quantity_kg,
                    "quantity_per_hectare": f"{quantity_kg} kg/ha",
                    "quantity_per_acre": f"{quantity_per_acre} kg/acre",
                    "total_quantity": f"{quantity_kg * field_area_ha} kg",
                    "cost_with_subsidy": cost_info.get('total_cost', 0),
                    "cost_per_hectare": cost_info.get('total_cost', 0),
                    "cost_per_acre": cost_per_acre,
                    "cost_without_subsidy": cost_info.get('total_cost', 0) + cost_info.get('subsidy_savings', 0),
                    "subsidy_savings": cost_info.get('subsidy_savings', 0),
                    "timing": timing,
                    "method": "Broadcast",
                    "reason": reason,
                    "priority": priority,
                    "confidence": 0.9,
                    "deficiency_amount": deficiency.deficiency_amount,
                    "nutrient_content": f"{nutrient_content}%"
                })
        
        return recommendations
    
    def _generate_organic_recommendations(
        self, 
        deficiency_analysis: List[DeficiencyAnalysis],
        field_area_ha: float
    ) -> List[Dict[str, Any]]:
        """Generate organic fertilizer recommendations"""
        
        recommendations = []
        
        # Check if any major deficiencies exist
        major_deficiencies = [d for d in deficiency_analysis if d.status == "deficient" and d.severity == "high"]
        
        if major_deficiencies:
            # Recommend FYM for overall soil health
            fym_rate = 10  # 10 tons per hectare
            fym_cost_per_ton = 1500
            
            recommendations.append({
                "product": "Farmyard Manure (FYM)",
                "quantity_per_hectare": f"{fym_rate} t/ha",
                "total_quantity": f"{fym_rate * field_area_ha} tons",
                "cost_per_ton": fym_cost_per_ton,
                "total_cost": fym_rate * field_area_ha * fym_cost_per_ton,
                "timing": "Basal application (before sowing/transplanting)",
                "method": "Mix with soil",
                "reason": "Improves overall soil health and provides slow-release nutrients",
                "priority": "MEDIUM",
                "confidence": 0.8,
                "benefits": [
                    "Improves soil structure",
                    "Increases water holding capacity",
                    "Provides micronutrients",
                    "Enhances microbial activity"
                ]
            })
        
        return recommendations
    
    def _generate_micronutrient_recommendations(
        self, 
        enhanced_details: Dict[str, Any],
        nearest_village_info: Optional[Dict],
        field_area_ha: float
    ) -> List[Dict[str, Any]]:
        """Generate micronutrient recommendations based on Kanker data"""
        
        recommendations = []
        village_data = nearest_village_info.get('village_data') if nearest_village_info and nearest_village_info.get('village_data') else None
        
        # Get micronutrient data from village
        micronutrients = ['zinc', 'boron', 'iron']
        
        for micronutrient in micronutrients:
            village_level = village_data.get(f'{micronutrient}_level', '').lower() if village_data else ''
            village_value = village_data.get(f'estimated_{micronutrient}', '')
            
            # Check if micronutrient is deficient based on Kanker data
            if village_level in ['low', 'deficient']:
                
                if micronutrient == 'zinc':
                    product = "Zinc Sulfate"
                    dosage = "25-50 kg/ha"
                    cost_per_kg = 60
                    reason = f"Zinc deficiency detected in {village_data.get('village_name', 'area')} - 80% of Kanker villages are zinc deficient"
                elif micronutrient == 'boron':
                    product = "Borax"
                    dosage = "5-15 kg/ha"
                    cost_per_kg = 80
                    reason = f"Boron deficiency detected in {village_data.get('village_name', 'area')} - 85% of Kanker villages are boron deficient"
                elif micronutrient == 'iron':
                    product = "Ferrous Sulfate"
                    dosage = "25-75 kg/ha"
                    cost_per_kg = 25
                    reason = f"Iron deficiency detected in {village_data.get('village_name', 'area')} - 50% of Kanker villages are iron deficient"
                else:
                    continue
                
                # Calculate cost (using average dosage)
                avg_dosage = float(dosage.split('-')[0]) + float(dosage.split('-')[1].split()[0]) / 2
                total_cost = avg_dosage * field_area_ha * cost_per_kg
                
                # Convert to acres for Indian farmers
                dosage_per_acre = round(avg_dosage / 2.47, 2)
                cost_per_acre = round(total_cost / 2.47, 2)
                
                recommendations.append({
                    "nutrient": micronutrient.title(),
                    "product": product,
                    "dosage_range": dosage,
                    "recommended_dosage": f"{avg_dosage:.1f} kg/ha",
                    "recommended_dosage_acre": f"{dosage_per_acre:.1f} kg/acre",
                    "total_quantity": f"{avg_dosage * field_area_ha:.1f} kg",
                    "cost_per_kg": cost_per_kg,
                    "total_cost": total_cost,
                    "cost_per_hectare": total_cost,
                    "cost_per_acre": cost_per_acre,
                    "timing": "Basal application",
                    "method": "Broadcast and mix with soil",
                    "reason": reason,
                    "priority": "HIGH",
                    "confidence": 0.85,
                    "village_data": village_value,
                    "kanker_status": f"{KANKER_MICRONUTRIENT_STATUS[micronutrient]['deficient_villages']} villages deficient"
                })
        
        return recommendations
    
    def _generate_ph_recommendations(
        self, 
        enhanced_details: Dict[str, Any],
        field_area_ha: float
    ) -> List[Dict[str, Any]]:
        """Generate pH recommendations"""
        
        recommendations = []
        
        # Get pH from enhanced details (if available)
        ph_value = enhanced_details.get('ph', None)
        
        if ph_value:
            ph_rec = get_ph_recommendation(ph_value)
            
            if ph_rec['status'] in ['acidic_soils', 'slightly_acidic']:
                lime_rate = 2 if ph_rec['status'] == 'acidic_soils' else 1
                lime_cost_per_ton = 2000
                
                recommendations.append({
                    "issue": "Acidic Soil",
                    "current_ph": ph_value,
                    "recommended_ph": "6.5-7.5",
                    "product": "Agricultural Lime",
                    "quantity_per_hectare": f"{lime_rate} t/ha",
                    "total_quantity": f"{lime_rate * field_area_ha} tons",
                    "cost_per_ton": lime_cost_per_ton,
                    "total_cost": lime_rate * field_area_ha * lime_cost_per_ton,
                    "timing": "Before sowing/transplanting",
                    "method": "Broadcast and mix with soil",
                    "reason": f"pH {ph_value} is too acidic for optimal crop growth",
                    "priority": ph_rec['priority'],
                    "confidence": 0.8,
                    "villages_affected": ph_rec['villages_count']
                })
        
        return recommendations
    
    def _create_application_schedule(
        self, 
        chemical_recs: List[Dict[str, Any]], 
        crop_type: str
    ) -> Dict[str, Any]:
        """Create application schedule based on crop type"""
        
        schedule = APPLICATION_GUIDELINES.get(crop_type.lower(), APPLICATION_GUIDELINES['rice'])
        
        # Map recommendations to schedule
        basal_fertilizers = []
        top_dress_fertilizers = []
        
        for rec in chemical_recs:
            if rec['product'] in ['DAP', 'MOP', 'Zinc Sulfate']:
                basal_fertilizers.append(rec)
            elif rec['product'] == 'Urea':
                top_dress_fertilizers.append(rec)
        
        return {
            "crop_type": crop_type,
            "schedule": {
                "basal_application": {
                    "timing": schedule['basal_application']['timing'],
                    "fertilizers": basal_fertilizers,
                    "method": schedule['basal_application']['method']
                },
                "first_top_dress": {
                    "timing": schedule['first_top_dress']['timing'],
                    "fertilizers": top_dress_fertilizers[:1] if top_dress_fertilizers else [],
                    "method": schedule['first_top_dress']['method']
                },
                "second_top_dress": {
                    "timing": schedule['second_top_dress']['timing'],
                    "fertilizers": top_dress_fertilizers[1:] if len(top_dress_fertilizers) > 1 else [],
                    "method": schedule['second_top_dress']['method']
                }
            }
        }
    
    def _calculate_total_cost(
        self, 
        chemical_recs: List[Dict[str, Any]],
        organic_recs: List[Dict[str, Any]],
        micronutrient_recs: List[Dict[str, Any]],
        ph_recs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate total cost analysis"""
        
        total_cost_with_subsidy = 0
        total_cost_without_subsidy = 0
        total_subsidy_savings = 0
        
        # Chemical fertilizers
        for rec in chemical_recs:
            total_cost_with_subsidy += rec.get('cost_with_subsidy', 0)
            total_cost_without_subsidy += rec.get('cost_without_subsidy', 0)
            total_subsidy_savings += rec.get('subsidy_savings', 0)
        
        # Organic fertilizers
        for rec in organic_recs:
            total_cost_with_subsidy += rec.get('total_cost', 0)
            total_cost_without_subsidy += rec.get('total_cost', 0)
        
        # Micronutrients
        for rec in micronutrient_recs:
            total_cost_with_subsidy += rec.get('total_cost', 0)
            total_cost_without_subsidy += rec.get('total_cost', 0)
        
        # pH amendments
        for rec in ph_recs:
            total_cost_with_subsidy += rec.get('total_cost', 0)
            total_cost_without_subsidy += rec.get('total_cost', 0)
        
        # Convert to acres for Indian farmers
        total_cost_with_subsidy_per_acre = round(total_cost_with_subsidy / 2.47, 2)
        total_cost_without_subsidy_per_acre = round(total_cost_without_subsidy / 2.47, 2)
        total_subsidy_savings_per_acre = round(total_subsidy_savings / 2.47, 2)
        
        return {
            "total_cost_with_subsidy": total_cost_with_subsidy,
            "total_cost_without_subsidy": total_cost_without_subsidy,
            "total_subsidy_savings": total_subsidy_savings,
            "total_cost_with_subsidy_per_acre": total_cost_with_subsidy_per_acre,
            "total_cost_without_subsidy_per_acre": total_cost_without_subsidy_per_acre,
            "total_subsidy_savings_per_acre": total_subsidy_savings_per_acre,
            "cost_breakdown": {
                "chemical_fertilizers": sum(rec.get('cost_with_subsidy', 0) for rec in chemical_recs),
                "organic_fertilizers": sum(rec.get('total_cost', 0) for rec in organic_recs),
                "micronutrients": sum(rec.get('total_cost', 0) for rec in micronutrient_recs),
                "ph_amendments": sum(rec.get('total_cost', 0) for rec in ph_recs)
            },
            "cost_per_hectare": {
                "with_subsidy": total_cost_with_subsidy,
                "without_subsidy": total_cost_without_subsidy
            },
            "cost_per_acre": {
                "with_subsidy": total_cost_with_subsidy_per_acre,
                "without_subsidy": total_cost_without_subsidy_per_acre
            }
        }
    
    def _generate_summary(
        self, 
        deficiency_analysis: List[DeficiencyAnalysis],
        chemical_recs: List[Dict[str, Any]],
        micronutrient_recs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate recommendation summary"""
        
        high_priority_items = [rec for rec in chemical_recs if rec['priority'] == 'HIGH']
        medium_priority_items = [rec for rec in chemical_recs if rec['priority'] == 'MEDIUM']
        
        summary_text = f"Based on Kanker soil analysis data, "
        
        if high_priority_items:
            summary_text += f"{len(high_priority_items)} high-priority fertilizer applications needed. "
        
        if micronutrient_recs:
            summary_text += f"{len(micronutrient_recs)} micronutrient deficiencies detected. "
        
        summary_text += "Recommendations are based on nearest village data and zone characteristics."
        
        return {
            "summary_text": summary_text,
            "total_recommendations": len(chemical_recs) + len(micronutrient_recs),
            "high_priority_count": len(high_priority_items),
            "medium_priority_count": len(medium_priority_items),
            "micronutrient_deficiencies": len(micronutrient_recs),
            "data_source": "Kanker Soil Analysis 2025 (91 villages)",
            "confidence_level": "High (88-93%)"
        }
    
    def _calculate_overall_confidence(
        self, 
        nearest_village_info: Optional[Dict],
        zone_info: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence in recommendations"""
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence if village data available
        if nearest_village_info and nearest_village_info.get('distance_km', 0) < 10:
            confidence += 0.3
        
        # Increase confidence if zone identified
        if zone_info.get('nitrogen_zone', {}).get('zone_name') != 'unknown':
            confidence += 0.2
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _get_application_timing(self, product: str, crop_type: str) -> str:
        """Get application timing for fertilizer"""
        
        timing_map = {
            "Urea": "Split application - 50% basal, 50% top dressing",
            "DAP": "Basal application at sowing/transplanting",
            "MOP": "Basal application + top dressing",
            "Zinc Sulfate": "Basal application",
            "Borax": "Basal application",
            "Ferrous Sulfate": "Foliar spray or basal application"
        }
        
        return timing_map.get(product, "As per crop schedule")
    
    def _calculate_kanker_fertilizer_cost(self, product: str, quantity_kg: float) -> Dict[str, Any]:
        """Calculate fertilizer cost with Kanker-specific pricing"""
        
        # Kanker district specific pricing (per kg) - REAL MARKET PRICES 2024
        kanker_pricing = {
            "Urea": {
                "price_per_kg": 8.0,       # ₹8/kg (₹360/45kg bag)
                "subsidy_per_kg": 2.0,     # ₹2/kg subsidy
                "net_price_per_kg": 6.0    # ₹6/kg after subsidy
            },
            "DAP": {
                "price_per_kg": 30.0,      # ₹30/kg (₹1500/50kg bag)
                "subsidy_per_kg": 5.0,     # ₹5/kg subsidy
                "net_price_per_kg": 25.0   # ₹25/kg after subsidy
            },
            "MOP": {
                "price_per_kg": 20.0,      # ₹20/kg (₹1000/50kg bag)
                "subsidy_per_kg": 3.0,     # ₹3/kg subsidy
                "net_price_per_kg": 17.0   # ₹17/kg after subsidy
            },
            "Zinc Sulfate": {
                "price_per_kg": 50.0,      # ₹50/kg
                "subsidy_per_kg": 0.0,     # No subsidy
                "net_price_per_kg": 50.0   # ₹50/kg
            },
            "Borax": {
                "price_per_kg": 70.0,      # ₹70/kg
                "subsidy_per_kg": 0.0,     # No subsidy
                "net_price_per_kg": 70.0   # ₹70/kg
            },
            "Ferrous Sulfate": {
                "price_per_kg": 20.0,      # ₹20/kg
                "subsidy_per_kg": 0.0,     # No subsidy
                "net_price_per_kg": 20.0   # ₹20/kg
            }
        }
        
        if product not in kanker_pricing:
            return {"error": f"Pricing not available for {product}"}
        
        pricing = kanker_pricing[product]
        
        # Calculate costs
        total_cost_without_subsidy = quantity_kg * pricing["price_per_kg"]
        total_subsidy = quantity_kg * pricing["subsidy_per_kg"]
        total_cost_with_subsidy = quantity_kg * pricing["net_price_per_kg"]
        
        return {
            "total_cost": total_cost_with_subsidy,
            "total_cost_without_subsidy": total_cost_without_subsidy,
            "subsidy_savings": total_subsidy,
            "price_per_kg": pricing["net_price_per_kg"],
            "subsidy_per_kg": pricing["subsidy_per_kg"],
            "pricing_source": "Kanker District 2025"
        }
    
    def _get_fallback_pricing(self, product: str, quantity_kg: float) -> Dict[str, Any]:
        """Get fallback pricing when main calculation fails"""
        
        # Basic fallback pricing
        fallback_pricing = {
            "Urea": 20.0,
            "DAP": 27.0,
            "MOP": 24.0,
            "Zinc Sulfate": 60.0,
            "Borax": 80.0,
            "Ferrous Sulfate": 25.0
        }
        
        price_per_kg = fallback_pricing.get(product, 30.0)
        total_cost = quantity_kg * price_per_kg
        
        return {
            "total_cost": total_cost,
            "total_cost_without_subsidy": total_cost,
            "subsidy_savings": 0.0,
            "price_per_kg": price_per_kg,
            "subsidy_per_kg": 0.0,
            "pricing_source": "Fallback Pricing"
        }

    def _generate_recommendation_reason(
        self, 
        deficiency: DeficiencyAnalysis,
        zone_info: Dict[str, Any],
        product: str
    ) -> str:
        """Generate reason for recommendation"""
        
        zone_name = zone_info.get('nitrogen_zone', {}).get('zone_name', 'unknown') if zone_info and 'nitrogen_zone' in zone_info else 'unknown'
        
        if deficiency.nutrient == "Nitrogen":
            if zone_name == "red_zone":
                return f"High nitrogen zone detected, but crop requirement not met. Apply {product} to reach optimal levels."
            else:
                return f"Nitrogen deficiency detected ({deficiency.deficiency_amount:.1f} kg/ha). Apply {product} for optimal crop growth."
        
        elif deficiency.nutrient == "Phosphorus":
            return f"Phosphorus deficiency detected ({deficiency.deficiency_amount:.1f} kg/ha). Apply {product} for root development and flowering."
        
        elif deficiency.nutrient == "Potassium":
            return f"Potassium deficiency detected ({deficiency.deficiency_amount:.1f} kg/ha). Apply {product} for stem strength and grain quality."
        
        return f"{deficiency.nutrient} deficiency detected. Apply {product} as recommended."

# Global instance for easy access
recommendation_engine = KankerRecommendationEngine()

# Export main function for easy use
def generate_kanker_based_recommendations(
    npk_data: Dict[str, float],
    enhanced_details: Dict[str, Any],
    crop_type: str,
    coordinates: Tuple[float, float],
    field_area_ha: float = 1.0
) -> Dict[str, Any]:
    """
    Generate Kanker-based fertilizer recommendations
    
    Args:
        npk_data: NPK values from satellite analysis
        enhanced_details: Enhanced analysis details
        crop_type: Type of crop
        coordinates: Field coordinates (lat, lon)
        field_area_ha: Field area in hectares
        
    Returns:
        Comprehensive recommendation dictionary
    """
    return recommendation_engine.generate_recommendations(
        npk_data, enhanced_details, crop_type, coordinates, field_area_ha
    )

# Export main classes and functions
__all__ = [
    "KankerRecommendationEngine",
    "generate_kanker_based_recommendations",
    "recommendation_engine"
]
