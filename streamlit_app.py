import streamlit as st
from datetime import datetime
import pandas as pd

# Fungsi perhitungan tetap sama seperti aslinya
def calculate_depreciation(initial_cost, acquisition_date, useful_life, reporting_date, capitalizations=None, corrections=None):
    if capitalizations is None:
        capitalizations = []
    if corrections is None:
        corrections = []
    
    useful_life_semesters = useful_life * 2
    remaining_life = useful_life_semesters
    original_life = useful_life_semesters
    
    cap_dict = {}
    for cap in capitalizations:
        cap_year = cap['date'].year
        cap_semester = 1 if cap['date'].month <= 6 else 2
        key = (cap_year, cap_semester)
        cap_dict.setdefault(key, []).append(cap)
    
    correction_dict = {}
    for corr in corrections:
        corr_year = corr['date'].year
        corr_semester = 1 if corr['date'].month <= 6 else 2
        key = (corr_year, corr_semester)
        correction_dict.setdefault(key, []).append(corr)
    
    book_value = initial_cost
    current_year = acquisition_date.year
    current_semester = 1 if acquisition_date.month <= 6 else 2
    reporting_year = reporting_date.year
    reporting_semester = 1 if reporting_date.month <= 6 else 2
    reporting_key = (reporting_year, reporting_semester)
    
    accumulated_dep = 0
    schedule = []
    
    while remaining_life > 0 and (current_year, current_semester) <= reporting_key:
        current_key = (current_year, current_semester)
        
        # Proses kapitalisasi
        if current_key in cap_dict:
            for cap in cap_dict[current_key]:
                book_value += cap['amount']
                life_extension = cap.get('life_extension', 0) * 2
                remaining_life = min(remaining_life + life_extension, original_life)
        
        # Proses koreksi
        if current_key in correction_dict:
            for corr in correction_dict[current_key]:
                book_value -= corr['amount']
                # Pastikan book_value tidak menjadi negatif
                book_value = max(book_value, 0)
        
        if remaining_life <= 0 or book_value <= 0:
            break
        
        dep_per_semester = book_value / remaining_life
        accumulated_dep += dep_per_semester
        
        schedule.append({
            'year': current_year,
            'semester': current_semester,
            'depreciation': round(dep_per_semester, 2),
            'accumulated': round(accumulated_dep, 2),
            'book_value': round(book_value - dep_per_semester, 2),
            'sisa_mm': remaining_life - 1
        })
        
        book_value -= dep_per_semester
        remaining_life -= 1
        
        if current_semester == 1:
            current_semester = 2
        else:
            current_semester = 1
            current_year += 1
    
    return schedule

# UI Streamlit
st.title("Kalkulator Penyusutan Semesteran")

# Inisialisasi session state
if 'capitalizations' not in st.session_state:
    st.session_state.capitalizations = []
if 'corrections' not in st.session_state:
    st.session_state.corrections = []

# Input Parameter Utama
col1, col2 = st.columns(2)
with col1:
    acquisition_date = st.date_input(
        "Tanggal Perolehan", 
        value=datetime(2023, 1, 1),
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2024, 12, 31)
    )
    initial_cost = st.number_input("Initial Cost (Rp)", min_value=0.0, format="%.2f")
    if acquisition_date.year < 1900 or acquisition_date.year > 2024:
        st.error("❌ Tanggal Perolehan harus antara tahun 1900 sampai 2024")
        st.stop()

with col2:
    useful_life = st.number_input("Masa Manfaat (tahun)", min_value=1, step=1)
    reporting_date = st.date_input(
        "Tanggal Pelaporan", 
        value=datetime(2024, 12, 31),  # Default tanggal pelaporan
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2024, 12, 31)
    )

# Form Kapitalisasi
with st.expander("Tambah Kapitalisasi"):
    with st.form("kapitalisasi_form"):
        cap_col1, cap_col2, cap_col3 = st.columns(3)
        with cap_col1:
            cap_date = st.date_input("Tanggal Kapitalisasi", key="cap_date")
        with cap_col2:
            cap_amount = st.number_input("Jumlah (Rp)", key="cap_amount", min_value=0.0)
        with cap_col3:
            life_extension = st.number_input("Perpanjangan Masa Manfaat (tahun)", key="life_ext", min_value=0, step=1)
        
        if st.form_submit_button("Tambah Kapitalisasi"):
            if cap_date < acquisition_date or cap_date > reporting_date:
                st.error("Tanggal harus antara Tanggal Perolehan dan Pelaporan")
            else:
                st.session_state.capitalizations.append({
                    'date': cap_date,
                    'amount': cap_amount,
                    'life_extension': life_extension
                })
                st.success("Kapitalisasi ditambahkan")

