# ESG Data Engine: End-to-End Scope 3 (Categories 1, 4, 5, 9)
# Output formatting aligned with CSRD ESRS E1 Compliance

# 1. Constants: Emission Factors (kg CO2e per unit)
VDW_PROBAS_CORRUGATED_EF = 0.491
UBA_PROBAS_GLASS_EF = 0.85
ECOINVENT_BREWING_EF = 0.70
PROBAS_PLASTIC_TAPE_EF = 1.95
PROBAS_ADHESIVE_LABEL_EF = 1.15
PROBAS_WASTE_INCINERATION_EF = 0.33  # Cat 5: Mixed commercial waste incineration
# Cat 4: HGV Diesel Truck (per tonne-kilometer)
HGV_DIESEL_TONNE_KM_EF = 0.111
DHL_GOGREEN_NET_EF = 0.0            # Cat 9: DHL GoGreen certified net-zero delivery

# 2. Activity Data: Distances & Weights
DISTANCE_COBURG_INBOUND_KM = 75     # Estimated km from Coburg to local warehouse

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
    "packing_waste_kg": 0.010     # Estimated 10g waste generated per order
}

# 3. Calculation Engine


def calculate_full_scope3_pcf(order_type):
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
    # Convert total product weight to tonnes to calculate tonne-kilometers (tkm)
    beer_weight_tonnes = (
        (WEIGHTS["glass_bottle_05L_kg"] + WEIGHTS["beer_liquid_volume_L"]) * bottles) / 1000
    inbound_tkm = beer_weight_tonnes * DISTANCE_COBURG_INBOUND_KM
    inbound_transport_pcf = inbound_tkm * HGV_DIESEL_TONNE_KM_EF

    # --- D. CATEGORY 9: OUTBOUND TRANSPORT (DHL to Customer) ---
    outbound_transport_pcf = DHL_GOGREEN_NET_EF

    # --- GRAND TOTAL ---
    total_order_pcf = packaging_pcf + product_pcf + waste_pcf + \
        inbound_transport_pcf + outbound_transport_pcf

    return {
        "cat1_packaging": round(packaging_pcf, 4),
        "cat1_product": round(product_pcf, 4),
        "cat5_waste": round(waste_pcf, 4),
        "cat4_inbound": round(inbound_transport_pcf, 4),
        "cat9_outbound": round(outbound_transport_pcf, 4),
        "total_co2e": round(total_order_pcf, 4)
    }


# 4. Execution
for order in ['6-bottle', '12-bottle', '18-bottle']:
    res = calculate_full_scope3_pcf(order)
    print(f"--- {order.upper()} ORDER ---")
    print(f"Cat 1: Packaging Goods:  {res['cat1_packaging']} kg CO2e")
    print(f"Cat 1: Product (Beer):   {res['cat1_product']} kg CO2e")
    print(f"Cat 4: Inbound (Coburg): {res['cat4_inbound']} kg CO2e")
    print(f"Cat 5: Packing Waste:    {res['cat5_waste']} kg CO2e")
    print(
        f"Cat 9: Outbound (DHL):   {res['cat9_outbound']} kg CO2e (GoGreen Offset)")
    print(f"GRAND TOTAL PCF:         {res['total_co2e']} kg CO2e\n")
