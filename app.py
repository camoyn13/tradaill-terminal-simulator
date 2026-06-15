import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Tradaill Terminal Simulator", layout="wide")

st.title("Tradaill Terminal Simulator")
st.caption("Marine terminal sorting, crane movement, and pickup scheduling simulator")

st.sidebar.header("Terminal Setup")

stacks = st.sidebar.number_input("Number of stacks", min_value=1, value=25)
stack_length = st.sidebar.number_input("Stack length", min_value=1, value=12)
stack_width = st.sidebar.number_input("Stack width", min_value=1, value=3)
max_height = st.sidebar.number_input("Max stack height", min_value=1, value=6)

st.sidebar.header("Equipment")

rtgs = st.sidebar.number_input("RTG cranes", min_value=0, value=3)
rmgs = st.sidebar.number_input("RMG cranes", min_value=0, value=1)
straddles = st.sidebar.number_input("Straddle carriers", min_value=0, value=4)

st.sidebar.header("Weekly Volume")

vessels_per_week = st.sidebar.number_input("Vessels per week", min_value=0, value=2)
containers_per_vessel = st.sidebar.slider("Containers discharged per vessel", 100, 1000, 500)
export_containers = st.sidebar.number_input("Export containers per week", min_value=0, value=400)
empty_returns = st.sidebar.number_input("Empty returns per week", min_value=0, value=350)

st.sidebar.header("Pickup Model")

pickup_model = st.sidebar.selectbox(
    "Pickup model",
    ["Free-Time / Random Pickup", "RAV Appointment-Based Pickup"]
)

yard_capacity = stacks * stack_length * stack_width * max_height
weekly_imports = vessels_per_week * containers_per_vessel
weekly_volume = weekly_imports + export_containers + empty_returns
yard_utilization = weekly_volume / yard_capacity if yard_capacity else 0

equipment_count = max(1, rtgs + rmgs + straddles)

baseline_moves_per_container = 2.8
baseline_rehandle_rate = 0.42
baseline_wait = 72

if pickup_model == "RAV Appointment-Based Pickup":
    optimized_moves_per_container = 1.75
    optimized_rehandle_rate = 0.22
    optimized_wait = 34
else:
    optimized_moves_per_container = 2.25
    optimized_rehandle_rate = 0.34
    optimized_wait = 55

equipment_efficiency = min(1.35, 1 + equipment_count / 20)
straddle_bonus = 1 + straddles * 0.035

optimized_moves_per_container /= equipment_efficiency
optimized_rehandle_rate /= straddle_bonus
optimized_wait /= straddle_bonus

baseline_moves = weekly_volume * baseline_moves_per_container
optimized_moves = weekly_volume * optimized_moves_per_container

baseline_rehandles = weekly_volume * baseline_rehandle_rate
optimized_rehandles = weekly_volume * optimized_rehandle_rate

col1, col2, col3, col4 = st.columns(4)

col1.metric("Yard Capacity", f"{yard_capacity:,.0f} slots")
col2.metric("Weekly Volume", f"{weekly_volume:,.0f} containers")
col3.metric("Yard Utilization", f"{yard_utilization:.1%}")
col4.metric("Equipment Units", f"{equipment_count}")

st.divider()

st.subheader("Free-Time vs Optimized Terminal Flow")

results = pd.DataFrame({
    "Metric": [
        "Weekly equipment moves",
        "Weekly rehandles",
        "Average truck wait time",
        "Moves per container",
        "Rehandle rate"
    ],
    "Free-Time Model": [
        round(baseline_moves, 0),
        round(baseline_rehandles, 0),
        f"{baseline_wait:.1f} min",
        baseline_moves_per_container,
        f"{baseline_rehandle_rate:.1%}"
    ],
    "Optimized Model": [
        round(optimized_moves, 0),
        round(optimized_rehandles, 0),
        f"{optimized_wait:.1f} min",
        round(optimized_moves_per_container, 2),
        f"{optimized_rehandle_rate:.1%}"
    ]
})

st.dataframe(results, use_container_width=True)

st.subheader("Estimated Improvement")

c1, c2, c3 = st.columns(3)

c1.metric("Move Reduction", f"{baseline_moves - optimized_moves:,.0f}")
c2.metric("Rehandle Reduction", f"{baseline_rehandles - optimized_rehandles:,.0f}")
c3.metric("Truck Wait Reduction", f"{baseline_wait - optimized_wait:.1f} min")

st.divider()

st.subheader("Sorting Logic")

logic = pd.DataFrame({
    "Method": [
        "Pickup-Time Layering",
        "Weight-Safe Stacking",
        "Compliance-Aware Sorting",
        "Straddle Carrier Recovery",
        "Crane Corridor Minimization",
        "Export Load Sequencing",
        "Empty Return Pooling"
    ],
    "Purpose": [
        "Earlier pickup appointments receive more accessible positions.",
        "Heavier containers are placed lower in the stack.",
        "TIQ-cleared containers receive priority access.",
        "Straddle carriers recover misplaced containers across the yard.",
        "Containers are grouped near the most efficient equipment corridor.",
        "Export containers are staged by vessel cutoff and load sequence.",
        "Empty containers are grouped in lower-priority areas unless needed for exports."
    ]
})

st.dataframe(logic, use_container_width=True)

st.subheader("Estimated Yard Block Utilization")

np.random.seed(7)
block_ids = [f"Block {i+1}" for i in range(stacks)]
utilization = np.clip(
    np.random.normal(loc=yard_utilization, scale=0.12, size=stacks),
    0,
    1
)

yard_df = pd.DataFrame({
    "Block": block_ids,
    "Utilization": utilization,
    "Estimated Containers": (utilization * stack_length * stack_width * max_height).round(0)
})

st.bar_chart(yard_df.set_index("Block")["Utilization"])
st.dataframe(yard_df, use_container_width=True)

st.caption("Prototype model. Results are estimated and should be calibrated with real terminal operating data.")
