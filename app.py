import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sales Data Analysis System", layout="wide")

REQUIRED_COLUMNS = [
    "Order ID",
    "Date",
    "Customer",
    "Product",
    "Category",
    "Region",
    "Quantity",
    "Unit Price",
]


def empty_sales_data():
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def prepare_sales_data(data):
    df = data.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors="coerce").fillna(0)
    df = df.dropna(subset=["Date"])
    df["Revenue"] = df["Quantity"] * df["Unit Price"]
    return df


def show_dashboard(data):
    df = prepare_sales_data(data)

    if df.empty:
        st.warning("No valid sales data yet. Upload a CSV or enter a sale manually.")
        return

    st.sidebar.header("Filters")

    regions = st.sidebar.multiselect(
        "Select Region",
        options=sorted(df["Region"].dropna().unique()),
        default=sorted(df["Region"].dropna().unique()),
    )

    categories = st.sidebar.multiselect(
        "Select Category",
        options=sorted(df["Category"].dropna().unique()),
        default=sorted(df["Category"].dropna().unique()),
    )

    filtered_df = df[
        (df["Region"].isin(regions)) &
        (df["Category"].isin(categories))
    ]

    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
        return

    st.subheader("Sales Data Preview")
    st.dataframe(filtered_df, use_container_width=True)

    total_revenue = filtered_df["Revenue"].sum()
    total_orders = filtered_df["Order ID"].nunique()
    total_quantity = filtered_df["Quantity"].sum()
    average_order_value = total_revenue / total_orders if total_orders else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"Rs {total_revenue:,.2f}")
    col2.metric("Total Orders", total_orders)
    col3.metric("Items Sold", int(total_quantity))
    col4.metric("Avg Order Value", f"Rs {average_order_value:,.2f}")

    chart_col1, chart_col2 = st.columns(2)

    filtered_df["Month"] = filtered_df["Date"].dt.to_period("M").astype(str)
    monthly_sales = filtered_df.groupby("Month", as_index=False)["Revenue"].sum()

    fig_monthly = px.line(
        monthly_sales,
        x="Month",
        y="Revenue",
        markers=True,
        title="Monthly Sales Trend",
    )
    chart_col1.plotly_chart(fig_monthly, use_container_width=True)

    category_sales = filtered_df.groupby("Category", as_index=False)["Revenue"].sum()
    fig_category = px.bar(
        category_sales,
        x="Category",
        y="Revenue",
        title="Sales by Category",
    )
    chart_col2.plotly_chart(fig_category, use_container_width=True)

    region_sales = filtered_df.groupby("Region", as_index=False)["Revenue"].sum()
    fig_region = px.pie(
        region_sales,
        names="Region",
        values="Revenue",
        title="Sales by Region",
    )
    st.plotly_chart(fig_region, use_container_width=True)

    st.subheader("Top Selling Products")
    top_products = (
        filtered_df.groupby("Product", as_index=False)
        .agg({"Quantity": "sum", "Revenue": "sum"})
        .sort_values(by="Revenue", ascending=False)
    )
    st.dataframe(top_products, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Filtered Data",
        data=csv,
        file_name="sales_report.csv",
        mime="text/csv",
    )


if "manual_sales" not in st.session_state:
    st.session_state.manual_sales = empty_sales_data()

st.title("Sales Data Analysis System")

entry_tab, upload_tab, dashboard_tab = st.tabs(
    ["Enter Data", "Upload CSV", "Dashboard"]
)

with entry_tab:
    st.subheader("Enter a Sale")

    with st.form("sales_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        order_id = col1.text_input("Order ID")
        date = col2.date_input("Date")
        customer = col1.text_input("Customer")
        product = col2.text_input("Product")
        category = col1.text_input("Category")
        region = col2.text_input("Region")
        quantity = col1.number_input("Quantity", min_value=1, step=1)
        unit_price = col2.number_input("Unit Price", min_value=0.0, step=100.0)

        submitted = st.form_submit_button("Add Sale")

        if submitted:
            if not order_id or not customer or not product or not category or not region:
                st.error("Please fill in all text fields.")
            else:
                new_sale = pd.DataFrame(
                    [
                        {
                            "Order ID": order_id,
                            "Date": date,
                            "Customer": customer,
                            "Product": product,
                            "Category": category,
                            "Region": region,
                            "Quantity": quantity,
                            "Unit Price": unit_price,
                        }
                    ]
                )
                st.session_state.manual_sales = pd.concat(
                    [st.session_state.manual_sales, new_sale],
                    ignore_index=True,
                )
                st.success("Sale added successfully.")

    if not st.session_state.manual_sales.empty:
        st.subheader("Entered Sales")
        edited_sales = st.data_editor(
            st.session_state.manual_sales,
            use_container_width=True,
            num_rows="dynamic",
            key="manual_sales_editor",
        )

        save_col, clear_col = st.columns([1, 4])

        if save_col.button("Save Changes"):
            st.session_state.manual_sales = edited_sales[REQUIRED_COLUMNS].reset_index(
                drop=True
            )
            st.success("Changes saved.")

        if clear_col.button("Clear Entered Sales"):
            st.session_state.manual_sales = empty_sales_data()
            st.rerun()

with upload_tab:
    st.subheader("Upload Sales CSV")
    uploaded_file = st.file_uploader("Upload your sales CSV file", type=["csv"])

    if uploaded_file:
        uploaded_df = pd.read_csv(uploaded_file)
        missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in uploaded_df.columns
        ]

        if missing_columns:
            st.error("Missing columns: " + ", ".join(missing_columns))
        else:
            st.session_state.uploaded_sales = uploaded_df[REQUIRED_COLUMNS]
            st.success("CSV uploaded successfully.")
            st.dataframe(st.session_state.uploaded_sales, use_container_width=True)

    st.caption(
        "Required columns: Order ID, Date, Customer, Product, Category, Region, Quantity, Unit Price"
    )

with dashboard_tab:
    st.subheader("Sales Dashboard")

    data_sources = []

    if not st.session_state.manual_sales.empty:
        data_sources.append(st.session_state.manual_sales)

    if "uploaded_sales" in st.session_state:
        data_sources.append(st.session_state.uploaded_sales)

    if data_sources:
        all_sales = pd.concat(data_sources, ignore_index=True)
    else:
        all_sales = empty_sales_data()

    show_dashboard(all_sales)
