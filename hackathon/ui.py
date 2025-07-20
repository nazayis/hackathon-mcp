import streamlit as st
from dotenv import load_dotenv
import asyncio
import uuid
import pandas as pd
import plotly.graph_objects as go

# Ortam değişkenlerini yükle
load_dotenv()

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(layout="wide", page_title="Portfi Portföy Asistanım")

# --- Ajan Mantığının İçe Aktarılması ---
try:
    from agent import run_portfolio_interaction, riskometre_kb
except ImportError as e:
    st.error(f"Ajan mantığı 'agent.py' dosyasından içe aktarılamadı: {e}")
    st.info("Lütfen 'agent.py' dosyasındaki yeni 'run_portfolio_interaction' fonksiyonunu kontrol edin.")
    st.stop()

# --- Asenkron Olay Döngüsü Yönetimi ---
def get_or_create_event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

# --- Bilgi Bankası Yükleme ---
@st.cache_resource
def load_knowledge_base():
    try:
        riskometre_kb.load(recreate=False)
    except Exception as e:
        st.error(f"Bilgi Bankası yüklenirken bir hata oluştu: {e}")
        st.stop()

# --- 2. BİLGİ BANKASI YÜKLEME ---
load_knowledge_base()


# --- 3. ÖZEL CSS STİLLERİ (YENİ TASARIM) ---
st.markdown("""
<style>
/* --- Sayfa Arka Planı (Gradient) --- */
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(135deg, #1d2b4b 0%, #1a1a2e 100%);
    background-attachment: fixed;
}

/* --- Genel Metin Rengi --- */
body, .st-emotion-cache-10trblm, .st-emotion-cache-16txtl3 { color: #E0E0E0; }
h1, h2, h3 { color: #FFFFFF; }

/* --- Kenarlıklı Kart Konteyneri (Piyasa Verileri için) --- */
.card-container {
    background: rgba(29, 38, 69, 0.5);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
}

/* --- Kenarlıksız, Sade Konteyner (Portföy ve Varlık için) --- */
.minimal-container {
    margin-bottom: 2rem;
}

/* --- Sohbet Mesajları --- */
div[data-testid="stChatMessage"] {
    background-color: rgba(45, 56, 91, 0.7);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 12px 16px;
}
div[data-testid="stChatMessage"] p { margin: 0; }

/* --- Buton Stilleri --- */
div[data-testid="stButton"] > button, div[data-testid="stLinkButton"] > a {
    background-color: #2d385b;
    color: #FFFFFF !important;
    border: 1px solid #4a5578;
    border-radius: 12px;
    padding: 10px 24px;
    font-weight: 600;
    transition: background-color 0.2s, border-color 0.2s;
    text-decoration: none;
}
div[data-testid="stButton"] > button:hover, div[data-testid="stLinkButton"] > a:hover {
    background-color: #4a5578;
    border-color: #6c7a9c;
    color: #FFFFFF !important;
}
div[data-testid="stButton"] > button:focus, div[data-testid="stLinkButton"] > a:focus {
    box-shadow: 0 0 0 2px #353C58, 0 0 0 4px #6C7A9C;
}


/* --- Sohbet Giriş Alanı --- */
div[data-testid="stChatInput"] { background-color: transparent; border-top: 1px solid rgba(255, 255, 255, 0.1); }
div[data-testid="stChatInput"] > div > div > textarea { background-color: rgba(29, 38, 69, 0.7); border-radius: 12px; border: 1px solid #4A5578; color: #FFFFFF; }

/* --- Sütunlar Arası Ayırıcı ve Boşluk --- */
div[data-testid="stHorizontalBlock"] { gap: 2rem; }
[data-testid="stVerticalBlock"] > [style*="flex-basis: 66"] { border-right: 1px solid rgba(255, 255, 255, 0.1); padding-right: 2rem; }

/* --- Varlık Dağılımı Legend Stilleri --- */
.legend-item { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-size: 14px; color: #E0E0E0; }
.legend-color { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
.legend-text-group { display: flex; align-items: center; }

.legend-item strong { margin-left: auto; }
</style>
""", unsafe_allow_html=True)


# --- 4. ANA SAYFA DÜZENİ: İKİ SÜTUN OLUŞTURMA ---
col_chat, col_data = st.columns([2, 1])

