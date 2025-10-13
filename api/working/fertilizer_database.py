"""
Fertilizer Database Module
Contains comprehensive database of Indian fertilizers with NPK content, pricing, and application guidelines
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class FertilizerProduct:
    """Fertilizer product data structure"""
    name: str
    n_content: float = 0.0
    p_content: float = 0.0
    k_content: float = 0.0
    s_content: float = 0.0
    zn_content: float = 0.0
    b_content: float = 0.0
    fe_content: float = 0.0
    cost_per_kg: float = 0.0
    subsidy_available: bool = False
    subsidy_price: float = 0.0
    application_method: str = "Broadcast"
    solubility: str = "Water Soluble"
    ph_effect: str = "Neutral"

# Chemical Fertilizers Database
CHEMICAL_FERTILIZERS = {
    "nitrogen": [
        FertilizerProduct(
            name="Urea",
            n_content=46.0,
            cost_per_kg=10.0,
            subsidy_available=True,
            subsidy_price=6.0,
            application_method="Split application",
            solubility="Highly Soluble",
            ph_effect="Slightly Acidic"
        ),
        FertilizerProduct(
            name="Ammonium Sulfate",
            n_content=21.0,
            s_content=24.0,
            cost_per_kg=8.0,
            subsidy_available=False,
            application_method="Basal application",
            solubility="Highly Soluble",
            ph_effect="Acidic"
        ),
        FertilizerProduct(
            name="CAN (Calcium Ammonium Nitrate)",
            n_content=25.0,
            cost_per_kg=12.0,
            subsidy_available=False,
            application_method="Top dressing",
            solubility="Highly Soluble",
            ph_effect="Neutral"
        ),
        FertilizerProduct(
            name="Ammonium Nitrate",
            n_content=33.0,
            cost_per_kg=15.0,
            subsidy_available=False,
            application_method="Split application",
            solubility="Highly Soluble",
            ph_effect="Slightly Acidic"
        )
    ],
    
    "phosphorus": [
        FertilizerProduct(
            name="DAP (Diammonium Phosphate)",
            n_content=18.0,
            p_content=46.0,
            cost_per_kg=50.0,
            subsidy_available=True,
            subsidy_price=30.0,
            application_method="Basal application",
            solubility="Water Soluble",
            ph_effect="Slightly Acidic"
        ),
        FertilizerProduct(
            name="SSP (Single Super Phosphate)",
            p_content=16.0,
            s_content=11.0,
            cost_per_kg=8.0,
            subsidy_available=False,
            application_method="Basal application",
            solubility="Water Soluble",
            ph_effect="Acidic"
        ),
        FertilizerProduct(
            name="TSP (Triple Super Phosphate)",
            p_content=46.0,
            cost_per_kg=25.0,
            subsidy_available=False,
            application_method="Basal application",
            solubility="Water Soluble",
            ph_effect="Acidic"
        ),
        FertilizerProduct(
            name="Rock Phosphate",
            p_content=20.0,
            cost_per_kg=6.0,
            subsidy_available=False,
            application_method="Basal application",
            solubility="Slow Release",
            ph_effect="Neutral"
        )
    ],
    
    "potassium": [
        FertilizerProduct(
            name="MOP (Muriate of Potash)",
            k_content=60.0,
            cost_per_kg=35.0,
            subsidy_available=True,
            subsidy_price=20.0,
            application_method="Basal + Top dressing",
            solubility="Highly Soluble",
            ph_effect="Neutral"
        ),
        FertilizerProduct(
            name="SOP (Sulfate of Potash)",
            k_content=50.0,
            s_content=18.0,
            cost_per_kg=50.0,
            subsidy_available=False,
            application_method="Basal + Top dressing",
            solubility="Highly Soluble",
            ph_effect="Neutral"
        ),
        FertilizerProduct(
            name="Potassium Nitrate",
            n_content=13.0,
            k_content=44.0,
            cost_per_kg=80.0,
            subsidy_available=False,
            application_method="Foliar spray",
            solubility="Highly Soluble",
            ph_effect="Neutral"
        )
    ],
    
    "npk_complexes": [
        FertilizerProduct(
            name="NPK 19:19:19",
            n_content=19.0,
            p_content=19.0,
            k_content=19.0,
            cost_per_kg=45.0,
            subsidy_available=True,
            subsidy_price=35.0,
            application_method="Basal + Top dressing",
            solubility="Water Soluble",
            ph_effect="Neutral"
        ),
        FertilizerProduct(
            name="NPK 20:20:20",
            n_content=20.0,
            p_content=20.0,
            k_content=20.0,
            cost_per_kg=50.0,
            subsidy_available=True,
            subsidy_price=40.0,
            application_method="Basal + Top dressing",
            solubility="Water Soluble",
            ph_effect="Neutral"
        ),
        FertilizerProduct(
            name="NPK 12:32:16",
            n_content=12.0,
            p_content=32.0,
            k_content=16.0,
            cost_per_kg=40.0,
            subsidy_available=True,
            subsidy_price=30.0,
            application_method="Basal application",
            solubility="Water Soluble",
            ph_effect="Slightly Acidic"
        ),
        FertilizerProduct(
            name="NPK 14:35:14",
            n_content=14.0,
            p_content=35.0,
            k_content=14.0,
            cost_per_kg=42.0,
            subsidy_available=True,
            subsidy_price=32.0,
            application_method="Basal application",
            solubility="Water Soluble",
            ph_effect="Slightly Acidic"
        )
    ],
    
    "micronutrients": [
        FertilizerProduct(
            name="Zinc Sulfate",
            zn_content=21.0,
            cost_per_kg=60.0,
            subsidy_available=False,
            application_method="Basal application",
            solubility="Water Soluble",
            ph_effect="Slightly Acidic"
        ),
        FertilizerProduct(
            name="Borax",
            b_content=11.0,
            cost_per_kg=80.0,
            subsidy_available=False,
            application_method="Basal application",
            solubility="Water Soluble",
            ph_effect="Slightly Alkaline"
        ),
        FertilizerProduct(
            name="Ferrous Sulfate",
            fe_content=19.0,
            cost_per_kg=25.0,
            subsidy_available=False,
            application_method="Foliar spray",
            solubility="Water Soluble",
            ph_effect="Acidic"
        ),
        FertilizerProduct(
            name="Manganese Sulfate",
            cost_per_kg=35.0,
            subsidy_available=False,
            application_method="Foliar spray",
            solubility="Water Soluble",
            ph_effect="Slightly Acidic"
        ),
        FertilizerProduct(
            name="Copper Sulfate",
            cost_per_kg=40.0,
            subsidy_available=False,
            application_method="Foliar spray",
            solubility="Water Soluble",
            ph_effect="Slightly Acidic"
        )
    ]
}

# Organic Fertilizers Database
ORGANIC_FERTILIZERS = {
    "farmyard_manure": FertilizerProduct(
        name="Farmyard Manure (FYM)",
        n_content=0.5,
        p_content=0.2,
        k_content=0.5,
        cost_per_kg=1.5,
        subsidy_available=False,
        application_method="Basal application",
        solubility="Slow Release",
        ph_effect="Neutral"
    ),
    "vermicompost": FertilizerProduct(
        name="Vermicompost",
        n_content=1.5,
        p_content=1.0,
        k_content=1.5,
        cost_per_kg=8.0,
        subsidy_available=False,
        application_method="Basal application",
        solubility="Slow Release",
        ph_effect="Neutral"
    ),
    "neem_cake": FertilizerProduct(
        name="Neem Cake",
        n_content=5.0,
        p_content=1.0,
        k_content=1.4,
        cost_per_kg=25.0,
        subsidy_available=False,
        application_method="Basal application",
        solubility="Slow Release",
        ph_effect="Neutral"
    ),
    "castor_cake": FertilizerProduct(
        name="Castor Cake",
        n_content=4.3,
        p_content=1.8,
        k_content=1.3,
        cost_per_kg=20.0,
        subsidy_available=False,
        application_method="Basal application",
        solubility="Slow Release",
        ph_effect="Neutral"
    ),
    "green_manure": FertilizerProduct(
        name="Green Manure",
        n_content=2.0,
        p_content=0.5,
        k_content=1.5,
        cost_per_kg=0.0,  # Self-produced
        subsidy_available=False,
        application_method="Basal application",
        solubility="Slow Release",
        ph_effect="Neutral"
    )
}

# Application Guidelines
APPLICATION_GUIDELINES = {
    "rice": {
        "basal_application": {
            "timing": "At transplanting",
            "fertilizers": ["DAP", "MOP", "Zinc Sulfate"],
            "method": "Mix with soil before transplanting"
        },
        "first_top_dress": {
            "timing": "20-25 days after transplanting (Tillering stage)",
            "fertilizers": ["Urea"],
            "method": "Broadcast in standing water"
        },
        "second_top_dress": {
            "timing": "40-45 days (Panicle initiation)",
            "fertilizers": ["Urea", "MOP"],
            "method": "Broadcast in standing water"
        }
    },
    "wheat": {
        "basal_application": {
            "timing": "At sowing",
            "fertilizers": ["DAP", "MOP", "Zinc Sulfate"],
            "method": "Mix with soil at sowing"
        },
        "first_top_dress": {
            "timing": "25-30 days after sowing (Crown root initiation)",
            "fertilizers": ["Urea"],
            "method": "Broadcast and irrigate"
        },
        "second_top_dress": {
            "timing": "45-50 days (Flowering stage)",
            "fertilizers": ["Urea"],
            "method": "Broadcast and irrigate"
        }
    },
    "maize": {
        "basal_application": {
            "timing": "At sowing",
            "fertilizers": ["DAP", "MOP", "Zinc Sulfate"],
            "method": "Place fertilizer 5-7 cm below seed"
        },
        "first_top_dress": {
            "timing": "25-30 days (Knee high stage)",
            "fertilizers": ["Urea"],
            "method": "Side dressing and earthing up"
        },
        "second_top_dress": {
            "timing": "45-50 days (Tasseling stage)",
            "fertilizers": ["Urea"],
            "method": "Side dressing"
        }
    }
}

# Deficiency Symptoms Database
DEFICIENCY_SYMPTOMS = {
    "nitrogen": {
        "symptoms": [
            "Yellowing of older leaves starting from tips",
            "Stunted growth and reduced tillering",
            "Early maturity with reduced yield",
            "Thin and weak stems"
        ],
        "affected_parts": "Older leaves first",
        "severity": "High impact on yield"
    },
    "phosphorus": {
        "symptoms": [
            "Dark green or purple coloration of leaves",
            "Poor root development",
            "Delayed maturity",
            "Reduced tillering and flowering"
        ],
        "affected_parts": "All plant parts",
        "severity": "Critical for root development"
    },
    "potassium": {
        "symptoms": [
            "Brown scorching of leaf tips and margins",
            "Weak stems leading to lodging",
            "Poor grain filling",
            "Increased disease susceptibility"
        ],
        "affected_parts": "Older leaves first",
        "severity": "High impact on quality"
    },
    "zinc": {
        "symptoms": [
            "Interveinal chlorosis in young leaves",
            "Stunted growth",
            "Reduced tillering",
            "Bronzing of leaves"
        ],
        "affected_parts": "Young leaves",
        "severity": "Common in alkaline soils"
    },
    "boron": {
        "symptoms": [
            "Cracking of stems",
            "Poor flowering and fruit set",
            "Brittle leaves",
            "Root tip necrosis"
        ],
        "affected_parts": "Growing points",
        "severity": "Critical for flowering"
    },
    "iron": {
        "symptoms": [
            "Interveinal chlorosis in young leaves",
            "Yellow leaves with green veins",
            "Stunted growth",
            "Poor chlorophyll formation"
        ],
        "affected_parts": "Young leaves",
        "severity": "Common in calcareous soils"
    }
}

# Cost Analysis Functions
def get_fertilizer_info(fertilizer_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a fertilizer product"""
    
    fertilizer_name_lower = fertilizer_name.lower()
    
    for category in CHEMICAL_FERTILIZERS.values():
        for fert in category:
            # Check if fertilizer name contains the search term or vice versa
            if (fertilizer_name_lower in fert.name.lower() or 
                fert.name.lower() in fertilizer_name_lower or
                fertilizer_name_lower == fert.name.lower()):
                return {
                    "name": fert.name,
                    "content_percentage": fert.n_content if hasattr(fert, 'n_content') else (fert.p_content if hasattr(fert, 'p_content') else fert.k_content),
                    "subsidy_price_per_kg": fert.cost_per_kg * 0.6,
                    "market_price_per_kg": fert.cost_per_kg,
                    "application_method": "Broadcast",
                    "deficiency_symptoms": "Nutrient deficiency",
                    "impact": "Improves crop growth"
                }
    
    return None

