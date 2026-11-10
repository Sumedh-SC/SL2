import streamlit as st
import pandas as pd
import numpy as np


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Building Energy Demand Dashboard",
    page_icon="⚡",
    layout="wide"
)

st.title("Building Energy Demand Analysis")
st.write("Annual and seasonal energy-demand projection using historical consumption and a 15-minute load profile.")


# --------------------------------------------------
# 2024 MONTHLY ENERGY CONSUMPTION DATA
# --------------------------------------------------

monthly_data = {
    "Month": [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ],
    "Heating": [
        191220, 111450, 117870, 100460, 78950, 78930,
        81610, 80380, 83082, 96178, 143340, 190890
    ],
    "Electricity": [
        116377, 109825, 119021, 120491, 132937, 147036,
        159972, 166841, 136687, 124326, 115590, 117714
    ]
}

df_monthly = pd.DataFrame(monthly_data)


# --------------------------------------------------
# 15-MINUTE LOAD PROFILE (22 OCTOBER 2025)
# --------------------------------------------------

load_values = [
    8.96, 8.34, 8.68, 8.38, 9.03, 8.43, 9.03, 8.73,
    9.43, 9.13, 9.16, 8.84, 9.67, 10.62, 10.65, 11.04,
    10.17, 10.71, 10.37, 10.74, 10.83, 10.87, 11.31, 10.51,
    10.44, 10.99, 11.06, 11.10, 10.47, 10.46, 10.16, 10.77,
    10.38, 10.29, 10.02, 9.96, 9.99, 9.95, 9.30, 9.60,
    9.28, 10.56, 9.60, 9.60, 8.96, 9.28, 9.92, 8.96,
    8.64, 8.64, 8.64, 9.60, 8.64, 8.64, 8.64, 8.64,
    9.60, 8.64, 8.96, 8.32, 9.28, 9.28, 8.64, 8.96
]


# --------------------------------------------------
# SIDEBAR SETTINGS
# --------------------------------------------------

st.sidebar.header("Projection Settings")

year = st.sidebar.selectbox(
    "Select projection year",
    [2025, 2026, 2027, 2028]
)

electricity_growth = st.sidebar.slider(
    "Annual electricity growth (%)",
    0.0, 10.0, 0.0, 0.5
)

heating_growth = st.sidebar.slider(
    "Annual heating growth (%)",
    0.0, 10.0, 0.0, 0.5
)

overnight_load = st.sidebar.slider(
    "Assumed overnight load (kW)",
    0.0, 15.0, 9.0, 0.1
)

emission_factor = st.sidebar.number_input(
    "Electricity emission factor (kg CO₂/kWh)",
    min_value=0.0,
    value=0.35,
    step=0.01
)


# --------------------------------------------------
# CREATE A 24-HOUR DAILY LOAD PROFILE
# --------------------------------------------------

# 00:00 to 07:45: assumed overnight load
night_values = [overnight_load] * 32

# 08:00 to 23:45: measured values
daily_profile = night_values + load_values

times = pd.date_range(
    "2025-10-22 00:00",
    periods=96,
    freq="15min"
)

df_daily = pd.DataFrame({
    "Time": times,
    "Load (kW)": daily_profile
})

df_daily["Hour"] = df_daily["Time"].dt.strftime("%H:%M")


# --------------------------------------------------
# GENERATE ANNUAL 15-MINUTE PROFILE
# --------------------------------------------------

# Scale monthly consumption to the selected year.
days_2024 = 366

days_target = 366 if pd.Timestamp(year=year, month=12, day=31).is_leap_year else 365

df_monthly["Days"] = [
    31, 29, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31
]

# Correct February for non-leap years in the baseline data.
df_monthly["Days"] = [
    31, 29, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31
]

df_monthly["Projected Electricity"] = (
    df_monthly["Electricity"]
    * (1 + electricity_growth / 100) ** (year - 2024)
    * df_monthly["Days"].apply(
        lambda x: x
    ) / df_monthly["Days"]
)

