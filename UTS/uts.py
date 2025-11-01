import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Smart Retail Dashboard", layout="wide")

st.markdown("""
    <style>
        body {background-color: #0E1117; color: #FAFAFA;}
        .stApp {background-color: #0E1117;}
        h1, h2, h3, h4, h5 {color: #00FFFF;}
        .css-18e3th9 {background-color: #0E1117;}
        .block-container {padding-top: 1rem;}
        [data-testid="stMetricValue"] {color: #39FF14;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "Copy of finalProj_df - 2022.csv"  # pakai nama file yang kamu punya
    df = pd.read_csv(file_path)

    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df["year"] = df["order_date"].dt.year
        df["month"] = df["order_date"].dt.strftime("%b")
        df["period"] = df["order_date"].dt.to_period("M")

    if "after_discount" in df.columns:
        df["revenue"] = df["after_discount"]
    elif "before_discount" in df.columns:
        df["revenue"] = df["before_discount"]

    if "cogs" in df.columns:
        df["profit"] = df["revenue"] - df["cogs"]

    if "qty_ordered" in df.columns:
        df["qty_ordered"] = pd.to_numeric(df["qty_ordered"], errors="coerce").fillna(0).astype(int)

    return df

df = load_data()

st.sidebar.title("🧭 Navigasi")
page = st.sidebar.radio("Pilih Halaman:", [
    "📊 Analisis Penjualan Produk",
    "📈 Analisis Tren Bulanan",
    "👥 Analisis Pelanggan"
])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Filter Data")

years = sorted(df["year"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect("📆 Pilih Tahun", years, default=years)

st.sidebar.markdown("### 🏷️ Pilih Kategori Produk")
categories = sorted(df["category"].dropna().unique().tolist())
select_all_cats = st.sidebar.checkbox("Pilih Semua Kategori", value=True)
if select_all_cats:
    selected_cats = categories
else:
    selected_cats = st.sidebar.multiselect("Pilih Kategori:", categories, default=[])

st.sidebar.markdown("### 🧾 Pilih Produk")
products = sorted(df["sku_name"].dropna().unique().tolist())
select_all_prods = st.sidebar.checkbox("Pilih Semua Produk", value=False)
if select_all_prods:
    selected_prods = products
else:
    selected_prods = st.sidebar.multiselect("Pilih Produk:", products, default=[])

filtered_df = df.copy()
if selected_years:
    filtered_df = filtered_df[filtered_df["year"].isin(selected_years)]
if selected_cats:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_cats)]
if selected_prods:
    filtered_df = filtered_df[filtered_df["sku_name"].isin(selected_prods)]

st.title("📈 Smart Retail Dashboard ")
st.caption("UTS VID A | Kristian Dwitama Adiyaksa | 230712341")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Revenue", f"Rp {filtered_df['revenue'].sum():,.0f}")
col2.metric("📦 Total Orders", f"{filtered_df['id'].nunique():,}")
col3.metric("👥 Unique Customers", f"{filtered_df['customer_id'].nunique():,}")
col4.metric("💹 Total Profit", f"Rp {filtered_df['profit'].sum():,.0f}")

st.markdown("---")

if page == "📊 Analisis Penjualan Produk":
    st.header("📊 Analisis Penjualan Produk")

    if "category" in filtered_df.columns:
        cat_rev = filtered_df.groupby("category")["revenue"].sum().reset_index()
        fig_pie = px.pie(cat_rev, values="revenue", names="category",
                         title="Kontribusi Revenue per Kategori",
                         color_discrete_sequence=px.colors.sequential.Tealgrn,
                         template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

    if "sku_name" in filtered_df.columns:
        top10 = filtered_df.groupby("sku_name")["revenue"].sum().nlargest(10).reset_index()
        fig_bar = px.bar(top10, x="revenue", y="sku_name",
                         orientation="h", title="Top 10 Produk Berdasarkan Revenue",
                         color="revenue", color_continuous_scale="Blues", template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("📋 Lihat Detail Produk"):
        show_cols = ["sku_name", "category", "revenue", "profit", "qty_ordered"]
        if all(c in filtered_df.columns for c in show_cols):
            st.dataframe(filtered_df[show_cols].sort_values("revenue", ascending=False).head(50))

elif page == "📈 Analisis Tren Bulanan":
    st.header("📈 Analisis Tren Bulanan")

    monthly = filtered_df.groupby("period").agg(
        Revenue=("revenue", "sum"),
        Profit=("profit", "sum")
    ).reset_index()
    monthly["period_str"] = monthly["period"].astype(str)

    fig_line = px.line(monthly, x="period_str", y=["Revenue", "Profit"],
                       markers=True, title="Tren Bulanan Revenue & Profit",
                       color_discrete_sequence=["#00FFFF", "#39FF14"], template="plotly_dark")
    st.plotly_chart(fig_line, use_container_width=True)

    if "category" in filtered_df.columns:
        cat_month = filtered_df.groupby(["period", "category"])["revenue"].sum().reset_index()
        cat_month["period_str"] = cat_month["period"].astype(str)
        fig_cat = px.bar(cat_month, x="period_str", y="revenue", color="category",
                         title="Perbandingan Revenue antar Kategori",
                         template="plotly_dark")
        st.plotly_chart(fig_cat, use_container_width=True)

    if not monthly.empty:
        best = monthly.loc[monthly["Revenue"].idxmax()]
        worst = monthly.loc[monthly["Revenue"].idxmin()]
        st.info(f"""
        **📅 Ringkasan:**
        - Bulan terbaik: **{best['period_str']}** (Revenue Rp {best['Revenue']:,.0f})
        - Bulan terendah: **{worst['period_str']}** (Revenue Rp {worst['Revenue']:,.0f})
        - Rata-rata profit bulanan: Rp {monthly['Profit'].mean():,.0f}
        """)

elif page == "👥 Analisis Pelanggan":
    st.header("👥 Analisis Pelanggan")

    if "payment_method" in filtered_df.columns:
        pay_share = filtered_df.groupby("payment_method")["id"].nunique().reset_index()
        fig_pay = px.bar(pay_share, x="payment_method", y="id", text_auto=True,
                         title="Distribusi Metode Pembayaran",
                         color="id", color_continuous_scale="Viridis", template="plotly_dark")
        st.plotly_chart(fig_pay, use_container_width=True)

    if "registered_date" in filtered_df.columns and "order_date" in filtered_df.columns:
        filtered_df["registered_date"] = pd.to_datetime(filtered_df["registered_date"], errors="coerce")
        filtered_df["is_new_customer"] = filtered_df["registered_date"].dt.year == filtered_df["year"]
        cust_share = filtered_df["is_new_customer"].value_counts().reset_index()
        cust_share.columns = ["Customer Type", "Count"]
        cust_share["Customer Type"] = cust_share["Customer Type"].map({True: "Pelanggan Baru", False: "Pelanggan Lama"})

        fig_donut = px.pie(cust_share, values="Count", names="Customer Type",
                           hole=0.4, title="Proporsi Pelanggan Baru vs Lama",
                           color_discrete_sequence=["#00FFFF", "#39FF14"], template="plotly_dark")
        st.plotly_chart(fig_donut, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total Customers", f"{filtered_df['customer_id'].nunique():,}")
    c2.metric("🛒 Rata-rata Order per Customer", f"{filtered_df.groupby('customer_id')['id'].nunique().mean():.2f}")
    c3.metric("💰 Rata-rata Revenue per Customer", f"Rp {filtered_df.groupby('customer_id')['revenue'].sum().mean():,.0f}")

st.markdown("---")
