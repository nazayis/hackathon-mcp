from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import database as db
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import date
from contextlib import asynccontextmanager # <--- YENİ İMPORT

# --- DEĞİŞTİRİLDİ: Bu satırı buradan kaldırıyoruz ---
# db.create_db_and_tables() 


# --- YENİ EKLENDİ: Lifespan context manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlamadan önce çalıştırılacak kod
    print("--- Uygulama başlıyor: Veritabanı ve tablolar oluşturuluyor... ---")
    db.create_db_and_tables()
    print("--- Veritabanı hazır. ---")
    yield
    # Uygulama kapandıktan sonra çalıştırılacak kod (isteğe bağlı)
    print("--- Uygulama kapanıyor. ---")


# --- DEĞİŞTİRİLDİ: app tanımına lifespan'i ekliyoruz ---
app = FastAPI(
    title="Simulated Open Banking API",
    lifespan=lifespan # <--- YENİ EKLENDİ
)

# Dependency to get DB session
def get_db():
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()

# Pydantic modelleri (API'nin ne alıp ne döndüreceğini tanımlar)
class TransferRequest(BaseModel):
    source_account_id: int
    destination_account_id: int
    amount: float

# --- API Endpoints ---

@app.get("/accounts", summary="Get All Accounts for a User", operation_id="get_all_accounts")
def get_all_accounts_for_user(user_name: str = Query(..., description="Hesapları getirilecek kullanıcının adı"), database: Session = Depends(get_db)):
    """Kullanıcının tüm bankalardaki hesaplarını ve varlıklarını getirir."""
    # Fonksiyonun içi aynı kalabilir, sadece decorator ve parametre tanımı değişti.
    user = database.query(db.User).filter(db.User.name == user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # SQLAlchemy'nin lazy loading objelerini JSON'a çevirirken sorun yaşamamak için
    # __dict__'ten güvenli bir kopya oluşturalım.
    accounts_data = []
    if user.accounts:
        for acc in user.accounts:
            # Döngüsel referansları önlemek için gerekli alanları manuel seçmek en iyisidir
            accounts_data.append({
                "id": acc.id,
                "bank_name": acc.bank_name,
                "account_type": acc.account_type,
                "balance": acc.balance
            })
            
    return {"user": user.name, "accounts": accounts_data}

@app.post("/transfer", summary="Transfer Funds Between Accounts", operation_id="transfer_funds")
def transfer(request: TransferRequest, database: Session = Depends(get_db)):
    """İki hesap arasında para transferi yapar."""
    source_acc = database.query(db.Account).filter(db.Account.id == request.source_account_id).first()
    dest_acc = database.query(db.Account).filter(db.Account.id == request.destination_account_id).first()

    if not source_acc or not dest_acc:
        raise HTTPException(status_code=404, detail="Account not found")
    if source_acc.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    try:
        source_acc.balance -= request.amount
        dest_acc.balance += request.amount
        database.commit()
        return {"status": "success", "message": f"{request.amount} TL transfer edildi."}
    except Exception as e:
        database.rollback()
        raise HTTPException(status_code=500, detail=f"Transfer failed: {e}")
    

@app.get("/transactions/{user_name}", summary="Query Transactions", operation_id="query_transactions")
def query_transactions(
    user_name: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[Literal["income", "expense", "transfer"]] = None,
    category: Optional[str] = None,
    database: Session = Depends(get_db)
):
    """
    Kullanıcının işlemlerini tarih aralığı, işlem tipi (gelir/gider) veya kategoriye göre sorgular.
    """
    user = database.query(db.User).filter(db.User.name == user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Temel sorguyu oluştur: Kullanıcının tüm işlemlerini getir
    query = (
        database.query(db.Transaction)
        .join(db.Account)
        .filter(db.Account.owner_id == user.id)
    )

    # Gelen parametrelere göre sorguyu dinamik olarak filtrele
    if start_date:
        query = query.filter(db.Transaction.date >= start_date)
    if end_date:
        query = query.filter(db.Transaction.date <= end_date)
    if transaction_type:
        query = query.filter(db.Transaction.transaction_type == transaction_type)
    if category:
        query = query.filter(db.Transaction.category == category)
        
    transactions = query.order_by(db.Transaction.date.desc()).all()

    # Sonuçları daha anlaşılır bir formata dönüştür
    results = [
        {
            "id": t.id,
            "bank": t.account.bank_name,
            "description": t.description,
            "amount": t.amount,
            "type": t.transaction_type,
            "category": t.category,
            "date": t.date.isoformat(),
        }
        for t in transactions
    ]
    return results


# banking_api.py - Bu kısmı en alta veya diğer endpoint'lerin arasına ekle

@app.get("/", summary="Welcome Message", include_in_schema=False)
def read_root():
    """
    Sunucunun çalıştığını belirten basit bir karşılama mesajı.
    """
    return {
        "message": "Riskometre Portföy API ve MCP Sunucusu çalışıyor!",
        "api_docs": "API dokümantasyonu için /docs adresini ziyaret edin.",
        "mcp_endpoint": "MCP istemcileri için endpoint /mcp/ adresidir."
    }


# banking_api.py dosyasının EN ALTINA bunu ekleyin

if __name__ == "__main__":
    import uvicorn
    # Bu, sadece bu dosyayı doğrudan çalıştırdığımızda API'yi başlatır.
    uvicorn.run(app, host="127.0.0.1", port=8000)
    