"""EcoSignal Image Analyzer — system prompts for Claude Vision API.

Claude identifies items and portions/quantities. CO2 estimation is done
separately via the Climatiq API using the identified categories.
"""

MEAL_PROMPT = """Analizza questa foto di un pasto. Per ogni alimento visibile:
1. Identifica il nome dell'alimento
2. Stima la porzione in grammi
3. Assegna una categoria tra: carne_rossa, pollo, pesce, latticini, verdure, cereali_pasta, frutta, altro

Rispondi SOLO in JSON:
{"items": [{"name": "...", "portion_g": 0.0, "category": "..."}], "confidence": "low|medium|high"}"""

GROCERY_PROMPT = """Analizza questa foto della spesa. Per ogni prodotto visibile:
1. Identifica il nome del prodotto
2. Stima la quantità (numero di pezzi)
3. Stima il peso in kg per pezzo
4. Assegna una categoria tra: carne_rossa, pollo, pesce, latticini, verdure_fresche, frutta_fresca, cereali_pasta_riso, bevande, surgelati, snack_dolci, altro

Rispondi SOLO in JSON:
{"items": [{"name": "...", "quantity": 1, "weight_kg": 0.0, "category": "..."}], "confidence": "low|medium|high"}"""

CLOTHING_PROMPT = """Analizza questa foto di un capo di abbigliamento o acquisto di vestiti. Per ogni capo visibile:
1. Identifica il tipo di capo (maglietta, pantaloni, giacca, ecc.)
2. Identifica il materiale principale tra: cotone, poliestere, lana, lino, nylon, seta, misti, pelle
3. Prova a indovinare il brand (o null se non riconoscibile)
4. Stima il peso in kg del capo

Rispondi SOLO in JSON:
{"items": [{"type": "...", "material": "...", "brand_guess": "..." o null, "weight_kg": 0.5}], "confidence": "low|medium|high"}"""