def calculate_fertilizer_cost(fertilizer_name: str, quantity_kg: float, use_subsidy: bool = True) -> Dict[str, float]:
    """Calculate cost for specific fertilizer"""
    
    # Find fertilizer in database
    fertilizer = None
    fertilizer_name_lower = fertilizer_name.lower()
    
    for category in CHEMICAL_FERTILIZERS.values():
        for fert in category:
            # Check if fertilizer name contains the search term or vice versa
            if (fertilizer_name_lower in fert.name.lower() or 
                fert.name.lower() in fertilizer_name_lower or
                fertilizer_name_lower == fert.name.lower()):
                fertilizer = fert
                break
        if fertilizer:
            break
    
    if not fertilizer:
        return {"error": "Fertilizer not found"}
    
    if use_subsidy and fertilizer.subsidy_available:
        cost_per_kg = fertilizer.subsidy_price
        subsidy_savings = (fertilizer.cost_per_kg - fertilizer.subsidy_price) * quantity_kg
    else:
        cost_per_kg = fertilizer.cost_per_kg
        subsidy_savings = 0.0
    
    total_cost = cost_per_kg * quantity_kg
    
    return {
        "fertilizer_name": fertilizer.name,
        "quantity_kg": quantity_kg,
        "cost_per_kg": cost_per_kg,
        "total_cost": total_cost,
        "subsidy_savings": subsidy_savings,
        "subsidy_available": fertilizer.subsidy_available
    }

