import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sales Data Analysis System", layout="wide")

st.title("Sales Data Analysis System")

uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    df["Date"] = pd.to_datetime(df["Date"])
    df["Revenue"] = df["Quantity"] * df["Unit Price"]

    st.sidebar.header("Filters")

    regions = st.sidebar.multiselect(
        "Select Region",
        options=df["Region"].unique(),
        default=df["Region"].unique()
    )

    categories = st.sidebar.multiselect(
        "Select Category",
        options=df["Category"].unique(),
        default=df["Category"].unique()
    )

    df = df[
        (df["Region"].isin(regions)) &
        (df["Category"].isin(categories))
    ]

    st.subheader("Sales Data Preview")
    st.dataframe(df)

    total_revenue = df["Revenue"].sum()
    total_orders = df["Order ID"].nunique()
    total_quantity = df["Quantity"].sum()
    average_order_value = total_revenue / total_orders if total_orders else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    col2.metric("Total Orders", total_orders)
    col3.metric("Items Sold", total_quantity)
    col4.metric("Avg Order Value", f"₹{average_order_value:,.2f}")

    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    monthly_sales = df.groupby("Month", as_index=False)["Revenue"].sum()

    fig_monthly = px.line(
        monthly_sales,
        x="Month",
        y="Revenue",
        markers=True,
        title="Monthly Sales Trend"
    )

    st.plotly_chart(fig_monthly, use_container_width=True)

    category_sales = df.groupby("Category", as_index=False)["Revenue"].sum()

    fig_category = px.bar(
        category_sales,
        x="Category",
        y="Revenue",
        title="Sales by Category"
    )

    st.plotly_chart(fig_category, use_container_width=True)

    region_sales = df.groupby("Region", as_index=False)["Revenue"].sum()

    fig_region = px.pie(
        region_sales,
        names="Region",
        values="Revenue",
        title="Sales by Region"
    )

    st.plotly_chart(fig_region, use_container_width=True)

    st.subheader("Top Selling Products")

    top_products = (
        df.groupby("Product", as_index=False)
        .agg({"Quantity": "sum", "Revenue": "sum"})
        .sort_values(by="Revenue", ascending=False)
    )

    st.dataframe(top_products)

else:
    st.info("Upload a CSV file to begin analysis.")