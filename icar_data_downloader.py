#!/usr/bin/env python3
"""
ICAR Soil Data Downloader for Complete India
Downloads and processes ICAR Soil Health Card data for calibration
"""

import requests
import pandas as pd
import json
import sqlite3
from typing import Dict, List, Optional
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ICARDataDownloader:
    """Download ICAR Soil Health Card data for complete India"""
    
    def __init__(self):
        self.base_url = "https://soilhealth.dac.gov.in"
        self.api_base = "https://soilhealth.dac.gov.in/api"
        self.headers = {
            "User-Agent": "ZumAgro-Calibration-System/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # India states and union territories
        self.india_states = {
            "andhra_pradesh": {"code": "AP", "name": "Andhra Pradesh"},
            "arunachal_pradesh": {"code": "AR", "name": "Arunachal Pradesh"},
            "assam": {"code": "AS", "name": "Assam"},
            "bihar": {"code": "BR", "name": "Bihar"},
            "chhattisgarh": {"code": "CG", "name": "Chhattisgarh"},
            "goa": {"code": "GA", "name": "Goa"},
            "gujarat": {"code": "GJ", "name": "Gujarat"},
            "haryana": {"code": "HR", "name": "Haryana"},
            "himachal_pradesh": {"code": "HP", "name": "Himachal Pradesh"},
            "jharkhand": {"code": "JH", "name": "Jharkhand"},
            "karnataka": {"code": "KA", "name": "Karnataka"},
            "kerala": {"code": "KL", "name": "Kerala"},
            "madhya_pradesh": {"code": "MP", "name": "Madhya Pradesh"},
            "maharashtra": {"code": "MH", "name": "Maharashtra"},
            "manipur": {"code": "MN", "name": "Manipur"},
            "meghalaya": {"code": "ML", "name": "Meghalaya"},
            "mizoram": {"code": "MZ", "name": "Mizoram"},
            "nagaland": {"code": "NL", "name": "Nagaland"},
            "odisha": {"code": "OR", "name": "Odisha"},
            "punjab": {"code": "PB", "name": "Punjab"},
            "rajasthan": {"code": "RJ", "name": "Rajasthan"},
            "sikkim": {"code": "SK", "name": "Sikkim"},
            "tamil_nadu": {"code": "TN", "name": "Tamil Nadu"},
            "telangana": {"code": "TG", "name": "Telangana"},
            "tripura": {"code": "TR", "name": "Tripura"},
            "uttar_pradesh": {"code": "UP", "name": "Uttar Pradesh"},
            "uttarakhand": {"code": "UK", "name": "Uttarakhand"},
            "west_bengal": {"code": "WB", "name": "West Bengal"},
            # Union Territories
            "andaman_nicobar": {"code": "AN", "name": "Andaman and Nicobar Islands"},
            "chandigarh": {"code": "CH", "name": "Chandigarh"},
            "dadra_nagar_haveli": {"code": "DN", "name": "Dadra and Nagar Haveli"},
            "daman_diu": {"code": "DD", "name": "Daman and Diu"},
            "delhi": {"code": "DL", "name": "Delhi"},
            "jammu_kashmir": {"code": "JK", "name": "Jammu and Kashmir"},
            "ladakh": {"code": "LA", "name": "Ladakh"},
            "lakshadweep": {"code": "LD", "name": "Lakshadweep"},
            "puducherry": {"code": "PY", "name": "Puducherry"}
        }
    
    def test_api_connection(self) -> bool:
        """Test connection to ICAR API"""
        try:
            response = self.session.get(f"{self.api_base}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ ICAR API connection successful")
                return True
            else:
                logger.warning(f"⚠️ ICAR API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ ICAR API connection failed: {e}")
            return False
    
    def get_state_districts(self, state_code: str) -> List[Dict]:
        """Get all districts for a state"""
        try:
            url = f"{self.api_base}/districts/{state_code}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📊 Found {len(data)} districts in {state_code}")
                return data
            else:
                logger.warning(f"⚠️ Failed to get districts for {state_code}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting districts for {state_code}: {e}")
            return []
    
    def get_district_villages(self, district_code: str) -> List[Dict]:
        """Get all villages for a district"""
        try:
            url = f"{self.api_base}/villages/{district_code}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🏘️ Found {len(data)} villages in {district_code}")
                return data
            else:
                logger.warning(f"⚠️ Failed to get villages for {district_code}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting villages for {district_code}: {e}")
            return []
    
    def get_village_soil_data(self, village_code: str) -> List[Dict]:
        """Get soil data for a village"""
        try:
            url = f"{self.api_base}/soil-data/{village_code}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🌱 Found {len(data)} soil samples in {village_code}")
                return data
            else:
                logger.warning(f"⚠️ Failed to get soil data for {village_code}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting soil data for {village_code}: {e}")
            return []
    
    def download_state_data(self, state_code: str, max_districts: int = None) -> List[Dict]:
        """Download complete soil data for a state"""
        logger.info(f"🚀 Starting download for {state_code}")
        
        all_soil_data = []
        
        # Get districts
        districts = self.get_state_districts(state_code)
        if not districts:
            logger.warning(f"⚠️ No districts found for {state_code}")
            return []
        
        # Limit districts if specified
        if max_districts:
            districts = districts[:max_districts]
            logger.info(f"📊 Limited to {max_districts} districts for testing")
        
        for district in districts:
            district_code = district.get("code")
            district_name = district.get("name")
            
            logger.info(f"🏘️ Processing district: {district_name}")
            
            # Get villages
            villages = self.get_district_villages(district_code)
            
            for village in villages:
                village_code = village.get("code")
                village_name = village.get("name")
                
                # Get soil data
                soil_data = self.get_village_soil_data(village_code)
                
                # Add metadata
                for sample in soil_data:
                    sample["state_code"] = state_code
                    sample["district_code"] = district_code
                    sample["district_name"] = district_name
                    sample["village_code"] = village_code
                    sample["village_name"] = village_name
                
                all_soil_data.extend(soil_data)
                
                # Rate limiting
                time.sleep(0.1)
        
        logger.info(f"✅ Downloaded {len(all_soil_data)} soil samples for {state_code}")
        return all_soil_data
    
    def download_complete_india_data(self, max_states: int = None, max_districts_per_state: int = None) -> pd.DataFrame:
        """Download complete India soil dataset"""
        logger.info("🇮🇳 Starting complete India soil data download")
        
        all_data = []
        total_samples = 0
        
        states_to_process = list(self.india_states.items())
        if max_states:
            states_to_process = states_to_process[:max_states]
            logger.info(f"📊 Limited to {max_states} states for testing")
        
        for state_key, state_info in states_to_process:
            state_code = state_info["code"]
            state_name = state_info["name"]
            
            logger.info(f"🌍 Processing state: {state_name}")
            
            # Download state data
            state_data = self.download_state_data(state_code, max_districts_per_state)
            
            # Add state metadata
            for sample in state_data:
                sample["state_name"] = state_name
                sample["state_key"] = state_key
            
            all_data.extend(state_data)
            total_samples += len(state_data)
            
            logger.info(f"📈 Total samples so far: {total_samples}")
            
            # Rate limiting between states
            time.sleep(1)
        
        logger.info(f"🎉 Download complete! Total samples: {total_samples}")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        return df
    
    def save_to_database(self, data: pd.DataFrame, db_path: str = "icar_soil_data.db"):
        """Save data to SQLite database"""
        logger.info(f"💾 Saving {len(data)} samples to database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        
        # Create table
        data.to_sql("soil_data", conn, if_exists="replace", index=False)
        
        # Create indexes for faster queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON soil_data(state_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_district ON soil_data(district_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_coordinates ON soil_data(latitude, longitude)")
        
        conn.close()
        logger.info("✅ Database saved successfully")
    
    def generate_calibration_summary(self, data: pd.DataFrame) -> Dict:
        """Generate calibration summary from downloaded data"""
        logger.info("📊 Generating calibration summary")
        
        summary = {}
        
        # State-wise analysis
        for state_code in data["state_code"].unique():
            state_data = data[data["state_code"] == state_code]
            
            # Calculate NPK ranges
            npk_ranges = {
                "nitrogen": {
                    "min": state_data["nitrogen"].min(),
                    "max": state_data["nitrogen"].max(),
                    "mean": state_data["nitrogen"].mean(),
                    "median": state_data["nitrogen"].median(),
                    "std": state_data["nitrogen"].std()
                },
                "phosphorus": {
                    "min": state_data["phosphorus"].min(),
                    "max": state_data["phosphorus"].max(),
                    "mean": state_data["phosphorus"].mean(),
                    "median": state_data["phosphorus"].median(),
                    "std": state_data["phosphorus"].std()
                },
                "potassium": {
                    "min": state_data["potassium"].min(),
                    "max": state_data["potassium"].max(),
                    "mean": state_data["potassium"].mean(),
                    "median": state_data["potassium"].median(),
                    "std": state_data["potassium"].std()
                },
                "soc": {
                    "min": state_data["soc"].min(),
                    "max": state_data["soc"].max(),
                    "mean": state_data["soc"].mean(),
                    "median": state_data["soc"].median(),
                    "std": state_data["soc"].std()
                }
            }
            
            summary[state_code] = {
                "sample_count": len(state_data),
                "npk_ranges": npk_ranges,
                "calibration_multipliers": self.calculate_calibration_multipliers(npk_ranges)
            }
        
        return summary
    
    def calculate_calibration_multipliers(self, npk_ranges: Dict) -> Dict:
        """Calculate calibration multipliers based on ICAR data"""
        multipliers = {}
        
        for nutrient, data in npk_ranges.items():
            if nutrient == "soc":
                continue
                
            # Calculate multiplier based on ICAR mean and range
            icar_mean = data["mean"]
            icar_range = data["max"] - data["min"]
            
            # Calibration formula
            if nutrient == "nitrogen":
                multiplier = (icar_mean / 100) * (icar_range / 50) + 1.0
            elif nutrient == "phosphorus":
                multiplier = (icar_mean / 50) * (icar_range / 25) + 1.0
            elif nutrient == "potassium":
                multiplier = (icar_mean / 150) * (icar_range / 75) + 1.0
            
            multipliers[f"{nutrient}_multiplier"] = round(multiplier, 2)
        
        # SOC multiplier
        soc_mean = npk_ranges["soc"]["mean"]
        soc_range = npk_ranges["soc"]["max"] - npk_ranges["soc"]["min"]
        multipliers["soc_multiplier"] = round((soc_mean / 2.0) * (soc_range / 1.0) + 1.0, 2)
        
        return multipliers

def main():
    """Main function to download ICAR data"""
    downloader = ICARDataDownloader()
    
    # Test API connection
    if not downloader.test_api_connection():
        logger.error("❌ Cannot connect to ICAR API. Please check your internet connection.")
        return
    
    # Download data (limited for testing)
    logger.info("🚀 Starting ICAR data download (limited for testing)")
    
    # Download data for first 3 states, max 2 districts per state
    data = downloader.download_complete_india_data(max_states=3, max_districts_per_state=2)
    
    if len(data) > 0:
        # Save to database
        downloader.save_to_database(data)
        
        # Generate calibration summary
        summary = downloader.generate_calibration_summary(data)
        
        # Save summary
        with open("icar_calibration_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info("✅ ICAR data download and processing complete!")
        logger.info(f"📊 Total samples downloaded: {len(data)}")
        logger.info(f"💾 Data saved to: icar_soil_data.db")
        logger.info(f"📋 Summary saved to: icar_calibration_summary.json")
    else:
        logger.error("❌ No data downloaded. Please check API access.")

if __name__ == "__main__":
    main()

