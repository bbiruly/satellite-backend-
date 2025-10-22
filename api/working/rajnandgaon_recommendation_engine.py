import math
from typing import Dict, Any, List, Tuple, Optional
from collections import namedtuple

from .fertilizer_database import calculate_fertilizer_cost
from .crop_requirements_kanker import get_crop_requirement, get_nutrient_status_level, get_ph_status_level
from .rajnandgaon_data_loader import rajnandgaon_data_loader

# Define a simple get_fertilizer_info function locally
def get_fertilizer_info(fertilizer_name: str):
    """Simple fertilizer info function"""
    fertilizer_info = {
        "Urea": {"content_percentage": 46, "subsidy_price_per_kg": 6.0, "market_price_per_kg": 10.0, "application_method": "Broadcast"},
        "DAP": {"content_percentage": 46, "subsidy_price_per_kg": 30.0, "market_price_per_kg": 50.0, "application_method": "Basal application"},
        "MOP": {"content_percentage": 60, "subsidy_price_per_kg": 20.0, "market_price_per_kg": 35.0, "application_method": "Basal application"},
        "Zinc Sulfate": {"content_percentage": 21, "subsidy_price_per_kg": 40.0, "market_price_per_kg": 70.0, "application_method": "Soil application"},
        "Borax": {"content_percentage": 11, "subsidy_price_per_kg": 60.0, "market_price_per_kg": 100.0, "application_method": "Soil application"},
        "Ferrous Sulphate": {"content_percentage": 19, "subsidy_price_per_kg": 35.0, "market_price_per_kg": 60.0, "application_method": "Soil application"},
        "Ferrous Sulfate": {"content_percentage": 19, "subsidy_price_per_kg": 35.0, "market_price_per_kg": 60.0, "application_method": "Soil application"},
        "Lime": {"content_percentage": 0, "subsidy_price_per_kg": 5.0, "market_price_per_kg": 8.0, "application_method": "Broadcast"},
        "Gypsum": {"content_percentage": 0, "subsidy_price_per_kg": 4.0, "market_price_per_kg": 7.0, "application_method": "Broadcast"}
    }
    return fertilizer_info.get(fertilizer_name)

# Define named tuples for better readability
DeficiencyAnalysis = namedtuple("DeficiencyAnalysis", ["nutrient", "current_value", "optimal_min", "optimal_max", "deficiency_amount", "severity"])
Recommendation = namedtuple("Recommendation", ["nutrient", "product", "quantity_kg", "cost_with_subsidy", "cost_without_subsidy", "timing", "reason", "priority", "confidence"])

