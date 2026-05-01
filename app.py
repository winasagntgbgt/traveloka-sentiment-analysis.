import streamlit as st
import pandas as pd
import plotly.express as px
from google_play_scraper import Sort, reviews

# Konfigurasi Halaman
st.set_page_config(page_title="Analisis Sentimen Traveloka", layout="wide")

# --- JUDUL DASHBOARD ---
st.title("🚀 Traveloka Sentiment Intelligence Dashboard")
st.markdown("Analisis ulasan pengguna secara real-time dari Google Play Store")

# --- SIDEBAR (Pengaturan) ---
st.sidebar.header("Konfigurasi Data")
limit = st.sidebar.slider("Jumlah Ulasan yang Ditarik", 500, 5000, 1000)

# --- FUNGSI AMBIL DATA ---
@st.cache_data
def load_data(n_reviews):
    result, _ = reviews(
        'com.traveloka.android', 
        lang='id', 
        country='id', 
        sort=Sort.NEWEST, 
        count=n_reviews
    )
    data = pd.DataFrame(result)
    data['at'] = pd.to_datetime(data['at'])
    data['year'] = data['at'].dt.year
    
    # 1. LABEL SENTIMEN
    def label_sentiment(score):
        if score >= 4: return 'Positif'
        elif score <= 2: return 'Negatif'
        return 'Netral'
    data['sentiment'] = data['score'].apply(label_sentiment)
    
    # 2. ANALISIS BERBASIS ASPEK (Kamus Diperluas)
    aspek_dict = {
        'Performa': ['lag', 'lemot', 'crash', 'lambat', 'lancar', 'cepat', 'ringan', 'bug', 'error', 'loading'],
        'UI/UX': ['tampilan', 'desain', 'bingung', 'ribet', 'bagus', 'keren', 'mudah', 'simpel', 'tombol', 'warna'],
        'Fitur': ['tiket', 'hotel', 'pesawat', 'paylater', 'refund', 'kereta', 'lengkap', 'bermanfaat', 'pesan'],
        'Harga': ['mahal', 'promo', 'murah', 'diskon', 'ekonomis', 'hemat', 'pajak', 'terjangkau', 'biaya']
    }
    
    def detect_aspect(text):
        text = str(text).lower()
        for k, v in aspek_dict.items():
            if any(word in text for word in v): return k
        return 'Lainnya'
    
    data['aspek'] = data['content'].apply(detect_aspect)
    return data

df = load_data(limit)

# --- KONFIGURASI WARNA (Sesuai Permintaan) ---
# Positif = Biru (#3498db), Negatif = Merah (#e74c3c), Netral = Abu-abu (#95a5a6)
warna_custom = {'Positif': '#3498db', 'Negatif': '#e74c3c', 'Netral': '#95a5a6'}

# --- RINGKASAN METRIK ---
st.subheader("📌 Ringkasan Utama")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Ulasan", len(df))
c2.metric("Rata-rata Rating", f"⭐ {round(df['score'].mean(), 1)}")
c3.metric("Sentimen Positif", f"{len(df[df['sentiment']=='Positif'])}")
c4.metric("Sentimen Negatif", f"{len(df[df['sentiment']=='Negatif'])}")

st.divider()

# --- GRAFIK TREN TAHUN KE TAHUN ---
st.subheader("📈 Tren Sentimen Tahun ke Tahun")
trend = df.groupby(['year', 'sentiment']).size().reset_index(name='jumlah')
fig_line = px.line(trend, x='year', y='jumlah', color='sentiment', markers=True, 
                 color_discrete_map=warna_custom)
st.plotly_chart(fig_line, use_container_width=True)

# --- GRAFIK ASPEK ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🎯 Sentimen Berdasarkan Aspek")
    aspek_chart = df[df['aspek'] != 'Lainnya'].groupby(['aspek', 'sentiment']).size().reset_index(name='total')
    fig_bar = px.bar(aspek_chart, x='aspek', y='total', color='sentiment', barmode='group',
                   color_discrete_map=warna_custom)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.subheader("🔥 Ulasan Paling Relevan (Banyak Disukai)")
    top_reviews = df.sort_values(by='thumbsUpCount', ascending=False).head(5)
    for index, row in top_reviews.iterrows():
        # Menampilkan box ulasan dengan warna indikator
        warna_box = "info" if row['sentiment'] == 'Positif' else "error" if row['sentiment'] == 'Negatif' else "warning"
        st.info(f"**[{row['sentiment']} - {row['year']}]** ({row['thumbsUpCount']} Likes)\n\n{row['content'][:150]}...")

# --- TABEL DATA ---
st.divider()
st.subheader("🔍 Detail Data Ulasan")
st.dataframe(df[['at', 'sentiment', 'aspek', 'content', 'thumbsUpCount']].sort_values(by='at', ascending=False), use_container_width=True)
