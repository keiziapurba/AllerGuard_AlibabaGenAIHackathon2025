import streamlit as st
import dashscope
from dashscope import Generation, ImageSynthesis
import time
import base64
from PIL import Image
import io
import requests
import os

# ==============================
# KONFIGURASI DASAR
# ==============================
DASHSCOPE_API_KEY = [API_KEY]
dashscope.api_key = DASHSCOPE_API_KEY
dashscope.base_http_api_url = [API_URL]

# ==============================
# SETUP TAMPILAN UNIVERSAL
# ==============================
st.set_page_config(
    page_title="AllerGuard",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Kustom (Universal Theme)
st.markdown("""
<style>
    :root {
        --primary: #4CAF50;
        --secondary: #FF5252;
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
        background-color: var(--primary);
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    
    .haram-badge {
        background-color: var(--secondary);
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    
    .syubhat-badge {
        background-color: #FFC107;
        color: black;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    
    .allergy-warning {
        border-left: 4px solid #FF9800;
        padding-left: 15px;
        margin: 15px 0;
        font-weight: bold;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding: 0 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 15px 30px !important;
        border-radius: 10px 10px 0 0 !important;
        background: var(--card-bg) !important;
        margin: 0 5px !important;
        font-weight: bold !important;
        transition: all 0.3s !important;
        border: 1px solid var(--border-color) !important;
        font-size: 1.1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
        border-color: var(--accent) !important;
    }
    
    .custom-card {
        border-radius: 15px;
        padding: 25px;
        background: var(--card-bg);
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        margin-bottom: 25px;
        border-left: 6px solid var(--accent);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    .object-detection-result {
        margin-top: 15px;
        padding: 15px;
        background: rgba(33, 150, 243, 0.1);
        border-radius: 10px;
        border-left: 4px solid var(--accent);
    }
    
    .detected-object {
        display: inline-block;
        margin: 5px;
        padding: 5px 10px;
        background: #e3f2fd;
        border-radius: 15px;
        font-size: 0.9em;
    }
    
    .confidence-bar {
        height: 5px;
        background: #bbdefb;
        margin-top: 3px;
        border-radius: 3px;
    }
    
    .confidence-fill {
        height: 100%;
        background: var(--accent);
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# FUNGSI UTAMA
# ==============================
def analyze_halal(food_desc, user_allergies=[]):
    """Analisis makanan untuk halal dan alergi"""
    messages = [
        {
            'role': 'system',
            'content': f"""Anda adalah ahli makanan halal dan alergi. Berikan analisis dengan format:
            
            **🍽️ Nama Makanan**: [nama]
            
            **🕌 Status Halal**: 
            - [Halal/Haram/Syubhat]
            - Alasan: [penjelasan rinci dengan dasar syar'i]
            
            **⚠️ Deteksi Alergen**: 
            - Bahan berisiko: [daftar]
            - Reaksi untuk: {', '.join(user_allergies) if user_allergies else 'Tidak ada alergi terdaftar'}
            
            **💡 Saran Konsumsi**: 
            - [rekomendasi untuk muslim]
            - [alternatif jika haram/syubhat]
            
            Gunakan bahasa Indonesia formal."""
        },
        {
            'role': 'user',
            'content': food_desc
        }
    ]
    
    response = Generation.call(
        model="qwen-turbo",
        messages=messages,
        result_format='message',
        api_key=DASHSCOPE_API_KEY
    )
    return response.output.choices[0].message.content

def generate_halal_alternative(food_name):
    """Generate alternatif makanan halal"""
    response = Generation.call(
        model="qwen-turbo",
        prompt=f"""Berikan 3 alternatif halal untuk {food_name} dengan format:
        1. [Nama Makanan]
           - Bahan: [daftar]
           - Keunggulan: [penjelasan]
        2. [Nama Makanan]
           ... dan seterusnya""",
        api_key=DASHSCOPE_API_KEY
    )
    return response.output.text

def generate_halal_image(prompt):
    """Generate gambar makanan halal"""
    response = ImageSynthesis.call(
        model="wanxiang-v1",
        prompt=f"{prompt} yang halal dan sehat",
        n=1,
        size="1024x1024",
        api_key=DASHSCOPE_API_KEY
    )
    return response.output.images[0].url

def detect_objects_in_image(uploaded_file):
    """Deteksi objek dalam gambar menggunakan model computer vision"""
    try:
        # Simpan gambar sementara
        img = Image.open(uploaded_file)
        temp_path = "temp_upload.jpg"
        img.save(temp_path)
        
        # Contoh panggilan ke API model computer vision
        # GANTI DENGAN API ENDPOINT ANDA SENDIRI
        api_url = "https://your-custom-model-api.com/predict"  # Contoh endpoint
        
        # Jika menggunakan DashScope Image Understanding
        if DASHSCOPE_API_KEY:
            from dashscope import ImageUnderstanding
            response = ImageUnderstanding.call(
                model="resnet50",
                image=base64.b64encode(uploaded_file.getvalue()).decode(),
                task="classification"
            )
            
            if hasattr(response, 'output'):
                predictions = response.output.get('predictions', [])
                if predictions:
                    result = "**Objek Terdeteksi:**\n\n"
                    for pred in predictions[:5]:  # Ambil 5 prediksi teratas
                        label = pred.get('label', 'Unknown')
                        confidence = pred.get('confidence', 0)
                        result += f"<div class='detected-object'>{label} <small>({confidence:.0%})</small>"
                        result += f"<div class='confidence-bar'><div class='confidence-fill' style='width:{confidence*100}%'></div></div></div>"
                    return result
        
        # Fallback jika API tidak tersedia
        return "⚠️ Model deteksi objek belum dikonfigurasi. Silakan deploy model computer vision terlebih dahulu."
    
    except Exception as e:
        return f"❌ Error dalam deteksi objek: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ==============================
# TAB 1: ANALISIS MAKANAN
# ==============================
def tab_analysis():
    st.header("🔍 Analisis Kehalalan", divider="blue")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        tab1, tab2 = st.tabs(["📝 Deskripsi Makanan", "🖼️ Upload Gambar"])
        
        with tab1:
            food_name = st.text_input("Nama Makanan/Minuman:")
            ingredients = st.text_area("Daftar Bahan (pisahkan dengan koma):", height=150)
            user_allergies = st.multiselect(
                "Alergi Anda:", 
                ["Kacang", "Seafood", "Gluten", "Susu", "Telur", "Wijen", "MSG"],
                default=["Kacang"]
            )
            
            if st.button("🚀 Analisis Sekarang", use_container_width=True, key="analyze_text"):
                if not food_name or not ingredients:
                    st.warning("Mohon isi nama makanan dan bahan-bahannya")
                else:
                    with st.spinner("Menganalisis kehalalan dan alergen..."):
                        try:
                            start_time = time.time()
                            result = analyze_halal(f"{food_name}. Bahan: {ingredients}", user_allergies)
                            process_time = time.time() - start_time
                            
                            st.markdown(f"""
                            <div class="custom-card fade-in">
                                <h3 style="color: var(--accent); margin-top: 0;">HASIL ANALISIS</h3>
                                <small>Diproses dalam {process_time:.1f} detik</small>
                                {result}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Tampilkan badge status
                            if "Halal" in result:
                                st.markdown("<div class='halal-badge'>✔ HALAL</div>", unsafe_allow_html=True)
                            elif "Haram" in result:
                                st.markdown("<div class='haram-badge'>✖ HARAM</div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<div class='syubhat-badge'>⁉ SYUBHAT</div>", unsafe_allow_html=True)
                            
                            # Peringatan alergi
                            if any(allergen.lower() in result.lower() for allergen in user_allergies):
                                st.markdown("""
                                <div class="allergy-warning">
                                    ⚠️ PERINGATAN: Makanan ini mengandung bahan yang dapat memicu alergi Anda!
                                </div>
                                """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"Terjadi error: {str(e)}")
        
        with tab2:
            uploaded_file = st.file_uploader("Upload gambar kemasan makanan:", type=["jpg", "png", "jpeg"])
            if uploaded_file:
                st.image(uploaded_file, caption="Gambar yang diupload", use_column_width=True)
                
                analysis_mode = st.radio(
                    "Mode Analisis:",
                    ["🔠 Deteksi Teks (OCR)", "🖼️ Deteksi Objek (Gambar)"],
                    horizontal=True,
                    key="analysis_mode"
                )
                
                if st.button("🔍 Analisis Sekarang", use_container_width=True, key="analyze_image"):
                    with st.spinner("Memproses gambar..."):
                        try:
                            if analysis_mode == "🔠 Deteksi Teks (OCR)":
                                img_bytes = base64.b64encode(uploaded_file.getvalue()).decode()
                                prompt = """Analisis gambar ini untuk:
                                1. Daftar bahan
                                2. Potensi kandungan haram
                                3. Sertifikasi halal jika terlihat
                                
                                Berikan dalam format markdown."""
                                
                                response = Generation.call(
                                    model="qwen-vl-plus",
                                    prompt=prompt,
                                    api_key=DASHSCOPE_API_KEY
                                )
                                
                                if hasattr(response.output, 'text'):
                                    result_text = response.output.text
                                else:
                                    result_text = "Tidak dapat mendeteksi teks dalam gambar. Mohon pastikan gambar jelas dan mengandung teks yang terbaca."
                                
                                st.markdown(f"""
                                <div class="custom-card fade-in">
                                    <h3 style="color: var(--accent); margin-top: 0;">HASIL SCAN TEKS</h3>
                                    {result_text}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            else:  # Deteksi Objek
                                result_text = detect_objects_in_image(uploaded_file)
                                
                                st.markdown(f"""
                                <div class="custom-card fade-in">
                                    <h3 style="color: var(--accent); margin-top: 0;">HASIL DETEKSI OBJEK</h3>
                                    <div class="object-detection-result">
                                        {result_text}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"Error saat menganalisis gambar: {str(e)}")
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <h4>💡 Contoh Makanan Umum</h4>
            <ul>
                <li><strong>Rendang</strong> (daging, santan, bumbu)</li>
                <li><strong>Mie Ayam</strong> (mie, ayam, pangsit)</li>
                <li><strong>Es Campur</strong> (sirup, santan, jelly)</li>
                <li><strong>Kue Coklat</strong> (terigu, coklat, telur)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card">
            <h4>📌 Tips Analisis Akurat</h4>
            <ol>
                <li>Sebutkan <strong>semua bahan</strong>, termasuk bumbu</li>
                <li>Tambahkan <strong>metode pengolahan</strong> (digoreng, dibakar, dll)</li>
                <li>Jika makanan kemasan, foto <strong>daftar bahan</strong></li>
                <li>Untuk hasil terbaik, sertakan <strong>merek produk</strong></li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card">
            <h4>🕌 Panduan Status</h4>
            <p><span class="halal-badge">HALAL</span>: Bahan dan proses sesuai syariat</p>
            <p><span class="haram-badge">HARAM</span>: Mengandung bahan haram</p>
            <p><span class="syubhat-badge">SYUBHAT</span>: Meragukan, perlu penelitian lebih lanjut</p>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# TAB 2: REKOMENDASI HALAL
# ==============================
def tab_recommendation():
    st.header("🥗 Rekomendasi Makanan Halal", divider="green")
    
    tab1, tab2 = st.tabs(["🔍 Cari Alternatif", "🎨 Generate Ide"])
    
    with tab1:
        st.subheader("Temukan Alternatif Halal")
        food_to_replace = st.text_input("Makanan yang ingin diganti:", key="alt_food")
        
        if st.button("Cari Alternatif", key="find_alt"):
            if not food_to_replace:
                st.warning("Masukkan nama makanan terlebih dahulu")
            else:
                with st.spinner("Mencari alternatif halal..."):
                    try:
                        alternatives = generate_halal_alternative(food_to_replace)
                        st.markdown(f"""
                        <div class="custom-card fade-in">
                            <h3>Alternatif Halal untuk {food_to_replace}</h3>
                            {alternatives}
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Generate Ide Makanan")
        food_theme = st.text_input("Tema makanan (contoh: 'menu buka puasa', 'makanan anak'):", key="food_theme")
        
        if st.button("Generate Ide", key="generate_idea"):
            if not food_theme:
                st.warning("Masukkan tema makanan terlebih dahulu")
            else:
                with st.spinner("Membuat ide makanan halal..."):
                    try:
                        # Generate teks rekomendasi
                        prompt = f"""Buat 3 ide {food_theme} yang halal dengan format:
                        1. [Nama Menu]
                           - Bahan: [daftar]
                           - Cara membuat: [singkat]
                        2. [Nama Menu]
                           ... dan seterusnya"""
                        
                        response = Generation.call(
                            model="qwen-turbo",
                            prompt=prompt,
                            api_key=DASHSCOPE_API_KEY
                        )
                        
                        # Generate gambar contoh
                        img_url = generate_halal_image(food_theme)
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.image(img_url, caption=f"Contoh {food_theme} halal")
                        with col2:
                            st.markdown(f"""
                            <div class="custom-card fade-in">
                                <h3>Ide {food_theme.capitalize()} Halal</h3>
                                {response.output.text}
                            </div>
                            """, unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# ==============================
# TAB 3: EDUKASI HALAL
# ==============================
def tab_education():
    st.header("📚 Panduan Makanan Halal", divider="orange")
    
    tab1, tab2, tab3 = st.tabs(["🧐 Dasar Syar'i", "🛒 Belanja Aman", "📞 Bantuan"])
    
    with tab1:
        st.markdown("""
        <div class="custom-card">
            <h3>Prinsip Dasar Makanan Halal</h3>
            <ol>
                <li><strong>Hukum Asal</strong>: Semua makanan halal kecuali yang diharamkan</li>
                <li><strong>Bahan Haram</strong>:
                    <ul>
                        <li>Babi dan turunannya</li>
                        <li>Hewan tidak disembelih dengan syariat Islam</li>
                        <li>Darah, bangkai</li>
                        <li>Khamar/minuman memabukkan</li>
                    </ul>
                </li>
                <li><strong>Kontaminasi</strong>: Alat masak tidak boleh terkontaminasi haram</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card">
            <h3>Kategori Syubhat</h3>
            <p>Makanan meragukan yang perlu dicek:</p>
            <ul>
                <li>Mengandung emulsifier/mono-digliserida</li>
                <li>Mengandung enzim hewani</li>
                <li>Mengandung E-numbers tanpa penjelasan</li>
                <li>Makanan import tanpa sertifikasi jelas</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("""
        <div class="custom-card">
            <h3>Tips Belanja Aman</h3>
            <ol>
                <li>Cari logo sertifikasi halal MUI/LPPOM</li>
                <li>Baca daftar bahan dengan teliti</li>
                <li>Waspadai istilah teknis:
                    <ul>
                        <li>Gelatin (bisa dari babi/sapi)</li>
                        <li>Shortening (bisa mengandung lemak hewani)</li>
                        <li>Lecithin (bisa dari kedelai/telur/babi)</li>
                    </ul>
                </li>
                <li>Untuk produk import, cek badan sertifikasi negara asal</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card">
            <h3>Aplikasi Pendukung</h3>
            <ul>
                <li><strong>HalalMUI</strong>: Cek sertifikasi resmi</li>
                <li><strong>HalalCorner</strong>: Komunitas pemeriksa produk</li>
                <li><strong>Muslim Pro</strong>: Direktori restoran halal</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("""
        <div class="custom-card">
            <h3>Lembaga Resmi</h3>
            <ul>
                <li><strong>MUI</strong>: 1500-533 (Hotline Halal)</li>
                <li><strong>LPPOM MUI</strong>: <a href="https://www.halalmui.org">www.halalmui.org</a></li>
                <li><strong>BPJPH</strong>: Badan Penyelenggara Jaminan Produk Halal</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card">
            <h3>Laporkan Produk Meragukan</h3>
            <p>Kirim laporan ke:</p>
            <ol>
                <li>Foto kemasan produk</li>
                <li>Daftar bahan</li>
                <li>Lokasi pembelian</li>
                <li>Kirim ke: <a href="mailto:halal@mui.or.id">halal@mui.or.id</a></li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# TAMPILAN UTAMA
# ==============================
st.title("🕌 AllerGuard")
st.markdown("**Aplikasi Cerdas untuk Memastikan Kehalalan dan Keamanan Makanan**")

tab1, tab2, tab3 = st.tabs([
    "🔍 Analisis Makanan", 
    "🥗 Rekomendasi Halal", 
    "📚 Edukasi"
])

with tab1:
    tab_analysis()

with tab2:
    tab_recommendation()

with tab3:
    tab_education()

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-primary); font-size: 0.9rem; opacity: 0.7;">
    <p>© 2025 HalalGuard Pro+ | Dibangun dengan Alibaba Cloud Qwen & Wanxiang</p>
    <p style="font-size: 0.8rem;">Disclaimer: Hasil analisis bersifat informatif, bukan pengganti sertifikasi resmi</p>
</div>
""", unsafe_allow_html=True)
