import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Seasonal Date Engine", layout="wide")

st.title("MAYA AI 🦅: 5-Year Date History & Tier Swapping Engine")
st.markdown("Yeh system aaj ki date ka pichle 5 saalon ka record check karta hai taaki aaj ki prediction confirm ho sake.")

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
shift_names = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]
target_shift_name = st.sidebar.selectbox("Target Shift", shift_names)
selected_date = st.sidebar.date_input("Prediction For (Target Date)", datetime(2026, 4, 21))
max_limit = st.sidebar.slider("Max Repeat Limit", 2, 5, 4)

if uploaded_file is not None:
    try:
        # --- 2. Data Cleaning ---
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df = df.sort_values(by='DATE').reset_index(drop=True)
        for col in shift_names:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')

        # --- 3. Core Engine Functions ---
        def run_elimination(shift_list, limit):
            shift_list = [int(x) for x in shift_list if pd.notna(x)]
            eliminated = set()
            scores = Counter()
            for days in range(1, 31):
                if len(shift_list) < days: continue
                sheet = shift_list[-days:]
                counts = Counter(sheet)
                if len(counts) == len(sheet) and len(sheet) > 1: eliminated.update(sheet)
                for num, freq in counts.items():
                    if freq >= limit: eliminated.add(num)
                    else: scores[num] += 1
            return eliminated, scores

        def get_tiers(elim_set, score_dict):
            safe = sorted([n for n in range(100) if n not in elim_set], key=lambda x: score_dict[x], reverse=True)
            if not safe: return [], [], [], sorted(list(elim_set))
            n_s = len(safe)
            return safe[:int(n_s*0.33)], safe[int(n_s*0.33):int(n_s*0.66)], safe[int(n_s*0.66):], sorted(list(elim_set))

        # --- 4. 5-YEAR SAME DATE ANALYSIS ---
        st.markdown("---")
        target_day = selected_date.day
        target_month = selected_date.month
        
        st.subheader(f"📅 5-Year History for {target_day}/{target_month} (Same Date Across Years)")
        
        seasonal_hits = {"High": 0, "Medium": 0, "Low": 0, "Eliminated": 0}
        history_rows = []

        # Scanning pichle 6 saalon ka data same date ke liye
        for year in range(2020, selected_date.year):
            past_target_date = pd.Timestamp(year, target_month, target_day)
            
            # Check if this date exists in data
            day_data = df[df['DATE'] == past_target_date]
            if not day_data.empty:
                actual_val = day_data[target_shift_name].values[0]
                if pd.notna(actual_val):
                    # Analysis for that specific historical day
                    past_history = df[df['DATE'] < past_target_date][target_shift_name].tolist()
                    e, s = run_elimination(past_history, max_limit)
                    h, m, l, el = get_tiers(e, s)
                    
                    actual_num = int(actual_val)
                    status = "Eliminated"
                    if actual_num in h: status = "High"
                    elif actual_num in m: status = "Medium"
                    elif actual_num in l: status = "Low"
                    
                    seasonal_hits[status] += 1
                    history_rows.append({"Year": year, "Result": f"{actual_num:02d}", "Hit Tier": status})

        if history_rows:
            st.table(pd.DataFrame(history_rows))
            best_seasonal_tier = max(seasonal_hits, key=seasonal_hits.get)
        else:
            st.warning("Pichle saalon ka is date ka data nahi mila.")
            best_seasonal_tier = "High"

        # --- 5. LIVE PREDICTION & SWAPPING ---
        st.markdown("---")
        st.header(f"🎯 Final Verdict for {selected_date.strftime('%d %B %Y')}")
        
        current_history = df[df['DATE'] < pd.Timestamp(selected_date)][target_shift_name].tolist()
        e_f, s_f = run_elimination(current_history, max_limit)
        h_f, m_f, l_f, el_f = get_tiers(e_f, s_f)

        # Swapping Logic: Agar is date par history 'Medium' ki rahi hai, toh Medium ko pick karo
        st.success(f"### AI Recommendation: [{best_seasonal_tier.upper()} TIER]")
        st.write(f"**Reason:** Pichle 5-6 saalon mein {target_day}/{target_month} ki date par sabse zyada **{best_seasonal_tier} Tier** ke numbers pass hue hain.")

        # Display Tiers
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"#### 🔥 High {'✅' if best_seasonal_tier=='High' else ''}")
            st.write(", ".join([f"{x:02d}" for x in h_f]))
        with c2:
            st.markdown(f"#### ⚡ Medium {'✅' if best_seasonal_tier=='Medium' else ''}")
            st.write(", ".join([f"{x:02d}" for x in m_f]))
        with c3:
            st.markdown(f"#### ❄️ Low {'✅' if best_seasonal_tier=='Low' else ''}")
            st.write(", ".join([f"{x:02d}" for x in l_f]))
        with c4:
            st.markdown(f"#### 🚫 Eliminated {'✅' if best_seasonal_tier=='Eliminated' else ''}")
            st.write(", ".join([f"{x:02d}" for x in el_f]))

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👈 Please upload your data to start Seasonal Verification.")

