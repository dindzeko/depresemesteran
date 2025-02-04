import streamlit as st
from datetime import datetime
import pandas as pd

# Fungsi perhitungan tetap sama seperti aslinya
def calculate_depreciation(initial_cost, acquisition_date, useful_life, reporting_date, capitalizations=None):
    if capitalizations is None:
        capitalizations = []
    
    useful_life_semesters = useful_life * 2
    remaining_life = useful_life_semesters
    original_life = useful_life_semesters
    
    cap_dict = {}
    for cap in capitalizations:
        cap_year = cap['date'].year
        cap_semester = 1 if cap['date'].month <= 6 else 2
        key = (cap_year, cap_semester)
        cap_dict.setdefault(key, []).append(cap)
    
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
        if current_key in cap_dict:
            for cap in cap_dict[current_key]:
                book_value += cap['amount']
                life_extension = cap.get('life_extension', 0) * 2
                remaining_life = min(remaining_life + life_extension, original_life)
        
        if remaining_life <= 0:
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

# Input Parameter Utama
col1, col2 = st.columns(2)
with col1:
    acquisition_date = st.date_input("Tanggal Perolehan", value=datetime(2023, 1, 1))
    initial_cost = st.number_input("Initial Cost (Rp)", min_value=0.0, format="%.2f")
    
with col2:
    useful_life = st.number_input("Masa Manfaat (tahun)", min_value=1, step=1)
    reporting_date = st.date_input("Tanggal Pelaporan", value=datetime.now())

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

# Tampilkan Kapitalisasi
if st.session_state.capitalizations:
    st.subheader("Daftar Kapitalisasi")
    cap_df = pd.DataFrame([{
        'Tanggal': cap['date'].strftime("%d/%m/%Y"),
        'Jumlah': f"Rp{cap['amount']:,.2f}",
        'Perpanjangan': f"{cap['life_extension']} tahun"
    } for cap in st.session_state.capitalizations])
    st.dataframe(cap_df, use_container_width=True)
    
    if st.button("Hapus Semua Kapitalisasi"):
        st.session_state.capitalizations = []
        st.rerun()

# Tombol Aksi
action_col1, action_col2, action_col3 = st.columns([1,1,2])
with action_col1:
    if st.button("🔄 Reset Semua"):
        st.session_state.capitalizations = []
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
            capitalizations=st.session_state.capitalizations
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
