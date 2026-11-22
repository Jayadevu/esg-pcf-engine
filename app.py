import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Scope 3 Packaging PCF Engine | CSRD ESRS E1",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM EXECUTIVE SaaS STYLING ---
st.markdown("""
    <style>
    .block-container {padding-top: 1.8rem; padding-bottom: 2.5rem;}
    
    /* Sleek KPI Cards with Emerald Top Accent */
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #161E2E 0%, #111827 100%);
        border: 1px solid #1F2937;
        border-top: 3px solid #10B981;
        padding: 16px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #064E3B 0%, #111827 65%, #1E293B 100%);
        border: 1px solid #059669;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 22px;
        color: #F9FAFB;
    }
    .hero-banner h3 {
        margin: 0 0 8px 0;
        color: #34D399;
        font-size: 18px;
    }
    .hero-banner p {
        margin: 0;
        font-size: 14px;
        line-height: 1.6;
        color: #E5E7EB;
    }

    /* Clean Auto-Width Centered Audit Tables */
    .centered-audit-table {
        width: auto;
        min-width: 70%;
        border-collapse: collapse;
        margin: 15px auto;
        font-size: 14px;
        background-color: #111827;
        color: #E5E7EB;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    .centered-audit-table th, .centered-audit-table td {
        border: 1px solid #1F2937;
        padding: 11px 20px;
        text-align: center !important;
    }
    .centered-audit-table th {
        background-color: #1F2937;
        font-weight: 600;
        color: #34D399;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.05em;
    }
    .centered-audit-table tr:nth-child(even) {
        background-color: #0F172A;
    }

    /* --- FORCED HIGH-VISIBILITY PILL TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px !important;
        background-color: #111827 !important;
        padding: 12px 16px !important;
        border-radius: 14px !important;
        border: 1px solid #374151 !important;
        margin-bottom: 22px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px !important;
        background-color: #1F2937 !important;
        color: #E5E7EB !important;
        border: 1px solid #4B5563 !important;
        border-radius: 8px !important;
        padding: 0 24px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #374151 !important;
        border-color: #10B981 !important;
        color: #FFFFFF !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
        color: #0B0F19 !important;
        border-color: #34D399 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER & CASE STUDY CONTEXT BANNER ---
st.title("🌱 Scope 3 Logistics & Packaging PCF Engine")
st.caption("ISO 14067 & GHG Protocol (Categories 1, 4, 5, 9) • Cradle-to-Customer Carbon Intelligence for Beverage Fulfillment")

st.markdown("""
<div class="hero-banner">
    <h3>📦 Case Study Context: German E-Commerce Beverage Fulfillment</h3>
    <p style="margin-bottom: 12px;">
        <strong>The Challenge:</strong> Beverage distributors under <strong>CSRD / ESRS E1</strong> mandates must report Scope 3 emissions, yet generic spend-based estimates mask real operational hotspots. This engine models a live regional fulfillment workflow—from inbound brewery freight (Coburg, 75 km) through warehouse pick-and-pack (6-, 12-, and 18-bottle cartons) to last-mile <strong>DHL GoGreen</strong> delivery.<br>
        <strong>The Goal:</strong> Separate direct, controllable warehouse packaging emissions from circular product footprints (Germany's <em>Pfand / Mehrweg</em> glass pool) to guide data-driven decarbonization.
    </p>
    <hr style="border-color: rgba(52, 211, 153, 0.3); margin: 10px 0;">
    <p>
        • <strong>Bottom-Up Primary LCI:</strong> Built from direct physical carton dimensioning and gravimetric tape roll audits (151g net PP film/roll).<br>
        • <strong>Circular Pfand Modeling:</strong> Amortizes container glass manufacturing across 30 reuse rotations vs. single-use (<em>Einweg</em>) baselines.<br>
        • <strong>Audit-Ready Output:</strong> Maps activity data directly to GHG Protocol Scope 3 (Cat. 1, 4, 5, 9) with one-click CSV ledger exports.
    </p>
</div>
""", unsafe_allow_html=True)

# --- 1. CONSTANTS: EMISSION FACTORS (kg CO2e per unit) ---
VDW_PROBAS_CORRUGATED_EF = 0.491
UBA_PROBAS_GLASS_EF = 0.85
ECOINVENT_BREWING_EF = 0.70
PROBAS_PLASTIC_TAPE_EF = 1.95
PROBAS_ADHESIVE_LABEL_EF = 1.15
PROBAS_WASTE_INCINERATION_EF = 0.33
HGV_DIESEL_TONNE_KM_EF = 0.111
DHL_GOGREEN_NET_EF = 0.0

# --- 2. EMPIRICAL ACTIVITY DATA ---
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
st.sidebar.header("⚙️ Scenario Parameters")
order_type = st.sidebar.selectbox("Packaging Variant", ["6-bottle", "12-bottle", "18-bottle"], index=2)
st.sidebar.caption(f"Measured Carton: **{BOX_DIMENSIONS[order_type]}**")

bottle_system = st.sidebar.radio(
    "Glass Lifecycle System (Pfand)",
    ["Reusable (Mehrweg - 30x Cycles)", "Single-Use (Einweg - 1x Cycle)"],
    index=0
)

monthly_order_volume = st.sidebar.number_input("Monthly Shipment Volume (Orders)", value=1200, step=100)
custom_distance = st.sidebar.slider("Inbound Brewery Distance (km)", 20, 300, DISTANCE_COBURG_INBOUND_KM)
enable_gogreen = st.sidebar.toggle("DHL GoGreen Outbound Offset (Cat. 9)", value=True)

st.sidebar.divider()
st.sidebar.success(
    "**Compliance Boundaries:**\n"
    "• GHG Protocol Scope 3\n"
    "• CSRD / ESRS E1 Aligned\n"
    "• ISO 14067 System Boundary"
)

# --- 4. CALCULATION ENGINE ---
def calculate_full_scope3_pcf(variant, distance_km, gogreen_active, system_choice):
    if variant == '6-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_6_bottle"], 1, 6, WEIGHTS["tape_6_bottle_kg"]
    elif variant == '12-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_12_bottle"], 2, 12, WEIGHTS["tape_12_bottle_kg"]
    elif variant == '18-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_18_bottle"], 3, 18, WEIGHTS["tape_18_bottle_kg"]
    else:
        raise ValueError("Invalid configuration")

    glass_multiplier = (1.0 / 30.0) if "Mehrweg" in system_choice else 1.0

    # Category 1: Packaging
    cardboard_kg = outer_box + (inserts * WEIGHTS["insert_module"])
    co2_cardboard = cardboard_kg * VDW_PROBAS_CORRUGATED_EF
    co2_tape = tape * PROBAS_PLASTIC_TAPE_EF
    co2_labels = (WEIGHTS["hazard_sticker_kg"] + WEIGHTS["shipping_label_kg"]) * PROBAS_ADHESIVE_LABEL_EF
    packaging_pcf = co2_cardboard + co2_tape + co2_labels

    # Category 1: Product (Glass + Brewing)
    co2_glass = (WEIGHTS["glass_bottle_05L_kg"] * UBA_PROBAS_GLASS_EF * glass_multiplier) * bottles
    co2_liquid = (WEIGHTS["beer_liquid_volume_L"] * ECOINVENT_BREWING_EF) * bottles
    product_pcf = co2_glass + co2_liquid

    # Category 5: Waste
    waste_pcf = WEIGHTS["packing_waste_kg"] * PROBAS_WASTE_INCINERATION_EF

    # Category 4: Inbound Freight
    beer_weight_tonnes = ((WEIGHTS["glass_bottle_05L_kg"] + WEIGHTS["beer_liquid_volume_L"]) * bottles) / 1000.0
    inbound_tkm = beer_weight_tonnes * distance_km
    inbound_transport_pcf = inbound_tkm * HGV_DIESEL_TONNE_KM_EF

    # Category 9: Outbound Freight
    outbound_transport_pcf = DHL_GOGREEN_NET_EF if gogreen_active else 0.052

    total_order_pcf = packaging_pcf + product_pcf + waste_pcf + inbound_transport_pcf + outbound_transport_pcf

    return {
        "bottles": bottles,
        "cat1_packaging": round(packaging_pcf, 4),
        "cat1_product": round(product_pcf, 4),
        "cat5_waste": round(waste_pcf, 4),
        "cat4_inbound": round(inbound_transport_pcf, 4),
        "cat9_outbound": round(outbound_transport_pcf, 4),
        "total_co2e": round(total_order_pcf, 4),
        "per_bottle_co2e": round(total_order_pcf / bottles, 4),
        "ops_per_bottle": round((packaging_pcf + waste_pcf + inbound_transport_pcf + outbound_transport_pcf) / bottles, 4),
        "sub_cardboard": round(co2_cardboard, 4),
        "sub_tape": round(co2_tape, 4),
        "sub_labels": round(co2_labels, 4),
        "sub_glass": round(co2_glass, 4),
        "sub_liquid": round(co2_liquid, 4)
    }

res = calculate_full_scope3_pcf(order_type, custom_distance, enable_gogreen, bottle_system)
einweg_baseline = calculate_full_scope3_pcf(order_type, custom_distance, enable_gogreen, "Single-Use (Einweg)")
pfand_savings = round(einweg_baseline["total_co2e"] - res["total_co2e"], 4)
annual_total_tonnes = (res['total_co2e'] * monthly_order_volume * 12) / 1000.0

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs([
    "📊 Executive Dashboard & Carbon Flow",
    "⚙️ Engineering Process & LCA Methodology",
    "📚 Emission Factor & LCI Registry"
])

# ==============================================================================
# TAB 1: EXECUTIVE DASHBOARD
# ==============================================================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Total Batch PCF",
        f"{res['total_co2e']} kg CO₂e",
        f"{res['per_bottle_co2e']} kg CO₂e / bottle"
    )
    col2.metric(
        "Annualized Scope 3",
        f"{annual_total_tonnes:.2f} t CO₂e",
        f"{monthly_order_volume:,} orders / mo"
    )
    col3.metric(
        "Pfand Circular Savings",
        f"-{pfand_savings:.3f} kg CO₂e",
        "vs. Single-Use (Einweg)" if pfand_savings > 0 else "Einweg Baseline Active",
        delta_color="normal"
    )
    col4.metric(
        "Controllable Ops Share",
        f"{((res['total_co2e'] - res['cat1_product']) / res['total_co2e']) * 100:.1f}%",
        "Packaging & Freight"
    )

    st.divider()

    # --- SANKEY FLOW DIAGRAM ---
    st.subheader("1. Cradle-to-Customer Carbon Flow (Sankey Allocation)")
    
    sankey_labels = [
        "Brewing Liquid",            # 0
        "Container Glass (Pfand)",   # 1
        "Corrugated Cardboard",      # 2
        "PP Tape & Labels",          # 3
        "Inbound HGV Freight",       # 4
        "Warehouse Waste",           # 5
        "Outbound DHL Freight",      # 6
        "Cat. 1: Product",           # 7
        "Cat. 1: Packaging",         # 8
        "Cat. 4, 5 & 9: Logistics",  # 9
        f"Total Order PCF ({res['total_co2e']} kg)" # 10
    ]

    outbound_val = max(res['cat9_outbound'], 0.0001)

    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18,
            thickness=22,
            line=dict(color="#1F2937", width=1),
            label=sankey_labels,
            color=[
                "#34D399", "#6EE7B7", "#38BDF8", "#7DD3FC",
                "#FBBF24", "#F87171", "#A78BFA",
                "#10B981", "#0284C7", "#D97706", "#059669"
            ]
        ),
        link=dict(
            source=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            target=[7, 7, 8, 8, 9, 9, 9, 10, 10, 10],
            value=[
                res['sub_liquid'],
                max(res['sub_glass'], 0.0001),
                res['sub_cardboard'],
                res['sub_tape'] + res['sub_labels'],
                res['cat4_inbound'],
                res['cat5_waste'],
                outbound_val,
                res['cat1_product'],
                res['cat1_packaging'],
                res['cat4_inbound'] + res['cat5_waste'] + outbound_val
            ],
            color="rgba(16, 185, 129, 0.22)"
        )
    )])
    fig_sankey.update_layout(
        height=340,
        margin=dict(t=15, b=15, l=15, r=15),
        paper_bgcolor="rgba(0,0,0,
