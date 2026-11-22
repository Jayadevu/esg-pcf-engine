import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Scope 3 Packaging PCF Engine (CSRD ESRS E1)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM STYLING FOR CLEAN EXECUTIVE LOOK ---
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 15px 20px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("Scope 3 Logistics & Packaging PCF Engine")
st.markdown(
    "**ISO 14067 & GHG Protocol (Categories 1, 4, 5, 9)** | "
    "Cradle-to-Customer Product Carbon Footprint Model for E-Commerce Beverage Fulfillment"
)

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
def calculate_full_scope3_pcf(order_type, distance_km, gogreen_active):
    if order_type == '6-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_6_bottle"], 1, 6, WEIGHTS["tape_6_bottle_kg"]
    elif order_type == '12-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_12_bottle"], 2, 12, WEIGHTS["tape_12_bottle_kg"]
    elif order_type == '18-bottle':
        outer_box, inserts, bottles, tape = WEIGHTS["box_18_bottle"], 3, 18, WEIGHTS["tape_18_bottle_kg"]
    else:
        raise ValueError("Invalid configuration")

    # Category 1: Purchased Goods (Packaging + Beer)
    cardboard_kg = outer_box + (inserts * WEIGHTS["insert_module"])
    co2_cardboard = cardboard_kg * VDW_PROBAS_CORRUGATED_EF
    co2_tape = tape * PROBAS_PLASTIC_TAPE_EF
    co2_labels = (WEIGHTS["hazard_sticker_kg"] + WEIGHTS["shipping_label_kg"]) * PROBAS_ADHESIVE_LABEL_EF
    packaging_pcf = co2_cardboard + co2_tape + co2_labels

    single_beer_pcf = (WEIGHTS["glass_bottle_05L_kg"] * UBA_PROBAS_GLASS_EF) + \
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

res = calculate_full_scope3_pcf(order_type, custom_distance, enable_gogreen)
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
        fig_total.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_total, use_container_width=True)

    with chart_col2:
        st.subheader("2. Operational & Packaging Hotspot")
        df_ops = pd.DataFrame({
            "Operational Driver": [
                "Corrugated Box & Inserts",
                "Inbound HGV Transport",
                "PP Adhesive Tape",
                "Labels & Hazard Stickers",
                "Packing Waste Incineration"
            ],
            "kg CO2e": [
                res['sub_cardboard'],
                res['cat4_inbound'],
                res['sub_tape'],
                res['sub_labels'],
                res['cat5_waste']
            ]
        })
        fig_ops = px.bar(
            df_ops,
            x="kg CO2e",
            y="Operational Driver",
            orientation="h",
            text_auto=".4f",
            color="kg CO2e",
            color_continuous_scale="Teal"
        )
        fig_ops.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_ops, use_container_width=True)

    st.subheader("CSRD ESRS E1 Audit Breakdown")
    st.dataframe(df_audit, use_container_width=True, hide_index=True)

    csv_data = df_audit.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSRD Audit Report (CSV)",
        data=csv_data,
        file_name=f"scope3_pcf_{order_type}_audit.csv",
        mime="text/csv",
        use_container_width=True
    )

