import requests
import json

# Test API endpoint
response = requests.get('http://localhost:8000/api/projects/pasang-wedding-slideshow/media?limit=10&type=all')
data = response.json()

print("=" * 80)
print("API RESPONSE CHECK")
print("=" * 80)

if 'media' in data:
    media_list = data['media']
    print(f"\nTotal items: {len(media_list)}")
    
    # Check first 5 items
    print("\nFirst 5 items:")
    for i, item in enumerate(media_list[:5]):
        print(f"\n{i+1}. {item.get('name', 'NO NAME')}")
        print(f"   Rating: {item.get('rating', 'MISSING')}")
        print(f"   Color:  {item.get('color', 'MISSING')}")
        print(f"   Blur:   {item.get('blur', {}).get('laplacian', 'MISSING')}")
        print(f"   Keywords: {item.get('keywords', 'MISSING')}")
        
    # Find items with color
    colored = [m for m in media_list if m.get('color')]
    print(f"\n\nItems with color label: {len(colored)}")
    if colored:
        print("Sample colored items:")
        for item in colored[:3]:
            print(f"  - {item['name']}: color={item['color']}")
    
    # Find items with rating
    rated = [m for m in media_list if m.get('rating', 0) > 0]
    print(f"\nItems with rating: {len(rated)}")
    if rated:
        print("Sample rated items:")
        for item in rated[:3]:
            print(f"  - {item['name']}: rating={item['rating']}")
else:
    print("ERROR: No 'media' key in response!")
    print(f"Response keys: {data.keys()}")
