import streamlit as st
import dashscope
from dashscope import Generation, MultiModalConversation
import time
import pandas as pd

# ==============================
# KONFIGURASI DASAR
# ==============================
DASHSCOPE_API_KEY = 'sk-3267b1bc571f48f6aa26160953d4f387'  # Ganti dengan API key Anda
dashscope.api_key = DASHSCOPE_API_KEY

# ==============================
# SETUP TAMPILAN
# ==============================
st.set_page_config(
    page_title="🕌 Halal & Allergy Food Scanner",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Kustom
st.markdown("""
<style>
    :root {
        --primary: #4CAF50;  /* Hijau untuk halal */
        --secondary: #FF5252;  /* Merah untuk alergi */
        --accent: #2196F3;
        --text-primary: #000000;
        --bg-primary: #FFFFFF;
        --card-bg: #F5F5F5;
        --border-color: #E0E0E0;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --text-primary: #FFFFFF;
            --bg-primary: #121212;
            --card-bg: #1E1E1E;
            --border-color: #333333;
        }
    }
    
    .halal-badge {
        background-color: #4CAF50;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        display: inline-block;
    }
    
    .haram-badge {
        background-color: #FF5252;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        display: inline-block;
    }
    
    .allergy-warning {
        border-left: 4px solid #FF9800;
        padding-left: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# FUNGSI UTAMA
# ==============================
def analyze_food(food_desc, user_allergies=[]):
    """Analisis makanan untuk halal dan alergi"""
    messages = [
        {
            'role': 'system',
            'content': f"""Anda adalah ahli makanan halal dan alergi. Berikan analisis dengan format:
            🍽️ **Nama Makanan**: [nama]
            🕌 **Status Halal**: [Halal/Haram/Syubhat]
               - Alasan: [penjelasan]
            ⚠️ **Deteksi Alergen**: 
               - [daftar alergen yang terdeteksi]
               - Reaksi untuk: {', '.join(user_allergies) if user_allergies else 'Tidak ada alergi terdaftar'}
            💡 **Saran**: [rekomendasi]
            
            Gunakan bahasa Indonesia sederhana."""
        },
        {
            'role': 'user',
            'content': food_desc
        }
    ]
    
    response = Generation.call(
        model="qwen-turbo",
        messages=messages,
        result_format='message'
    )
    return response.output.choices[0].message.content

def analyze_food_image(image_url):
    """Analisis gambar makanan"""
    response = MultiModalConversation.call(
        model="qwen-vl-plus",
        messages=[
            {
                "role": "user",
                "content": [
                    {"image": image_url},
                    {"text": "Analisis makanan ini untuk bahan haram dan alergen umum (kacang, seafood, gluten, susu). Berikan output dalam format: Bahan: [list], Status Halal: [Ya/Tidak], Alergen: [list]"}
                ]
            }
        ]
    )
    return response.output.choices[0].message.content

# ==============================
# TAB ANALISIS MAKANAN
# ==============================
def tab_analysis():
    st.header("🔍 Halal & Allergy Scanner", divider="green")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        tab_text, tab_image = st.tabs(["📝 Text Input", "🖼️ Image Scan"])
        
        with tab_text:
            food_desc = st.text_area(
                "Deskripsikan makanan/minuman:",
                placeholder="Contoh: 'Nasi padang dengan rendang + es teh manis'",
                height=150,
                key="food_input"
            )
            
            user_allergies = st.multiselect(
                "Alergi Anda:",
                ["Kacang", "Seafood", "Gluten", "Susu", "Telur", "Laktosa"],
                key="allergies"
            )
            
            if st.button("🔍 Analisis Sekarang", use_container_width=True):
                if not food_desc.strip():
                    st.warning("Mohon isi deskripsi makanan")
                else:
                    with st.spinner("Menganalisis kehalalan dan alergen..."):
                        try:
                            start_time = time.time()
                            result = analyze_food(food_desc, user_allergies)
                            process_time = time.time() - start_time
                            
                            st.markdown(f"""
                            <div class="custom-card fade-in">
                                <h3 style="color: var(--primary); margin-top: 0;">HASIL ANALISIS</h3>
                                <small>Diproses dalam {process_time:.1f} detik</small>
                                {result}
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"⚠️ Error: {str(e)}")
        
        with tab_image:
            uploaded_file = st.file_uploader("Upload gambar makanan", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                st.image(uploaded_file, caption="Gambar yang diupload", use_column_width=True)
                if st.button("🖼️ Scan Gambar", use_container_width=True):
                    with st.spinner("Menganalisis gambar..."):
                        try:
                            # Simpan gambar ke temporary file
                            with open("temp_image.jpg", "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            start_time = time.time()
                            result = analyze_food_image("temp_image.jpg")
                            process_time = time.time() - start_time
                            
                            st.markdown(f"""
                            <div class="custom-card fade-in">
                                <h3 style="color: var(--primary); margin-top: 0;">HASIL ANALISIS GAMBAR</h3>
                                <small>Diproses dalam {process_time:.1f} detik</small>
                                {result}
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"⚠️ Error: {str(e)}")
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <h4 style="margin-top: 0;">🍱 Contoh Makanan</h4>
            <ul>
                <li><strong>Rendang Daging</strong> (Halal, mengandung santan)</li>
                <li><strong>Bakso Babi</strong> (Haram, mengandung daging babi)</li>
                <li><strong>Salad Caesar</strong> (Syubhat, mungkin mengandung bacon)</li>
                <li><strong>Kue Coklat</strong> (Mengandung telur dan gluten)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card">
            <h4 style="margin-top: 0;">📌 Panduan Cepat</h4>
            <p><span class="halal-badge">HALAL</span> Makanan yang diizinkan</p>
            <p><span class="haram-badge">HARAM</span> Makanan yang dilarang</p>
            <p><strong>SYUBHAT</strong> Status meragukan, perlu dicek lebih lanjut</p>
            <div class="allergy-warning">
                <strong>⚠️ PERHATIAN:</strong> Selalu konfirmasi ke merchant untuk alergi parah
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# TAB RESTORAN HALAL
# ==============================
def tab_restaurants():
    st.header("🏪 Restoran Halal Terdekat", divider="blue")
    
    # Data contoh restoran
    halal_restaurants = pd.DataFrame({
        'Nama': ['Warung Steak Halal', 'RM Padang Sederhana', 'KFC Halal', 'Solaria'],
        'Jarak': ['0.5 km', '1.2 km', '2.0 km', '3.5 km'],
        'Rating': [4.8, 4.5, 4.3, 4.0],
        'Sertifikat': ['MUI', 'MUI', 'JAKIM', 'MUI'],
        'Alergen': ['Kacang, Susu', 'Seafood', 'Gluten, Telur', 'Kacang, MSG']
    })
    
    st.dataframe(
        halal_restaurants,
        column_config={
            "Rating": st.column_config.NumberColumn(
                format="%.1f ⭐",
            )
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.map(pd.DataFrame({
        'lat': [-6.200000, -6.201000, -6.199000, -6.205000],
        'lon': [106.816666, 106.815000, 106.818000, 106.812000],
        'name': halal_restaurants['Nama']
    }))

# ==============================
# TAMPILAN UTAMA
# ==============================
st.title("🕌 Halal & Allergy Food Scanner")
st.markdown("Deteksi kehalalan dan alergen makanan dengan AI")

tab1, tab2 = st.tabs(["🔍 Food Scanner", "🏪 Restoran Halal"])

with tab1:
    tab_analysis()

with tab2:
    tab_restaurants()

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-primary); font-size: 0.9rem; opacity: 0.7;">
    © 2025 HalalGuard AI | Dibangun dengan Alibaba Cloud Qwen | Tidak menggantikan sertifikasi resmi
</div>
""", unsafe_allow_html=True)