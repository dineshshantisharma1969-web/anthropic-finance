# Indian Food Database

The accuracy moat. Photos are matched against this reference table instead of trusting raw AI estimates; nutrition values derive from **IFCT 2017** (India's official food composition tables). Lives as the `Food Database` tab of `Food_Intake_Tracker` (999 rows) → moves to Supabase in v2.

## Schema

| Column | Example | Notes |
|---|---|---|
| `food_name` | Aloo Paratha | Canonical English name |
| `aliases` | `Potato Paratha\|आलू पराठा` | **Pipe-separated**, includes Hindi/regional names — critical for text-input matching |
| `category` | Breads | See category list below |
| `region` | North Indian | North/South/East Indian, Punjabi, Gujarati, Maharashtrian, Hyderabadi, Rajasthani, Indo-Chinese, All India, Street Food |
| `serving_size` | 1 piece / 1 bowl (150g) / 1 plate (200g) | **Household units** — katori, roti-count, plate; never raw grams alone |
| `serving_grams` | 100 | Gram equivalent of the serving |
| `calories` … `sugar_g` | 300 / 6 / 40 / 13 / 3 / 2 | kcal, protein_g, carbs_g, fat_g, fiber_g, sugar_g per serving |
| `is_verified` | 1 | Human-verified flag — only verified rows should override AI output |

## Categories (as present in the sheet)

Breads · Rice · Dal · Sabzi Dry · Sabzi Gravy · South Indian · Snacks · Street Food · Non-Veg · Sweets · Beverages · Accompaniments

Sample entries for calibration:

| Dish | Serving | kcal | P/C/F |
|---|---|---|---|
| Roti (Chapati/Phulka) | 1 piece (30g) | 72 | 2.5 / 15 / 0.4 |
| Dal Tadka | 1 bowl (150g) | 180 | 9 / 22 / 6 |
| Chicken Biryani | 1 plate (250g) | 450 | 25 / 50 / 16 |
| Masala Dosa | 1 piece | ~250 | — |
| Chole | 1 bowl (150g) | 240 | 10 / 32 / 8 |

## Rules

1. **Alias-first matching** — user text ("phulka", "रोटी") resolves through `aliases` before any AI call; a DB hit costs ₹0 in AI tokens
2. **Portion multipliers** — Small/Medium/Large scale from `serving_grams`; "2 roti" = 2 × the base serving
3. **Verified beats AI** — when Vision identifies a dish that exists verified in the DB, the DB nutrition wins; AI only fills gaps
4. **Corrections feed the DB** — every user correction (dish or portion) is stored; recurring corrections trigger a review → new verified row or alias
5. **Cache common dishes** — top ~100 dishes cover the vast majority of logs; caching their Vision results is the main AI-cost lever (see the ₹15/user/mo assumption in the [Business Plan](Business-Plan.md))

## Expansion plan

- **Now → launch:** re-verify the high-frequency dishes actually appearing in the 1,183-row Food Log (dal-chawal combos, parathas, poha, curd, seasonal fruit)
- **Launch → M6:** 999 → 1,500 dishes; add combo-plate entries ("2 Roti + Dal + Sabzi" as single rows) since real logs are combos, not single dishes
- **M6+:** regional depth (Bengali, Tamil, Kerala, street food by city), packaged-food barcodes, restaurant-chain standards
- Each verified dish is also an SEO landing page ("aloo paratha calories") — the DB doubles as the content-marketing engine

## Data hygiene (found during the July 2026 audit)

The `Food Database` tab export shows some Food-Log-style rows mixed in at the tail (dated entries like "12-July", free-text combos, stray `chat_id` values). Before v2 migration:

- [ ] Strip non-dish rows from the Food Database tab (they belong in Food Log)
- [ ] Enforce numeric types on kcal/macros; `is_verified` strictly 0/1
- [ ] De-duplicate dishes that appear both as canonical rows and as log spillover ("Dal Tadka", "Roti")
