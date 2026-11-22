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

    /* High-Visibility Pill Navigation Tabs */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #111827;
        padding: 10px 14px;
        border-radius: 12px;
        border: 1px solid #374151;
        margin-bottom: 18px;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        background-color: #1F2937;
        color: #E5E7EB;
        border: 1px solid #4B5563;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
        background-color: #374151;
        border-color: #10B981;
        color: #FFFFFF;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
        color: #0B0F19 !important;
        border-color: #34D399 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none;
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
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F9FAFB", size=12)
    )
    st.plotly_chart(fig_sankey, use_container_width=True)

    st.divider()

    # --- DUAL CHARTS ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("2. Controllable Operational Hotspots")
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
            color_continuous_scale="Emrld"
        )
        fig_ops.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_ops, use_container_width=True)

    with chart_col2:
        st.subheader("3. Batch Size Efficiency (Ops CO₂e / Bottle)")
        comp_rows = []
        for v in ["6-bottle", "12-bottle", "18-bottle"]:
            r = calculate_full_scope3_pcf(v, custom_distance, enable_gogreen, bottle_system)
            comp_rows.append({
                "Carton Size": v.upper(),
                "Ops Emissions per Bottle (kg CO₂e)": r["ops_per_bottle"],
                "Highlight": "Selected" if v == order_type else "Alternative"
            })
        df_comp = pd.DataFrame(comp_rows)
        fig_comp = px.bar(
            df_comp,
            x="Carton Size",
            y="Ops Emissions per Bottle (kg CO₂e)",
            text_auto=".4f",
            color="Highlight",
            color_discrete_map={"Selected": "#10B981", "Alternative": "#374151"}
        )
        fig_comp.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.subheader("CSRD ESRS E1 Audit Breakdown")
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
        ],
        "Share of Total (%)": [
            f"{(res['cat1_product'] / res['total_co2e']) * 100:.2f}%",
            f"{(res['cat1_packaging'] / res['total_co2e']) * 100:.2f}%",
            f"{(res['cat4_inbound'] / res['total_co2e']) * 100:.2f}%",
            f"{(res['cat5_waste'] / res['total_co2e']) * 100:.2f}%",
            f"{(res['cat9_outbound'] / res['total_co2e']) * 100:.2f}%"
        ]
    })

    st.markdown(
        df_audit.to_html(index=False, classes="centered-audit-table", float_format=lambda x: f"{x:.4f}"),
        unsafe_allow_html=True
    )

    csv_data = df_audit.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSRD Audit Ledger (CSV)",
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
        "Engineered from bottom-up **primary operational data** collected directly on the warehouse floor, "
        "following the four-phase Life Cycle Assessment (LCA) framework:"
    )

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.info("### 1. Goal & Scope\n**System Boundary:** Cradle-to-Customer.\n\n**Functional Unit:** 1 fulfilled e-commerce order (6, 12, or 18 × 0.5L bottles) aligned with **GHG Protocol Scope 3**.")
    with p2:
        st.info("### 2. Primary LCI Data\n**Empirical Collection:** Physical dimensioning of cartons and digital scale gravimetric testing of tape rolls (183g gross − 32g core = **151g net PP**).")
    with p3:
        st.info("### 3. Secondary EF Mapping\n**German LCI Databases:** Activity mass & tonne-kilometers mapped to verified German factors (**UBA ProBas**, **VDW**, and **Ecoinvent**).")
    with p4:
        st.info("### 4. Impact Aggregation\n**CSRD / ESRS E1 Output:** Automated category aggregation (Cat. 1, 4, 5, 9), hotspot identification, and audit-ready CSV reporting.")

    st.divider()

    st.subheader("⚖️ CSRD / ESRS E1 Compliance Mapping & Strategic Recommendations")
    st.markdown("""
    Under the **Corporate Sustainability Reporting Directive (CSRD)** and European Standard **ESRS E1 (Climate Change)**, companies must transparently report greenhouse gas emissions across their value chain. This tool maps directly to mandatory disclosures:
    - **ESRS E1-6 (Scope 3 Emissions):** Automatically segregates and calculates gross upstream and downstream emissions across Categories 1 (Purchased Goods), 4 (Upstream Transport), 5 (Operational Waste), and 9 (Downstream Distribution).
    
    ### 🎯 Actionable Decarbonization Recommendations for Leadership:
    1. **Prioritize Supplier Engagement (Cat. 1):** Because container glass and brewing account for the bulk of upstream intensity, distributors must partner with regional breweries utilizing biogas/green hydrogen rather than focusing solely on warehouse tape or box weights.
    2. **Enforce Circular *Mehrweg* Pools:** Leveraging Germany's returnable glass pool amortizes container manufacturing across 30 cycles, preventing massive carbon inflation compared to single-use (*Einweg*) systems.
    3. **Optimize Carton Density:** Scaling from 6-bottle to 18-bottle configurations significantly reduces packaging emissions per bottle delivered, optimizing transport efficiency (tkm).
    """)

    st.divider()

    st.subheader("Advanced LCA Allocation: The German Pfand (Mehrweg) System")
    st.markdown("""
    - **Allocation Methodology (ISO 14044):** Standard cradle-to-gate databases assign 100% of container glass production to a single use. By accounting for Germany's **Mehrweg pool infrastructure**, glass bottles are modeled across an average of **30 rotation cycles**, radically shifting product footprint attribution.
    - **Strategic Distributor Takeaway:** Toggling between *Einweg* and *Mehrweg* proves that direct warehouse packaging operations (boxes, tape) represent the primary direct control levers for a distributor, whereas product-level carbon is governed by circular packaging pools and reverse logistics.
    """)

    st.divider()

    st.subheader("Mathematical Formulation (First-Principles Model)")
    f_col1, f_col2 = st.columns(2)

    with f_col1:
        st.markdown("**1. Category 1 — Purchased Goods & Packaging ($E_{\\text{Cat1}}$):**")
        st.latex(r"E_{\text{pack}} = (m_{\text{box}} + n_{\text{ins}} \cdot m_{\text{ins}}) \cdot EF_{\text{VDW}} + m_{\text{tape}} \cdot EF_{\text{PP}} + m_{\text{lbl}} \cdot EF_{\text{lbl}}")
        st.latex(r"E_{\text{prod}} = N_{\text{bottles}} \cdot \left( \left(\frac{m_{\text{glass}}}{N_{\text{rotations}}}\right) \cdot EF_{\text{UBA}} + V_{\text{beer}} \cdot EF_{\text{brew}} \right)")

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

    st.markdown(ef_table.to_html(index=False, classes="centered-audit-table"), unsafe_allow_html=True)
