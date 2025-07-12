import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

# Step 1: Load your exported order data
df = pd.read_csv('order_data.csv')

# Step 2: Pivot it into the format: each row = 1 user, each column = 1 product
basket = df.groupby(['user_id', 'product_id']).size().unstack(fill_value=0)
basket = basket.applymap(lambda x: 1 if x > 0 else 0)

# Step 3: Run Apriori algorithm to find frequent itemsets
frequent_items = apriori(basket, min_support=0.01, use_colnames=True)

# Step 4: Generate association rules
rules = association_rules(frequent_items, metric="lift", min_threshold=1.0)

# Step 5: Output recommendations as product ID pairs
recommendations = []

for _, row in rules.iterrows():
    for item in row['consequents']:
        for base in row['antecedents']:
            recommendations.append((base, item))

# Step 6: Save to CSV
recommendation_df = pd.DataFrame(recommendations, columns=["product_id", "recommended_product_id"])
recommendation_df.drop_duplicates().to_csv('recommendations.csv', index=False)

print("✅ recommendations.csv generated!")
