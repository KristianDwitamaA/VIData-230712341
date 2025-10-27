import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ======================================================
# KONFIGURASI DASAR
# ======================================================
st.set_page_config(page_title="UTS Visualisasi & Interpretasi Data A", layout="wide")

# ======================================================
# FUNGSI LOAD DATA
# ======================================================
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file)

        # --- Konversi tanggal ---
        if "order_date" in df.columns:
            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
            df = df[df["order_date"].notna()]
            df["year"] = df["order_date"].dt.year
            df["month_name"] = df["order_date"].dt.strftime("%b")
            df["order_period"] = df["order_date"].dt.to_period("M")

        # --- Revenue & Profit ---
        if "after_discount" in df.columns:
            df["revenue"] = df["after_discount"]
        elif "before_discount" in df.columns:
            df["revenue"] = df["before_discount"]
        if "cogs" in df.columns and "revenue" in df.columns:
            df["profit"] = df["revenue"] - df["cogs"]

        # --- Quantity ---
        if "qty_ordered" in df.columns:
            df["qty_ordered"] = pd.to_numeric(df["qty_ordered"], errors="coerce").fillna(0).astype(int)

        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

# ======================================================
# SIDEBAR: INPUT DATA
# ======================================================
st.sidebar.header("⚙️ Data & Filter")

default_path = Path("Copy of finalProj_df - 2022.csv")

uploaded_file = st.sidebar.file_uploader("📂 Upload File CSV", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
elif default_path.exists():
    st.sidebar.info("Menggunakan file default lokal (karena belum upload).")
    df = load_data(default_path)
else:
    st.warning("Silakan upload file CSV terlebih dahulu.")
    st.stop()

if df.empty:
    st.error("Dataset kosong atau gagal dibaca.")
    st.stop()

# ======================================================
# FILTER GLOBAL
# ======================================================
years = sorted(df["year"].dropna().unique().tolist()) if "year" in df.columns else []
categories = sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else []

selected_years = st.sidebar.multiselect("Pilih Tahun", years, default=years)
selected_cats = st.sidebar.multiselect("Pilih Kategori Produk", categories, default=categories)

filtered_df = df.copy()
if selected_years:
    filtered_df = filtered_df[filtered_df["year"].isin(selected_years)]
if selected_cats:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_cats)]

df_2022 = filtered_df[filtered_df["year"] == 2022]

# ======================================================
# NAVIGASI HALAMAN
# ======================================================
st.sidebar.markdown("---")
page = st.sidebar.radio("📑 Pilih Halaman Dashboard:", ["📊 Product Sales", "📈 Campaign Performance"])

# ======================================================
# KPI GLOBAL
# ======================================================
st.title("🧠 UTS Visualisasi dan Interpretasi Data A")
st.caption("Kristian Dwitama Adiyaksa - 230712341")

def safe_sum(df, col): return df[col].sum() if col in df.columns else 0
def safe_nunique(df, col): return df[col].nunique() if col in df.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Total Revenue", f"Rp {safe_sum(filtered_df, 'revenue'):,.0f}")
c2.metric("📦 Total Orders", f"{safe_nunique(filtered_df, 'id'):,}")
c3.metric("👥 Unique Customers", f"{safe_nunique(filtered_df, 'customer_id'):,}")
c4.metric("💹 Total Profit", f"Rp {safe_sum(filtered_df, 'profit'):,.0f}")

st.markdown("---")

# ======================================================
# DASHBOARD 1 - PRODUCT SALES
# ======================================================
if page == "📊 Product Sales":
    st.header("📊 Dashboard 1 – Product Sales (2022, All Categories)")

    q2022 = safe_sum(df_2022, "qty_ordered")
    c2022 = safe_nunique(df_2022, "customer_id")
    o2022 = safe_nunique(df_2022, "id")

    k1, k2, k3 = st.columns(3)
    k1.metric("🛒 Quantity (2022)", f"{q2022:,}")
    k2.metric("👥 Customers (2022)", f"{c2022:,}")
    k3.metric("📦 Orders (2022)", f"{o2022:,}")

    st.markdown("---")

    # --- Detail Transaksi ---
    st.subheader("📋 Detail Transaksi (2022)")
    cols = ["order_date", "category", "payment_method", "sku_name", "qty_ordered",
            "revenue", "profit", "customer_id", "id"]
    if all(c in df_2022.columns for c in cols):
        st.dataframe(df_2022[cols].sort_values("order_date", ascending=False), height=360)
    else:
        st.warning("Kolom transaksi tidak lengkap di dataset.")

    st.markdown("---")

    # --- Share Orders per Payment ---
    st.subheader("💳 Share Orders per Payment (2022)")
    if "payment_method" in df_2022.columns and "id" in df_2022.columns:
        pay_share = df_2022.groupby("payment_method")["id"].nunique().reset_index()
        pay_share.columns = ["Payment Method", "Orders"]

        col1, col2 = st.columns(2)
        col1.dataframe(pay_share.sort_values("Orders", ascending=False))
        fig_pay = px.bar(
            pay_share.sort_values("Orders", ascending=False),
            x="Payment Method",
            y="Orders",
            text_auto=True,
            color="Orders",
            color_continuous_scale="Tealgrn",
            title="Jumlah Orders per Metode Pembayaran (2022)"
        )
        col2.plotly_chart(fig_pay, config={"displayModeBar": False})
    else:
        st.info("Kolom 'payment_method' tidak tersedia di dataset.")

