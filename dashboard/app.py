import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="RO Water Plant Analytics", layout="wide")
alt.data_transformers.disable_max_rows()

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    return pd.read_csv(
        "data/processed/cleaned_data.csv",
        parse_dates=["created_at"]
    )

df = load_data()

# -----------------------------
# TITLE
# -----------------------------
st.title("🚰 RO Water Plant Business Analytics Dashboard")

# -----------------------------
# DATE FILTER
# -----------------------------
min_date = df["created_at"].min().date()
max_date = df["created_at"].max().date()

start_date, end_date = st.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

filtered_df = df[
    (df["created_at"].dt.date >= start_date) &
    (df["created_at"].dt.date <= end_date)
].copy()

if filtered_df.empty:
    st.warning("No data available for selected range.")
    st.stop()

# -----------------------------
# KPI METRICS
# -----------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Revenue (₹)", round(filtered_df["amount"].sum(), 2))
c2.metric("Transactions", len(filtered_df))
c3.metric("Unique Customers", filtered_df["upi_id"].nunique())
c4.metric(
    "Avg Revenue / Day (₹)",
    round(
        filtered_df.groupby(filtered_df["created_at"].dt.date)["amount"]
        .sum()
        .mean(),
        2
    )
)

# =========================================================
# DAILY TREND + DAY OF WEEK
# =========================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Daily Revenue Trend")

    filtered_df["date"] = filtered_df["created_at"].dt.normalize()
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

    filtered_df["day"] = filtered_df["created_at"].dt.day_name()
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
        filtered_df.groupby(filtered_df["created_at"].dt.hour)["amount"]
        .sum()
        .reset_index(name="revenue")
    )

    st.altair_chart(
        alt.Chart(hourly).mark_bar().encode(
            x="created_at:O",
            y="revenue:Q",
            tooltip=["created_at","revenue"]
        ),
        use_container_width=True
    )

with col4:
    st.subheader("📊 Monthly Growth Rate")

    filtered_df["month"] = filtered_df["created_at"].dt.to_period("M").astype(str)
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

filtered_df["hour"] = filtered_df["created_at"].dt.hour
filtered_df["date_only"] = filtered_df["created_at"].dt.date.astype(str)

heatmap = (
    filtered_df.groupby(["date_only","hour"])["amount"]
    .sum()
    .reset_index()
)

st.altair_chart(
    alt.Chart(heatmap).mark_rect().encode(
        x="date_only:O",
        y="hour:O",
        color="amount:Q",
        tooltip=["date_only","hour","amount"]
    ),
    use_container_width=True
)

# =========================================================
# 2️⃣ CUSTOMER LIFETIME VALUE (CLV)
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
        x=alt.X("upi_id:N", sort="-y", title="Customer"),
        y="total_spent:Q",
        tooltip=["upi_id","total_spent"]
    ),
    use_container_width=True
)

#  

# =========================================================
# 4️⃣ DAY-WISE AVERAGE REVENUE
# =========================================================
st.subheader("📊 Average Revenue per Day")

avg_day = (
    filtered_df.groupby(filtered_df["created_at"].dt.date)["amount"]
    .sum()
    .mean()
)

st.metric("Average Daily Revenue (₹)", round(avg_day, 2))

# =========================================================
# 5️⃣ MONTHLY BUSINESS HEALTH SCORE
# =========================================================
st.subheader("🏥 Business Health Score")

monthly["health_score"] = (
    (monthly["growth_%"].fillna(0)) -
    (filtered_df["settlement_status"] != "processed").mean() * 100
)

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
# 🔟 DOWNLOAD REPORTS
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
