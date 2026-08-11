import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

# ==========================================
# 1. PAGE CONFIGURATION (BETTER INTERFACE)
# ==========================================
st.set_page_config(page_title="Universal SCM Engine", layout="wide", initial_sidebar_state="expanded")

st.title("🌐 Universal Supplier Selection & Allocation Engine")
st.markdown("Based on Professor Banerjee's Two-Phase MCDM & Goal Programming Framework.")
st.divider()

# ==========================================
# 2. SIDEBAR (UNIVERSAL SETTINGS)
# ==========================================
st.sidebar.header("⚙️ Project Parameters")
st.sidebar.markdown("Define your specific procurement scenario here.")

# Make it universal: The user decides what they are buying!
product_name = st.sidebar.text_input("What product are you procuring?", value="Lithium Batteries")
total_demand = st.sidebar.number_input(f"Total {product_name} Needed:", min_value=1, value=1000)

# ==========================================
# 3. MAIN STAGE: DYNAMIC DATA ENTRY
# ==========================================
st.subheader(f"📊 Step 1: Input Supplier Data for {product_name}")
st.markdown("You can evaluate **any number of suppliers**. Click the bottom row to add a new one, or select a row and press 'Delete' to remove it.")

# Generic starting data, but the user can change all of it
default_data = {
    "Supplier Name": ["Vendor Alpha", "Vendor Beta", "Vendor Gamma"],
    "Cost per Unit ($)": [120.0, 110.0, 115.0],
    "Defect Rate (%)": [2.0, 4.5, 1.5],
    "Delivery Lead Time (Days)": [14, 21, 10],
    "Max Capacity (Units)": [600, 500, 400]
}
df = pd.DataFrame(default_data)

# 'num_rows="dynamic"' is the magic that allows infinite companies
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)

# ==========================================
# 4. THE MATH ENGINE (RUNS ON BUTTON CLICK)
# ==========================================
# Wait for the user to finish entering data before running the math
if st.button("🚀 Run SCM Optimization Engine", type="primary"):
    
    # 🛡️ THE FIX: Automatically remove any rows that have blank cells
    edited_df = edited_df.dropna() 
    
    if edited_df.empty:
        st.error("⚠️ Error: Please make sure you have at least one supplier with fully completed data (no blank cells).")
    else:
        st.divider()
        
        # Create two side-by-side columns for a much cleaner interface
        col1, col2 = st.columns(2)

        # ----------------------------------
        # PHASE 1: TOPSIS (LEFT COLUMN)
        # ----------------------------------
        with col1:
            st.subheader("🏆 Phase 1: TOPSIS Ranking")
            
            # Normalize the data (adding a tiny decimal to prevent dividing by zero errors)
            norm_cost = 1 / (edited_df["Cost per Unit ($)"] + 0.0001)
            norm_defect = 1 / (edited_df["Defect Rate (%)"] + 0.0001)
            norm_speed = 1 / (edited_df["Delivery Lead Time (Days)"] + 0.0001)

            edited_df["TOPSIS Score"] = (norm_cost + norm_defect + norm_speed) / 3
            ranked_df = edited_df.sort_values(by="TOPSIS Score", ascending=False).reset_index(drop=True)

            # Display a visually appealing heatmap table
            st.dataframe(ranked_df[["Supplier Name", "TOPSIS Score"]].style.background_gradient(cmap="Greens"), use_container_width=True)
            st.bar_chart(ranked_df.set_index("Supplier Name")["TOPSIS Score"])

        # ----------------------------------
        # PHASE 2: ALLOCATION (RIGHT COLUMN)
        # ----------------------------------
        with col2:
            st.subheader("📦 Phase 2: Optimal Order Allocation")
            
            costs = -ranked_df["TOPSIS Score"].values
            capacities = ranked_df["Max Capacity (Units)"].values
            bounds = [(0, cap) for cap in capacities]

            # Dynamic constraints based on however many suppliers the user added
            A_eq = [[1] * len(ranked_df)]
            b_eq = [total_demand]

            result = linprog(costs, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

            if result.success:
                ranked_df["Units to Order"] = np.round(result.x).astype(int)
                
                # UI UPGRADE: Large Metric Display for the winner
                top_supplier = ranked_df.iloc[0]["Supplier Name"]
                top_order = ranked_df.iloc[0]["Units to Order"]
                st.metric(label="🌟 Primary Supplier Recommendation", value=top_supplier, delta=f"{top_order} units allocated")
                
                st.success(f"Algorithm successfully allocated all {total_demand} units without exceeding factory capacities.")
                st.dataframe(ranked_df[["Supplier Name", "Units to Order"]].style.highlight_max(subset=["Units to Order"], color='lightblue'), use_container_width=True)
            else:
                total_cap = sum(capacities)
                st.error(f"⚠️ Capacity Error: You requested {total_demand} units, but your current suppliers only have a combined maximum capacity of {total_cap} units. Please add more suppliers or reduce demand.")