# Form Koreksi
with st.expander("Tambah Koreksi"):
    with st.form("koreksi_form"):
        corr_col1, corr_col2 = st.columns(2)
        with corr_col1:
            corr_date = st.date_input("Tanggal Koreksi", key="corr_date")
        with corr_col2:
            corr_amount = st.number_input("Jumlah Koreksi (Rp)", key="corr_amount", min_value=0.0)
        
        if st.form_submit_button("Tambah Koreksi"):
            if corr_date < acquisition_date or corr_date > reporting_date:
                st.error("Tanggal harus antara Tanggal Perolehan dan Pelaporan")
            else:
                st.session_state.corrections.append({
                    'date': corr_date,
                    'amount': corr_amount
                })
                st.success("Koreksi ditambahkan")

# Tampilkan Kapitalisasi
if st.session_state.capitalizations:
    st.subheader("Daftar Kapitalisasi")
    cap_df = pd.DataFrame([{
        'Tanggal': cap['date'].strftime("%d/%m/%Y"),
        'Jumlah': f"Rp{cap['amount']:,.2f}",
        'Perpanjangan': f"{cap['life_extension']} tahun"
    } for cap in st.session_state.capitalizations])
    st.dataframe(cap_df, use_container_width=True)

# Tampilkan Koreksi
if st.session_state.corrections:
    st.subheader("Daftar Koreksi")
    corr_df = pd.DataFrame([{
        'Tanggal': corr['date'].strftime("%d/%m/%Y"),
        'Jumlah': f"Rp{corr['amount']:,.2f}"
    } for corr in st.session_state.corrections])
    st.dataframe(corr_df, use_container_width=True)

# Tombol Aksi
action_col1, action_col2, action_col3 = st.columns([1,1,2])
with action_col1:
    if st.button("🔄 Reset Semua"):
        st.session_state.capitalizations = []
        st.session_state.corrections = []
        st.rerun()
        
with action_col2:
    if st.button("💾 Export Excel"):
        if 'schedule' in st.session_state:
            df = pd.DataFrame(st.session_state.schedule)
            df['Semester'] = df['semester'].apply(lambda x: f"Semester {x}")
            df = df.rename(columns={
                'year': 'Tahun',
                'semester': 'Semester',
                'depreciation': 'Penyusutan',
                'accumulated': 'Akumulasi',
                'book_value': 'Nilai Buku',
                'sisa_mm': 'Sisa MM'
            })
            
            # Konversi format mata uang
            currency_cols = ['Penyusutan', 'Akumulasi', 'Nilai Buku']
            for col in currency_cols:
                df[col] = df[col].apply(lambda x: f"Rp{x:,.2f}")
            
            st.download_button(
                label="Download Excel",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name="depresiasi.csv",
                mime="text/csv"
            )

# Hitung Penyusutan
if st.button("🧮 Hitung Penyusutan"):
    try:
        schedule = calculate_depreciation(
            initial_cost=initial_cost,
            acquisition_date=acquisition_date,
            useful_life=useful_life,
            reporting_date=reporting_date,
            capitalizations=st.session_state.capitalizations,
            corrections=st.session_state.corrections
        )
        
        st.session_state.schedule = schedule
        
        # Format hasil untuk tampilan
        df = pd.DataFrame(schedule)
        df['Semester'] = df['semester'].apply(lambda x: f"Semester {x}")
        df['Penyusutan'] = df['depreciation'].apply(lambda x: f"Rp{x:,.2f}")
        df['Akumulasi'] = df['accumulated'].apply(lambda x: f"Rp{x:,.2f}")
        df['Nilai Buku'] = df['book_value'].apply(lambda x: f"Rp{x:,.2f}")
        
        st.subheader("Jadwal Penyusutan")
        st.dataframe(df[['year', 'Semester', 'Penyusutan', 'Akumulasi', 'Nilai Buku', 'sisa_mm']]
                     .rename(columns={'year': 'Tahun', 'sisa_mm': 'Sisa MM'}),
                     use_container_width=True,
                     hide_index=True)
        
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
