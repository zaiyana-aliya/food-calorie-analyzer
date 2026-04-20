from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__)

# Load dataset once at startup
# Load both datasets
df_usda = pd.read_csv('comprehensive_foods_usda.csv')
df_indian = pd.read_csv('indian_foods.csv')
df = pd.concat([df_usda, df_indian], ignore_index=True)
df['food_name_lower'] = df['food_name'].str.lower()

def search_food(query):
    query = query.lower().strip()
    # Exact match
    match = df[df['food_name_lower'] == query]
    if len(match) == 0:
        # Partial match
        match = df[df['food_name_lower'].str.contains(query, na=False)]
    if len(match) == 0:
        return None
    return match.iloc[0]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    food = data.get("food", "").strip()
    
    result = search_food(food)
    
    if result is not None:
        def val(col):
            v = result.get(col, 'N/A')
            return round(float(v), 1) if str(v) not in ['nan', 'N/A', ''] else 'N/A'
        
        response = f"""🥗 Nutrition Facts for {result['food_name']}

📊 Per 100g:
• Calories: {val('calories')} kcal
• Protein: {val('protein_g')}g
• Carbohydrates: {val('carbs_g')}g
• Fat: {val('fat_g')}g
• Fiber: {val('fiber_g')}g
• Sugar: {val('sugar_g')}g

💊 Minerals:
• Calcium: {val('calcium_mg')}mg
• Iron: {val('iron_mg')}mg
• Sodium: {val('sodium_mg')}mg

🏷️ Category: {result.get('food_category', 'N/A')}
⭐ Health Score: {val('health_score')}/100

⚠️ Values are per 100g serving."""
        return jsonify({"result": response, "found": True})
    else:
        return jsonify({"result": f"❌ '{food}' not found. Try searching with simpler terms like 'banana', 'chicken', 'rice'", "found": False})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)