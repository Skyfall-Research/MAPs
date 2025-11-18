import yaml

# Load the configuration
with open('./shared/config.yaml', 'r') as file:
    config = yaml.safe_load(file)

print("=" * 80)
print("THEME PARK RIDE & SHOP ANALYSIS")
print("=" * 80)

print("\n🎢 RIDE ANALYSIS")
print("-" * 50)

for ride_type, variants in config['rides'].items():
    print(f"\n{ride_type.upper().replace('_', ' ')}:")
    print("-" * 30)
    
    for variant, specs in variants.items():
        # Calculate ride metrics
        max_profit_per_operation = specs['capacity'] * specs['max_ticket_price'] - specs['cost_per_operation']
        operations_to_break_even = specs['building_cost'] / max_profit_per_operation if max_profit_per_operation > 0 else float('inf')
        park_rating_points = specs['excitement'] + 5 - abs(5 - specs['intensity'])
        
        print(f"  {variant.upper()} Variant:")
        print(f"    Max Profit per Operation: ${max_profit_per_operation:.2f}")
        print(f"    Operations to Break Even: {operations_to_break_even:.1f}")
        print(f"    Park Rating Points: {park_rating_points}")
        print(f"    Building Cost: ${specs['building_cost']}")
        print(f"    Capacity: {specs['capacity']} guests")
        print(f"    Max Ticket Price: ${specs['max_ticket_price']}")
        print(f"    Cost per Operation: ${specs['cost_per_operation']}")
        print(f"    Excitement: {specs['excitement']}")
        print(f"    Intensity: {specs['intensity']}")

print("\n🏪 SHOP ANALYSIS")
print("-" * 50)

for shop_type, variants in config['shops'].items():
    print(f"\n{shop_type.upper()} SHOP:")
    print("-" * 20)
    
    for variant, specs in variants.items():
        # Calculate shop metrics
        markup =  specs['max_item_price'] / specs['item_cost'] if specs['max_item_price'] > 0 and specs['item_cost'] > 0 else float('inf')
        sales_to_break_even = specs['building_cost'] / (specs['max_item_price'] - specs['item_cost']) if specs['max_item_price'] > 0 else float('inf')
        
        print(f"  {variant.upper()} Variant:")
        print(f"    Markup: {markup:.2f}")
        print(f"    Sales to Break Even: {sales_to_break_even:.1f}")
        print(f"    Building Cost: ${specs['building_cost']}")
        print(f"    Max Item Price: ${specs['max_item_price']}")
        print(f"    Item Cost: ${specs['item_cost']}")
        
        # Show additional benefits if they exist
        benefits = []
        if 'thirst_reduction' in specs:
            benefits.append(f"Thirst Reduction: {specs['thirst_reduction']}")
        if 'hunger_reduction' in specs:
            benefits.append(f"Hunger Reduction: {specs['hunger_reduction']}")
        if 'happiness_boost' in specs:
            benefits.append(f"Happiness Boost: {specs['happiness_boost']}")
        if 'energy_boost' in specs:
            benefits.append(f"Energy Boost: {specs['energy_boost']}")
        if 'money_withdrawal' in specs:
            benefits.append(f"Money Withdrawal: ${specs['money_withdrawal']}")
        if 'thirst_boost' in specs:
            benefits.append(f"Thirst Boost: {specs['thirst_boost']}")
        if 'hunger_boost' in specs:
            benefits.append(f"Hunger Boost: {specs['hunger_boost']}")
        if 'caffeinated_steps' in specs:
            benefits.append(f"Caffeinated Steps: {specs['caffeinated_steps']}")
        
        if benefits:
            print(f"    Benefits: {', '.join(benefits)}")

print("\n" + "=" * 80)
print("SUMMARY RANKINGS")
print("=" * 80)

# Create summary tables for easy comparison
print("\n🏆 BEST RIDES BY METRIC:")
print("-" * 30)