class RajnandgaonRecommendationEngine:
    def __init__(self):
        self.data_loader = rajnandgaon_data_loader

    def _get_nutrient_status(self, npk_data: Dict[str, float], crop_type: str, village_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determines the status (low, medium, high, excess) for NPK, SOC, and micronutrients.
        Prioritizes village data for micronutrients and pH.
        """
        nutrient_status = {}
        crop_req = get_crop_requirement(crop_type)

        if not crop_req:
            return {"error": f"Crop type '{crop_type}' not found in requirements."}

        # NPK and SOC from satellite data - BULLETPROOF SOC key handling
        for nutrient in ['Nitrogen', 'Phosphorus', 'Potassium', 'Soc']:
            # BULLETPROOF: Handle both 'SOC' and 'Soc' keys from satellite data
            current_value = 0
            if nutrient == 'Soc':
                # Try 'Soc' first, then 'SOC', then default to 0
                current_value = npk_data.get('Soc', npk_data.get('SOC', 0))
            else:
                current_value = npk_data.get(nutrient, 0)
            
            # Map nutrient names to crop requirements keys
            if nutrient == 'Nitrogen':
                nutrient_key = 'N'
            elif nutrient == 'Phosphorus':
                nutrient_key = 'P'
            elif nutrient == 'Potassium':
                nutrient_key = 'K'
            elif nutrient == 'Soc':
                nutrient_key = 'Soc'
            else:
                nutrient_key = nutrient
            status = get_nutrient_status_level(current_value, nutrient_key, crop_type)
            nutrient_status[nutrient] = {"value": current_value, "unit": "kg/ha" if nutrient != "Soc" else "%", "status": status, "source": "satellite"}

        # Micronutrients and pH - prioritize Rajnandgaon village data
        for nutrient in ['Boron', 'Iron', 'Zinc']:
            if village_data:
                # Rajnandgaon data stores values directly
                nutrient_value = village_data.get(f"{nutrient.lower()}_value")
                if nutrient_value is not None:
                    try:
                        status = get_nutrient_status_level(nutrient_value, nutrient, crop_type)
                        nutrient_status[nutrient] = {"value": nutrient_value, "unit": "ppm", "status": status, "source": "rajnandgaon_village"}
                    except KeyError as e:
                        # Fallback for missing status_ranges
                        nutrient_status[nutrient] = {"value": nutrient_value, "unit": "ppm", "status": "sufficient", "source": "rajnandgaon_village"}
                else:
                    nutrient_status[nutrient] = {"value": None, "unit": "ppm", "status": "not_available", "source": "rajnandgaon_village"}
            else:
                nutrient_status[nutrient] = {"value": None, "unit": "ppm", "status": "no_village_data", "source": "fallback_generic"}

        # Soil pH
        if village_data:
            ph_value = village_data.get("soil_ph_value")
            if ph_value is not None:
                status = get_ph_status_level(ph_value, crop_type)
                nutrient_status['Soil_pH'] = {"value": ph_value, "unit": "pH", "status": status, "source": "rajnandgaon_village"}
            else:
                nutrient_status['Soil_pH'] = {"value": None, "unit": "pH", "status": "not_available", "source": "rajnandgaon_village"}
        else:
            nutrient_status['Soil_pH'] = {"value": None, "unit": "pH", "status": "no_village_data", "source": "fallback_generic"}
        
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
        
        for nutrient in ['Nitrogen', 'Phosphorus', 'Potassium', 'Soc']:
            # BULLETPROOF: Handle both 'SOC' and 'Soc' keys from satellite data
            current_value = 0
            if nutrient == 'Soc':
                # Try 'Soc' first, then 'SOC', then default to 0
                current_value = npk_data.get('Soc', npk_data.get('SOC', 0))
            else:
                current_value = npk_data.get(nutrient, 0)
            
            # Map nutrient names to crop requirements keys
            if nutrient == 'Nitrogen':
                nutrient_key = 'N'
            elif nutrient == 'Phosphorus':
                nutrient_key = 'P'
            elif nutrient == 'Potassium':
                nutrient_key = 'K'
            elif nutrient == 'Soc':
                nutrient_key = 'Soc'
            else:
                continue
                
            optimal_min = crop_req.optimal_npk[nutrient_key]['min']
            optimal_max = crop_req.optimal_npk[nutrient_key]['max']
            
            # FIXED: Use ICAR ranges for deficiency analysis instead of optimal ranges
            if nutrient_key == 'P':  # Phosphorus - use ICAR ranges
                icar_min = 10  # ICAR minimum
                icar_max = 25  # ICAR maximum
                
                if current_value < icar_min:
                    deficiency_amount = icar_min - current_value
                    severity = "high" if deficiency_amount > (icar_max - icar_min) * 1.5 else "medium"
                    deficiencies.append(DeficiencyAnalysis(nutrient, current_value, icar_min, icar_max, round(deficiency_amount, 2), severity))
                elif current_value > icar_max:
                    # Consider excess as a "deficiency" in terms of needing action (e.g., no application)
                    deficiency_amount = current_value - icar_max
                    deficiencies.append(DeficiencyAnalysis(nutrient, current_value, icar_min, icar_max, round(deficiency_amount, 2), "excess"))
                # If within ICAR range (10-25), no deficiency
            else:  # Other nutrients - use optimal ranges
                if current_value < optimal_min:
                    deficiency_amount = optimal_min - current_value
                    severity = "high" if deficiency_amount > (optimal_max - optimal_min) * 1.5 else "medium"
                    deficiencies.append(DeficiencyAnalysis(nutrient, current_value, optimal_min, optimal_max, round(deficiency_amount, 2), severity))
                elif current_value > optimal_max:
                    # Consider excess as a "deficiency" in terms of needing action (e.g., no application)
                    deficiency_amount = current_value - optimal_max
                    deficiencies.append(DeficiencyAnalysis(nutrient, current_value, optimal_min, optimal_max, round(deficiency_amount, 2), "excess"))

        # Micronutrient deficiencies (based on status from _get_nutrient_status)
        for nutrient in ['Boron', 'Iron', 'Zinc']:
            status_info = nutrient_status.get(nutrient)
            if status_info and status_info['status'] in ["deficient", "low"]:
                deficiencies.append(DeficiencyAnalysis(nutrient, status_info['value'] or 0, 
                                                      crop_req.optimal_micronutrients[nutrient]['min'], 
                                                      crop_req.optimal_micronutrients[nutrient]['max'], 
                                                      1.0, # Placeholder for amount
                                                      status_info['status']))
        
        # Soil pH correction
        ph_info = nutrient_status.get('Soil_pH')
        if ph_info and ph_info['value'] is not None:
            ph_value = ph_info['value']
            optimal_ph_min, optimal_ph_max = crop_req.optimal_ph_range
            
            if ph_value < optimal_ph_min:
                deficiencies.append(DeficiencyAnalysis("Soil_pH", ph_value, optimal_ph_min, optimal_ph_max, round(optimal_ph_min - ph_value, 2), "acidic"))
            elif ph_value > optimal_ph_max:
                deficiencies.append(DeficiencyAnalysis("Soil_pH", ph_value, optimal_ph_min, optimal_ph_max, round(ph_value - optimal_ph_max, 2), "alkaline"))

        return deficiencies

    def _get_recommended_fertilizer_product(self, deficiency: DeficiencyAnalysis) -> Optional[str]:
        """Selects the primary fertilizer product for a given nutrient deficiency."""
        if deficiency.nutrient == "Nitrogen":
            return "Urea"
        elif deficiency.nutrient == "Phosphorus":
            return "DAP" # Primary P source
        elif deficiency.nutrient == "Potassium":
            return "MOP" # Primary K source
        elif deficiency.nutrient == "Zinc":
            return "Zinc Sulfate"
        elif deficiency.nutrient == "Boron":
            return "Borax"
        elif deficiency.nutrient == "Iron":
            return "Ferrous Sulphate"
        elif deficiency.nutrient == "Soil_pH":
            if deficiency.severity == "acidic":
                return "Lime"
            elif deficiency.severity == "alkaline":
                return "Gypsum" # For alkaline soils
        return None

    def _get_application_timing(self, product: str, crop_type: str) -> str:
        """Determines the optimal application timing based on crop growth stages."""
        crop_req = get_crop_requirement(crop_type)
        if not crop_req:
            return "General application"

        # Simplified timing logic for demonstration
        if product == "Urea":
            return crop_req.growth_stages.get("tillering", {}).get("timing", "Split application")
        elif product in ["DAP", "SSP", "MOP", "Lime", "Gypsum"]:
            return crop_req.growth_stages.get("basal", {}).get("timing", "Basal application")
        elif product in ["Zinc Sulfate", "Borax", "Ferrous Sulphate"]:
            return "Basal or Foliar as needed"
        return "General application"

    def _generate_recommendation_reason(self, deficiency: DeficiencyAnalysis, village_data: Optional[Dict[str, Any]], product: str) -> str:
        """Generates a detailed reason for the recommendation."""
        reason_parts = []
        
        if deficiency.nutrient == "Nitrogen" and deficiency.severity == "excess":
            reason_parts.append(f"आपके खेत में नाइट्रोजन की मात्रा अधिक है ({deficiency.current_value} kg/ha).")
            if village_data:
                reason_parts.append(f"यह {village_data.get('village_name', 'इस क्षेत्र')} के लिए सामान्य है जहाँ नाइट्रोजन का स्तर {village_data.get('nitrogen_level', 'अधिक')} रहता है।")
            reason_parts.append(f"फसल की आवश्यकता ({deficiency.optimal_min}-{deficiency.optimal_max} kg/ha) से अधिक होने के कारण {product} का प्रयोग न करें।")
            reason_parts.append("अधिक नाइट्रोजन से फसल गिर सकती है और उपज प्रभावित हो सकती है।")
        elif deficiency.nutrient == "Soil_pH":
            if deficiency.severity == "acidic":
                reason_parts.append(f"आपके खेत की मिट्टी अम्लीय है (pH {deficiency.current_value}).")
                reason_parts.append(f"फसल के लिए आदर्श pH ({deficiency.optimal_min}-{deficiency.optimal_max}) प्राप्त करने के लिए {product} का प्रयोग करें।")
                reason_parts.append("सही pH से पोषक तत्वों की उपलब्धता बढ़ती है।")
            elif deficiency.severity == "alkaline":
                reason_parts.append(f"आपके खेत की मिट्टी क्षारीय है (pH {deficiency.current_value}).")
                reason_parts.append(f"फसल के लिए आदर्श pH ({deficiency.optimal_min}-{deficiency.optimal_max}) प्राप्त करने के लिए {product} का प्रयोग करें।")
                reason_parts.append("सही pH से पोषक तत्वों की उपलब्धता बढ़ती है।")
        else:
            reason_parts.append(f"आपके खेत में {deficiency.nutrient} की कमी है ({deficiency.current_value} {'kg/ha' if deficiency.nutrient not in ['Boron', 'Iron', 'Zinc'] else 'ppm'}).")
            if village_data:
                reason_parts.append(f"यह {village_data.get('village_name', 'इस क्षेत्र')} में {deficiency.nutrient} के {deficiency.severity} स्तर के कारण है।")
            reason_parts.append(f"फसल की इष्टतम वृद्धि के लिए {deficiency.optimal_min}-{deficiency.optimal_max} {'kg/ha' if deficiency.nutrient not in ['Boron', 'Iron', 'Zinc'] else 'ppm'} {deficiency.nutrient} की आवश्यकता है।")
            reason_parts.append(f"{product} का प्रयोग {deficiency.nutrient} की कमी को पूरा करेगा और उपज बढ़ाएगा।")
        
        return " ".join(reason_parts)

    def generate_recommendations(
        self,
        npk_data: Dict[str, float],
        enhanced_details: Dict[str, Any],
        crop_type: str,
        coordinates: Tuple[float, float],
        field_area_ha: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generates comprehensive fertilizer recommendations based on NPK data,
        Rajnandgaon village data, crop requirements, and fertilizer database.
        """
        lat, lon = coordinates
        
        # NUCLEAR OPTION: Replace all SOC/Soc references with bulletproof handling
        print(f"🔍 Debug: Input npk_data keys: {list(npk_data.keys())}")
        print(f"🔍 Debug: Input npk_data values: {npk_data}")
        
        # Create a completely safe copy with guaranteed keys
        safe_npk_data = {
            'Nitrogen': npk_data.get('Nitrogen', 0),
            'Phosphorus': npk_data.get('Phosphorus', 0),
            'Potassium': npk_data.get('Potassium', 0),
            'Soc': npk_data.get('Soc', npk_data.get('SOC', 0)),  # BULLETPROOF SOC handling
            'Boron': npk_data.get('Boron', 0),
            'Iron': npk_data.get('Iron', 0),
            'Zinc': npk_data.get('Zinc', 0),
            'Soil_pH': npk_data.get('Soil_pH', 0)
        }
        
        print(f"🔍 Debug: Safe npk_data keys: {list(safe_npk_data.keys())}")
        print(f"🔍 Debug: Safe npk_data values: {safe_npk_data}")
        
        # Use safe_npk_data for all operations
        npk_data = safe_npk_data
        
        # 1. Get nearest village data
        nearest_village = self.data_loader.find_nearest_village(lat, lon)
        print(f"🔍 Debug: nearest_village = {nearest_village}")
        
        # Handle case when no village data is available
        if not nearest_village:
            return {
                "error": "No village data available for Rajnandgaon district",
                "dataSource": "Rajnandgaon Soil Analysis 2025",
                "fallback": True,
                "coordinates": coordinates,
                "crop_type": crop_type
            }
        
        village_name = nearest_village['village_name']
        distance_to_village = nearest_village['distance_km']

        # 2. Get nutrient status (combining satellite and village data)
        nutrient_status = self._get_nutrient_status(npk_data, crop_type, nearest_village)
        if "error" in nutrient_status:
            return {"error": nutrient_status["error"], "dataSource": "Rajnandgaon Soil Analysis 2025", "fallback": True}

        # 3. Analyze deficiencies
        deficiencies = self._analyze_deficiencies(npk_data, crop_type, nutrient_status)
        
        recommendations = []
        total_subsidy_savings = 0.0
        total_cost_with_subsidy = 0.0
        total_cost_without_subsidy = 0.0

        for deficiency in deficiencies:
            product = self._get_recommended_fertilizer_product(deficiency)
            if not product:
                continue
            
            # Get nutrient content from fertilizer database
            product_info = get_fertilizer_info(product)
            if not product_info:
                print(f"❌ Error: Fertilizer product '{product}' not found in database.")
                continue
            
            nutrient_content = product_info['content_percentage']
            
            # Skip if nutrient content is 0 (e.g., for pH correctors, handled differently)
            if nutrient_content == 0 and deficiency.nutrient != "Soil_pH":
                continue
            
            # Calculate quantity needed
            quantity_kg = (deficiency.deficiency_amount * 100) / nutrient_content if nutrient_content > 0 else 0
            quantity_kg = round(quantity_kg, 2)
            
            # For pH correction, quantity is in tons/ha, not kg/ha based on nutrient content
            if deficiency.nutrient == "Soil_pH":
                # Example: 1 unit of pH deficiency might need 1 ton of lime
                # This needs to be refined based on actual soil science for pH correction
                if deficiency.severity == "acidic":
                    quantity_kg = round(deficiency.deficiency_amount * 1000, 2) # Placeholder: 1 unit pH needs 1000 kg (1 ton)
                    product_unit = "kg/ha"
                elif deficiency.severity == "alkaline":
                    quantity_kg = round(deficiency.deficiency_amount * 500, 2) # Placeholder
                    product_unit = "kg/ha"
                else:
                    quantity_kg = 0
                    product_unit = "kg/ha"
                
                if quantity_kg == 0:
                    continue
                
                # Convert to tons if quantity is large
                if quantity_kg >= 1000:
                    quantity_kg = round(quantity_kg / 1000, 2)
                    product_unit = "tons/ha"
            else:
                product_unit = "kg/ha"

            # Calculate cost
            cost_info = calculate_fertilizer_cost(product, quantity_kg)
            
            # Check if cost calculation was successful
            if 'error' in cost_info:
                print(f"❌ Cost calculation error for {product}: {cost_info['error']}")
                continue
            
            # Convert to acres for Indian farmers
            quantity_per_acre = round(quantity_kg / 2.47, 2)  # 1 hectare = 2.47 acres
            cost_per_acre = round(cost_info.get('total_cost', 0) / 2.47, 2)
            
            # Determine priority
            priority = "HIGH" if deficiency.severity == "high" or deficiency.nutrient in ['Boron', 'Zinc', 'Iron'] else "MEDIUM"
            if deficiency.nutrient == "Nitrogen" and deficiency.severity == "excess":
                priority = "LOW" # No application needed

            # Determine timing
            timing = self._get_application_timing(product, crop_type)
            
            # Generate reason
            reason = self._generate_recommendation_reason(
                deficiency, nearest_village, product
            )
            
            recommendations.append({
                "nutrient": deficiency.nutrient,
                "product": product,
                "quantity_kg": quantity_kg,
                "unit": product_unit,
                "quantity_per_hectare": f"{quantity_kg} {product_unit}",
                "quantity_per_acre": f"{quantity_per_acre} {product_unit}",
                "total_quantity_field": f"{round(quantity_kg * field_area_ha, 2)} {product_unit}",
                "cost_with_subsidy": cost_info.get('total_cost', 0),
                "cost_per_hectare": cost_info.get('total_cost', 0),
                "cost_per_acre": cost_per_acre,
                "cost_without_subsidy": cost_info.get('total_cost', 0) + cost_info.get('subsidy_savings', 0),
                "subsidy_savings": cost_info.get('subsidy_savings', 0),
                "timing": timing,
                "method": product_info.get('application_method', 'Broadcast'),
                "reason": reason,
                "priority": priority,
                "confidence": 0.9, # Base confidence
                "deficiency_amount": deficiency.deficiency_amount,
                "nutrient_content": f"{nutrient_content}%" if nutrient_content > 0 else "N/A"
            })
            
            total_subsidy_savings += cost_info.get('subsidy_savings', 0)
            total_cost_with_subsidy += cost_info.get('total_cost', 0)
            total_cost_without_subsidy += (cost_info.get('total_cost', 0) + cost_info.get('subsidy_savings', 0))

        # Overall confidence score (can be dynamic based on data quality, conflicts, etc.)
        overall_confidence = "85-90%" # Rajnandgaon specific confidence

        summary_message = f"आपके खेत के लिए {len(recommendations)} उर्वरक सिफारिशें उपलब्ध हैं। कुल अनुमानित लागत (सब्सिडी के साथ): ₹{round(total_cost_with_subsidy, 2)} प्रति हेक्टेयर।"
        if total_subsidy_savings > 0:
            summary_message += f" आपको लगभग ₹{round(total_subsidy_savings, 2)} की सब्सिडी बचत होगी।"

        return {
            "summary": summary_message,
            "confidence": overall_confidence,
            "dataSource": "Rajnandgaon Soil Analysis 2025 (khairagarh tehsil)",
            "nearest_village": village_name,
            "distance_to_village_km": distance_to_village,
            "nutrient_status": nutrient_status,
            "recommendations_list": recommendations,
            "total_cost_with_subsidy_per_ha": round(total_cost_with_subsidy, 2),
            "total_cost_without_subsidy_per_ha": round(total_cost_without_subsidy, 2),
            "total_subsidy_savings_per_ha": round(total_subsidy_savings, 2),
            "total_cost_with_subsidy_per_acre": round(total_cost_with_subsidy / 2.47, 2),
            "total_cost_without_subsidy_per_acre": round(total_cost_without_subsidy / 2.47, 2),
            "total_subsidy_savings_per_acre": round(total_subsidy_savings / 2.47, 2),
            "total_cost_with_subsidy_for_field": round(total_cost_with_subsidy * field_area_ha, 2),
            "total_cost_without_subsidy_for_field": round(total_cost_without_subsidy * field_area_ha, 2),
            "total_subsidy_savings_for_field": round(total_subsidy_savings * field_area_ha, 2),
            "farmers_note": {
                "language": "hindi",
                "message": summary_message + " ये सिफारिशें आपके खेत की मिट्टी और फसल की ज़रूरतों पर आधारित हैं। अधिक जानकारी के लिए स्थानीय कृषि अधिकारी से संपर्क करें।"
            }
        }

# Initialize the recommendation engine
rajnandgaon_recommendation_engine = RajnandgaonRecommendationEngine()

def generate_rajnandgaon_based_recommendations(
    npk_data: Dict[str, float],
    enhanced_details: Dict[str, Any],
    crop_type: str,
    coordinates: Tuple[float, float],
    field_area_ha: float = 1.0
) -> Dict[str, Any]:
    """
    Public function to generate Rajnandgaon-based recommendations.
    """
    return rajnandgaon_recommendation_engine.generate_recommendations(
        npk_data, enhanced_details, crop_type, coordinates, field_area_ha
    )
