from app.compatibility import calculate_compatibility_score


sample_outfit = [
    {
        "item_id": "P001",
        "title": "Black Casual Crop Top",
        "category": "top",
        "color": ["black"],
        "style": ["casual"]
    },
    {
        "item_id": "P002",
        "title": "Blue Denim Jeans",
        "category": "bottom",
        "color": ["blue"],
        "style": ["casual"]
    },
    {
        "item_id": "P003",
        "title": "White Casual Jacket",
        "category": "outerwear",
        "color": ["white"],
        "style": ["casual"]
    }
]


result = calculate_compatibility_score(
    outfit_items=sample_outfit,
    occasion="casual"
)

print(result)