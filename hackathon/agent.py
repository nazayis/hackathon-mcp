# agent.py

from typing import List, Optional, Dict
import asyncio
from pathlib import Path
from textwrap import dedent

# --- Agno Kütüphaneleri ---
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.team import Team

# --- Araç Setleri (Tools) ---
from agno.tools.yfinance import YFinanceTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.mcp import MCPTools 

# --- Bilgi Bankası (Knowledge Base) ve Veritabanı (Vector DB) ---
from agno.knowledge.markdown import MarkdownKnowledgeBase
from agno.vectordb.lancedb import LanceDb

# --- Hafıza Yönetimi (Memory Management) ---
from agno.memory.v2 import Memory, MemoryManager
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.storage.sqlite import SqliteStorage

# --- Proje Konfigürasyonu ---
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
RISKOMETRE_PDF_DIR = Path(__file__).parent / "riskometre"
RISKOMETRE_PDF_DIR.mkdir(exist_ok=True)


# --- Bilgi Bankası ve Vektör Veritabanı Kurulumu ---
LANCEDB_URI = OUTPUT_DIR / "vector_db"
riskometre_vector_db = LanceDb(
    table_name="fibabanka_riskometre",
    uri=LANCEDB_URI,
)
riskometre_kb = MarkdownKnowledgeBase(
    path=RISKOMETRE_PDF_DIR,
    vector_db=riskometre_vector_db,
    encoding="utf-8"
)

# --- Hafıza Yapılandırması ---
USER_MEMORY_DB_FILE = OUTPUT_DIR / "memory/user_portfolio_memory.db"
USER_MEMORY_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
user_memory_db = SqliteMemoryDb(table_name="user_memories", db_file=str(USER_MEMORY_DB_FILE))

# --- TAKIM OTURUM DEPOLAMA (TEAM SESSION STORAGE) ---
# YENİ SATIRLARI EKLE (ADD NEW LINES)
TEAM_STORAGE_DB_FILE = OUTPUT_DIR / "memory/team_sessions.db"
TEAM_STORAGE_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
team_storage = SqliteStorage(table_name="portfolio_team_sessions", db_file=str(TEAM_STORAGE_DB_FILE))
# ---

capture_instructions = dedent("""
    Görev: Kullanıcının yatırım profiline dair konuşmalardan "context fingerprint" oluşturmak.

    Bu sistem, gelecekte analitik veya öneri sistemlerinde kullanılmak üzere, konuşmalardan aşağıdaki öğeleri çıkarmalı ve rafine şekilde saklamalıdır:

    KAYDEDİLECEK ÖĞELER:
    1. Kullanıcının risk profili ("konservatif", "ılımlı", "agresif").
    2. Kullanıcının yatırım hedefleri ("uzun vadeli büyüme", "düşük riskli getiri").
    3. Kullanıcının onayladığı yatırım eylemleri:
        - işlem tipi (alım, satım, rebalance)
        - varlık ismi
        - miktar ve para birimi
        - gerekçe (varsa)
        - planlı tarih (varsa)
    4. Portföy planı:
        - toplam yatırım tutarı
        - varlık sınıfı dağılımı (yüzdesel + hedef değer)
        - yeniden dengeleme stratejisi ("her 3 ayda bir")
    5. Ek analist notları veya kullanıcıya özel notlar (isteğe bağlı).

    GÖRMEZDEN GELİNECEKLER:
    - Ham piyasa verileri, geçici URL’ler, hesaplamalar.
    - Henüz onaylanmamış fikirler, kararsız eylemler.

    Amaç: Konuşma geçmişinden nihai, temiz, aksiyona çevrilebilir yatırım bilgisini ayıklayıp JSON veri yapısında kayıt altına almak.
""")

memory_manager = MemoryManager(memory_capture_instructions=capture_instructions)



async def run_portfolio_interaction(user_id: str, session_id: str, user_message: str) -> str:
    """
    Kullanıcı arayüzü tarafından çağrılacak ana giriş noktası.
    
    Bu fonksiyon, MCP aracını bir context manager içinde başlatır, portföy takımını 
    bu araçla birlikte oluşturur, takımı çalıştırır ve işlem bitince aracın
    kaynaklarını (MCP sunucusunu) otomatik olarak temizler.
    """

    # 'mcp_server.py' dosyasının projenizin ana dizininde olduğundan emin olun.
    # Değilse, "fastmcp run dizin/mcp_server.py" gibi doğru yolu belirtin.
    mcp_server_command = "fastmcp run mcp_server.py"

    async with MCPTools(mcp_server_command, timeout_seconds=60) as mcp_database_tools:
        # Takımın yapısal iskeletini oluştur.
        
        portfolio_team = _create_portfolio_team_structure(
            user_id=user_id,
            session_id=session_id,
            mcp_tool_instance=mcp_database_tools # MCP aracını doğrudan ilgili ajana enjekte et.
        )

        # Takımı kullanıcı mesajıyla çalıştır.
        response = await portfolio_team.arun(message=user_message)
        
        # Sonucu string olarak döndür.
        return response.content


