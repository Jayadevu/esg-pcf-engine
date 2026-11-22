import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Scope 3 Packaging PCF Engine (CSRD ESRS E1)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM STYLING FOR EXECUTIVE LOOK, AUTO-WIDTH TABLES & TAKEAWAYS ---
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 15px 20px;
        border-radius: 10px;
    }
    /* Clean, auto-width centered tables without stretched whitespace */
    .centered-audit-table {
        width: auto;
        min-width: 65%;
        border-collapse: collapse;
        margin: 15px auto;
        font-size: 14px;
        background-color: #161B22;
        color: #C9D1D9;
        border-radius: 8px;
        overflow: hidden;
    }
    .centered-audit-table th, .centered-audit-table td {
        border: 1px solid #30363D;
        padding: 10px 18px;
        text-align: center !important;
    }
    .centered-audit-table th {
        background-color: #21262D;
        font-weight: 600;
        color: #F0F6FC;
    }
    .centered-audit-table tr:nth-child(even) {
        background-color: #111418;
    }
    /* Executive Takeaways Banner */
    .takeaway-box {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border-left: 4px solid #2ea043;
        padding: 16px 20px;
        border-radius: 6px;
        margin-bottom: 25px;
        color: #F0F6FC;
        font-size: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("Scope 3 Logistics & Packaging PCF Engine")
st.markdown(
    "**ISO 14067 & GHG Protocol (Categories 1, 4, 5, 9)** | "
    "Cradle-to-Customer Product Carbon Footprint Model for E-Commerce Beverage Fulfillment"
)

# --- EXECUTIVE TAKEAWAYS BANNER ---
st.markdown("""
<div class="takeaway-box">
    <strong>🎯 Executive Takeaways for Hiring Managers:</strong><br>
    • <strong>Bottom-Up Primary Data:</strong> Bypasses generic secondary estimates by integrating physical box geometry[cite: 7] and gravimetric tape roll audits (151g net PP)[cite: 8, 9].<br>
    • <strong>German Pfand (Mehrweg) Integration:</strong> Amortizes container glass manufacturing across 30 rotation cycles, reflecting real-world circular infrastructure.<br>
    • <strong>Regulatory Alignment:</strong> Fully structured for <strong>CSRD / ESRS E1</strong> mandatory disclosure and ISO 14067 life cycle verification.
</div>
""", unsafe_allow_html=True)

# --- 1. CONSTANTS: EMISSION FACTORS (kg CO2e per unit) ---
VDW_PROBAS_CORRUGATED_EF = 0.491
UBA_PROBAS_GLASS_EF = 0.85
ECOINVENT_BREWING_EF = 0.70
PROBAS_PLASTIC_TAPE_EF = 1.95
PROBAS_ADHESIVE_LABEL_EF = 1.15
PROBAS_WASTE_INCINERATION_EF = 0.33  # Cat 5: Mixed commercial waste incineration
HGV_DIESEL_TONNE_KM_EF = 0.111       # Cat 4: HGV Diesel Truck (per tonne-kilometer)
DHL_GOGREEN_NET_EF = 0.0             # Cat 9: DHL GoGreen certified net-zero delivery

# --- 2. EMPIRICAL ACTIVITY DATA (Measured & Operational) ---
DISTANCE_COBURG_INBOUND_KM = 75

BOX_DIMENSIONS = {
    "6-bottle": "29 × 21 × 34 cm (0.46 m²)",
    "12-bottle": "41 × 29 × 34 cm (0.71 m²)",
    "18-bottle": "60 × 29 × 34 cm (0.95 m²)"
}

WEIGHTS = {
    "box_6_bottle": 0.38,
    "box_12_bottle": 0.79,
    "box_18_bottle": 0.85,
    "insert_module": 0.15,
    "glass_bottle_05L_kg": 0.35,
    "beer_liquid_volume_L": 0.5,
    "tape_6_bottle_kg": 0.015,
    "tape_12_bottle_kg": 0.020,
    "tape_18_bottle_kg": 0.030,
    "hazard_sticker_kg": 0.004,
    "shipping_label_kg": 0.003,
    "packing_waste_kg": 0.010
}

# --- 3. SIDEBAR: INTERACTIVE SCENARIO CONTROLS ---
st.sidebar.header("Scenario Parameters")
order_type = st.sidebar.selectbox("Packaging Variant", ["6-bottle", "12-bottle", "18-bottle"], index=2)
st.sidebar.caption(f"Measured Geometry: **{BOX_DIMENSIONS[order_type]}**")

# Pfand & Bottle System Toggle
bottle_system = st.sidebar.radio(
    "Glass Lifecycle System", 
    ["Reusable (Mehrweg - 30x Avg Cycles)", "Single-Use (Einweg - 1x Cycle)"],
    index=0
)

monthly_order_volume = st.sidebar.number_input("Monthly Shipment Volume (Orders)", value=1200, step=100)
custom_distance = st.sidebar.slider("Inbound Brewery Distance (km)", 20, 300, DISTANCE_COBURG_INBOUND_KM)
enable_gogreen = st.sidebar.toggle("DHL GoGreen Outbound Offset (Cat. 9)", value=True)

st.sidebar.divider()
st.sidebar.info(
    "**Methodology Standard:**\n"
    "• GHG Protocol Scope 3\n"
    "• CSRD / ESRS E1 Ready\n"
    "• ISO 14067 System Boundary"
)

# --- 4. CALCULATION ENGINE ---
def calculate_full_scope3_pcf(order_type, distance_km, gogreen_active, system_choice):
    if order_type == '6-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_6_bottle"], 1, 6, WEIGHTS["tape_6_bottle_kg"]
    elif order_type == '12-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_12_bottle"], 2, 12, WEIGHTS["tape_12_bottle_kg"]
    elif order_type == '18-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_18_bottle"], 3, 18, WEIGHTS["tape_18_bottle_kg"]
    else:
        raise ValueError("Invalid configuration")

    # Allocation multiplier based on Pfand system
    if "Mehrweg" in system_choice:
        glass_allocation_multiplier = 1.0 / 30.0  # Amortized across 30 average cycles
    else:
        glass_allocation_multiplier = 1.0        # Full burden for single-use

    # Category 1: Purchased Goods (Packaging + Beer)
    cardboard_kg = outer_box + (inserts * WEIGHTS["insert_module"])
    co2_cardboard = cardboard_kg * VDW_PROBAS_CORRUGATED_EF
    co2_tape = tape * PROBAS_PLASTIC_TAPE_EF
    co2_labels = (WEIGHTS["hazard_sticker_kg"] + WEIGHTS["shipping_label_kg"]) * PROBAS_ADHESIVE_LABEL_EF
    packaging_pcf = co2_cardboard + co2_tape + co2_labels

    # Product PCF with Amortized Glass Allocation
    single_beer_pcf = (WEIGHTS["glass_bottle_05L_kg"] * UBA_PROBAS_GLASS_EF * glass_allocation_multiplier) + \
                      (WEIGHTS["beer_liquid_volume_L"] * ECOINVENT_BREWING_EF)
    product_pcf = single_beer_pcf * bottles

    # Category 5: Operational Waste
    waste_pcf = WEIGHTS["packing_waste_kg"] * PROBAS_WASTE_INCINERATION_EF

    # Category 4: Inbound Transport (Coburg to Warehouse)
    beer_weight_tonnes = ((WEIGHTS["glass_bottle_05L_kg"] + WEIGHTS["beer_liquid_volume_L"]) * bottles) / 1000.0
    inbound_tkm = beer_weight_tonnes * distance_km
    inbound_transport_pcf = inbound_tkm * HGV_DIESEL_TONNE_KM_EF

    # Category 9: Outbound Transport (DHL to Customer)
    outbound_transport_pcf = DHL_GOGREEN_NET_EF if gogreen_active else 0.052

    total_order_pcf = packaging_pcf + product_pcf + waste_pcf + inbound_transport_pcf + outbound_transport_pcf

    return {
        "cat1_packaging": round(packaging_pcf, 4),
        "cat1_product": round(product_pcf, 4),
        "cat5_waste": round(waste_pcf, 4),
        "cat4_inbound": round(inbound_transport_pcf, 4),
        "cat9_outbound": round(outbound_transport_pcf, 4),
        "total_co2e": round(total_order_pcf, 4),
        "per_bottle_co2e": round(total_order_pcf / bottles, 4),
        "sub_cardboard": round(co2_cardboard, 4),
        "sub_tape": round(co2_tape, 4),
        "sub_labels": round(co2_labels, 4),
        "cardboard_kg": round(cardboard_kg, 3),
        "inbound_tkm": round(inbound_tkm, 3)
    }

res = calculate_full_scope3_pcf(order_type, custom_distance, enable_gogreen, bottle_system)
annual_total_tonnes = (res['total_co2e'] * monthly_order_volume * 12) / 1000.0

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs([
    "📊 Executive Dashboard & Simulator",
    "⚙️ Engineering Process & LCA Methodology",
    "📚 Emission Factor & LCI Registry"
])

# ==============================================================================
# TAB 1: EXECUTIVE DASHBOARD
# ==============================================================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Batch PCF", f"{res['total_co2e']} kg CO₂e", f"{res['per_bottle_co2e']} kg CO₂e / bottle")
    col2.metric("Annualized Scope 3", f"{annual_total_tonnes:.2f} t CO₂e", f"{monthly_order_volume:,} orders / mo")
    col3.metric("Product Share (Cat. 1)", f"{(res['cat1_product'] / res['total_co2e']) * 100:.1f}%", "Glass & Brewing")
    col4.metric("Packaging & Logistics", f"{((res['total_co2e'] - res['cat1_product']) / res['total_co2e']) * 100:.1f}%", "Controllable Operations")

    st.divider()

    chart_col1, chart_col2 = st.columns(2)

    df_audit = pd.DataFrame({
        "Scope 3 Category": [
            "Cat. 1: Product (Beer & Glass)",
            "Cat. 1: Packaging Materials",
            "Cat. 4: Inbound Freight (HGV)",
            "Cat. 5: Operational Waste",
            "Cat. 9: Outbound Freight (DHL)"
        ],
        "Emissions (kg CO2e)": [
            res['cat1_product'],
            res['cat1_packaging'],
            res['cat4_inbound'],
            res['cat5_waste'],
            res['cat9_outbound']
        ]
    })

    with chart_col1:
        st.subheader("1. Full Value-Chain Split")
        fig_total = px.pie(
            df_audit,
            names="Scope 3 Category",
            values="Emissions (kg CO2e)",
            hole=0.48,
            color_discrete_sequence=px.colors.sequential.Tealgrn
        )
        fig_total.update_traces(textposition="inside", textinfo="percent")
        fig_total.update_layout(margin=dict(t=10, b=10, l=10, r=1
