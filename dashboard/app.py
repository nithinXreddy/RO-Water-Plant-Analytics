import streamlit as st
import pandas as pd
import altair as alt
import json

st.set_page_config(page_title="RO Water Plant Analytics", layout="wide")
alt.data_transformers.disable_max_rows()

# =========================================================
# FILE UPLOAD
# =========================================================
st.title("🚰 RO Water Plant Business Analytics Dashboard")

uploaded_file = st.file_uploader(
    "📤 Upload RO Water Plant Transactions (Excel)",
    type=["xlsx", "xls"]
)

if uploaded_file is None:
    st.info("Please upload the Excel file to view the dashboard")
    st.stop()

# =========================================================
# LOAD & CLEAN DATA
# =========================================================
@st.cache_data
def load_and_clean_data(file):
    df = pd.read_excel(file)

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        format="%d/%m/%y %H:%M",
        errors="coerce"
    )

    def extract_upi(x):
        try:
            return json.loads(x).get("upiId")
        except:
            return None

    df["upi_id"] = df["payments_notes"].apply(extract_upi)

    df = df.dropna(subset=["created_at", "upi_id"])

    df["date"] = df["created_at"].dt.normalize()
    df["hour"] = df["created_at"].dt.hour
    df["day"] = df["created_at"].dt.day_name()
    df["month"] = df["created_at"].dt.to_period("M").astype(str)

    return df

df = load_and_clean_data(uploaded_file)

# =========================================================
# DATE FILTER
# =========================================================
min_date = df["date"].min().date()
max_date = df["date"].max().date()

start_date, end_date = st.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

filtered_df = df[
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
].copy()

if filtered_df.empty:
    st.warning("No data available for selected range.")
    st.stop()

# =========================================================
# KPI METRICS
# =========================================================
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Revenue (₹)", round(filtered_df["amount"].sum(), 2))
c2.metric("Transactions", len(filtered_df))
c3.metric("Unique Customers", filtered_df["upi_id"].nunique())
c4.metric(
    "Avg Revenue / Day (₹)",
    round(filtered_df.groupby("date")["amount"].sum().mean(), 2)
)

# =========================================================
# DAILY TREND + DAY OF WEEK
# =========================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Daily Revenue Trend")

    daily = filtered_df.groupby("date")["amount"].sum().reset_index()
    daily["7_day_avg"] = daily["amount"].rolling(7).mean()

    chart = alt.Chart(daily).mark_line(opacity=0.3).encode(
        x="date:T",
        y="amount:Q",
        tooltip=["date:T", "amount:Q"]
    )

    avg = alt.Chart(daily).mark_line(strokeWidth=3, color="orange").encode(
        x="date:T",
        y="7_day_avg:Q",
        tooltip=["date:T", "7_day_avg:Q"]
    )

    st.altair_chart(chart + avg, use_container_width=True)

with col2:
    st.subheader("📅 Day-of-Week Demand")

    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    dow = (
        filtered_df.groupby("day")["amount"]
        .sum()
        .reindex(order)
        .reset_index()
    )

    st.altair_chart(
        alt.Chart(dow).mark_bar().encode(
            x=alt.X("day:O", sort=order),
            y="amount:Q",
            tooltip=["day","amount"]
        ),
        use_container_width=True
    )

# =========================================================
# PEAK HOURS + MONTHLY GROWTH
# =========================================================
col3, col4 = st.columns(2)

with col3:
    st.subheader("⏰ Peak Demand Hours")

    hourly = (
        filtered_df.groupby("hour")["amount"]
        .sum()
        .reset_index(name="revenue")
    )

    st.altair_chart(
        alt.Chart(hourly).mark_bar().encode(
            x="hour:O",
            y="revenue:Q",
            tooltip=["hour","revenue"]
        ),
        use_container_width=True
    )

with col4:
    st.subheader("📊 Monthly Growth Rate")

    monthly = filtered_df.groupby("month")["amount"].sum().reset_index()
    monthly["growth_%"] = monthly["amount"].pct_change() * 100

    st.altair_chart(
        alt.Chart(monthly).mark_line(point=True).encode(
            x="month:O",
            y="growth_%:Q",
            tooltip=["month","growth_%"]
        ),
        use_container_width=True
    )

# =========================================================
# HEATMAP
# =========================================================
st.subheader("🔥 Revenue by Hour Heatmap")

heatmap = (
    filtered_df.groupby(["date","hour"])["amount"]
    .sum()
    .reset_index()
)

st.altair_chart(
    alt.Chart(heatmap).mark_rect().encode(
        x="date:T",
        y="hour:O",
        color="amount:Q",
        tooltip=["date","hour","amount"]
    ),
    use_container_width=True
)

# =========================================================
# CUSTOMER LIFETIME VALUE
# =========================================================
st.subheader("💰 Customer Lifetime Value")

clv = (
    filtered_df.groupby("upi_id")["amount"]
    .sum()
    .reset_index(name="total_spent")
    .sort_values("total_spent", ascending=False)
)

st.altair_chart(
    alt.Chart(clv.head(10)).mark_bar().encode(
        x=alt.X("upi_id:N", sort="-y"),
        y="total_spent:Q",
        tooltip=["upi_id","total_spent"]
    ),
    use_container_width=True
)

# =========================================================
# BUSINESS HEALTH SCORE
# =========================================================
st.subheader("🏥 Business Health Score")

monthly["health_score"] = monthly["growth_%"].fillna(0)

st.altair_chart(
    alt.Chart(monthly).mark_bar().encode(
        x="month:O",
        y="health_score:Q",
        tooltip=["month","health_score"]
    ),
    use_container_width=True
)

# =========================================================
# TOP LOYAL CUSTOMERS
# =========================================================
st.subheader("🏆 Top 10 Loyal Customers")

top_customers = (
    filtered_df.groupby("upi_id")
    .size()
    .reset_index(name="transactions")
    .sort_values("transactions", ascending=False)
    .head(10)
)

top_customers.index = range(1, len(top_customers) + 1)
st.dataframe(top_customers, use_container_width=True)

# =========================================================
# DOWNLOADS
# =========================================================
st.subheader("📥 Download Reports")

st.download_button(
    "Download Filtered Data (CSV)",
    filtered_df.to_csv(index=False),
    "filtered_data.csv"
)

st.download_button(
    "Download Monthly Summary (CSV)",
    monthly.to_csv(index=False),
    "monthly_summary.csv"
)
