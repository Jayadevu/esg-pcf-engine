import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Scope 3 Packaging PCF Engine (CSRD ESRS E1)", 
    layout="wide"
)

# --- HEADER ---
st.title("Scope 3 Logistics & Packaging PCF Engine")
st.caption("Empirical Product Carbon Footprint (PCF) model aligned with CSRD ESRS E1 Compliance & GHG Protocol (Cat. 1, 4, 5, 9)")

# --- 1. CONSTANTS: EMISSION FACTORS (kg CO2e per unit) ---
VDW_PROBAS_CORRUGATED_EF = 0.491
UBA_PROBAS_GLASS_EF = 0.85
ECOINVENT_BREWING_EF = 0.70
PROBAS_PLASTIC_TAPE_EF = 1.95
PROBAS_ADHESIVE_LABEL_EF = 1.15
PROBAS_WASTE_INCINERATION_EF = 0.33  # Cat 5: Mixed commercial waste incineration
HGV_DIESEL_TONNE_KM_EF = 0.111       # Cat 4: HGV Diesel Truck (per tonne-kilometer)
DHL_GOGREEN_NET_EF = 0.0             # Cat 9: DHL GoGreen certified net-zero delivery

# --- 2. BASE WEIGHTS & DISTANCES ---
DISTANCE_COBURG_INBOUND_KM = 75

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
st.sidebar.header("Scenario Configuration")
order_type = st.sidebar.selectbox("Select Order Variant", ["6-bottle", "12-bottle", "18-bottle"])
monthly_order_volume = st.sidebar.number_input("Monthly Order Volume (Batches)", value=1200, step=100)
custom_distance = st.sidebar.slider("Inbound Transport Distance (Coburg, km)", 20, 300, DISTANCE_COBURG_INBOUND_KM)
enable_gogreen = st.sidebar.toggle("Include DHL GoGreen (Cat. 9 Offset)", value=True)

# --- 4. CALCULATION ENGINE (Your Exact Logic) ---
def calculate_full_scope3_pcf(order_type, distance_km, gogreen_active):
    if order_type == '6-bottle':
        outer_box = WEIGHTS["box_6_bottle"]
        inserts = 1
        bottles = 6
        tape = WEIGHTS["tape_6_bottle_kg"]
    elif order_type == '12-bottle':
        outer_box = WEIGHTS["box_12_bottle"]
        inserts = 2
        bottles = 12
        tape = WEIGHTS["tape_12_bottle_kg"]
    elif order_type == '18-bottle':
        outer_box = WEIGHTS["box_18_bottle"]
        inserts = 3
        bottles = 18
        tape = WEIGHTS["tape_18_bottle_kg"]
    else:
        raise ValueError("Invalid configuration")

    # --- A. CATEGORY 1: PURCHASED GOODS (Packaging + Beer) ---
    cardboard_kg = outer_box + (inserts * WEIGHTS["insert_module"])
    packaging_pcf = (cardboard_kg * VDW_PROBAS_CORRUGATED_EF) + \
                    (tape * PROBAS_PLASTIC_TAPE_EF) + \
                    (WEIGHTS["hazard_sticker_kg"] * PROBAS_ADHESIVE_LABEL_EF) + \
                    (WEIGHTS["shipping_label_kg"] * PROBAS_ADHESIVE_LABEL_EF)

    single_beer_pcf = (WEIGHTS["glass_bottle_05L_kg"] * UBA_PROBAS_GLASS_EF) + \
                      (WEIGHTS["beer_liquid_volume_L"] * ECOINVENT_BREWING_EF)
    product_pcf = single_beer_pcf * bottles

    # --- B. CATEGORY 5: OPERATIONAL WASTE ---
    waste_pcf = WEIGHTS["packing_waste_kg"] * PROBAS_WASTE_INCINERATION_EF

    # --- C. CATEGORY 4: INBOUND TRANSPORT (Coburg to Warehouse) ---
    beer_weight_tonnes = ((WEIGHTS["glass_bottle_05L_kg"] + WEIGHTS["beer_liquid_volume_L"]) * bottles) / 1000.0
    inbound_tkm = beer_weight_tonnes * distance_km
    inbound_transport_pcf = inbound_tkm * HGV_DIESEL_TONNE_KM_EF

    # --- D. CATEGORY 9: OUTBOUND TRANSPORT (DHL to Customer) ---
    outbound_transport_pcf = DHL_GOGREEN_NET_EF if gogreen_active else 0.052

    # --- GRAND TOTAL ---
    total_order_pcf = packaging_pcf + product_pcf + waste_pcf + inbound_transport_pcf + outbound_transport_pcf

    return {
        "cat1_packaging": round(packaging_pcf, 4),
        "cat1_product": round(product_pcf, 4),
        "cat5_waste": round(waste_pcf, 4),
        "cat4_inbound": round(inbound_transport_pcf, 4),
        "cat9_outbound": round(outbound_transport_pcf, 4),
        "total_co2e": round(total_order_pcf, 4)
    }