# --- SAĞ SÜTUN: VERİ PANELLERİ ---
with col_data:
    # --- EKLENEN SATIR (ADDED LINE) ---
    st.link_button("Dashboard", "http://localhost:3000", use_container_width=True)
    st.write("") # Buton ile altındaki içerik arasına boşluk koyar

    # Portföy özeti (Kenarlıksız ve Paddingsiz)
    with st.container():
        st.markdown('<div class="minimal-container">', unsafe_allow_html=True) 
        st.header("Portföy Özeti")
        st.metric(label="Toplam Portföy Değeri", value="₺325.750,42", delta="+2.3%")
        chart_data = pd.DataFrame({'Tarih': ['1 Mar', '1 Nis', '1 Oca', '1 Şub'], 'Değer': [328000, 325750, 315000, 320000]})
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=chart_data['Tarih'], y=chart_data['Değer'], mode='lines', line=dict(color='#00BFFF', width=2)))
        fig_line.update_layout(height=200, margin=dict(t=20, b=20, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, color='rgba(255,255,255,0.5)'), yaxis=dict(gridcolor='rgba(255,255,255,0.1)', color='rgba(255,255,255,0.5)'))
        st.plotly_chart(fig_line, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Varlık dağılımı (Kenarlıksız ve Paddingsiz)
    with st.container():
        st.markdown('<div class="minimal-container">', unsafe_allow_html=True)
        st.subheader("Varlık Dağılımı")
        labels, values, colors = ['Hisse Senetleri', 'Tahvil/Bono', 'Nakit', 'Altın'], [40, 30, 20, 10], ['#1f77b4', '#2ca02c', '#ff7f0e', '#ffd700']
        fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker=dict(colors=colors))])
        fig_donut.update_traces(textinfo='none', hoverinfo='label+percent')
        fig_donut.update_layout(showlegend=False, height=200, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        
        col1, col2 = st.columns([0.6, 0.4])
        with col1: 
            st.plotly_chart(fig_donut, use_container_width=True)
        with col2:
            st.markdown("""
                <div class="legend-item"><div class="legend-text-group"><div class="legend-color" style="background-color:#1f77b4;"></div>Hisse</div><strong>40%</strong></div>
                <div class="legend-item"><div class="legend-text-group"><div class="legend-color" style="background-color:#2ca02c;"></div>Tahvil</div><strong>30%</strong></div>
                <div class="legend-item"><div class="legend-text-group"><div class="legend-color" style="background-color:#ff7f0e;"></div>Nakit</div><strong>20%</strong></div>
                <div class="legend-item"><div class="legend-text-group"><div class="legend-color" style="background-color:#ffd700;"></div>Altın</div><strong>10%</strong></div>
            """, unsafe_allow_html=True)
        st.button("Tüm Portföyü Görüntüle >", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Piyasa verileri (Kenarlıklı ve Paddingli)
    with st.container():
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.header("Piyasa Verileri")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="BIST100", value="10,366.16", delta="-0.03%")
            st.metric(label="EUR/TRY", value="46.99", delta="+0.3%")
        with col2:
            st.metric(label="USD/TRY", value="40.35", delta="+0.46%")
            st.metric(label="Gram Altın (₺)", value="4,352.40", delta="±0.0%")
        st.markdown('</div>', unsafe_allow_html=True)

# --- SOL SÜTUN: SOHBET ARAYÜZÜ ---
with col_chat:
    st.title("Portfi Portföy Asistanım")
    st.caption("Riskometre verileri ve yapay zeka ile yatırımlarınızı yönetin.")

    # Oturum Durumu ve Sohbet Geçmişi
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Merhaba! Ben Fibabanka Portföy Asistanınız. Yatırımlarınızı yönetmenize nasıl yardımcı olabilirim?"}]
        st.session_state.user_id = "hackathon_user"
        st.session_state.session_id = str(uuid.uuid4())
    
    chat_container = st.container(height=600)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Örnek Senaryo Butonu
    if len(st.session_state.messages) == 1:
        investment_scenario_text = "Merhaba, 55.000 TL yatırım yapmak istiyorum. Mevcut piyasa koşullarına göre ılımlı bir riskle paramı nasıl değerlendirebilirim?"
        if st.button("💰 55.000 TL yatırım senaryosunu dene", use_container_width=True):
            st.session_state.prompt_from_button = investment_scenario_text
            st.rerun()

    # Ana Etkileşim
    prompt = st.chat_input("Yatırım hedefinizi veya sorunuzu yazın...")
    if "prompt_from_button" in st.session_state:
        prompt = st.session_state.pop("prompt_from_button")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
# --- Ajan Çağrısı (Rerun sonrası çalışır) ---
if st.session_state.messages[-1]["role"] == "user":
    user_message = st.session_state.messages[-1]["content"]
    with col_chat:
        with st.chat_message("assistant"):
            with st.spinner("Asistanınız sizin için en iyi yatırım seçeneklerini düşünüyor..."):
                loop = get_or_create_event_loop()
                ai_response = loop.run_until_complete(
                    run_portfolio_interaction(
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.session_id,
                        user_message=user_message
                    )
                )
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                st.rerun()
