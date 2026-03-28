"""EcoSignal Image Analyzer — system prompts for Claude Vision API."""

MEAL_PROMPT = """Analizza questa foto di un pasto. Identifica ogni alimento, stima la porzione in grammi, e calcola l'impatto CO2 in kg basandoti su questi fattori medi:
- Carne rossa: 0.027 kg CO2/g
- Pollo: 0.0069 kg CO2/g
- Pesce: 0.006 kg CO2/g
- Latticini: 0.0033 kg CO2/g
- Verdure: 0.002 kg CO2/g
- Cereali/pasta: 0.0014 kg CO2/g
- Frutta: 0.001 kg CO2/g
Rispondi SOLO in JSON: {"items": [{"name": "...", "portion_g": 0.0, "estimated_co2_kg": 0.0}], "total_co2_kg": 0.0, "confidence": "low|medium|high"}"""

GROCERY_PROMPT = """Analizza questa foto della spesa. Identifica ogni prodotto, stima la quantità, la categoria e l'impatto CO2 in kg basandoti su questi fattori medi per unità:
- Carne rossa: 27.0 kg CO2/kg
- Pollo: 6.9 kg CO2/kg
- Pesce: 6.0 kg CO2/kg
- Latticini (latte, formaggio, yogurt): 3.3 kg CO2/kg
- Verdure fresche: 2.0 kg CO2/kg
- Frutta fresca: 1.0 kg CO2/kg
- Cereali/pasta/riso: 1.4 kg CO2/kg
- Bevande confezionate: 1.5 kg CO2/L
- Prodotti surgelati: 3.5 kg CO2/kg (include catena del freddo)
- Snack/dolci confezionati: 2.5 kg CO2/kg
Rispondi SOLO in JSON: {"items": [{"name": "...", "quantity": 1, "category": "...", "estimated_co2_kg": 0.0}], "total_co2_kg": 0.0, "confidence": "low|medium|high"}"""

CLOTHING_PROMPT = """Analizza questa foto di un capo di abbigliamento o acquisto di vestiti. Identifica ogni capo, il materiale, prova a indovinare il brand, e stima l'impatto CO2 in kg basandoti sul ciclo di vita del materiale:
- Cotone: 8 kg CO2/capo
- Poliestere: 12 kg CO2/capo
- Lana: 10 kg CO2/capo
- Lino: 5 kg CO2/capo
- Nylon: 11 kg CO2/capo
- Seta: 15 kg CO2/capo
- Materiali misti: 9 kg CO2/capo
- Pelle: 17 kg CO2/capo
Rispondi SOLO in JSON: {"items": [{"type": "...", "material": "...", "brand_guess": "..." o null, "estimated_co2_kg": 0.0}], "total_co2_kg": 0.0, "confidence": "low|medium|high"}"""
