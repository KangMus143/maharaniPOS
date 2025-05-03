import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime, timedelta
from modules.database import get_db_connection

def get_sales_report(start_date, end_date):
    """Get sales report between two dates"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                t.transaction_id,
                t.transaction_date,
                t.customer_name,
                t.total_amount,
                t.payment_method
            FROM transactions t
            WHERE t.transaction_date BETWEEN ? AND ?
            ORDER BY t.transaction_date DESC
        """, (start_date, end_date + " 23:59:59"))
        
        transactions = cursor.fetchall()
        return [dict(row) for row in transactions]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def get_product_sales_report(start_date, end_date):
    """Get product sales report between two dates"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                p.product_id,
                p.name as product_name,
                p.category,
                SUM(td.quantity) as total_quantity,
                SUM(td.subtotal) as total_sales
            FROM transaction_details td
            JOIN transactions t ON td.transaction_id = t.transaction_id
            JOIN products p ON td.product_id = p.product_id
            WHERE t.transaction_date BETWEEN ? AND ?
            GROUP BY p.product_id, p.name, p.category
            ORDER BY total_sales DESC
        """, (start_date, end_date + " 23:59:59"))
        
        products = cursor.fetchall()
        return [dict(row) for row in products]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def get_category_sales_report(start_date, end_date):
    """Get category sales report between two dates"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                p.category,
                SUM(td.quantity) as total_quantity,
                SUM(td.subtotal) as total_sales
            FROM transaction_details td
            JOIN transactions t ON td.transaction_id = t.transaction_id
            JOIN products p ON td.product_id = p.product_id
            WHERE t.transaction_date BETWEEN ? AND ?
            GROUP BY p.category
            ORDER BY total_sales DESC
        """, (start_date, end_date + " 23:59:59"))
        
        categories = cursor.fetchall()
        return [dict(row) for row in categories]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def get_payment_method_report(start_date, end_date):
    """Get payment method distribution report"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                payment_method,
                COUNT(*) as transaction_count,
                SUM(total_amount) as total_amount
            FROM transactions
            WHERE transaction_date BETWEEN ? AND ?
            GROUP BY payment_method
            ORDER BY total_amount DESC
        """, (start_date, end_date + " 23:59:59"))
        
        payment_methods = cursor.fetchall()
        return [dict(row) for row in payment_methods]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def get_daily_sales_report(start_date, end_date):
    """Get daily sales trend report"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                DATE(transaction_date) as date,
                COUNT(*) as transaction_count,
                SUM(total_amount) as total_amount
            FROM transactions
            WHERE transaction_date BETWEEN ? AND ?
            GROUP BY DATE(transaction_date)
            ORDER BY date
        """, (start_date, end_date + " 23:59:59"))
        
        daily_sales = cursor.fetchall()
        return [dict(row) for row in daily_sales]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def get_hourly_sales_report(start_date, end_date):
    """Get hourly sales distribution report"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                strftime('%H', transaction_date) as hour,
                COUNT(*) as transaction_count,
                SUM(total_amount) as total_amount
            FROM transactions
            WHERE transaction_date BETWEEN ? AND ?
            GROUP BY strftime('%H', transaction_date)
            ORDER BY hour
        """, (start_date, end_date + " 23:59:59"))
        
        hourly_sales = cursor.fetchall()
        
        # Format hour for better display
        for entry in hourly_sales:
            entry['hour'] = f"{entry['hour']}:00"
        
        return [dict(row) for row in hourly_sales]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def get_inventory_report():
    """Get current inventory status report"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                product_id,
                name,
                category,
                price,
                stock,
                price * stock as inventory_value
            FROM products
            ORDER BY inventory_value DESC
        """)
        
        inventory = cursor.fetchall()
        return [dict(row) for row in inventory]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def get_low_stock_report(threshold=10):
    """Get low stock alert report"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                product_id,
                name,
                category,
                price,
                stock
            FROM products
            WHERE stock <= ?
            ORDER BY stock
        """, (threshold,))
        
        low_stock = cursor.fetchall()
        return [dict(row) for row in low_stock]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def create_bar_chart(data, x_col, y_col, title, x_label, y_label):
    """Create a bar chart from dataframe"""
    plt.figure(figsize=(10, 6))
    sns.barplot(x=x_col, y=y_col, data=data)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save figure to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def create_pie_chart(data, values_col, labels_col, title):
    """Create a pie chart from dataframe"""
    plt.figure(figsize=(8, 8))
    plt.pie(data[values_col], labels=data[labels_col], autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title(title)
    plt.tight_layout()
    
    # Save figure to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def create_line_chart(data, x_col, y_col, title, x_label, y_label):
    """Create a line chart from dataframe"""
    plt.figure(figsize=(10, 6))
    plt.plot(data[x_col], data[y_col], marker='o', linestyle='-')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save figure to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def get_image_base64(buf):
    """Convert image buffer to base64 for display in HTML"""
    img_str = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def export_to_excel(data, filename):
    """Export data to Excel file"""
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Report', index=False)
    
    b64 = base64.b64encode(output.getvalue()).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel file</a>'

def export_to_csv(data, filename):
    """Export data to CSV file"""
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:text/csv;base64,{b64}" download="{filename}">Download CSV file</a>'

def display_sales_dashboard():
    """Display sales dashboard UI in Streamlit"""
    st.header("Dashboard Penjualan")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.now().date()
        start_date = st.date_input("Tanggal Mulai", today - timedelta(days=30))
    with col2:
        end_date = st.date_input("Tanggal Akhir", today)
    
    if start_date > end_date:
        st.error("Tanggal akhir harus setelah tanggal mulai")
        return
    
    # Format dates for SQL query
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # Sales summary
    sales_data = get_sales_report(start_date_str, end_date_str)
    if not sales_data:
        st.info(f"Tidak ada data penjualan dalam rentang {start_date} hingga {end_date}")
        return
    
    # Summary metrics
    total_sales = sum(item['total_amount'] for item in sales_data)
    total_transactions = len(sales_data)
    avg_transaction = total_sales / total_transactions if total_transactions > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Penjualan", f"Rp {total_sales:,.0f}")
    with col2:
        st.metric("Jumlah Transaksi", f"{total_transactions}")
    with col3:
        st.metric("Rata-rata Transaksi", f"Rp {avg_transaction:,.0f}")
    
    # Charts
    st.subheader("Grafik Penjualan")
    chart_type = st.selectbox("Pilih Grafik", [
        "Penjualan Harian", 
        "Distribusi Kategori", 
        "Metode Pembayaran",
        "Penjualan per Jam",
        "Produk Terlaris"
    ])
    
    if chart_type == "Penjualan Harian":
        daily_sales = get_daily_sales_report(start_date_str, end_date_str)
        if daily_sales:
            df = pd.DataFrame(daily_sales)
            chart = create_line_chart(
                df, 'date', 'total_amount', 
                'Penjualan Harian', 'Tanggal', 'Total Penjualan (Rp)'
            )
            st.image(chart)
    
    elif chart_type == "Distribusi Kategori":
        category_sales = get_category_sales_report(start_date_str, end_date_str)
        if category_sales:
            df = pd.DataFrame(category_sales)
            chart = create_pie_chart(
                df, 'total_sales', 'category', 
                'Distribusi Penjualan per Kategori'
            )
            st.image(chart)
    
    elif chart_type == "Metode Pembayaran":
        payment_methods = get_payment_method_report(start_date_str, end_date_str)
        if payment_methods:
            df = pd.DataFrame(payment_methods)
            chart = create_bar_chart(
                df, 'payment_method', 'total_amount', 
                'Penjualan per Metode Pembayaran', 'Metode Pembayaran', 'Total Penjualan (Rp)'
            )
            st.image(chart)
    
    elif chart_type == "Penjualan per Jam":
        hourly_sales = get_hourly_sales_report(start_date_str, end_date_str)
        if hourly_sales:
            df = pd.DataFrame(hourly_sales)
            chart = create_bar_chart(
                df, 'hour', 'total_amount', 
                'Penjualan per Jam', 'Jam', 'Total Penjualan (Rp)'
            )
            st.image(chart)
    
    elif chart_type == "Produk Terlaris":
        product_sales = get_product_sales_report(start_date_str, end_date_str)
        if product_sales:
            df = pd.DataFrame(product_sales).head(10)  # Top 10 products
            chart = create_bar_chart(
                df, 'product_name', 'total_sales', 
                '10 Produk Terlaris', 'Produk', 'Total Penjualan (Rp)'
            )
            st.image(chart)
    
    # Detailed data tables
    st.subheader("Laporan Detail")
    report_type = st.selectbox("Pilih Laporan", [
        "Transaksi", 
        "Penjualan per Produk", 
        "Penjualan per Kategori",
        "Stok Inventaris",
        "Stok Menipis"
    ])
    
    if report_type == "Transaksi":
        data = sales_data
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(export_to_excel(data, f"transaksi_{start_date_str}_to_{end_date_str}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(export_to_csv(data, f"transaksi_{start_date_str}_to_{end_date_str}.csv"), unsafe_allow_html=True)
    
    elif report_type == "Penjualan per Produk":
        data = get_product_sales_report(start_date_str, end_date_str)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(export_to_excel(data, f"produk_{start_date_str}_to_{end_date_str}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(export_to_csv(data, f"produk_{start_date_str}_to_{end_date_str}.csv"), unsafe_allow_html=True)
    
    elif report_type == "Penjualan per Kategori":
        data = get_category_sales_report(start_date_str, end_date_str)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(export_to_excel(data, f"kategori_{start_date_str}_to_{end_date_str}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(export_to_csv(data, f"kategori_{start_date_str}_to_{end_date_str}.csv"), unsafe_allow_html=True)
    
    elif report_type == "Stok Inventaris":
        data = get_inventory_report()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(export_to_excel(data, f"inventaris_{datetime.now().strftime('%Y-%m-%d')}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(export_to_csv(data, f"inventaris_{datetime.now().strftime('%Y-%m-%d')}.csv"), unsafe_allow_html=True)
    
    elif report_type == "Stok Menipis":
        threshold = st.number_input("Batas Stok Minimum", min_value=1, value=10)
        data = get_low_stock_report(threshold)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(export_to_excel(data, f"stok_menipis_{datetime.now().strftime('%Y-%m-%d')}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(export_to_csv(data, f"stok_menipis_{datetime.now().strftime('%Y-%m-%d')}.csv"), unsafe_allow_html=True)

def display_report_ui():
    """Main UI function for reports module"""
    st.title("Laporan dan Analisis")
    
    report_options = {
        "Dashboard Penjualan": display_sales_dashboard,
        "Laporan Inventaris": display_inventory_report,
        "Performa Produk": display_product_performance
    }
    
    selected_report = st.sidebar.selectbox("Pilih Laporan", list(report_options.keys()))
    
    # Display the selected report
    report_options[selected_report]()

def display_inventory_report():
    """Display inventory report UI"""
    st.header("Laporan Inventaris")
    
    # Inventory overview
    inventory_data = get_inventory_report()
    if not inventory_data:
        st.info("Tidak ada data inventaris")
        return
    
    # Summary metrics
    total_products = len(inventory_data)
    total_inventory_value = sum(item['inventory_value'] for item in inventory_data)
    total_items = sum(item['stock'] for item in inventory_data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Produk", f"{total_products}")
    with col2:
        st.metric("Total Stok", f"{total_items} unit")
    with col3:
        st.metric("Nilai Inventaris", f"Rp {total_inventory_value:,.0f}")
    
    # Low stock alerts
    low_stock = get_low_stock_report()
    if low_stock:
        st.subheader("⚠️ Peringatan Stok Menipis")
        st.write(f"Ada {len(low_stock)} produk dengan stok di bawah ambang batas (10 unit)")
        st.dataframe(pd.DataFrame(low_stock))
    
    # Inventory by category
    st.subheader("Inventaris per Kategori")
    df_inventory = pd.DataFrame(inventory_data)
    
    if not df_inventory.empty:
        # Group by category
        category_inventory = df_inventory.groupby('category').agg({
            'stock': 'sum',
            'inventory_value': 'sum'
        }).reset_index()
        
        # Create pie chart
        buf = create_pie_chart(category_inventory, 'inventory_value', 'category', 'Nilai Inventaris per Kategori')
        st.image(buf)
        
        # Display table
        st.dataframe(category_inventory)
    
    # Complete inventory listing
    st.subheader("Daftar Lengkap Inventaris")
    st.dataframe(df_inventory)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(export_to_excel(inventory_data, f"inventaris_lengkap_{datetime.now().strftime('%Y-%m-%d')}.xlsx"), unsafe_allow_html=True)
    with col2:
        st.markdown(export_to_csv(inventory_data, f"inventaris_lengkap_{datetime.now().strftime('%Y-%m-%d')}.csv"), unsafe_allow_html=True)

def display_product_performance():
    """Display product performance analysis UI"""
    st.header("Analisis Performa Produk")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.now().date()
        start_date = st.date_input("Tanggal Mulai", today - timedelta(days=30))
    with col2:
        end_date = st.date_input("Tanggal Akhir", today)
    
    if start_date > end_date:
        st.error("Tanggal akhir harus setelah tanggal mulai")
        return
    
    # Format dates for SQL query
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # Get product sales data
    product_sales = get_product_sales_report(start_date_str, end_date_str)
    if not product_sales:
        st.info(f"Tidak ada data penjualan produk dalam rentang {start_date} hingga {end_date}")
        return
    
    # Top products
    st.subheader("Produk Terlaris")
    df_products = pd.DataFrame(product_sales)
    
    # Top 10 by quantity
    top_by_quantity = df_products.sort_values('total_quantity', ascending=False).head(10)
    st.write("Berdasarkan Jumlah Terjual:")
    buf = create_bar_chart(
        top_by_quantity, 'product_name', 'total_quantity', 
        '10 Produk Terlaris (Kuantitas)', 'Produk', 'Jumlah Terjual'
    )
    st.image(buf)
    
    # Top 10 by revenue
    top_by_revenue = df_products.sort_values('total_sales', ascending=False).head(10)
    st.write("Berdasarkan Penjualan:")
    buf = create_bar_chart(
        top_by_revenue, 'product_name', 'total_sales', 
        '10 Produk Terlaris (Penjualan)', 'Produk', 'Total Penjualan (Rp)'
    )
    st.image(buf)
    
    # Category performance
    st.subheader("Performa Kategori")
    category_sales = get_category_sales_report(start_date_str, end_date_str)
    if category_sales:
        df_categories = pd.DataFrame(category_sales)
        
        # Category pie chart
        buf = create_pie_chart(
            df_categories, 'total_sales', 'category', 
            'Distribusi Penjualan per Kategori'
        )
        st.image(buf)
        
        # Category table
        st.dataframe(df_categories)
    
    # Complete product performance table
    st.subheader("Performa Semua Produk")
    st.dataframe(df_products)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(export_to_excel(product_sales, f"performa_produk_{start_date_str}_to_{end_date_str}.xlsx"), unsafe_allow_html=True)
    with col2:
        st.markdown(export_to_csv(product_sales, f"performa_produk_{start_date_str}_to_{end_date_str}.csv"), unsafe_allow_html=True)
