# Portfi: Akıllı Portföy Yönetim Asistanı (Hackathon Projesi)

**Portfi**, kullanıcıların yatırım kararlarını, Fibabanka'nın haftalık **Riskometre** raporları ve gelişmiş yapay zeka ajanları ile destekleyen bir portföy yönetim platformudur. Bu proje, `nazayis-hackathon-mcp` kapsamında, karmaşık finansal verileri basitleştirerek ve kişiselleştirilmiş yatırım stratejileri sunarak son kullanıcıya akıllı bir finansal asistan deneyimi yaşatmayı hedefler.

## 🚀 Temel Özellikler

*   **Sohbet Tabanlı Arayüz:** Kullanıcılar, doğal dil ile sohbet ederek portföylerini analiz edebilir, yatırım talimatları verebilir ve piyasa hakkında sorular sorabilirler.
*   **Riskometre Entegrasyonu:** Fibabanka tarafından yayınlanan haftalık piyasa risk analizlerini (Riskometre) bir bilgi bankası olarak kullanır. Bu sayede, yatırım önerileri güncel piyasa risklerine dayalıdır.
*   **Akıllı Ajan Takımı:** Proje, farklı uzmanlık alanlarına sahip yapay zeka ajanlarından (Analiz, Risk Profilleme, Portföy Oluşturma, Yeniden Dengeleme) oluşan bir takım tarafından yönetilir. Bu takım, kullanıcı taleplerini en uygun uzmana yönlendirerek verimli bir iş akışı sağlar.
*   **Açık Bankacılık Simülasyonu:** `fastmcp` ve `FastAPI` kullanılarak oluşturulan bir API ile kullanıcının farklı bankalardaki hesap verilerini tek bir yerden (simüle edilmiş olarak) yönetir.
*   **Dinamik Veri Görselleştirme:** Kullanıcının portföy özeti, varlık dağılımı ve piyasa verileri, `Streamlit` ve `Plotly` kullanılarak oluşturulmuş interaktif bir arayüzde sunulur.
*   **Hafıza Yönetimi:** Kullanıcıların geçmiş konuşmaları ve yatırım tercihleri, gelecekteki önerileri kişiselleştirmek için bir hafıza sisteminde saklanır.

## 🏛️ Mimari ve Teknoloji

Proje, modern ve modüler bir mimari üzerine kurulmuştur. Ana bileşenler şunlardır:

*   **Frontend:** Kullanıcı arayüzü için `Streamlit` kullanılmıştır. Dinamik ve veri odaklı paneller `Plotly` ile zenginleştirilmiştir.
*   **Backend (API):** `FastAPI` ile sahte bir açık bankacılık API'si oluşturulmuştur. Bu API, hesap bilgilerini getirme, para transferi yapma gibi işlemleri simüle eder.
*   **MCP Sunucusu:** `mcp_server.py`, `FastAPI` uygulamasını `fastmcp` aracılığıyla otomatik olarak bir Model Bağlam Protokolü (MCP) sunucusuna dönüştürür. Bu, yapay zeka ajanlarının bankacılık API'sini standart bir araç seti olarak kullanmasını sağlar.
*   **Ajan Orkestrasyonu:** `agno` kütüphanesi kullanılarak bir ajan takımı (`Team`) oluşturulmuştur. Bu takım, `Gemini` modellerini kullanarak düşünür, plan yapar ve görevleri delege eder.
*   **Veritabanı:** `SQLAlchemy` ORM'i ile yönetilen bir `SQLite` veritabanı, kullanıcı, hesap, varlık ve işlem verilerini saklar.
*   **Bilgi Bankası (Knowledge Base):** Haftalık Riskometre `Markdown` dosyaları, `LanceDB` üzerinde bir vektör veritabanına yüklenerek anlamsal arama ve RAG (Retrieval-Augmented Generation) için kullanılır.

<img width="1280" height="780" alt="image" src="https://github.com/user-attachments/assets/db15aca6-fd92-4dba-8b0c-807249877f97" />


## 📂 Dosya Yapısı

Projenin ana dizinleri ve dosyaları aşağıda açıklanmıştır:

```
└── nazayis-hackathon-mcp/
    └── hackathon/
        ├── README.md               # Bu dosya
        ├── agent.py                # Ajanların ve takımın tanımlandığı ana mantık dosyası
        ├── banking_api.py          # FastAPI ile oluşturulan bankacılık API endpoint'leri
        ├── database.py             # SQLAlchemy veritabanı modelleri
        ├── init_db.py              # Veritabanını başlangıç verileriyle dolduran betik
        ├── mcp_server.py           # FastAPI uygulamasını MCP sunucusuna dönüştüren betik
        ├── ui.py                   # Streamlit ile oluşturulan kullanıcı arayüzü
        ├── portfolio.db            # Ana uygulama veritabanı dosyası
        ├── riskometre/             # Haftalık riskometre raporlarının bulunduğu klasör
        │   ├── ...
        └── output/                 # Ajanların çalışma sırasında oluşturduğu çıktılar
            ├── memory/             # Ajan hafızası ve oturum veritabanları
            └── vector_db/          # Riskometre verileri için LanceDB vektör veritabanı
```

