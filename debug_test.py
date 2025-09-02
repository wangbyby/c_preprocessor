#!/usr/bin/env python3
import json

# Load test_3.json and analyze the coordinates
with open('test_ascii/test_3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

elements = data.get('elements', [])

print("First 10 elements analysis:")
for i, element in enumerate(elements[:10]):
    element_type = element.get('type', '')
    x = element.get('x', 0)
    y = element.get('y', 0)
    width = element.get('width', 0)
    height = element.get('height', 0)
    text = element.get('text', '')
    
    print(f"{i+1}. Type: {element_type}")
    print(f"   Position: ({x:.1f}, {y:.1f})")
    print(f"   Size: {width}x{height}")
    if text:
        print(f"   Text: '{text}'")
    print()

# Calculate bounds
min_x = min_y = float('inf')
max_x = max_y = float('-inf')

for element in elements:
    x = element.get('x', 0)
    y = element.get('y', 0)
    width = element.get('width', 0)
    height = element.get('height', 0)
    
    min_x = min(min_x, x)
    min_y = min(min_y, y)
    max_x = max(max_x, x + width)
    max_y = max(max_y, y + height)

print(f"Bounds: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})")
print(f"Content size: {max_x - min_x:.1f} x {max_y - min_y:.1f}")