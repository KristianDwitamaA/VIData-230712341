import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Smart Retail Dashboard", layout="wide")

st.markdown("""
    <style>
        body {background-color: #0E1117; color: #FAFAFA;}
        .stApp {background-color: rgba(14, 17, 23, 0.85);}
        .stSidebar {background: rgba(20, 20, 20, 0.6);}
        h1, h2, h3, h4, h5 {color: #00FFFF;}
        [data-testid="stMetricValue"] {color: #39FF14;}
        .block-container {padding-top: 1rem;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "Copy of finalProj_df - 2022.csv"
    df = pd.read_csv(file_path)
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df = df.dropna(subset=["order_date"])
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
    if "registered_date" in df.columns:
        df["registered_date"] = pd.to_datetime(df["registered_date"], errors="coerce")
        df["is_new_customer"] = (df["registered_date"].dt.year == df["year"]).fillna(False)
    return df

df = load_data()

st.sidebar.title("🧭 Navigasi")
page = st.sidebar.radio("Pilih Halaman:", [
    "📊 Analisis Penjualan Produk",
    "📈 Analisis Tren Bulanan",
    "🧩 Perbandingan Produk & Kategori",
    "📑 Informasi Penjualan",
    "🔍 Pencarian Data",
    "👥 Analisis Pelanggan"
])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Filter Data")

years = sorted(df["year"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect("📆 Pilih Tahun", years, default=years)
st.sidebar.markdown("### 🏷️ Pilih Kategori Produk")
categories = sorted(df["category"].dropna().unique().tolist())
select_all_cats = st.sidebar.checkbox("Pilih Semua Kategori", value=True)
selected_cats = categories if select_all_cats else st.sidebar.multiselect("Pilih Kategori:", categories)
st.sidebar.markdown("### 🧾 Pilih Produk")
products = sorted(df["sku_name"].dropna().unique().tolist())
select_all_prods = st.sidebar.checkbox("Pilih Semua Produk", value=False)
selected_prods = products if select_all_prods else st.sidebar.multiselect("Pilih Produk:", products)
st.sidebar.markdown("### 💳 Pilih Metode Pembayaran")
if "payment_method" in df.columns:
    pay_methods = sorted(df["payment_method"].dropna().unique().tolist())
    select_all_pay = st.sidebar.checkbox("Pilih Semua Metode Pembayaran", value=True)
    selected_pay = pay_methods if select_all_pay else st.sidebar.multiselect("Pilih Metode Pembayaran:", pay_methods, default=[])
else:
    selected_pay = []
st.sidebar.markdown("### 👥 Jenis Pelanggan")
customer_filter = st.sidebar.radio("Tampilkan Data Berdasarkan:", ["Semua Pelanggan", "Pelanggan Baru", "Pelanggan Lama"], horizontal=True)
st.sidebar.markdown("### 🧮 Jumlah Data yang Ditampilkan")
top_n = st.sidebar.slider("Tampilkan Top N Produk/Kategori:", 5, 30, 10)

filtered_df = df.copy()
if selected_years:
    filtered_df = filtered_df[filtered_df["year"].isin(selected_years)]
if selected_cats:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_cats)]
if selected_prods:
    filtered_df = filtered_df[filtered_df["sku_name"].isin(selected_prods)]
if selected_pay:
    filtered_df = filtered_df[filtered_df["payment_method"].isin(selected_pay)]
if customer_filter == "Pelanggan Baru":
    filtered_df = filtered_df[filtered_df.get("is_new_customer") == True]
elif customer_filter == "Pelanggan Lama":
    filtered_df = filtered_df[filtered_df.get("is_new_customer") == False]

st.title("📈 Smart Retail Dashboard")
st.caption("UTS VID A | Kristian Dwitama Adiyaksa | 230712341")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Revenue", f"Rp {filtered_df['revenue'].sum():,.0f}")
col2.metric("📦 Total Orders", f"{filtered_df['id'].nunique():,}")
col3.metric("👥 Unique Customers", f"{filtered_df['customer_id'].nunique():,}")
col4.metric("💹 Total Profit", f"Rp {filtered_df['profit'].sum():,.0f}")
st.markdown("---")

if page == "📊 Analisis Penjualan Produk":
    st.header("📊 Analisis Penjualan Produk")
    cat_rev = filtered_df.groupby("category")["revenue"].sum().nlargest(top_n).reset_index()
    fig_pie = px.pie(cat_rev, values="revenue", names="category",
                     title=f"Kontribusi Revenue (Top {top_n} Kategori)",
                     color_discrete_sequence=px.colors.sequential.Tealgrn, template="plotly_dark")
    st.plotly_chart(fig_pie, use_container_width=True)
    top_products = filtered_df.groupby("sku_name")["revenue"].sum().nlargest(top_n).reset_index()
    fig_bar = px.bar(top_products, x="revenue", y="sku_name",
                     orientation="h", title=f"Top {top_n} Produk Berdasarkan Revenue",
                     color="revenue", color_continuous_scale="Blues", template="plotly_dark")
    st.plotly_chart(fig_bar, use_container_width=True)

elif page == "📈 Analisis Tren Bulanan":
    st.header("📈 Analisis Tren Bulanan")
    if filtered_df.empty:
        st.warning("⚠️ Tidak ada data sesuai filter.")
    else:
        monthly = filtered_df.groupby("period").agg(Revenue=("revenue", "sum"), Profit=("profit", "sum")).reset_index()
        monthly["period_str"] = monthly["period"].astype(str)
        fig_line = px.line(monthly, x="period_str", y=["Revenue", "Profit"],
                           markers=True, title="📆 Tren Bulanan Revenue & Profit",
                           color_discrete_sequence=["#00FFFF", "#39FF14"], template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)
        if "category" in filtered_df.columns:
            cat_month = filtered_df.groupby(["period", "category"])["revenue"].sum().reset_index()
            cat_month["period_str"] = cat_month["period"].astype(str)
            fig_cat = px.bar(cat_month, x="period_str", y="revenue", color="category",
                             title="📊 Perbandingan Revenue antar Kategori per Bulan",
                             template="plotly_dark")
            st.plotly_chart(fig_cat, use_container_width=True)

elif page == "🧩 Perbandingan Produk & Kategori":
    st.header("🧩 Perbandingan Produk & Kategori")
    compare_type = st.radio("Bandingkan Berdasarkan:", ["Kategori", "Produk"], horizontal=True)
    if compare_type == "Kategori":
        cat_opts = sorted(filtered_df["category"].dropna().unique().tolist())
        cat1 = st.selectbox("Kategori 1:", cat_opts)
        cat2 = st.selectbox("Kategori 2:", cat_opts, index=1 if len(cat_opts) > 1 else 0)
        comp = filtered_df[filtered_df["category"].isin([cat1, cat2])]
        comp_group = comp.groupby(["period", "category"])["revenue"].sum().reset_index()
        comp_group["period_str"] = comp_group["period"].astype(str)
        fig_comp = px.line(comp_group, x="period_str", y="revenue", color="category", markers=True,
                           title=f"Perbandingan Revenue: {cat1} vs {cat2}",
                           color_discrete_sequence=["#00FFFF", "#39FF14"], template="plotly_dark")
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        prod_opts = sorted(filtered_df["sku_name"].dropna().unique().tolist())
        p1 = st.selectbox("Produk 1:", prod_opts)
        p2 = st.selectbox("Produk 2:", prod_opts, index=1 if len(prod_opts) > 1 else 0)
        comp = filtered_df[filtered_df["sku_name"].isin([p1, p2])]
        comp_group = comp.groupby(["period", "sku_name"])["revenue"].sum().reset_index()
        comp_group["period_str"] = comp_group["period"].astype(str)
        fig_prod = px.line(comp_group, x="period_str", y="revenue", color="sku_name", markers=True,
                           title=f"Perbandingan Revenue: {p1} vs {p2}",
                           color_discrete_sequence=["#00FFFF", "#39FF14"], template="plotly_dark")
        st.plotly_chart(fig_prod, use_container_width=True)

elif page == "📑 Informasi Penjualan":
    st.header("📑 Informasi Penjualan")
    if not filtered_df.empty:
        best_month = filtered_df.groupby("month")["revenue"].sum().idxmax()
        best_category = filtered_df.groupby("category")["profit"].sum().idxmax()
        top_product = filtered_df.groupby("sku_name")["revenue"].sum().idxmax()
        st.success(f"💡 Bulan dengan revenue tertinggi: **{best_month}**")
        st.info(f"🏆 Kategori paling menguntungkan: **{best_category}**")
        st.warning(f"🔥 Produk dengan penjualan tertinggi: **{top_product}**")
        monthly = filtered_df.groupby("period")["revenue"].sum().reset_index().sort_values("period")
        monthly["period_str"] = monthly["period"].astype(str)
        monthly["pct_change"] = monthly["revenue"].pct_change() * 100
        latest_change = monthly["pct_change"].iloc[-1] if len(monthly) > 1 else None
        if pd.notna(latest_change):
            if latest_change > 0:
                st.markdown(f"<span style='color:#39FF14;'>📈 Revenue meningkat **{latest_change:.2f}%** dibanding bulan sebelumnya.</span>", unsafe_allow_html=True)
            elif latest_change < 0:
                st.markdown(f"<span style='color:#FF3131;'>📉 Revenue menurun **{abs(latest_change):.2f}%** dibanding bulan sebelumnya.</span>", unsafe_allow_html=True)
            else:
                st.markdown("⏸️ Tidak ada perubahan revenue dibanding bulan sebelumnya.")
        else:
            st.info("Belum cukup data untuk menghitung perubahan revenue antar bulan.")
        fig_trend = px.line(monthly, x="period_str", y="revenue", markers=True,
                            title="Tren Revenue Keseluruhan per Bulan",
                            color_discrete_sequence=["#00FFFF"], template="plotly_dark")
        st.plotly_chart(fig_trend, use_container_width=True)

elif page == "🔍 Pencarian Data":
    st.header("🔍 Pencarian Data Produk dan Transaksi")
    st.write("Gunakan kolom pencarian di bawah untuk menemukan produk atau data transaksi tertentu dengan cepat dan interaktif.")
    search_query = st.text_input("🔎 Cari Produk / Kategori / Metode Pembayaran:", "").strip().lower()
    if search_query:
        search_results = filtered_df[
            filtered_df.apply(
                lambda row: (
                    search_query in str(row["sku_name"]).lower()
                    or search_query in str(row["category"]).lower()
                    or search_query in str(row.get("payment_method", "")).lower()
                    or search_query in str(row.get("customer_id", "")).lower()
                ),
                axis=1
            )
        ]
        st.success(f"Ditemukan **{len(search_results)}** baris data yang cocok dengan kata kunci: **{search_query}**")
        st.dataframe(search_results, use_container_width=True, height=500)
    else:
        st.info("Ketik kata kunci untuk mencari produk, kategori, atau metode pembayaran tertentu.")
        st.dataframe(filtered_df, use_container_width=True, height=500)
    st.caption("💡 Tips: Anda dapat mencari berdasarkan nama produk, kategori, metode pembayaran, atau ID pelanggan.")

elif page == "👥 Analisis Pelanggan":
    st.header("👥 Analisis Pelanggan")
    if "payment_method" in filtered_df.columns:
        pay_share = filtered_df.groupby("payment_method")["id"].nunique().reset_index()
        fig_pay = px.bar(pay_share, x="payment_method", y="id", text_auto=True,
                         title="Distribusi Metode Pembayaran",
                         color="id", color_continuous_scale="Viridis", template="plotly_dark")
        st.plotly_chart(fig_pay, use_container_width=True)
    if "is_new_customer" in filtered_df.columns:
        cust_share = filtered_df["is_new_customer"].value_counts().reset_index()
        cust_share.columns = ["Customer Type", "Count"]
        cust_share["Customer Type"] = cust_share["Customer Type"].map({True: "Pelanggan Baru", False: "Pelanggan Lama"})
        fig_donut = px.pie(cust_share, values="Count", names="Customer Type",
                           hole=0.4, title="Proporsi Pelanggan Baru vs Lama",
                           color_discrete_sequence=["#00FFFF", "#39FF14"], template="plotly_dark")
        st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")
