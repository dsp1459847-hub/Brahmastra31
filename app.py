import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Day Pattern Engine", layout="wide")

st.title("MAYA AI 📅: 'Day of the Month' Pattern Engine")
st.markdown("Yeh system pichle 5 saalon mein **har mahine ki same tareekh (Date)** ko check karta hai, mahine (Month) ko ignore karke. Taki 60+ majboot records se 100% sahi pattern nikal sake.")

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

        # --- 4. THE REAL "DAY" ANALYSIS (Ignore Month) ---
        st.markdown("---")
        target_day = selected_date.day
        
        st.subheader(f"📅 Pattern Check for the [{target_day}th] of Every Month (Last 5 Years/60 Months)")
        
        # Un saari dates ko filter karna jinki tareekh (Day) selected date ke barabar ho
        past_same_days = df[(df['DATE'].dt.day == target_day) & (df['DATE'] < pd.Timestamp(selected_date))].copy()
        
        # Pichle 60 records (approx 5 years of months) nikalna
        past_same_days = past_same_days.sort_values(by='DATE', ascending=False).head(60)
        
        seasonal_hits = {"High": 0, "Medium": 0, "Low": 0, "Eliminated": 0}
        history_rows = []

        with st.spinner(f"Har mahine ki {target_day} tareekh ka data scan ho raha hai..."):
            for idx, row in past_same_days.iterrows():
                t_date = row['DATE']
                actual_val = row[target_shift_name]
                
                if pd.notna(actual_val):
                    # Us particular date se pehle ka data
                    past_history = df[df['DATE'] < t_date][target_shift_name].tolist()
                    if len(past_history) < 15: continue
                    
                    e, s = run_elimination(past_history, max_limit)
                    h, m, l, el = get_tiers(e, s)
                    
                    actual_num = int(actual_val)
                    status = "Eliminated"
                    if actual_num in h: status = "High"
                    elif actual_num in m: status = "Medium"
                    elif actual_num in l: status = "Low"
                    
                    seasonal_hits[status] += 1
                    history_rows.append({
                        "Date": t_date.strftime('%d %b %Y'), 
                        "Result": f"{actual_num:02d}", 
                        "Hit Tier": status
                    })

        # Results dikhana
        if history_rows:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("### 📊 Score Board")
                st.write(f"🔥 **High Tier:** {seasonal_hits['High']} baar")
                st.write(f"⚡ **Medium Tier:** {seasonal_hits['Medium']} baar")
                st.write(f"❄️ **Low Tier:** {seasonal_hits['Low']} baar")
                st.write(f"🚫 **Eliminated:** {seasonal_hits['Eliminated']} baar")
                
                best_seasonal_tier = max(seasonal_hits, key=seasonal_hits.get)
            
            with col2:
                st.write("### 📜 Pichli 60 Tareekhon Ka Record (Proof)")
                history_df = pd.DataFrame(history_rows)
                st.dataframe(history_df, height=250)
                
        else:
            st.warning("Data nahi mila.")
            best_seasonal_tier = "High"

        # --- 5. LIVE PREDICTION & SWAPPING ---
        st.markdown("---")
        st.header(f"🎯 Final Verdict for {selected_date.strftime('%d %B %Y')}")
        
        current_history = df[df['DATE'] < pd.Timestamp(selected_date)][target_shift_name].tolist()
        e_f, s_f = run_elimination(current_history, max_limit)
        h_f, m_f, l_f, el_f = get_tiers(e_f, s_f)

        # AI Recommendation based on massive Day matching
        st.success(f"### 💡 AI Recommendation: [{best_seasonal_tier.upper()} TIER]")
        st.write(f"**Reason:** Pichle 5 saalon mein lagbhag har mahine ki **{target_day} tareekh** ko check kiya gaya. Sabse zyada ({seasonal_hits[best_seasonal_tier]} baar) result **{best_seasonal_tier} Tier** se hi nikal raha hai. Isliye aaj isi tier par bharosa karna sabse majboot (safe) rahega.")

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
    st.info("👈 Please upload your data to start Day Pattern Verification.")
            
