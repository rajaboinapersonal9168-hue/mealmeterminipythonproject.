# Daily Meal Cost Calculator

A Streamlit application built to satisfy the **Must-Have** requirements in the DataSpark Challenge Project #64 brief.

## Features mapped to the brief

1. **Interactive interface:** Sidebar menu with Dashboard, Add Meal, Meal Records, Search & Filter, and Reports & Export.
2. **Defensive input validation:** Required food-item validation, length checks, positive quantity checks, non-negative price checks, and bounded numeric inputs.
3. **Core calculation engine:** Calculates `quantity × unit price` for each item and aggregates daily and category costs.
4. **Local persistence:** Automatically saves records to both `data/meals.csv` and `data/meals.json`; data remains after app restarts.
5. **Record query & search:** Keyword search across food items/notes, category filtering, and date filtering.
6. **Executive summary:** Total spending, average per recorded day, average per entry, today's spending, category totals, daily trends, and budget-threshold warnings.

Also included: Markdown, TXT, and CSV report exports, plus sample CSV and JSON datasets (40 entries).

## Run on Windows

1. Install Python 3.10 or newer.
2. Extract the ZIP file.
3. Open Command Prompt in the extracted `daily_meal_cost_calculator` folder.
4. Install dependencies:

   ```bash
   py -m pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   py -m streamlit run app.py
   ```

6. Open the local URL shown in the terminal (usually `http://localhost:8501`).

## Data files

- `data/meals.csv` — sample meal records and the app's CSV persistence file.
- `data/meals.json` — same sample records in JSON format; the app updates both files whenever a record is saved.
- `reports/` — folder reserved for generated/local reports.

Keep the folder structure intact when running the app. For a clean start, make a backup and clear the rows in both data files.