# ======================================================
# DASHBOARD 2 - CAMPAIGN PERFORMANCE
# ======================================================
elif page == "📈 Campaign Performance":
    st.header("📈 Dashboard 2 – Campaign Performance (2022)")

    orders = safe_nunique(df_2022, "id")
    custs = safe_nunique(df_2022, "customer_id")
    val = safe_sum(df_2022, "before_discount") if "before_discount" in df_2022.columns else safe_sum(df_2022, "revenue")
    rev = safe_sum(df_2022, "revenue")
    aov = (rev / orders) if orders > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📦 Orders", f"{orders:,}")
    c2.metric("👥 Customers", f"{custs:,}")
    c3.metric("💸 Value", f"Rp {val:,.0f}")
    c4.metric("💰 Revenue", f"Rp {rev:,.0f}")
    c5.metric("📊 AOV", f"Rp {aov:,.0f}")

    st.markdown("---")

    # --- Tren Bulanan ---
    st.subheader("📅 Tren Bulanan 2022 (Orders, Revenue, AOV)")
    if "order_period" in df_2022.columns:
        monthly = df_2022.groupby("order_period").agg(
            orders=("id", "nunique"),
            revenue=("revenue", "sum")
        ).reset_index()
        monthly["aov"] = monthly["revenue"] / monthly["orders"]
        monthly["order_period_str"] = monthly["order_period"].astype(str)

        fig_trend = px.line(
            monthly,
            x="order_period_str",
            y=["orders", "revenue", "aov"],
            markers=True,
            title="Tren Bulanan 2022: Orders / Revenue / AOV"
        )
        st.plotly_chart(fig_trend, config={"displayModeBar": False})
    else:
        st.info("Kolom tanggal tidak tersedia untuk membuat tren bulanan.")

    st.markdown("---")

    # --- Performa Produk ---
    st.subheader("📋 Performa Produk (2022)")
    if "sku_name" in df_2022.columns:
        prod_perf = df_2022.groupby("sku_name").agg(
            Category=("category", "first"),
            Revenue=("revenue", "sum"),
            Profit=("profit", "sum"),
            Quantity=("qty_ordered", "sum"),
            Customers=("customer_id", "nunique"),
            Orders=("id", "nunique")
        ).reset_index().sort_values("Revenue", ascending=False)
        st.dataframe(prod_perf.head(30), height=360)

        st.subheader("🏆 Top 10 Produk Berdasarkan Revenue (2022)")
        top10 = prod_perf.head(10)
        fig_top10 = px.bar(
            top10,
            x="Revenue",
            y="sku_name",
            orientation="h",
            text_auto=True,
            title="Top 10 Produk – Revenue 2022",
            color="Revenue",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_top10, config={"displayModeBar": False})
    else:
        st.info("Kolom 'sku_name' tidak tersedia di dataset.")

    st.markdown("---")

    # --- Tren Produk Terpilih ---
    st.subheader("📈 Tren Bulanan Produk Terpilih (2022)")
    if "sku_name" in df_2022.columns and "order_period" in df_2022.columns:
        product_opts = sorted(df_2022["sku_name"].dropna().unique().tolist())
        selected_products = st.multiselect("Pilih Produk:", product_opts, default=product_opts[:3])
        if selected_products:
            prod_trend = df_2022[df_2022["sku_name"].isin(selected_products)]
            prod_trend = prod_trend.groupby(["order_period", "sku_name"])["revenue"].sum().reset_index()
            prod_trend["order_period_str"] = prod_trend["order_period"].astype(str)

            fig_prod = px.line(
                prod_trend,
                x="order_period_str",
                y="revenue",
                color="sku_name",
                markers=True,
                title="Tren Penjualan Produk Terpilih (Revenue, 2022)"
            )
            st.plotly_chart(fig_prod, config={"displayModeBar": False})
        else:
            st.warning("Pilih minimal satu produk untuk melihat tren.")
    else:
        st.info("Kolom produk atau tanggal tidak tersedia.")

    st.markdown("---")

    # --- Insight Otomatis ---
    st.subheader("🧠 Ringkasan Tren & Rekomendasi Aksi")
    if "monthly" in locals() and not monthly.empty:
        best_month = monthly.loc[monthly["revenue"].idxmax(), "order_period_str"]
        top_product = prod_perf.iloc[0]["sku_name"] if "prod_perf" in locals() else "-"
        st.info(f"""
        **Ringkasan Tren:**
        - Bulan dengan revenue tertinggi: **{best_month}**
        - Produk dengan kontribusi terbesar: **{top_product}**
        - AOV rata-rata tahun 2022: Rp {aov:,.0f}
        """)
        st.write("""
        **🚀 Rekomendasi Aksi:**
        1. Fokus promosi di bulan dengan revenue tertinggi.
        2. Kampanyekan produk dengan revenue tertinggi.
        3. Pertahankan metode pembayaran populer.
        4. Evaluasi produk margin rendah untuk efisiensi.
        """)
    else:
        st.warning("Tidak cukup data untuk insight otomatis.")

st.markdown("---")
st.caption("© 2025 | UTS Visualisasi & Interpretasi Data A | Kristian Dwitama Adiyaksa - 230712341")