# ==============================================================================
# TAB 2: ENGINEERING PROCESS & LCA METHODOLOGY
# ==============================================================================
with tab2:
    st.subheader("End-to-End ISO 14067 & GHG Protocol Engineering Workflow")
    st.markdown(
        "This model was engineered from bottom-up **primary operational data** collected directly on the warehouse floor, "
        "following the four-phase Life Cycle Assessment (LCA) framework:"
    )

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.info("### 1. Goal & Scope\n**System Boundary:** Cradle-to-Customer.\n\n**Functional Unit:** 1 fulfilled e-commerce order (6, 12, or 18 × 0.5L bottles) aligned with **GHG Protocol Scope 3**.")
    with p2:
        st.info("### 2. Primary LCI Data\n**Empirical Collection:** Direct physical dimensioning of cartons and digital scale gravimetric testing of tape rolls (183g gross − 32g core = **151g net PP**).")
    with p3:
        st.info("### 3. Secondary EF Mapping\n**German LCI Databases:** Activity mass & tonne-kilometers mapped to verified German factors (**UBA ProBas**, **VDW**, and **Ecoinvent**).")
    with p4:
        st.info("### 4. Impact Aggregation\n**CSRD / ESRS E1 Output:** Automated category aggregation (Cat. 1, 4, 5, 9), hotspot identification, and audit-ready CSV reporting.")

    st.divider()

    st.subheader("Mathematical Formulation (First-Principles Model)")
    f_col1, f_col2 = st.columns(2)

    with f_col1:
        st.markdown("**1. Category 1 — Purchased Goods & Packaging ($E_{\\text{Cat1}}$):**")
        st.latex(r"E_{\text{pack}} = (m_{\text{box}} + n_{\text{ins}} \cdot m_{\text{ins}}) \cdot EF_{\text{VDW}} + m_{\text{tape}} \cdot EF_{\text{PP}} + m_{\text{lbl}} \cdot EF_{\text{lbl}}")
        st.latex(r"E_{\text{prod}} = N_{\text{bottles}} \cdot \left( m_{\text{glass}} \cdot EF_{\text{UBA}} + V_{\text{beer}} \cdot EF_{\text{brew}} \right)")

    with f_col2:
        st.markdown("**2. Categories 4, 5 & 9 — Logistics & End-of-Life ($E_{\\text{Log}}$):**")
        st.latex(r"E_{\text{Cat4}} = \left( \frac{N_{\text{bottles}} \cdot (m_{\text{glass}} + m_{\text{beer}})}{1000} \cdot d_{\text{inbound}} \right) \cdot EF_{\text{HGV}}")
        st.latex(r"E_{\text{Cat5}} = m_{\text{waste}} \cdot EF_{\text{incin}}, \quad E_{\text{Cat9}} = 0 \text{ (DHL GoGreen)}")

    st.divider()

    st.subheader("Empirical Warehouse Data Collection Log")
    st.markdown("""
    - **Carton Geometry & Mass:** Measured external dimensions ($29\\times21\\times34\\text{ cm}$, $41\\times29\\times34\\text{ cm}$, $60\\times29\\times34\\text{ cm}$) and weighed outer boxes ($0.38\\text{ kg}$, $0.79\\text{ kg}$, $0.85\\text{ kg}$) plus modular corrugated dividers ($0.15\\text{ kg/module}$).
    - **Consumable Gravimetric Audit:** Weighed full commercial packaging tape roll ($183\\text{ g}$) vs. spent cardboard core ($32\\text{ g}$) to isolate **$151\\text{ g}$ net polypropylene film** per roll, allocating $15\\text{ g}$, $20\\text{ g}$, and $30\\text{ g}$ per box size.
    - **Inbound Logistics Modeling:** Calculated tonne-kilometers ($\\text{tkm}$) from brewery origin (Coburg, $75\\text{ km}$) using diesel HGV emission factors before applying DHL GoGreen net-zero outbound accounting.
    """)

# ==============================================================================
# TAB 3: EMISSION FACTOR REGISTRY
# ==============================================================================
with tab3:
    st.subheader("Verified Emission Factor & Activity Registry")
    ef_table = pd.DataFrame([
        {"Parameter": "Corrugated Cardboard (Box & Inserts)", "Scope 3 Cat.": "Cat. 1", "Value": VDW_PROBAS_CORRUGATED_EF, "Unit": "kg CO₂e / kg", "Source": "VDW / UBA ProBas"},
        {"Parameter": "Container Glass (0.5L Bottle)", "Scope 3 Cat.": "Cat. 1", "Value": UBA_PROBAS_GLASS_EF, "Unit": "kg CO₂e / kg", "Source": "UBA ProBas"},
        {"Parameter": "Brewing Process (0.5L Liquid)", "Scope 3 Cat.": "Cat. 1", "Value": ECOINVENT_BREWING_EF, "Unit": "kg CO₂e / L", "Source": "Ecoinvent v3"},
        {"Parameter": "Polypropylene Packaging Tape", "Scope 3 Cat.": "Cat. 1", "Value": PROBAS_PLASTIC_TAPE_EF, "Unit": "kg CO₂e / kg", "Source": "UBA ProBas"},
        {"Parameter": "Thermal & Hazard Adhesive Labels", "Scope 3 Cat.": "Cat. 1", "Value": PROBAS_ADHESIVE_LABEL_EF, "Unit": "kg CO₂e / kg", "Source": "UBA ProBas"},
        {"Parameter": "Inbound Diesel HGV Freight", "Scope 3 Cat.": "Cat. 4", "Value": HGV_DIESEL_TONNE_KM_EF, "Unit": "kg CO₂e / tkm", "Source": "UBA ProBas / TREMOD"},
        {"Parameter": "Commercial Packing Waste Incineration", "Scope 3 Cat.": "Cat. 5", "Value": PROBAS_WASTE_INCINERATION_EF, "Unit": "kg CO₂e / kg", "Source": "UBA ProBas"},
        {"Parameter": "Outbound Parcel Delivery (DHL GoGreen)", "Scope 3 Cat.": "Cat. 9", "Value": DHL_GOGREEN_NET_EF, "Unit": "kg CO₂e / order", "Source": "DHL GoGreen Certified"}
    ])
    st.dataframe(ef_table, use_container_width=True, hide_index=True)
