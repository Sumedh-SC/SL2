import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------
# 1. REAL COAL PLANT DATA (YOUR PROVIDED DATA)
# ---------------------------------------------------
plants_data = [
    {'plant_name':'North Karanpura STPP','coal_tons':7969147,'TSP':23907,'PM10':14344,'PM2.5':12910,'SO2':55784},
    {'plant_name':'Patratu STPP','coal_tons':8229144,'TSP':28802,'PM10':17281,'PM2.5':15553,'SO2':41146},
    {'plant_name':'Tenughat TPS','coal_tons':2233800,'TSP':15637,'PM10':9382,'PM2.5':8444,'SO2':13403},

    {'plant_name':'Talcher Kaniha','coal_tons':10704720,'TSP':42819,'PM10':25691,'PM2.5':23122,'SO2':85638},
    {'plant_name':'Darlipali','coal_tons':8563776,'TSP':29117,'PM10':17470,'PM2.5':15723,'SO2':33913},
    {'plant_name':'IB Thermal','coal_tons':9493650,'TSP':34177,'PM10':20506,'PM2.5':18456,'SO2':28196},

    {'plant_name':'Korba Super Thermal','coal_tons':9825216,'TSP':29476,'PM10':17685,'PM2.5':15917,'SO2':29181},
    {'plant_name':'Sipat Super Thermal','coal_tons':10233432,'TSP':34794,'PM10':20876,'PM2.5':18789,'SO2':50655}
]

df_plants = pd.DataFrame(plants_data)

# ---------------------------------------------------
# 2. CALCULATE REAL COAL EMISSION FACTORS
# ---------------------------------------------------
pollutants = ["TSP", "PM10", "PM2.5", "SO2"]
coal_EF_real = {pol: (df_plants[pol] / df_plants["coal_tons"]).mean() for pol in pollutants}

# ---------------------------------------------------
# 3. BIOGAS EMISSION FACTORS
# ---------------------------------------------------
biogas_EF = {
    'TSP':   0.05/1000,
    'PM10':  0.05/1000,
    'PM2.5': 0.02/1000,
    'SO2':   0.01/1000,
    'NOx':   0.50/1000
}

# ---------------------------------------------------
# STREAMLIT INTERFACE
# ---------------------------------------------------
st.title("Coal–Biogas Blended Emissions Calculator")
st.write("Calculate emission reductions for any coal plant using biogas blending.")

st.sidebar.header("Input Parameters")

coal_consumption = st.sidebar.number_input("Coal consumption (tons/year)", min_value=0.0, step=1000.0)

TSP_in = st.sidebar.number_input("TSP (tons/year)", min_value=0.0)
PM10_in = st.sidebar.number_input("PM10 (tons/year)", min_value=0.0)
PM25_in = st.sidebar.number_input("PM2.5 (tons/year)", min_value=0.0)
SO2_in = st.sidebar.number_input("SO2 (tons/year)", min_value=0.0)

biogas_frac = st.sidebar.slider("Biogas blending fraction", 0.0, 1.0, 0.0, 0.01)

ESP = st.sidebar.slider("ESP Efficiency (%)", 0, 100, 0)
FGD = st.sidebar.slider("FGD Efficiency (%)", 0, 100, 0)

if st.sidebar.button("Calculate Emissions"):

    coal_share = 1 - biogas_frac
    bio_share = biogas_frac

    coal_baseline = {
        "TSP": TSP_in,
        "PM10": PM10_in,
        "PM2.5": PM25_in,
        "SO2": SO2_in,
        "NOx": 0.0
    }

    results = {}

    for pol in coal_baseline:
        coal_part = coal_baseline[pol] * coal_share
        bio_part = biogas_EF[pol] * coal_consumption * bio_share
        total = coal_part + bio_part

        if pol in ["TSP", "PM10", "PM2.5"]:
            total *= (1 - ESP / 100)
        if pol == "SO2":
            total *= (1 - FGD / 100)

        results[pol] = total

    df_out = pd.DataFrame({
        "Pollutant": list(coal_baseline.keys()),
        "Baseline_Emissions_tons": list(coal_baseline.values()),
        "Blended_Emissions_tons": [results[p] for p in coal_baseline],
        "Reduction_%": [
            round((1 - results[p] / coal_baseline[p]) * 100, 2)
            if coal_baseline[p] > 0 else "N/A"
            for p in coal_baseline.keys()
        ]
    })

    st.subheader("Results")
    st.dataframe(df_out)