## Dashboard Arayüzü

<img width="1600" height="716" alt="image" src="https://github.com/user-attachments/assets/95631cb1-5e42-4ea4-9380-a39665f613f9" />

## Chatbot Arayüzü

<img width="1265" height="634" alt="Screenshot 2025-07-20 at 23 45 33" src="https://github.com/user-attachments/assets/f4cd883b-45e1-4f5d-9402-575a6274edfb" />

## 🛠️ Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:

1.  **Bağımlılıkları Yükleyin:**
    Gerekli Python kütüphanelerini yükleyin. (Proje bir `requirements.txt` dosyası içeriyorsa, `pip install -r requirements.txt` komutunu kullanın. Eğer içermiyorsa, `agent.py` ve diğer dosyalardaki import'lara göre manuel kurulum yapın: `pip install agno-lib streamlit fastapi uvicorn sqlalchemy python-dotenv lancedb plotly pandas`)

2.  **Veritabanını Başlatın:**
    Projenin ihtiyaç duyduğu veritabanı şemasını oluşturmak ve başlangıç verilerini (`NAZ AYIS` kullanıcısı ve hesapları) eklemek için aşağıdaki betiği çalıştırın:
    ```bash
    python hackathon/init_db.py
    ```
    Bu komut, `portfolio.db` dosyasını oluşturacak ve içini dolduracaktır.

3.  **Kullanıcı Arayüzünü Başlatın:**
    Streamlit uygulamasını başlatmak için terminalde aşağıdaki komutu çalıştırın:
    ```bash
    streamlit run hackathon/ui.py
    ```
    Bu komut, varsayılan web tarayıcınızda uygulamanın arayüzünü açacaktır.

4.  **Arka Plan Süreçleri:**
    `ui.py` arayüzü üzerinden bir sohbet başlattığınızda, `agent.py` içerisindeki `run_portfolio_interaction` fonksiyonu `mcp_server.py`'yi bir alt süreç olarak otomatik olarak başlatacaktır. Bu sayede manuel olarak ayrı bir sunucu çalıştırmanıza gerek kalmaz.

## Yatırım Senaryosu Örneği

Uygulama açıldığında, "💰 55.000 TL yatırım senaryosunu dene" butonuna tıklayarak aşağıdaki gibi bir senaryo başlatılabilir:

**Kullanıcı:** "Merhaba, 55.000 TL yatırım yapmak istiyorum. Mevcut piyasa koşullarına göre ılımlı bir riskle paramı nasıl değerlendirebilirim?"

**Sistem Arka Planda Ne Yapar?**

1.  **Team Leader (Portfolio Manager):** Talebi alır ve ilk olarak en güncel piyasa riskini öğrenmesi gerektiğini bilir.
2.  **Knowledge Base Search:** Bilgi bankasından (`riskometre` dosyaları) en güncel risk raporunu arar ve bulur.
3.  **Risk Profiler Agent:** Güncel piyasa riskini ve kullanıcının "ılımlı risk" tercihini analiz ederek bir risk profili oluşturur.
4.  **Portfolio Builder Agent:** Risk profiline ve 55.000 TL'lik bütçeye uygun, Riskometre'de öne çıkan düşük/orta riskli fon ve hisselerden bir sepet önerisi hazırlar.
5.  **Team Leader (Portfolio Manager):** Ajanlardan gelen teknik çıktıları (JSON) yorumlar ve kullanıcıya doğal dilde, gerekçeleriyle birlikte bir yatırım planı sunar.

55.000TL ile yatırım öneri tablosu:

<img width="2130" height="922" alt="image" src="https://github.com/user-attachments/assets/a1f81a60-3440-4756-ba3b-2855b70db88c" />


## Agent Yapısı (agent.py)

<img width="910" height="824" alt="image" src="https://github.com/user-attachments/assets/56a4005d-c576-441e-9682-5d27545cd22a" />

## 💬 Görüşleriniz Bizim İçin Değerli
Portfi'yi geliştirirken kullanıcı deneyimini en üst seviyeye taşımayı hedefliyoruz.
Görüş, öneri veya geri bildiriminiz varsa bizimle paylaşmaktan çekinmeyin.
👉 Fibabanka kanallarından bize doğrudan ulaşabilirsiniz!

made with 💝
