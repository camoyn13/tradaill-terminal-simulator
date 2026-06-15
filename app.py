import streamlit as st
import pandas as pd
import numpy as np
import math

from pathlib import Path

LOGO_PATH = Path("assets/tradaill_logo.jpg")

# -----------------------------
# Tradaill Branding
# -----------------------------

st.markdown("""
<style>
    .stApp {
        background-color: #062B38;
        color: #F4F7F8;
    }

    section[data-testid="stSidebar"] {
        background-color: #073442;
        border-right: 1px solid #0F5264;
    }

    h1, h2, h3 {
        color: #54E084;
        font-weight: 700;
    }

    .stMetric {
        background-color: #083D4C;
        border: 1px solid #1B6C7D;
        padding: 14px;
        border-radius: 12px;
    }

    .tradaill-header {
        background: linear-gradient(90deg, #073442 0%, #062B38 100%);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #1B6C7D;
        margin-bottom: 25px;
    }

    .tradaill-title {
        font-size: 34px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 1px;
    }

    .tradaill-subtitle {
        font-size: 16px;
        color: #B8D8DE;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Tradaill Terminal Simulator", layout="wide")

col_logo, col_title = st.columns([1, 4])

with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=260)

with col_title:
    st.markdown("""
    <div class="tradaill-header">
        <div class="tradaill-title">TERMINAL SIMULATOR</div>
        <div class="tradaill-subtitle">
            Marine terminal optimization • crane movement simulation • appointment-based yard flow
        </div>
    </div>
    """, unsafe_allow_html=True)

st.info(
    "Tradaill integrates terminal operations, truck scheduling, and compliance workflows "
    "through coordinated yard optimization."
)

# -----------------------------
# Sidebar Inputs
# -----------------------------

st.sidebar.header("Terminal Layout")

yard_blocks = st.sidebar.number_input("Yard blocks / stacks", min_value=1, value=25)
block_bays = st.sidebar.number_input("Containers long per block", min_value=1, value=12)
block_rows = st.sidebar.number_input("Containers wide per block", min_value=1, value=3)
max_stack_height = st.sidebar.number_input("Max stack height", min_value=1, value=6)

crane_corridors = st.sidebar.number_input("Crane corridors", min_value=1, value=5)
truck_roads = st.sidebar.number_input("Truck receiving roads", min_value=1, value=2)

st.sidebar.header("Vessel Flow")

vessels_per_week = st.sidebar.number_input("Vessels per week", min_value=0, value=2)
imports_per_vessel = st.sidebar.slider("Import containers discharged per vessel", 100, 1000, 500)
exports_per_week = st.sidebar.number_input("Export containers received per week", min_value=0, value=450)
empty_returns_per_week = st.sidebar.number_input("Empty returns per week", min_value=0, value=350)

st.sidebar.header("Dwell Time")

import_dwell_days = st.sidebar.slider("Average import dwell days", 1, 14, 4)
export_dwell_days = st.sidebar.slider("Average export dwell days", 1, 14, 3)
empty_dwell_days = st.sidebar.slider("Average empty dwell days", 1, 30, 7)

st.sidebar.header("Equipment")

rtgs = st.sidebar.number_input("RTG cranes", min_value=0, value=3)
rmgs = st.sidebar.number_input("RMG cranes", min_value=0, value=1)
straddles = st.sidebar.number_input("Straddle carriers", min_value=0, value=4)

rtg_moves_per_hour = st.sidebar.number_input("RTG moves/hour", min_value=1, value=22)
rmg_moves_per_hour = st.sidebar.number_input("RMG moves/hour", min_value=1, value=28)
straddle_moves_per_hour = st.sidebar.number_input("Straddle moves/hour", min_value=1, value=14)

equipment_hours_per_day = st.sidebar.number_input("Equipment operating hours/day", min_value=1, value=16)

st.sidebar.header("Truck Appointment Model")

pickup_days_per_week = st.sidebar.number_input("Pickup days/week", min_value=1, max_value=7, value=6)
pickup_hours_per_day = st.sidebar.number_input("Pickup hours/day", min_value=1, value=8)
truck_slots_per_hour = st.sidebar.number_input("Truck slots/hour", min_value=1, value=45)

appointment_model = st.sidebar.selectbox(
    "Pickup model",
    ["Free-Time / Random Pickup", "RAV Appointment-Based Pickup"]
)

st.sidebar.header("Operational Assumptions")

customs_hold_rate = st.sidebar.slider("Customs/document hold rate", 0.0, 0.5, 0.08)
late_truck_rate = st.sidebar.slider("Late / missed appointment rate", 0.0, 0.5, 0.12)
yard_imbalance = st.sidebar.slider("Yard imbalance / poor distribution", 0.0, 1.0, 0.35)

# -----------------------------
# Core Calculations
# -----------------------------

yard_capacity = yard_blocks * block_bays * block_rows * max_stack_height

weekly_imports = vessels_per_week * imports_per_vessel
weekly_volume = weekly_imports + exports_per_week + empty_returns_per_week

avg_daily_imports = weekly_imports / 7
avg_daily_exports = exports_per_week / 7
avg_daily_empties = empty_returns_per_week / 7

avg_yard_inventory = (
    avg_daily_imports * import_dwell_days
    + avg_daily_exports * export_dwell_days
    + avg_daily_empties * empty_dwell_days
)

yard_utilization = avg_yard_inventory / yard_capacity if yard_capacity else 0

truck_weekly_capacity = pickup_days_per_week * pickup_hours_per_day * truck_slots_per_hour
truck_capacity_ratio = truck_weekly_capacity / weekly_imports if weekly_imports else 1

weekly_equipment_capacity = (
    rtgs * rtg_moves_per_hour
    + rmgs * rmg_moves_per_hour
    + straddles * straddle_moves_per_hour
) * equipment_hours_per_day * 7

# -----------------------------
# More Realistic Move Logic
# -----------------------------

def congestion_multiplier(utilization):
    if utilization < 0.55:
        return 1.0
    if utilization < 0.75:
        return 1.15
    if utilization < 0.90:
        return 1.35
    return 1.70

def random_pickup_penalty(model):
    return 1.0 if model == "RAV Appointment-Based Pickup" else 1.28

def hold_penalty(hold_rate):
    return 1 + hold_rate * 1.8

def imbalance_penalty(imbalance):
    return 1 + imbalance * 0.55

def straddle_flex_credit(straddles):
    return min(0.28, straddles * 0.035)

def appointment_credit(model):
    return 0.26 if model == "RAV Appointment-Based Pickup" else 0.08

base_lift_moves = weekly_volume

baseline_rehandle_rate = (
    0.18
    * congestion_multiplier(yard_utilization)
    * random_pickup_penalty("Free-Time / Random Pickup")
    * hold_penalty(customs_hold_rate)
    * imbalance_penalty(yard_imbalance)
)

optimized_rehandle_rate = (
    0.18
    * congestion_multiplier(yard_utilization)
    * random_pickup_penalty(appointment_model)
    * hold_penalty(customs_hold_rate * 0.65)
    * imbalance_penalty(yard_imbalance * 0.55)
)

optimized_rehandle_rate = max(
    0.04,
    optimized_rehandle_rate - straddle_flex_credit(straddles) - appointment_credit(appointment_model)
)

baseline_rehandles = weekly_volume * baseline_rehandle_rate
optimized_rehandles = weekly_volume * optimized_rehandle_rate

baseline_total_moves = base_lift_moves + baseline_rehandles
optimized_total_moves = base_lift_moves + optimized_rehandles

equipment_utilization_baseline = baseline_total_moves / weekly_equipment_capacity if weekly_equipment_capacity else 0
equipment_utilization_optimized = optimized_total_moves / weekly_equipment_capacity if weekly_equipment_capacity else 0

# -----------------------------
# Truck Wait Logic
# -----------------------------

baseline_wait = (
    25
    + yard_utilization * 65
    + equipment_utilization_baseline * 35
    + late_truck_rate * 90
    + yard_imbalance * 30
)

optimized_wait = (
    18
    + yard_utilization * 42
    + equipment_utilization_optimized * 24
    + late_truck_rate * 45
    + yard_imbalance * 16
)

if appointment_model == "RAV Appointment-Based Pickup":
    optimized_wait *= 0.72

truck_capacity_warning = truck_capacity_ratio < 1

# -----------------------------
# Dashboard
# -----------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Static Yard Capacity", f"{yard_capacity:,.0f} slots")
col2.metric("Avg Yard Inventory", f"{avg_yard_inventory:,.0f} containers")
col3.metric("Yard Utilization", f"{yard_utilization:.1%}")
col4.metric("Weekly Volume", f"{weekly_volume:,.0f}")

st.divider()

if yard_utilization > 0.90:
    st.error("Yard is operating above 90% utilization. Severe congestion is likely.")
elif yard_utilization > 0.75:
    st.warning("Yard is approaching high utilization. Rehandles and truck delays will increase.")
else:
    st.success("Yard utilization is within a manageable operating range.")

if truck_capacity_warning:
    st.warning("Truck appointment capacity is lower than weekly import volume. Pickup backlog is likely.")

st.subheader("Free-Time vs Optimized Terminal Flow")

results = pd.DataFrame({
    "Metric": [
        "Base lift moves",
        "Estimated rehandles",
        "Total equipment moves",
        "Rehandle rate",
        "Equipment utilization",
        "Average truck wait",
        "Weekly truck pickup capacity"
    ],
    "Free-Time Model": [
        round(base_lift_moves, 0),
        round(baseline_rehandles, 0),
        round(baseline_total_moves, 0),
        f"{baseline_rehandle_rate:.1%}",
        f"{equipment_utilization_baseline:.1%}",
        f"{baseline_wait:.1f} min",
        f"{truck_weekly_capacity:,.0f}"
    ],
    "Optimized Model": [
        round(base_lift_moves, 0),
        round(optimized_rehandles, 0),
        round(optimized_total_moves, 0),
        f"{optimized_rehandle_rate:.1%}",
        f"{equipment_utilization_optimized:.1%}",
        f"{optimized_wait:.1f} min",
        f"{truck_weekly_capacity:,.0f}"
    ]
})

st.dataframe(results, use_container_width=True)

st.subheader("Estimated Improvement")

c1, c2, c3 = st.columns(3)

c1.metric("Move Reduction", f"{baseline_total_moves - optimized_total_moves:,.0f}")
c2.metric("Rehandle Reduction", f"{baseline_rehandles - optimized_rehandles:,.0f}")
c3.metric("Truck Wait Reduction", f"{baseline_wait - optimized_wait:.1f} min")

st.divider()

st.subheader("Terminal Flow Breakdown")

flow_df = pd.DataFrame({
    "Flow Type": ["Import Fulls", "Export Fulls", "Empty Returns"],
    "Weekly Volume": [weekly_imports, exports_per_week, empty_returns_per_week],
    "Average Dwell Days": [import_dwell_days, export_dwell_days, empty_dwell_days],
    "Estimated Yard Inventory": [
        avg_daily_imports * import_dwell_days,
        avg_daily_exports * export_dwell_days,
        avg_daily_empties * empty_dwell_days,
    ]
})

st.dataframe(flow_df, use_container_width=True)

st.subheader("Equipment Capacity")

equipment_df = pd.DataFrame({
    "Equipment": ["RTG", "RMG", "Straddle Carrier"],
    "Units": [rtgs, rmgs, straddles],
    "Moves / Hour / Unit": [rtg_moves_per_hour, rmg_moves_per_hour, straddle_moves_per_hour],
    "Weekly Capacity": [
        rtgs * rtg_moves_per_hour * equipment_hours_per_day * 7,
        rmgs * rmg_moves_per_hour * equipment_hours_per_day * 7,
        straddles * straddle_moves_per_hour * equipment_hours_per_day * 7,
    ]
})

st.dataframe(equipment_df, use_container_width=True)

st.subheader("Estimated Yard Block Utilization")

np.random.seed(7)
block_ids = [f"Block {i+1}" for i in range(yard_blocks)]

block_utilization = np.clip(
    np.random.normal(loc=yard_utilization, scale=0.10 + yard_imbalance * 0.08, size=yard_blocks),
    0,
    1
)

yard_df = pd.DataFrame({
    "Block": block_ids,
    "Utilization": block_utilization,
    "Estimated Containers": (
        block_utilization * block_bays * block_rows * max_stack_height
    ).round(0)
})

st.bar_chart(yard_df.set_index("Block")["Utilization"])
st.dataframe(yard_df, use_container_width=True)

st.subheader("Model Logic")

logic = pd.DataFrame({
    "Component": [
        "Yard Utilization",
        "Dwell Time",
        "Truck Appointment Capacity",
        "Equipment Capacity",
        "Customs Hold Rate",
        "Straddle Carrier Flexibility",
        "Yard Imbalance"
    ],
    "How It Affects the Model": [
        "Higher utilization increases congestion, rehandles, and wait time.",
        "Longer dwell time increases average yard inventory even if weekly vessel volume stays constant.",
        "If pickup capacity is below import volume, the model flags backlog risk.",
        "RTG, RMG, and straddle productivity determines how many weekly moves the terminal can absorb.",
        "Held containers create inefficient stacking and reduce access to released containers.",
        "Straddles reduce rehandle pressure because they can recover containers across the yard.",
        "Uneven distribution increases travel time, buried containers, and congestion."
    ]
})

st.dataframe(logic, use_container_width=True)

output = pd.DataFrame([{
    "yard_capacity": yard_capacity,
    "avg_yard_inventory": avg_yard_inventory,
    "yard_utilization": yard_utilization,
    "weekly_volume": weekly_volume,
    "weekly_imports": weekly_imports,
    "exports_per_week": exports_per_week,
    "empty_returns_per_week": empty_returns_per_week,
    "baseline_total_moves": baseline_total_moves,
    "optimized_total_moves": optimized_total_moves,
    "baseline_rehandles": baseline_rehandles,
    "optimized_rehandles": optimized_rehandles,
    "baseline_wait_minutes": baseline_wait,
    "optimized_wait_minutes": optimized_wait,
    "weekly_equipment_capacity": weekly_equipment_capacity,
    "truck_weekly_capacity": truck_weekly_capacity,
}])

csv = output.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Simulation Results CSV",
    csv,
    "tradaill_terminal_simulation_results.csv",
    "text/csv"
)

st.caption("Prototype simulator. Results are estimated and should be calibrated against actual terminal move logs, truck turn times, dwell data, and equipment productivity.")
