import pandas as pd

# 1. Load cleaned data
df = pd.read_csv(
    "data/processed/cleaned_data.csv",
    parse_dates=["created_at"]
)

# 2. Safety: sort by datetime
df = df.sort_values("created_at")

# -----------------------------
# DAILY REVENUE
# -----------------------------
daily_revenue = (
    df.groupby(df["created_at"].dt.date)["amount"]
    .sum()
    .reset_index()
)
daily_revenue.columns = ["date", "daily_revenue"]

# -----------------------------
# MONTHLY REVENUE
# -----------------------------
monthly_revenue = (
    df.groupby(df["created_at"].dt.to_period("M"))["amount"]
    .sum()
    .reset_index()
)
monthly_revenue["month"] = monthly_revenue["created_at"].astype(str)
monthly_revenue = monthly_revenue[["month", "amount"]]
monthly_revenue.columns = ["month", "monthly_revenue"]

# -----------------------------
# DAILY CUSTOMERS
# -----------------------------
daily_customers = (
    df.groupby(df["created_at"].dt.date)["upi_id"]
    .nunique()
    .reset_index()
)
daily_customers.columns = ["date", "unique_customers"]

# -----------------------------
# MONTHLY CUSTOMERS
# -----------------------------
monthly_customers = (
    df.groupby(df["created_at"].dt.to_period("M"))["upi_id"]
    .nunique()
    .reset_index()
)
monthly_customers["month"] = monthly_customers["created_at"].astype(str)
monthly_customers = monthly_customers[["month", "upi_id"]]
monthly_customers.columns = ["month", "unique_customers"]

# -----------------------------
# CUSTOMER FREQUENCY
# -----------------------------
customer_frequency = (
    df.groupby("upi_id")
    .size()
    .reset_index(name="purchase_count")
    .sort_values("purchase_count", ascending=False)
)

# -----------------------------
# TOP LOYAL CUSTOMERS
# -----------------------------
top_loyal_customers = customer_frequency.head(10)

# -----------------------------
# PEAK HOURS (HOURLY DEMAND)
# -----------------------------
hourly_demand = (
    df.groupby(df["created_at"].dt.hour)["amount"]
    .sum()
    .reset_index()
)
hourly_demand.columns = ["hour", "revenue"]

# -----------------------------
# SETTLEMENT STATUS
# -----------------------------
settlement_summary = (
    df["is_success"]
    .value_counts()
    .rename(index={True: "successful", False: "failed"})
    .reset_index()
)
settlement_summary.columns = ["status", "count"]

# -----------------------------
# SAVE OUTPUT FILES
# -----------------------------
daily_revenue.to_csv("data/processed/daily_revenue.csv", index=False)
monthly_revenue.to_csv("data/processed/monthly_revenue.csv", index=False)
daily_customers.to_csv("data/processed/daily_customers.csv", index=False)
monthly_customers.to_csv("data/processed/monthly_customers.csv", index=False)
customer_frequency.to_csv("data/processed/customer_frequency.csv", index=False)
top_loyal_customers.to_csv("data/processed/top_loyal_customers.csv", index=False)
hourly_demand.to_csv("data/processed/hourly_demand.csv", index=False)
settlement_summary.to_csv("data/processed/settlement_summary.csv", index=False)

# -----------------------------
# VALIDATION PRINTS
# -----------------------------
print("✅ Analytics generated successfully")
print("📅 Daily data starts from:", daily_revenue.iloc[0]["date"])
