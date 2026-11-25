import streamlit as st
import pandas as pd
import json, csv, io
from pathlib import Path
from datetime import date, datetime
import matplotlib.pyplot as plt

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
REPORT_DIR = APP_DIR / "reports"
CSV_FILE = DATA_DIR / "meals.csv"
JSON_FILE = DATA_DIR / "meals.json"
CATEGORIES = ["Breakfast", "Lunch", "Dinner", "Snacks", "Beverages", "Other"]

st.set_page_config(page_title="Daily Meal Cost Calculator", page_icon="🍽️", layout="wide")

def ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    if not CSV_FILE.exists():
        pd.DataFrame(columns=["id", "date", "item", "category", "quantity", "unit_price", "total_cost", "notes"]).to_csv(CSV_FILE, index=False)
    if not JSON_FILE.exists():
        JSON_FILE.write_text("[]", encoding="utf-8")

def load_records():
    ensure_files()
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty:
            return pd.DataFrame(columns=["id", "date", "item", "category", "quantity", "unit_price", "total_cost", "notes"])
        required = ["id", "date", "item", "category", "quantity", "unit_price", "total_cost", "notes"]
        for col in required:
            if col not in df.columns:
                df[col] = ""
        df["date"] = df["date"].astype(str)
        for col in ["quantity", "unit_price", "total_cost"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df[required]
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
        try:
            data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
            return pd.DataFrame(data)
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
            return pd.DataFrame(columns=["id", "date", "item", "category", "quantity", "unit_price", "total_cost", "notes"])

def save_records(df):
    ensure_files()
    df.to_csv(CSV_FILE, index=False, quoting=csv.QUOTE_MINIMAL)
    JSON_FILE.write_text(json.dumps(df.to_dict(orient="records"), indent=2, ensure_ascii=False), encoding="utf-8")

def valid_text(value, label, max_len=80):
    value = str(value).strip()
    if not value:
        raise ValueError(f"{label} cannot be blank.")
    if len(value) > max_len:
        raise ValueError(f"{label} must be {max_len} characters or fewer.")
    return value

def money(value):
    return f"₹{float(value):,.2f}"

ensure_files()
if "records" not in st.session_state:
    st.session_state.records = load_records()

st.title("🍽️ Daily Meal Cost Calculator")
st.caption("Track meal items, calculate daily spending, search records and generate clear summaries.")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose a section", ["Dashboard", "Add Meal", "Meal Records", "Search & Filter", "Reports & Export"])
st.sidebar.divider()
st.sidebar.metric("Saved meal entries", len(st.session_state.records))
st.sidebar.caption("Data is stored locally in CSV and JSON files.")

df = st.session_state.records.copy()
if not df.empty:
    df["date"] = df["date"].astype(str)

if page == "Dashboard":
    st.subheader("Executive Summary")
    if df.empty:
        st.info("No meal records yet. Open **Add Meal** to create your first record.")
    else:
        df["total_cost"] = pd.to_numeric(df["total_cost"], errors="coerce").fillna(0)
        total = df["total_cost"].sum()
        days = max(df["date"].nunique(), 1)
        avg_day = total / days
        avg_entry = df["total_cost"].mean()
        today_total = df.loc[df["date"] == date.today().isoformat(), "total_cost"].sum()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total spending", money(total))
        c2.metric("Average per recorded day", money(avg_day))
        c3.metric("Average per meal entry", money(avg_entry))
        c4.metric("Today's spending", money(today_total))
        st.markdown("#### Spending by category")
        category_totals = df.groupby("category", dropna=False)["total_cost"].sum().sort_values(ascending=False)
        st.bar_chart(category_totals)
        st.markdown("#### Daily spending trend")
        daily = df.groupby("date")["total_cost"].sum().sort_index()
        st.line_chart(daily)
        st.markdown("#### Cost status")
        daily_limit = st.number_input("Set a daily budget threshold (₹)", min_value=1.0, value=300.0, step=50.0)
        over = daily[daily > daily_limit]
        if len(over):
            st.warning(f"{len(over)} recorded day(s) exceeded {money(daily_limit)}.")
            st.dataframe(over.rename("Daily total").reset_index(), use_container_width=True, hide_index=True)
        else:
            st.success(f"No recorded day exceeded {money(daily_limit)}.")
        st.markdown("#### Recent entries")
        st.dataframe(df.sort_values(["date", "id"], ascending=[False, False]).head(10), use_container_width=True, hide_index=True)

elif page == "Add Meal":
    st.subheader("Add a meal record")
    with st.form("add_meal_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            meal_date = st.date_input("Meal date", value=date.today())
            item = st.text_input("Food item", placeholder="e.g., Vegetable biryani")
            category = st.selectbox("Category", CATEGORIES)
            notes = st.text_input("Notes (optional)", max_chars=200)
        with col2:
            quantity = st.number_input("Quantity", min_value=0.01, max_value=10000.0, value=1.0, step=0.5)
            unit_price = st.number_input("Price per unit (₹)", min_value=0.0, max_value=1000000.0, value=50.0, step=5.0)
            st.info(f"Estimated item cost: **{money(quantity * unit_price)}**")
        submitted = st.form_submit_button("Save meal record", type="primary")
        if submitted:
            try:
                clean_item = valid_text(item, "Food item", 80)
                if quantity <= 0:
                    raise ValueError("Quantity must be greater than zero.")
                if unit_price < 0:
                    raise ValueError("Price cannot be negative.")
                current = st.session_state.records.copy()
                new_id = int(pd.to_numeric(current["id"], errors="coerce").max()) + 1 if not current.empty else 1
                new_row = {"id": new_id, "date": meal_date.isoformat(), "item": clean_item,
                           "category": category, "quantity": float(quantity),
                           "unit_price": float(unit_price), "total_cost": round(float(quantity * unit_price), 2),
                           "notes": str(notes).strip()}
                current = pd.concat([current, pd.DataFrame([new_row])], ignore_index=True)
                save_records(current)
                st.session_state.records = current
                st.success(f"Saved {clean_item}. Total: {money(new_row['total_cost'])}")
            except ValueError as exc:
                st.error(str(exc))

elif page == "Meal Records":
    st.subheader("All meal records")
    if df.empty:
        st.info("No records available.")
    else:
        st.dataframe(df.sort_values(["date", "id"], ascending=[False, False]), use_container_width=True, hide_index=True)
        st.download_button("Download records as CSV", df.to_csv(index=False).encode("utf-8"), "meal_records.csv", "text/csv")
        if st.button("Reload records from local files"):
            st.session_state.records = load_records()
            st.rerun()

elif page == "Search & Filter":
    st.subheader("Find stored meal records")
    if df.empty:
        st.info("No records to search yet.")
    else:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            keyword = st.text_input("Search food item or notes", placeholder="Type a keyword")
        with col2:
            chosen_category = st.selectbox("Category", ["All"] + CATEGORIES)
        with col3:
            date_filter = st.date_input("Date (optional)", value=None)
        filtered = df.copy()
        if keyword.strip():
            mask = filtered["item"].astype(str).str.contains(keyword.strip(), case=False, na=False) | filtered["notes"].astype(str).str.contains(keyword.strip(), case=False, na=False)
            filtered = filtered[mask]
        if chosen_category != "All":
            filtered = filtered[filtered["category"] == chosen_category]
        if date_filter:
            filtered = filtered[filtered["date"].astype(str) == date_filter.isoformat()]
        st.caption(f"{len(filtered)} matching record(s)")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

elif page == "Reports & Export":
    st.subheader("Summary report and export")
    if df.empty:
        st.info("Add meal records to generate a report.")
    else:
        df["total_cost"] = pd.to_numeric(df["total_cost"], errors="coerce").fillna(0)
        total = df["total_cost"].sum()
        daily = df.groupby("date")["total_cost"].sum().sort_index()
        by_cat = df.groupby("category")["total_cost"].sum().sort_values(ascending=False)
        report = [
            "# Daily Meal Cost Summary",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total entries: {len(df)}",
            f"Recorded days: {df['date'].nunique()}",
            f"Total spending: {money(total)}",
            f"Average per recorded day: {money(total / max(df['date'].nunique(), 1))}",
            "", "## Spending by category"
        ]
        report += [f"- {cat}: {money(amount)}" for cat, amount in by_cat.items()]
        report += ["", "## Daily totals"]
        report += [f"- {day}: {money(amount)}" for day, amount in daily.items()]
        report_text = "\n".join(report)
        st.text_area("Report preview", report_text, height=300)
        st.download_button("Export Markdown report", report_text, "meal_cost_summary.md", "text/markdown")
        st.download_button("Export plain-text report", report_text, "meal_cost_summary.txt", "text/plain")
        st.download_button("Export CSV report", df.to_csv(index=False), "meal_cost_report.csv", "text/csv")
        st.markdown("#### Category summary")
        st.dataframe(by_cat.rename("Total cost").reset_index(), use_container_width=True, hide_index=True)

st.sidebar.caption("Tip: Keep the project folder together so local CSV/JSON persistence continues to work.")