res = calculate_full_scope3_pcf(order_type, custom_distance, enable_gogreen)
annual_total_tonnes = (res['total_co2e'] * monthly_order_volume * 12) / 1000.0

# --- 5. EXECUTIVE METRICS DASHBOARD ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Selected Variant PCF", f"{res['total_co2e']} kg CO₂e", delta=f"{order_type.upper()} Batch")
col2.metric("Annualized Scope 3 Footprint", f"{annual_total_tonnes:.2f} t CO₂e", delta=f"{monthly_order_volume} orders/mo")
col3.metric("Cat. 1 Product Share", f"{(res['cat1_product'] / res['total_co2e']) * 100:.1f}%")
col4.metric("Cat. 1 Packaging Share", f"{(res['cat1_packaging'] / res['total_co2e']) * 100:.1f}%")

st.divider()

# --- 6. VISUALIZATION & AUDIT TABLES ---
left_col, right_col = st.columns([1.2, 1])

df_audit = pd.DataFrame({
    "Scope 3 Category": [
        "Cat. 1: Purchased Goods (Packaging)",
        "Cat. 1: Purchased Goods (Beer & Glass)",
        "Cat. 4: Inbound Transport (Coburg HGV)",
        "Cat. 5: Operational Packing Waste",
        "Cat. 9: Outbound Transport (DHL GoGreen)"
    ],
    "Emissions (kg CO2e)": [
        res['cat1_packaging'],
        res['cat1_product'],
        res['cat4_inbound'],
        res['cat5_waste'],
        res['cat9_outbound']
    ]
})

with left_col:
    st.subheader("Emissions Hotspot Breakdown")
    fig = px.pie(
        df_audit, 
        names="Scope 3 Category", 
        values="Emissions (kg CO2e)", 
        hole=0.45,
        color_discrete_sequence=px.colors.sequential.Tealgrn
    )
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("CSRD ESRS E1 Audit Table")
    st.dataframe(df_audit, use_container_width=True, hide_index=True)
    
    csv_data = df_audit.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Audit Report (CSV)",
        data=csv_data,
        file_name=f"scope3_pcf_{order_type}_report.csv",
        mime="text/csv",
        use_container_width=True
    )

with st.expander("Methodology, Data Sources & Compliance Notes"):
    st.markdown(f"""
    - **Compliance:** Built in accordance with **CSRD ESRS E1** and **GHG Protocol Corporate Value Chain (Scope 3) Standard**.
    - **Emission Factor References:** 
        - Corrugated Cardboard: `VDW / PROBAS` ({VDW_PROBAS_CORRUGATED_EF} kg CO₂e/kg)
        - Glass & Brewing: `UBA / Ecoinvent` ({UBA_PROBAS_GLASS_EF} / {ECOINVENT_BREWING_EF} kg CO₂e/unit)
        - Transport: HGV Diesel Truck ({HGV_DIESEL_TONNE_KM_EF} kg CO₂e/tkm across {custom_distance} km inbound from Coburg).
    - **Verification:** Designed for live audit export and portfolio presentation to ESG hiring managers.
    """)
