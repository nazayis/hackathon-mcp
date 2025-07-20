# init_db.py

import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import database as db
from database import User, Account, Asset, Transaction

# --- VERİTABANINI TEMİZLE VE OLUŞTUR ---
DB_FILE = "portfolio.db"

def initialize_database():
    """
    Veritabanını sıfırlar, tabloları oluşturur ve API'nin beklediği
    "NAZ AYIS" kullanıcısı için örnek verilerle doldurur.
    """
    # 1. Adım: Varsa eski veritabanı dosyasını sil
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"'{DB_FILE}' dosyası silindi. Veritabanı sıfırlanıyor...")

    # 2. Adım: database.py'deki modellere göre tabloları oluştur
    db.create_db_and_tables()
    print("Veritabanı tabloları başarıyla oluşturuldu.")

    # 3. Adım: Veritabanı oturumu başlat
    session: Session = db.SessionLocal()
    print("Örnek veriler ekleniyor...")

    try:
        # --- KULLANICI OLUŞTUR ---
        # API endpoint'leri bu kullanıcı ismini bekliyor.
        user_naz = User(name="NAZ AYIS")
        session.add(user_naz)
        # ID'lerin atanması için veritabanına ön-kayıt yapıyoruz (commit değil)
        session.flush()

        # --- HESAPLARI OLUŞTUR ---
        fibabanka_acc = Account(
            bank_name="fibabanka",
            balance=253500.75,
            owner_id=user_naz.id # Kullanıcıya bağlıyoruz
        )
        garanti_acc = Account(
            bank_name="garanti",
            balance=8200.00,
            owner_id=user_naz.id
        )
        isbankasi_acc = Account(
            bank_name="isbankasi",
            balance=1450.50,
            owner_id=user_naz.id
        )
        session.add_all([fibabanka_acc, garanti_acc, isbankasi_acc])
        session.flush()

        # --- VARLIKLARI (HİSSE SENETLERİ) OLUŞTUR ---
        assets = [
            Asset(ticker="GARAN", quantity=100, account_id=garanti_acc.id),
            Asset(ticker="FROTO", quantity=15, account_id=garanti_acc.id),
            Asset(ticker="THYAO", quantity=50, account_id=garanti_acc.id),
        ]
        session.add_all(assets)

        # --- İŞLEMLERİ (TRANSACTIONS) OLUŞTUR ---
        # Son birkaç aya yayılan çeşitli ve gerçekçi işlemler
        today = datetime.utcnow()
        transactions = [
            # Fibabanka İşlemleri (Maaş ve Faturalar)
            Transaction(account_id=fibabanka_acc.id, description="Maaş Ödemesi", amount=450000.00, transaction_type="income", category="Maaş", date=today - timedelta(days=25)),
            Transaction(account_id=fibabanka_acc.id, description="Kira Ödemesi", amount=-18000.00, transaction_type="expense", category="Kira", date=today - timedelta(days=25)),
            Transaction(account_id=fibabanka_acc.id, description="Elektrik Faturası", amount=-750.45, transaction_type="expense", category="Fatura", date=today - timedelta(days=15)),
            Transaction(account_id=fibabanka_acc.id, description="İnternet Faturası", amount=-420.00, transaction_type="expense", category="Fatura", date=today - timedelta(days=12)),
            Transaction(account_id=fibabanka_acc.id, description="İş Bankası'na Transfer", amount=-2000.00, transaction_type="transfer", category="Transfer", date=today - timedelta(days=10)),
            Transaction(account_id=fibabanka_acc.id, description="Maaş Ödemesi", amount=45000.00, transaction_type="income", category="Maaş", date=today - timedelta(days=55)),
            Transaction(account_id=fibabanka_acc.id, description="Kira Ödemesi", amount=-18000.00, transaction_type="expense", category="Kira", date=today - timedelta(days=55)),

            # İş Bankası İşlemleri (Günlük Harcamalar)
            Transaction(account_id=isbankasi_acc.id, description="Fibabanka'dan Gelen Transfer", amount=2000.00, transaction_type="transfer", category="Transfer", date=today - timedelta(days=10)),
            Transaction(account_id=isbankasi_acc.id, description="Market Alışverişi", amount=-540.80, transaction_type="expense", category="Market", date=today - timedelta(days=9)),
            Transaction(account_id=isbankasi_acc.id, description="Netflix Aboneliği", amount=-179.99, transaction_type="expense", category="Eğlence", date=today - timedelta(days=8)),
            Transaction(account_id=isbankasi_acc.id, description="Kafe Harcaması", amount=-350.00, transaction_type="expense", category="Yeme-İçme", date=today - timedelta(days=7)),

            # Garanti İşlemleri (Yatırım)
            Transaction(account_id=garanti_acc.id, description="FROTO Hisse Alımı", amount=-5000.00, transaction_type="expense", category="Yatırım", date=today - timedelta(days=50)),
            Transaction(account_id=garanti_acc.id, description="GARAN Temettü Ödemesi", amount=750.00, transaction_type="income", category="Yatırım", date=today - timedelta(days=35)),
        ]
        session.add_all(transactions)

        # 4. Adım: Değişiklikleri veritabanına kaydet
        session.commit()
        print("Örnek veriler başarıyla eklendi.")

    except Exception as e:
        print(f"Veri eklenirken bir hata oluştu: {e}")
        session.rollback()
    finally:
        # 5. Adım: Oturumu kapat
        session.close()
        print("Veritabanı oturumu kapatıldı.")

if __name__ == "__main__":
    initialize_database()
    print("\nVeritabanı kurulumu tamamlandı! Artık 'python mcp_server.py' komutunu çalıştırabilirsiniz.")