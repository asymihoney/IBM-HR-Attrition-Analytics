import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HR Attrition Dashboard", layout="wide")

TEAL = "#2d5f6f"
GOLD = "#d4a941"
COLOR_MAP = {"No": TEAL, "Yes": GOLD}

@st.cache_data
def load_data():
    df = pd.read_csv("HR_Attrition_Cleaned.csv")
    df["TenureBucket"] = pd.cut(
        df["YearsAtCompany"],
        bins=[-1, 2, 5, 10, 100],
        labels=["0-2 yrs", "3-5 yrs", "6-10 yrs", "10+ yrs"]
    )
    return df

df = load_data()

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
dept = st.sidebar.multiselect("Department", sorted(df["Department"].unique()))
role = st.sidebar.multiselect("Job Role", sorted(df["JobRole"].unique()))
gender = st.sidebar.multiselect("Gender", sorted(df["Gender"].unique()))

filtered = df.copy()
if dept: filtered = filtered[filtered["Department"].isin(dept)]
if role: filtered = filtered[filtered["JobRole"].isin(role)]
if gender: filtered = filtered[filtered["Gender"].isin(gender)]

def attrition_rate(data):
    return (data["Attrition"] == "Yes").mean() if len(data) else 0

# ---------------- Tabs ----------------
tab1, tab2, tab3 = st.tabs(["Overview", "Attrition Drivers", "Compensation"])

# ===== PAGE 1: OVERVIEW =====
with tab1:
    total = len(filtered)
    attr_count = (filtered["Attrition"] == "Yes").sum()
    attr_rate = attrition_rate(filtered)
    avg_tenure = filtered["YearsAtCompany"].mean() if total else 0
    top_dept = (
        filtered[filtered["Attrition"] == "Yes"]["Department"]
        .value_counts().idxmax() if attr_count else "N/A"
    )

    st.title(f"Overall attrition sits at {attr_rate:.1%}, highest in {top_dept}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Employees", f"{total:,}")
    c2.metric("Attrition Count", f"{attr_count:,}")
    c3.metric("Attrition Rate", f"{attr_rate:.1%}")
    c4.metric("Avg Tenure", f"{avg_tenure:.1f}")

    col1, col2 = st.columns(2)
    with col1:
        donut_data = filtered[filtered["Attrition"] == "Yes"]["Department"].value_counts().reset_index()
        donut_data.columns = ["Department", "Attrition Count"]
        fig = px.pie(donut_data, names="Department", values="Attrition Count",
                     hole=0.6, title="Attrition Count by Department",
                     color_discrete_sequence=[TEAL, GOLD, "#a1522c"])
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        bar_data = filtered["Department"].value_counts().reset_index()
        bar_data.columns = ["Department", "Total Employees"]
        fig = px.bar(bar_data, x="Total Employees", y="Department", orientation="h",
                     title="Total Employees by Department", color_discrete_sequence=[TEAL])
        st.plotly_chart(fig, use_container_width=True)

# ===== PAGE 2: ATTRITION DRIVERS =====
with tab2:
    ot_yes = attrition_rate(filtered[filtered["OverTime"] == "Yes"])
    ot_no = attrition_rate(filtered[filtered["OverTime"] == "No"])
    ratio = ot_yes / ot_no if ot_no else 0

    st.title(f"Employees working overtime attrite at ~{ratio:.1f}x the rate of those who don't")

    col1, col2 = st.columns(2)
    with col1:
        rate_dept = filtered.groupby("Department")["Attrition"].apply(lambda x: (x == "Yes").mean()).reset_index()
        rate_dept.columns = ["Department", "Attrition Rate"]
        fig = px.bar(rate_dept, x="Attrition Rate", y="Department", orientation="h",
                     title="Attrition Rate by Department", color_discrete_sequence=[TEAL])
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        rate_ot = filtered.groupby("OverTime")["Attrition"].apply(lambda x: (x == "Yes").mean()).reset_index()
        rate_ot.columns = ["OverTime", "Attrition Rate"]
        fig = px.bar(rate_ot, x="Attrition Rate", y="OverTime", orientation="h",
                     title="Attrition Rate by OverTime", color="OverTime",
                     color_discrete_map={"Yes": GOLD, "No": TEAL})
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        rate_sat = filtered.groupby("JobSatisfaction")["Attrition"].apply(lambda x: (x == "Yes").mean()).reset_index()
        rate_sat.columns = ["JobSatisfaction", "Attrition Rate"]
        fig = px.bar(rate_sat, x="Attrition Rate", y="JobSatisfaction", orientation="h",
                     title="Attrition Rate by JobSatisfaction", color_discrete_sequence=[TEAL])
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        rate_tenure = filtered.groupby("TenureBucket", observed=True)["Attrition"].apply(lambda x: (x == "Yes").mean()).reset_index()
        rate_tenure.columns = ["TenureBucket", "Attrition Rate"]
        fig = px.bar(rate_tenure, x="Attrition Rate", y="TenureBucket", orientation="h",
                     title="Attrition Rate by TenureBucket", color_discrete_sequence=[TEAL])
        st.plotly_chart(fig, use_container_width=True)

# ===== PAGE 3: COMPENSATION =====
with tab3:
    avg_income_yes = filtered[filtered["Attrition"] == "Yes"]["MonthlyIncome"].mean()
    avg_income_no = filtered[filtered["Attrition"] == "No"]["MonthlyIncome"].mean()
    diff = (avg_income_no - avg_income_yes) / 1000 if pd.notna(avg_income_no) and pd.notna(avg_income_yes) else 0

    st.title(f"Employees who left earn on average ${diff:.2f}K less than those who stayed")

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.scatter(filtered, x="EmployeeNumber", y="MonthlyIncome", color="Attrition",
                          color_discrete_map=COLOR_MAP,
                          title="Attrition, EmployeeNumber and MonthlyIncome")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        income_role = filtered.groupby("JobRole")["MonthlyIncome"].mean().sort_values().reset_index()
        fig = px.bar(income_role, x="MonthlyIncome", y="JobRole", orientation="h",
                     title="Avg Monthly Income by JobRole", color_discrete_sequence=[TEAL])
        st.plotly_chart(fig, use_container_width=True)

        income_attr = filtered.groupby("Attrition")["MonthlyIncome"].mean().reset_index()
        fig = px.bar(income_attr, x="MonthlyIncome", y="Attrition", orientation="h",
                     title="Avg Monthly Income by Attrition", color="Attrition",
                     color_discrete_map=COLOR_MAP)
        st.plotly_chart(fig, use_container_width=True)