def get_fertilizer_by_nutrient(nutrient_type: str, nutrient_content: float) -> List[FertilizerProduct]:
    """Get fertilizers containing specific nutrient"""
    
    fertilizers = []
    
    for category_name, category_ferts in CHEMICAL_FERTILIZERS.items():
        for fert in category_ferts:
            if nutrient_type.lower() == "nitrogen" and fert.n_content >= nutrient_content:
                fertilizers.append(fert)
            elif nutrient_type.lower() == "phosphorus" and fert.p_content >= nutrient_content:
                fertilizers.append(fert)
            elif nutrient_type.lower() == "potassium" and fert.k_content >= nutrient_content:
                fertilizers.append(fert)
    
    return fertilizers

def get_optimal_fertilizer(deficiency: Dict[str, float]) -> Dict[str, Any]:
    """Get optimal fertilizer combination for given deficiencies"""
    
    recommendations = []
    
    # Nitrogen deficiency
    if deficiency.get("nitrogen", 0) > 0:
        urea_needed = (deficiency["nitrogen"] * 100) / 46  # Urea has 46% N
        recommendations.append({
            "nutrient": "Nitrogen",
            "fertilizer": "Urea",
            "quantity_kg": round(urea_needed, 2),
            "cost": calculate_fertilizer_cost("Urea", urea_needed)
        })
    
    # Phosphorus deficiency
    if deficiency.get("phosphorus", 0) > 0:
        dap_needed = (deficiency["phosphorus"] * 100) / 46  # DAP has 46% P
        recommendations.append({
            "nutrient": "Phosphorus",
            "fertilizer": "DAP",
            "quantity_kg": round(dap_needed, 2),
            "cost": calculate_fertilizer_cost("DAP", dap_needed)
        })
    
    # Potassium deficiency
    if deficiency.get("potassium", 0) > 0:
        mop_needed = (deficiency["potassium"] * 100) / 60  # MOP has 60% K
        recommendations.append({
            "nutrient": "Potassium",
            "fertilizer": "MOP",
            "quantity_kg": round(mop_needed, 2),
            "cost": calculate_fertilizer_cost("MOP", mop_needed)
        })
    
    return {
        "recommendations": recommendations,
        "total_cost": sum(rec["cost"].get("total_cost", 0) for rec in recommendations if "cost" in rec),
        "total_subsidy_savings": sum(rec["cost"].get("subsidy_savings", 0) for rec in recommendations if "cost" in rec)
    }

# Export main dictionaries for easy access
__all__ = [
    "CHEMICAL_FERTILIZERS",
    "ORGANIC_FERTILIZERS", 
    "APPLICATION_GUIDELINES",
    "DEFICIENCY_SYMPTOMS",
    "calculate_fertilizer_cost",
    "get_fertilizer_by_nutrient",
    "get_optimal_fertilizer"
]
