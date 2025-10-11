#!/usr/bin/env python3
"""
Remove redundant zone fields from kanker_complete_soil_analysis_data.json
"""

import json

def remove_redundant_zone_fields():
    """
    Remove redundant 'zone' field from village data as we now have specific nutrient zones
    """
    file_path = 'kanker_complete_soil_analysis_data.json'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return
    
    removed_count = 0
    
    # Remove redundant 'zone' field from each village
    if 'village_data' in data and 'villages' in data['village_data']:
        for village in data['village_data']['villages']:
            if 'zone' in village:
                del village['zone']
                removed_count += 1
    
    # Also remove from old structure if it exists
    if 'village_wise_data' in data and 'villages' in data['village_wise_data']:
        for village in data['village_wise_data']['villages']:
            if 'zone' in village:
                del village['zone']
                removed_count += 1
    
    # Save cleaned data
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully removed redundant 'zone' fields")
        print(f"   - Fields removed: {removed_count}")
        print(f"   - Reason: Redundant with specific nutrient zones")
        print(f"   - Now using: nitrogen_zone, phosphorus_zone, potassium_zone, etc.")
        
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")

if __name__ == "__main__":
    remove_redundant_zone_fields()
