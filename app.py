from flask import Flask, request, jsonify, render_template
import pandas as pd
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load dataset
df = pd.read_csv('comprehensive_foods_usda.csv')
df_indian = pd.read_csv('indian_foods.csv')
df = pd.concat([df, df_indian], ignore_index=True)
df['food_name_lower'] = df['food_name'].str.lower()

# Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def search_food(query):
    query = query.lower().strip()
    match = df[df['food_name_lower'] == query]
    if len(match) == 0:
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
    
    # Search CSV for nutrition data
    result = search_food(food)
    
    if result is not None:
        nutrition_context = f"""
        Food: {result['food_name']}
        Calories: {result.get('calories', 'N/A')} kcal per 100g
        Protein: {result.get('protein_g', 'N/A')}g
        Carbohydrates: {result.get('carbs_g', 'N/A')}g
        Fat: {result.get('fat_g', 'N/A')}g
        Fiber: {result.get('fiber_g', 'N/A')}g
        Calcium: {result.get('calcium_mg', 'N/A')}mg
        Iron: {result.get('iron_mg', 'N/A')}mg
        Sodium: {result.get('sodium_mg', 'N/A')}mg
        Health Score: {result.get('health_score', 'N/A')}/100
        Category: {result.get('food_category', 'N/A')}
        """
    else:
        nutrition_context = f"No specific data found for {food} in database."

    # Use Groq AI to give smart response
    prompt = f"""You are a friendly nutrition expert. 
    
A user asked about: "{food}"

Here is the nutrition data from our database:
{nutrition_context}

Give a helpful, conversational response that includes:
1. The key nutrition facts (calories, protein, carbs, fat)
2. Main health benefits
3. Who should eat this food (weight loss, diabetes, muscle building etc.)
4. One practical tip for consuming this food

Keep response under 200 words. Be friendly and helpful."""

    chat = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    
    return jsonify({"result": chat.choices[0].message.content, "found": result is not None})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)