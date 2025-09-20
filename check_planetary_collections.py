#!/usr/bin/env python3
"""
Check what collections are available in Microsoft Planetary Computer
"""
import pystac_client
import json

def check_planetary_collections():
    """Check all available collections in Planetary Computer"""
    try:
        # Open the Planetary Computer STAC catalog
        catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1/")
        
        print("🌍 Microsoft Planetary Computer Collections")
        print("=" * 60)
        
        # Get all collections
        collections = catalog.get_collections()
        
        soil_related = []
        satellite_related = []
        other_collections = []
        
        for collection in collections:
            collection_id = collection.id
            title = collection.title or "No title"
            description = collection.description or "No description"
            
            # Categorize collections
            if any(keyword in collection_id.lower() or keyword in title.lower() or keyword in description.lower() 
                   for keyword in ['soil', 'ph', 'texture', 'land', 'terrain', 'elevation']):
                soil_related.append((collection_id, title, description))
            elif any(keyword in collection_id.lower() or keyword in title.lower() 
                     for keyword in ['sentinel', 'landsat', 'modis', 'satellite', 'imagery']):
                satellite_related.append((collection_id, title, description))
            else:
                other_collections.append((collection_id, title, description))
        
        print(f"\n🛰️ SATELLITE DATA COLLECTIONS ({len(satellite_related)}):")
        print("-" * 40)
        for collection_id, title, description in satellite_related:
            print(f"📡 {collection_id}")
            print(f"   Title: {title}")
            print(f"   Description: {description[:100]}...")
            print()
        
        print(f"\n🌱 SOIL/LAND DATA COLLECTIONS ({len(soil_related)}):")
        print("-" * 40)
        for collection_id, title, description in soil_related:
            print(f"🌍 {collection_id}")
            print(f"   Title: {title}")
            print(f"   Description: {description[:100]}...")
            print()
        
        print(f"\n📊 OTHER COLLECTIONS ({len(other_collections)}):")
        print("-" * 40)
        for collection_id, title, description in other_collections[:10]:  # Show first 10
            print(f"📈 {collection_id}")
            print(f"   Title: {title}")
            print(f"   Description: {description[:100]}...")
            print()
        
        if len(other_collections) > 10:
            print(f"... and {len(other_collections) - 10} more collections")
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total Collections: {len(satellite_related) + len(soil_related) + len(other_collections)}")
        print(f"   Satellite Collections: {len(satellite_related)}")
        print(f"   Soil/Land Collections: {len(soil_related)}")
        print(f"   Other Collections: {len(other_collections)}")
        
        return {
            'satellite': satellite_related,
            'soil': soil_related,
            'other': other_collections
        }
        
    except Exception as e:
        print(f"❌ Error accessing Planetary Computer: {e}")
        return None

if __name__ == "__main__":
    collections = check_planetary_collections()