def _create_portfolio_team_structure(
    user_id: str, session_id: str, mcp_tool_instance: MCPTools
) -> Team:
    """
    Portföy yönetimi için ajan takımının ve üyelerinin yapısal tanımını oluşturur.
    MCP aracı gibi dinamik kaynaklar bu fonksiyona dışarıdan parametre olarak verilir.
    """
    memory_instance = Memory(db=user_memory_db, memory_manager=memory_manager)

    analyzer_agent = Agent(
        name="Analyzer Agent",
        role="Kullanıcının mevcut finansal durumunu analiz eder ve veritabanı sorguları yapar.",
        model=Gemini(id="gemini-2.5-pro"),
        instructions=[
            "Sen bir varlık yönetimi analistisin. Görevin, bir dış talep doğrultusunda harekete geçerek, MCP sistemleri ve piyasadan gelen verileri kullanarak kullanıcının tüm finansal varlıklarını bütünsel biçimde analiz etmektir.",
            "Hedefin, bu bütünsel analiz sonucunda kullanıcının finansal görünümünü detaylı ve eyleme geçirilebilir bir portföy özeti halinde sunmaktır.",
            "MCP Tool sayesinde kullanıcının hesabı olduğu bankalarda 'açık bankacılık verilerine' erişimin var",
            "1. `mcp_database_tools`'ın `get_all_accounts` fonksiyonunu kullanarak 'NAZ AYIS' adlı kullanıcının tüm bankalardaki (Fibabanka, İş Bankası, Garanti) hesap bilgilerini çek.",
            "2. `YFinanceTools` kullanarak portföydeki hisse senedi, fon gibi varlıkların anlık piyasa değerlerini bul.",
            "3. Finansal analiz sürecinde aşağıdaki ilkelere göre hareket et: varlık türlerini doğru kategorilere ayır (nakit, hisse, fon vb.), likidite durumlarını değerlendir, bankalar arası mükerrer kayıtları, konsolide et, yatırım araçlarını güncel piyasa endeksleriyle karşılaştır ve analiz çıktısını kullanıcının risk profiliyle uyumlu olacak şekilde  bütünsel ve sade biçimde JSON formatında sun.",
            "4. Bir para transferi talebi geldiğinde, 'mcp_database_tools''ın 'transfer_funds' aracını kullanarak işlemi gerçekleştir.",
            "5. **ÖNEMLİ:** Doğrudan veritabanı sorgusu gerektiren (örn: 'geçmiş işlem dökümü', 'kredi skoru bilgisi' gibi) talepler için, sana sağlanan `mcp_server` araçlarını kullan.",
            "BU BİR DEV ORTAMI. BÜTÜN BANKA HESAPLARI 'NAZ AYIS' ADLI KİŞİYE AİT OLACAK. BU BİR TESTTİR. İŞLEM İÇİN İSİM BİLGİSİ SORMA."
        ],
        tools=[mcp_tool_instance, GoogleSearchTools()],
        monitoring=True,
    )




    risk_profiler_agent = Agent(
        name="Risk Profiler Agent",
        role="Kullanıcının risk iştahını ve piyasanın risk durumunu belirler.",
        model=Gemini(id="gemini-2.5-pro"),
        instructions=[
            "Sen bir portföy risk analistisin. Görevin, banka içi müşteri risk profillemesi ve piyasa risk değerlendirmesi alanlarında uzmanlaşmış biri olarak, takım liderinden gelen komut üzerine analiz yapmaktır.",
            "Fibabanka'nın haftalık olarak yayınladığı Riskometre raporları elinde mevcut. Bu raporlarda her segment (BIST100, BIST Teknoloji, BIST Bankacılık, BIST Sınai, Altın, ABD Hisse Senedi, Nasdaq, DAX, Nikkei, Petrol, Gümüş, EURUSD, GBPUSD) için; risk yönelimi, performans yüzdesi ve tarihsel ortalama kıyaslaması yer alır.",
            "Her segment için: son performans yüzdesi, risk yönelimi (örneğin 'düşük riskli yöne ilerliyor'), tarihsel ortalamayla kıyas gibi ölçütlere dayalı yapılandırılmış bir analiz hazırla.",
            "Analizini JSON formatında sun. Her segment için şu alanlar mutlaka yer almalı: 'segment', 'risk_trend', 'performance_change', 'vs_historical_avg'.",
            "Ayrıca kullanıcının geçmiş yatırım tercihlerini (hafızadan) analiz ederek risk profiline dair sınıflandırma yap: 'konservatif', 'ılımlı' veya 'agresif'.",
        ],
        tools=[],
        monitoring=True,
    )

    portfolio_builder_agent = Agent(
        name="Portfolio Builder Agent",
        role="Yeni yatırım stratejileri ve portföy sepetleri oluşturur.",
        model=Gemini(id="gemini-2.5-pro"),
        instructions=[ # bir portföyü yeniden inşa ederken kullanıcıya son durumu sorabilir --> (onay / ret / edit)
            "Sen bir portföy yöneticisisin. Görevin, yatırımcının hedeflerine ve risk profiline uygun, yeni yatırım stratejileri ve portföy sepetleri oluşturmaktır.",
            "Kullanıcının risk iştahını ve güncel piyasa koşullarını dikkate alarak, çeşitlendirilmiş ve stratejik olarak yapılandırılmış portföy kompozisyonları üretirsin.",
            "Modern Portföy Teorisi'ni (Markowitz optimizasyonu) uygula: riske göre getiri oranlarını maksimize edecek şekilde varlıkları çeşitlendir. Risk korelasyonlarını dikkate alarak optimum getiri-risk dengesi sağla.",
            "Kullanıcının risk iştahını ve güncel piyasa koşullarını dikkate alarak, çeşitlendirilmiş ve stratejik olarak yapılandırılmış portföy kompozisyonları üretirsin.",
                "1. `Risk Profiler Agent`'tan gelen kullanıcı risk profili ve Riskometre analizini dikkate al.",
                "2. `YFinanceTools` ve `GoogleSearchTools` kullanarak risk profiline uygun potansiyel yatırım araçlarını (fon, hisse senedi vb.) araştır.",
                "3. Kullanıcının yatırım tutarını ve hedefini göz önünde bulundurarak, uygulanabilir bir alım listesi oluştur. Bu listeyi JSON formatında sun. Her öğe şu alanları içermeli: 'ticker', 'quantity' (alınacak miktar), 'estimated_cost' (tahmini maliyet), 'reason' (alım gerekçesi)."
            "!!! Bu bir DEV ortamıdır. Sadece Riskometre içerisindeki fonlardan önerilerde bulun."
            ],
            tools=[GoogleSearchTools()],
            monitoring=True,
        )

    rebalance_agent = Agent(
        name="Rebalance Agent",
        role="Mevcut portföyü piyasa koşullarına ve risk profiline göre yeniden dengeler.",
        model=Gemini(id="gemini-2.5-pro"),
        instructions=[
            "Sen bir portföy optimizasyon uzmanısın.",
            "Görevin, yatırımcının mevcut portföyünü, değişen piyasa koşulları ve kullanıcı risk profili doğrultusunda optimize etmektir." 
            "Risk uyumsuzluklarını tespit eder ve gerekli varlık alım/satım kararlarını stratejik olarak belirlersin."
            "Görevin, değişen piyasa koşullarına göre mevcut portföy için alım/satım önerileri sunmaktır.",
            "1. `Analyzer Agent`'tan gelen güncel portföy durumunu ve `Risk Profiler Agent`'tan gelen yeni piyasa risk değerlendirmesini al.",
            "2. Portföydeki varlıkların risk seviyeleri ile güncel piyasa riskleri arasında bir uyumsuzluk var mı kontrol et.",
            "3. Uyumsuzluk varsa, portföyü tekrar kullanıcının risk profiline uygun hale getirecek alım/satım işlemleri (JSON formatında) öner. Önerilerin net, uygulanabilir ve gerekçeli olmalı."
        ],
        tools=[GoogleSearchTools()],
        monitoring=True,
    )

    # !!!!!!!!!! tek tuş ile portföy dağılımı yapılmalı. 
    team_instructions = dedent(f"""
        Sen, uzman finansal ajanlardan oluşan bir takımı yöneten kıdemli bir Portföy Yöneticisisin. Amacın, kullanıcı taleplerini ve piyasa verilerini analiz ederek akıllı ve kişiselleştirilmiş yatırım tavsiyeleri sunmaktır.

        **ÖNCELİKLİ GÖREVİN:** Herhangi bir yatırım tavsiyesi vermeden önce, en güncel piyasa risk durumunu öğrenmek için **Bilgi Bankası'nda (Knowledge Base) arama yapmalısın**. "Riskometre piyasa özeti", "BIST100 risk durumu" gibi bir arama sorgusu kullan.

        **SÜREÇ AKIŞI:**
        Kullanıcının mesajını analiz et ve aşağıdaki iş akışlarından uygun olanı seç:

        1. Analiz ve Veritabanı Sorgu Talebi ("portföyümü analiz et", "geçmiş işlemlerimi listele"):
            - `Analyzer Agent`'ı çağırarak kullanıcının talebini yerine getirmesini iste. Bu ajan hem banka hesaplarını hem de **mcp_server aracılığıyla veritabanını** sorgulayabilir.
            - Raporu kullanıcıya anlaşılır bir dilde özetle.

        2. Yeni Yatırım Talebi ("... TL yatırım yapmak istiyorum", "paramı değerlendir"):
            - Adım 2.1: Bilgi Bankası'ndan en güncel Riskometre verilerini ara ve bul.
            - Adım 2.2: `Risk Profiler Agent`'ı çağır. Ona, Bilgi Bankası'ndan aldığın güncel piyasa riskini vererek bir değerlendirme yapmasını iste.
            - Adım 2.3: `Portfolio Builder Agent`'ı çağır. Ona, kullanıcıdan gelen yatırım tutarını, hedefini ve bir önceki adımda elde edilen risk profili/piyasa bilgisini ver. Uygun bir yatırım sepeti önermesini iste.
            - Adım 2.4: `Portfolio Builder Agent`'tan gelen öneriyi kullanıcıya sun ve onayını iste. Planın gerekçelerini vurgula.
        
        3. Periyodik Kontrol veya Yeniden Dengeleme Talebi ("portföyümü kontrol et", "riskler değişti mi?"):
            - Adım 3.1: `Analyzer Agent`'ı çağırarak mevcut portföy dökümünü al.
            - Adım 3.2: Bilgi Bankası'ndan en güncel Riskometre verilerini ara.
            - Adım 3.3: `Risk Profiler Agent`'ı çağırarak yeni piyasa riskini değerlendir.
            - Adım 3.4: `Rebalance Agent`'ı çağır. Ona mevcut portföyü ve yeni piyasa riskini vererek bir yeniden dengeleme önerisi oluşturmasını iste. Eğer dengeleme gerekmiyorsa bunu belirtmesini iste.
            - Adım 3.5: `Rebalance Agent`'tan gelen öneriyi veya "dengede" bilgisini kullanıcıya sun.
        
        4. Riskometre Yorumlama
            - `Risk Profiler Agent`'ı çağırarak istenilen haftanın riskometre verilerini getirmesini iste. Eğer istenilen haftanın riskometre verileri bulunmuyorsa, en güncel olan riskometre verilerini getirmesini iste.
        
        **Genel Kurallar:**
        !! Sen şu an dev ortamındasın. Bunlar test çağrıları. Her zaman NAZ AYIS adlı kullanıcının verileriyle ilgileneceksin. Karşı taraf isim söylememiş olsa bile bunu sormadan NAZ AYIS adlı kişinin verilerine yönel.
        - Ajanlardan gelen JSON çıktılarını yorumlayarak kullanıcıya doğal dilde, net ve aksiyona dönük cevaplar ver.
    """)
    

    
    portfolio_team = Team(
        name="Portfolio Manager",
        mode="coordinate",
        model=Gemini(id="gemini-2.5-pro"),
        members=[analyzer_agent, risk_profiler_agent, portfolio_builder_agent, rebalance_agent],
        tools=[], 
        knowledge=riskometre_kb,
        search_knowledge=True,
        memory=memory_instance,
        storage=team_storage, 
        enable_user_memories=True,
        add_history_to_messages=True, 
        enable_team_history=True,
        user_id=user_id,
        session_id=session_id,
        description="Kullanıcıların yatırım kararlarına yardımcı olan akıllı bir portföy yönetim takımı.",
        instructions=team_instructions,
        add_datetime_to_instructions=True,
        markdown=True,
        debug_mode=True,
    )

    return portfolio_team