import pandas as pd
import json

# 1. Read Excel and FORCE created_at as string
file_path = "data/raw/Transfers - 07 Apr 25 - 14 Nov 25(NEW).xlsx"

df = pd.read_excel(
    file_path,
    dtype={"created_at": str}
)

# 2. Strip spaces (Excel sometimes adds them)
df["created_at"] = df["created_at"].str.strip()

# 3. Parse datetime safely (DAY FIRST)
df["created_at"] = pd.to_datetime(
    df["created_at"],
    dayfirst=True,
    errors="coerce"
)

# 4. Drop rows where date parsing failed
df = df.dropna(subset=["created_at"])

# 5. Sort by actual datetime
df = df.sort_values("created_at")

# 6. Feature engineering
df["date"] = df["created_at"].dt.date
df["month"] = df["created_at"].dt.to_period("M").astype(str)
df["hour"] = df["created_at"].dt.hour

# 7. Extract UPI ID from JSON column
def extract_upi(x):
    try:
        return json.loads(x).get("upiId")
    except:
        return None

df["upi_id"] = df["payments_notes"].apply(extract_upi)

# 8. Settlement flags
df["is_success"] = df["settlement_status"].str.lower().eq("processed")
df["is_reversed"] = df["amount_reversed"].fillna(0) > 0

# 9. Drop rows with missing critical values
df = df.dropna(subset=["upi_id", "amount"])

# 10. Save cleaned data
output_path = "data/processed/cleaned_data.csv"
df.to_csv(output_path, index=False)

# 11. HARD VALIDATION (DO NOT SKIP)
print("✅ Data cleaning completed")
print("📅 DATE RANGE:")
print(df['created_at'].min(), "→", df['created_at'].max())
print("📊 Total records:", len(df))