# Adjust each month's energy for the number of days in the target year.
target_days = [
    31, 29 if days_target == 366 else 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31
]

df_monthly["Target Days"] = target_days

df_monthly["Projected Electricity"] = (
    df_monthly["Electricity"]
    * (1 + electricity_growth / 100) ** (year - 2024)
    * df_monthly["Target Days"] / df_monthly["Days"]
)

df_monthly["Projected Heating"] = (
    df_monthly["Heating"]
    * (1 + heating_growth / 100) ** (year - 2024)
    * df_monthly["Target Days"] / df_monthly["Days"]
)


# Normalise the daily shape so monthly energy totals are preserved.
profile_shape = np.array(daily_profile, dtype=float)

profile_shape = profile_shape / profile_shape.sum()

annual_records = []

for month in range(1, 13):

    month_days = target_days[month - 1]
    monthly_energy = df_monthly.loc[
        month - 1, "Projected Electricity"
    ]

    # Energy per 15-minute interval in kWh
    interval_energy = monthly_energy * profile_shape

    # Convert interval energy to average power in kW
    interval_power = interval_energy / 0.25

    for day in range(1, month_days + 1):

        date = pd.Timestamp(year=year, month=month, day=day)

        for interval in range(96):

            time = date + pd.Timedelta(minutes=15 * interval)

            annual_records.append({
                "DateTime": time,
                "Month": time.strftime("%b"),
                "Season": (
                    "Winter" if month in [12, 1, 2]
                    else "Spring" if month in [3, 4, 5]
                    else "Summer" if month in [6, 7, 8]
                    else "Autumn"
                ),
                "Load (kW)": interval_power[interval]
            })

df_annual = pd.DataFrame(annual_records)


# --------------------------------------------------
# KEY PERFORMANCE INDICATORS
# --------------------------------------------------

annual_electricity = df_monthly["Projected Electricity"].sum()
annual_heating = df_monthly["Projected Heating"].sum()

peak_load = df_annual["Load (kW)"].max()
average_load = df_annual["Load (kW)"].mean()

annual_co2 = annual_electricity * emission_factor


st.subheader(f"Energy Demand Overview – {year}")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Annual Electricity",
    f"{annual_electricity:,.0f} kWh"
)

col2.metric(
    "Annual Heating",
    f"{annual_heating:,.0f} kWh"
)

col3.metric(
    "Average Electricity Load",
    f"{average_load:.2f} kW"
)

col4.metric(
    "Peak Electricity Load",
    f"{peak_load:.2f} kW"
)


# --------------------------------------------------
# MONTHLY ENERGY CONSUMPTION
# --------------------------------------------------

st.subheader("1. Monthly Energy Consumption")

monthly_chart = df_monthly.set_index("Month")[
    ["Projected Electricity", "Projected Heating"]
]

st.bar_chart(monthly_chart)

st.dataframe(
    df_monthly[
        ["Month", "Projected Electricity", "Projected Heating"]
    ].round(2),
    hide_index=True,
    width="stretch"
)


# --------------------------------------------------
# SEASONAL ENERGY CONSUMPTION
# --------------------------------------------------

st.subheader("2. Seasonal Energy Consumption")

season_order = ["Winter", "Spring", "Summer", "Autumn"]

seasonal_data = {
    "Season": season_order,
    "Heating": [],
    "Electricity": []
}

season_months = {
    "Winter": [12, 1, 2],
    "Spring": [3, 4, 5],
    "Summer": [6, 7, 8],
    "Autumn": [9, 10, 11]
}

for season in season_order:

    months = season_months[season]

    seasonal_data["Heating"].append(
        sum(
            df_monthly.loc[m - 1, "Projected Heating"]
            for m in months
        )
    )

    seasonal_data["Electricity"].append(
        sum(
            df_monthly.loc[m - 1, "Projected Electricity"]
            for m in months
        )
    )

df_seasonal = pd.DataFrame(seasonal_data)