# Collect all rides for comparison
all_rides = []
for ride_type, variants in config['rides'].items():
    for variant, specs in variants.items():
        max_profit_per_operation = specs['capacity'] * specs['max_ticket_price'] - specs['cost_per_operation']
        operations_to_break_even = specs['building_cost'] / max_profit_per_operation if max_profit_per_operation > 0 else float('inf')
        park_rating_points = specs['excitement'] + 5 - abs(5 - specs['intensity'])
        
        all_rides.append({
            'name': f"{ride_type} ({variant})",
            'max_profit': max_profit_per_operation,
            'break_even_ops': operations_to_break_even,
            'rating_points': park_rating_points,
            'building_cost': specs['building_cost']
        })

# Sort by different metrics
print("\nHighest Profit per Operation:")
for ride in sorted(all_rides, key=lambda x: x['max_profit'], reverse=True):
    print(f"  {ride['name']}: ${ride['max_profit']:.2f}")

print("\nFastest Break Even (fewest operations):")
for ride in sorted(all_rides, key=lambda x: x['break_even_ops']):
    print(f"  {ride['name']}: {ride['break_even_ops']:.1f} operations")

print("\nHighest Park Rating Points:")
for ride in sorted(all_rides, key=lambda x: x['rating_points'], reverse=True):
    print(f"  {ride['name']}: {ride['rating_points']} points")

print("\n🏆 BEST SHOPS BY METRIC:")
print("-" * 30)

# Collect all shops for comparison
all_shops = []
for shop_type, variants in config['shops'].items():
    for variant, specs in variants.items():
        markup_percentage = specs['max_item_price'] / specs['item_cost'] if specs['max_item_price'] > 0 and specs['item_cost'] > 0 else float('inf')
        markup_amount = specs['max_item_price'] - specs['item_cost'] if specs['max_item_price'] > 0 and specs['item_cost'] > 0 else float('inf')
        sales_to_break_even = specs['building_cost'] / (specs['max_item_price'] - specs['item_cost']) if specs['max_item_price'] > 0 else float('inf')
        
        all_shops.append({
            'name': f"{shop_type} ({variant})",
            'markup_percentage': markup_percentage,
            'markup_amount': markup_amount,
            'sales_to_break_even': sales_to_break_even,
            'building_cost': specs['building_cost'],
            'max_item_price': specs['max_item_price']
        })

print("\nHighest Markup:")
for shop in sorted(all_shops, key=lambda x: x['markup_percentage'], reverse=True):
    if shop['markup_percentage'] != float('inf'):
        print(f"  {shop['name']}: {shop['markup_percentage']:.2f}x")

print("\nHighest Markup Amount:")
for shop in sorted(all_shops, key=lambda x: x['markup_amount'], reverse=True):
    if shop['markup_amount'] != float('inf'):
        print(f"  {shop['name']}: ${shop['markup_amount']:.2f}")

print("\nFastest Break Even (fewest sales):")
for shop in sorted(all_shops, key=lambda x: x['sales_to_break_even']):
    if shop['sales_to_break_even'] != float('inf'):
        print(f"  {shop['name']}: {shop['sales_to_break_even']:.1f} sales to break even")

print("\n📊 EXCITEMENT & INTENSITY SCORE DISTRIBUTION:")
print("-" * 50)

# Count excitement scores
excitement_counts = {}
intensity_counts = {}

for ride_type, variants in config['rides'].items():
    for variant, specs in variants.items():
        excitement = specs['excitement']
        intensity = specs['intensity']
        
        excitement_counts[excitement] = excitement_counts.get(excitement, 0) + 1
        intensity_counts[intensity] = intensity_counts.get(intensity, 0) + 1

print("\nExcitement Score Distribution:")
for score in sorted(excitement_counts.keys()):
    count = excitement_counts[score]
    print(f"  Score {score}: {count} ride{'s' if count != 1 else ''}")

print("\nIntensity Score Distribution:")
for score in sorted(intensity_counts.keys()):
    count = intensity_counts[score]
    print(f"  Score {score}: {count} ride{'s' if count != 1 else ''}")

print("\n" + "=" * 80)
