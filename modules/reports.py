import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime, timedelta
from modules.database import get_db_connection

def dapatkan_laporan_penjualan(tanggal_mulai, tanggal_akhir):
    """Dapatkan laporan penjualan antara dua tanggal"""
    conn = get_db_connection()  # Ganti dengan get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                t.id_transaksi,
                t.tanggal_transaksi,
                t.nama_pelanggan,
                t.total_belanja,
                t.metode_pembayaran
            FROM transaksi t
            WHERE t.tanggal_transaksi BETWEEN ? AND ?
            ORDER BY t.tanggal_transaksi DESC
        """, (tanggal_mulai, tanggal_akhir + " 23:59:59"))
        
        transaksi = cursor.fetchall()
        return [dict(row) for row in transaksi]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def dapatkan_laporan_penjualan_produk(tanggal_mulai, tanggal_akhir):
    """Dapatkan laporan penjualan produk antara dua tanggal"""
    conn = get_db_connection()  # Ganti dengan get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                p.id_produk,
                p.nama as nama_produk,
                p.kategori,
                SUM(dt.jumlah) as total_jumlah,
                SUM(dt.subtotal) as total_penjualan
            FROM detail_transaksi dt
            JOIN transaksi t ON dt.id_transaksi = t.id_transaksi
            JOIN produk p ON dt.id_produk = p.id_produk
            WHERE t.tanggal_transaksi BETWEEN ? AND ?
            GROUP BY p.id_produk, p.nama, p.kategori
            ORDER BY total_penjualan DESC
        """, (tanggal_mulai, tanggal_akhir + " 23:59:59"))
        
        produk = cursor.fetchall()
        return [dict(row) for row in produk]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def dapatkan_laporan_penjualan_kategori(tanggal_mulai, tanggal_akhir):
    """Dapatkan laporan penjualan kategori antara dua tanggal"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                p.kategori,
                SUM(dt.jumlah) as total_jumlah,
                SUM(dt.subtotal) as total_penjualan
            FROM detail_transaksi dt
            JOIN transaksi t ON dt.id_transaksi = t.id_transaksi
            JOIN produk p ON dt.id_produk = p.id_produk
            WHERE t.tanggal_transaksi BETWEEN ? AND ?
            GROUP BY p.kategori
            ORDER BY total_penjualan DESC
        """, (tanggal_mulai, tanggal_akhir + " 23:59:59"))
        
        kategori = cursor.fetchall()
        return [dict(row) for row in kategori]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def dapatkan_laporan_metode_pembayaran(tanggal_mulai, tanggal_akhir):
    """Dapatkan laporan distribusi metode pembayaran"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                metode_pembayaran,
                COUNT(*) as jumlah_transaksi,
                SUM(total_belanja) as total_belanja
            FROM transaksi
            WHERE tanggal_transaksi BETWEEN ? AND ?
            GROUP BY metode_pembayaran
            ORDER BY total_belanja DESC
        """, (tanggal_mulai, tanggal_akhir + " 23:59:59"))
        
        metode_pembayaran = cursor.fetchall()
        return [dict(row) for row in metode_pembayaran]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def dapatkan_laporan_penjualan_harian(tanggal_mulai, tanggal_akhir):
    """Dapatkan laporan tren penjualan harian"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                DATE(tanggal_transaksi) as tanggal,
                COUNT(*) as jumlah_transaksi,
                SUM(total_belanja) as total_belanja
            FROM transaksi
            WHERE tanggal_transaksi BETWEEN ? AND ?
            GROUP BY DATE(tanggal_transaksi)
            ORDER BY tanggal
        """, (tanggal_mulai, tanggal_akhir + " 23:59:59"))
        
        penjualan_harian = cursor.fetchall()
        return [dict(row) for row in penjualan_harian]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def dapatkan_laporan_penjualan_perjam(tanggal_mulai, tanggal_akhir):
    """Dapatkan laporan distribusi penjualan per jam"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                strftime('%H', tanggal_transaksi) as jam,
                COUNT(*) as jumlah_transaksi,
                SUM(total_belanja) as total_belanja
            FROM transaksi
            WHERE tanggal_transaksi BETWEEN ? AND ?
            GROUP BY strftime('%H', tanggal_transaksi)
            ORDER BY jam
        """, (tanggal_mulai, tanggal_akhir + " 23:59:59"))
        
        penjualan_perjam = cursor.fetchall()
        
        # Format jam untuk tampilan yang lebih baik
        for entry in penjualan_perjam:
            entry['jam'] = f"{entry['jam']}:00"
        
        return [dict(row) for row in penjualan_perjam]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def dapatkan_laporan_inventaris():
    """Dapatkan laporan status inventaris terkini"""
    conn = get_db_connection()  # Ganti dengan get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                id_produk,
                nama,
                kategori,
                harga,
                stok,
                harga * stok as nilai_inventaris
            FROM produk
            ORDER BY nilai_inventaris DESC
        """)
        
        inventaris = cursor.fetchall()
        return [dict(row) for row in inventaris]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def dapatkan_laporan_stok_rendah(ambang_batas=10):
    """Dapatkan laporan peringatan stok rendah"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                id_produk,
                nama,
                kategori,
                harga,
                stok
            FROM produk
            WHERE stok <= ?
            ORDER BY stok
        """, (ambang_batas,))
        
        stok_rendah = cursor.fetchall()
        return [dict(row) for row in stok_rendah]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def buat_grafik_batang(data, x_col, y_col, judul, label_x, label_y):
    """Membuat grafik batang dari dataframe"""
    plt.figure(figsize=(10, 6))
    sns.barplot(x=x_col, y=y_col, data=data)
    plt.title(judul)
    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Simpan gambar ke buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def buat_grafik_pie(data, values_col, labels_col, judul):
    """Membuat grafik pie dari dataframe"""
    plt.figure(figsize=(8, 8))
    plt.pie(data[values_col], labels=data[labels_col], autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title(judul)
    plt.tight_layout()
    
    # Simpan gambar ke buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def buat_grafik_garis(data, x_col, y_col, judul, label_x, label_y):
    """Membuat grafik garis dari dataframe"""
    plt.figure(figsize=(10, 6))
    plt.plot(data[x_col], data[y_col], marker='o', linestyle='-')
    plt.title(judul)
    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Simpan gambar ke buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def dapatkan_gambar_base64(buf):
    """Konversi buffer gambar ke base64 untuk ditampilkan di HTML"""
    img_str = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def ekspor_ke_excel(data, nama_file):
    """Ekspor data ke file Excel"""
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Laporan', index=False)
    
    b64 = base64.b64encode(output.getvalue()).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{nama_file}">Unduh file Excel</a>'

def ekspor_ke_csv(data, nama_file):
    """Ekspor data ke file CSV"""
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:text/csv;base64,{b64}" download="{nama_file}">Unduh file CSV</a>'

def tampilkan_dashboard_penjualan():
    """Tampilkan UI dashboard penjualan di Streamlit"""
    st.header("Dashboard Penjualan")
    
    # Pemilih rentang tanggal
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.now().date()
        tanggal_mulai = st.date_input("Tanggal Mulai", today - timedelta(days=30))
    with col2:
        tanggal_akhir = st.date_input("Tanggal Akhir", today)
    
    if tanggal_mulai > tanggal_akhir:
        st.error("Tanggal akhir harus setelah tanggal mulai")
        return
    
    # Format tanggal untuk kueri SQL
    tanggal_mulai_str = tanggal_mulai.strftime("%Y-%m-%d")
    tanggal_akhir_str = tanggal_akhir.strftime("%Y-%m-%d")
    
    # Ringkasan penjualan
    data_penjualan = dapatkan_laporan_penjualan(tanggal_mulai_str, tanggal_akhir_str)
    if not data_penjualan:
        st.info(f"Tidak ada data penjualan dalam rentang {tanggal_mulai} hingga {tanggal_akhir}")
        return
    
    # Metrik ringkasan
    total_penjualan = sum(item['total_belanja'] for item in data_penjualan)
    total_transaksi = len(data_penjualan)
    rata_rata_transaksi = total_penjualan / total_transaksi if total_transaksi > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Penjualan", f"Rp {total_penjualan:,.0f}")
    with col2:
        st.metric("Jumlah Transaksi", f"{total_transaksi}")
    with col3:
        st.metric("Rata-rata Transaksi", f"Rp {rata_rata_transaksi:,.0f}")
    
    # Grafik
    st.subheader("Grafik Penjualan")
    jenis_grafik = st.selectbox("Pilih Grafik", [
        "Penjualan Harian", 
        "Distribusi Kategori", 
        "Metode Pembayaran",
        "Penjualan per Jam",
        "Produk Terlaris"
    ])
    
    if jenis_grafik == "Penjualan Harian":
        penjualan_harian = dapatkan_laporan_penjualan_harian(tanggal_mulai_str, tanggal_akhir_str)
        if penjualan_harian:
            df = pd.DataFrame(penjualan_harian)
            grafik = buat_grafik_garis(
                df, 'tanggal', 'total_belanja', 
                'Penjualan Harian', 'Tanggal', 'Total Penjualan (Rp)'
            )
            st.image(grafik)
    
    elif jenis_grafik == "Distribusi Kategori":
        penjualan_kategori = dapatkan_laporan_penjualan_kategori(tanggal_mulai_str, tanggal_akhir_str)
        if penjualan_kategori:
            df = pd.DataFrame(penjualan_kategori)
            grafik = buat_grafik_pie(
                df, 'total_penjualan', 'kategori', 
                'Distribusi Penjualan per Kategori'
            )
            st.image(grafik)
    
    elif jenis_grafik == "Metode Pembayaran":
        metode_pembayaran = dapatkan_laporan_metode_pembayaran(tanggal_mulai_str, tanggal_akhir_str)
        if metode_pembayaran:
            df = pd.DataFrame(metode_pembayaran)
            grafik = buat_grafik_batang(
                df, 'metode_pembayaran', 'total_belanja', 
                'Penjualan per Metode Pembayaran', 'Metode Pembayaran', 'Total Penjualan (Rp)'
            )
            st.image(grafik)
    
    elif jenis_grafik == "Penjualan per Jam":
        penjualan_perjam = dapatkan_laporan_penjualan_perjam(tanggal_mulai_str, tanggal_akhir_str)
        if penjualan_perjam:
            df = pd.DataFrame(penjualan_perjam)
            grafik = buat_grafik_batang(
                df, 'jam', 'total_belanja', 
                'Penjualan per Jam', 'Jam', 'Total Penjualan (Rp)'
            )
            st.image(grafik)
    
    elif jenis_grafik == "Produk Terlaris":
        penjualan_produk = dapatkan_laporan_penjualan_produk(tanggal_mulai_str, tanggal_akhir_str)
        if penjualan_produk:
            df = pd.DataFrame(penjualan_produk).head(10)  # 10 produk teratas
            grafik = buat_grafik_batang(
                df, 'nama_produk', 'total_penjualan', 
                '10 Produk Terlaris', 'Produk', 'Total Penjualan (Rp)'
            )
            st.image(grafik)
    
    # Tabel data detail
    st.subheader("Laporan Detail")
    jenis_laporan = st.selectbox("Pilih Laporan", [
        "Transaksi", 
        "Penjualan per Produk", 
        "Penjualan per Kategori",
        "Stok Inventaris",
        "Stok Menipis"
    ])
    
    if jenis_laporan == "Transaksi":
        data = data_penjualan
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(ekspor_ke_excel(data, f"transaksi_{tanggal_mulai_str}_to_{tanggal_akhir_str}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(ekspor_ke_csv(data, f"transaksi_{tanggal_mulai_str}_to_{tanggal_akhir_str}.csv"), unsafe_allow_html=True)
    
    elif jenis_laporan == "Penjualan per Produk":
        data = dapatkan_laporan_penjualan_produk(tanggal_mulai_str, tanggal_akhir_str)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(ekspor_ke_excel(data, f"produk_{tanggal_mulai_str}_to_{tanggal_akhir_str}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(ekspor_ke_csv(data, f"produk_{tanggal_mulai_str}_to_{tanggal_akhir_str}.csv"), unsafe_allow_html=True)
    
    elif jenis_laporan == "Penjualan per Kategori":
        data = dapatkan_laporan_penjualan_kategori(tanggal_mulai_str, tanggal_akhir_str)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(ekspor_ke_excel(data, f"kategori_{tanggal_mulai_str}_to_{tanggal_akhir_str}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(ekspor_ke_csv(data, f"kategori_{tanggal_mulai_str}_to_{tanggal_akhir_str}.csv"), unsafe_allow_html=True)
    
    elif jenis_laporan == "Stok Inventaris":
        data = dapatkan_laporan_inventaris()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(ekspor_ke_excel(data, f"inventaris_{datetime.now().strftime('%Y-%m-%d')}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(ekspor_ke_csv(data, f"inventaris_{datetime.now().strftime('%Y-%m-%d')}.csv"), unsafe_allow_html=True)
    
    elif jenis_laporan == "Stok Menipis":
        ambang_batas = st.number_input("Batas Stok Minimum", min_value=1, value=10)
        data = dapatkan_laporan_stok_rendah(ambang_batas)
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(ekspor_ke_excel(data, f"stok_menipis_{datetime.now().strftime('%Y-%m-%d')}.xlsx"), unsafe_allow_html=True)
            with col2:
                st.markdown(ekspor_ke_csv(data, f"stok_menipis_{datetime.now().strftime('%Y-%m-%d')}.csv"), unsafe_allow_html=True)

def tampilkan_laporan_inventaris():
    """Tampilkan UI laporan inventaris"""
    st.header("Laporan Inventaris")
    
    # Gambaran inventaris
    data_inventaris = dapatkan_laporan_inventaris()
    if not data_inventaris:
        st.info("Tidak ada data inventaris")
        return
    
    # Metrik ringkasan
    total_produk = len(data_inventaris)
    total_nilai_inventaris = sum(item['nilai_inventaris'] for item in data_inventaris)
    total_item = sum(item['stok'] for item in data_inventaris)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Produk", f"{total_produk}")
    with col2:
        st.metric("Total Stok", f"{total_item} unit")
    with col3:
        st.metric("Nilai Inventaris", f"Rp {total_nilai_inventaris:,.0f}")
    
    # Peringatan stok rendah
    stok_rendah = dapatkan_laporan_stok_rendah()
    if stok_rendah:
        st.subheader("⚠️ Peringatan Stok Menipis")
        st.write(f"Ada {len(stok_rendah)} produk dengan stok di bawah ambang batas (10 unit)")
        st.dataframe(pd.DataFrame(stok_rendah))
    
    # Inventaris berdasarkan kategori
    st.subheader("Inventaris per Kategori")
    df_inventaris = pd.DataFrame(data_inventaris)
    
    if not df_inventaris.empty:
        # Kelompokkan berdasarkan kategori
        inventaris_kategori = df_inventaris.groupby('kategori').agg({
            'stok': 'sum',
            'nilai_inventaris': 'sum'
        }).reset_index()
        
        # Buat grafik pie
        buf = buat_grafik_pie(inventaris_kategori, 'nilai_inventaris', 'kategori', 'Nilai Inventaris per Kategori')
        st.image(buf)
        
        # Tampilkan tabel
        st.dataframe(inventaris_kategori)
    
    # Daftar lengkap inventaris
    st.subheader("Daftar Lengkap Inventaris")
    st.dataframe(df_inventaris)
    
    # Opsi ekspor
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(ekspor_ke_excel(data_inventaris, f"inventaris_lengkap_{datetime.now().strftime('%Y-%m-%d')}.xlsx"), unsafe_allow_html=True)
    with col2:
        st.markdown(ekspor_ke_csv(data_inventaris, f"inventaris_lengkap_{datetime.now().strftime('%Y-%m-%d')}.csv"), unsafe_allow_html=True)

def tampilkan_performa_produk():
    """Tampilkan UI analisis performa produk"""
    st.header("Analisis Performa Produk")
    
    # Pemilih rentang tanggal
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.now().date()
        tanggal_mulai = st.date_input("Tanggal Mulai", today - timedelta(days=30))
    with col2:
        tanggal_akhir = st.date_input("Tanggal Akhir", today)
    
    if tanggal_mulai > tanggal_akhir:
        st.error("Tanggal akhir harus setelah tanggal mulai")
        return
    
    # Format tanggal untuk kueri SQL
    tanggal_mulai_str = tanggal_mulai.strftime("%Y-%m-%d")
    tanggal_akhir_str = tanggal_akhir.strftime("%Y-%m-%d")
    
    # Dapatkan data penjualan produk
    penjualan_produk = dapatkan_laporan_penjualan_produk(tanggal_mulai_str, tanggal_akhir_str)
    if not penjualan_produk:
        st.info(f"Tidak ada data penjualan produk dalam rentang {tanggal_mulai} hingga {tanggal_akhir}")
        return
    
    # Produk teratas
    st.subheader("Produk Terlaris")
    df_produk = pd.DataFrame(penjualan_produk)
    
    # 10 teratas berdasarkan jumlah
    teratas_jumlah = df_produk.sort_values('total_jumlah', ascending=False).head(10)
    st.write("Berdasarkan Jumlah Terjual:")
    buf = buat_grafik_batang(
        teratas_jumlah, 'nama_produk', 'total_jumlah', 
        '10 Produk Terlaris (Kuantitas)', 'Produk', 'Jumlah Terjual'
    )
    st.image(buf)
    
    # 10 teratas berdasarkan pendapatan
    teratas_pendapatan = df_produk.sort_values('total_penjualan', ascending=False).head(10)
    st.write("Berdasarkan Penjualan:")
    buf = buat_grafik_batang(
        teratas_pendapatan, 'nama_produk', 'total_penjualan', 
        '10 Produk Terlaris (Penjualan)', 'Produk', 'Total Penjualan (Rp)'
    )
    st.image(buf)
    
    # Performa kategori
    st.subheader("Performa Kategori")
    penjualan_kategori = dapatkan_laporan_penjualan_kategori(tanggal_mulai_str, tanggal_akhir_str)
    if penjualan_kategori:
        df_kategori = pd.DataFrame(penjualan_kategori)
        
        # Grafik pie kategori
        buf = buat_grafik_pie(
            df_kategori, 'total_penjualan', 'kategori', 
            'Distribusi Penjualan per Kategori'
        )
        st.image(buf)
        
        # Tabel kategori
        st.dataframe(df_kategori)
    
    # Tabel performa semua produk
    st.subheader("Performa Semua Produk")
    st.dataframe(df_produk)
    
    # Opsi ekspor
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(ekspor_ke_excel(penjualan_produk, f"performa_produk_{tanggal_mulai_str}_to_{tanggal_akhir_str}.xlsx"), unsafe_allow_html=True)
    with col2:
        st.markdown(ekspor_ke_csv(penjualan_produk, f"performa_produk_{tanggal_mulai_str}_to_{tanggal_akhir_str}.csv"), unsafe_allow_html=True)

def tampilkan_ui_laporan():
    """Fungsi UI utama untuk modul laporan"""
    st.title("Laporan dan Analisis")
    
    opsi_laporan = {
        "Dashboard Penjualan": tampilkan_dashboard_penjualan,
        "Laporan Inventaris": tampilkan_laporan_inventaris,
        "Performa Produk": tampilkan_performa_produk
    }
    
    laporan_terpilih = st.sidebar.selectbox("Pilih Laporan", list(opsi_laporan.keys()))
    
    # Tampilkan laporan yang dipilih
    opsi_laporan[laporan_terpilih]()

def reports_dashboard():
    """Alias untuk tampilkan_ui_laporan"""
    tampilkan_ui_laporan()