st.bar_chart(
    df_seasonal.set_index("Season")
    [["Heating", "Electricity"]]
)

st.dataframe(
    df_seasonal.round(2),
    hide_index=True,
    width="stretch"
)


# --------------------------------------------------
# DAILY 15-MINUTE LOAD PROFILE
# --------------------------------------------------

st.subheader("3. Daily 15-Minute Load Profile")

st.write(
    "The measured profile covers 08:00–23:45. "
    "The overnight period is estimated using the selected assumed load."
)

st.line_chart(
    df_daily.set_index("Time")[["Load (kW)"]]
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Maximum Daily Load",
    f"{df_daily['Load (kW)'].max():.2f} kW"
)

col2.metric(
    "Minimum Daily Load",
    f"{df_daily['Load (kW)'].min():.2f} kW"
)

col3.metric(
    "Average Daily Load",
    f"{df_daily['Load (kW)'].mean():.2f} kW"
)


# --------------------------------------------------
# ANNUAL LOAD PROFILE
# --------------------------------------------------

st.subheader("4. Annual 15-Minute Load Projection")

st.write(
    "The measured daily shape is repeated and scaled to match "
    "the projected monthly electricity consumption."
)

# Select a sample month to keep the graph readable.
selected_month = st.selectbox(
    "Select month to view 15-minute load profile",
    list(df_annual["Month"].unique())
)

month_profile = df_annual[
    df_annual["Month"] == selected_month
]

st.line_chart(
    month_profile.set_index("DateTime")[["Load (kW)"]]
)


# --------------------------------------------------
# SEASONAL LOAD PROFILE
# --------------------------------------------------

st.subheader("5. Seasonal Load Profile")

season_selected = st.selectbox(
    "Select season",
    season_order
)

season_profile = df_annual[
    df_annual["Season"] == season_selected
]

# Display average 15-minute profile for the selected season.
season_profile = season_profile.copy()

season_profile["Time"] = (
    season_profile["DateTime"].dt.strftime("%H:%M")
)

average_season_profile = (
    season_profile.groupby("Time")["Load (kW)"]
    .mean()
)

st.line_chart(average_season_profile)


# --------------------------------------------------
# CO2 EMISSIONS
# --------------------------------------------------

st.subheader("6. Estimated CO₂ Emissions")

st.metric(
    "Annual Electricity-Related CO₂ Emissions",
    f"{annual_co2:,.0f} kg CO₂"
)

st.write(
    "Calculation: Annual projected electricity consumption × "
    "selected electricity emission factor."
)


# --------------------------------------------------
# DOWNLOAD DATA
# --------------------------------------------------

st.subheader("7. Download Projected Data")

csv = df_annual.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Annual 15-Minute Load Profile",
    data=csv,
    file_name=f"building_load_profile_{year}.csv",
    mime="text/csv"
)

monthly_csv = df_monthly.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Monthly Energy Data",
    data=monthly_csv,
    file_name=f"monthly_energy_{year}.csv",
    mime="text/csv"
)


# --------------------------------------------------
# METHODOLOGY AND LIMITATIONS
# --------------------------------------------------

st.subheader("8. Methodology and Assumptions")

st.markdown("""
- Historical 2024 monthly electricity and heating consumption is used as the baseline.
- The 15-minute load profile from 22 October 2025 is used as the daily electricity-demand shape.
- The missing overnight period (00:00–07:45) is estimated using the assumed overnight load.
- The daily profile is scaled separately for each month to match its projected electricity consumption.
- Heating demand is projected monthly using the selected annual growth rate.
- Seasonal consumption is calculated using meteorological seasons.

**Important limitations:**

- The same daily load shape is assumed throughout the year.
- Actual seasonal and weekday/weekend variations are not represented.
- Overnight demand is estimated, not measured.
- This is a synthetic projection, not a validated energy forecast.
- Confirm the original 15-minute readings' units and meter scope before using the results for engineering design.
""")
