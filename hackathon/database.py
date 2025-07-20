# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy import DateTime
import datetime

DATABASE_URL = "sqlite:///./portfolio.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Veritabanı Modelleri (Tablolar)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    accounts = relationship("Account", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    
    description = Column(String) # "Netflix Aboneliği", "Maaş Ödemesi"
    amount = Column(Float) # Gider için negatif (-79.99), gelir için pozitif (+15000)
    
    # Bu alanlar sorgulama için çok önemli
    transaction_type = Column(String, index=True) # 'income', 'expense', 'transfer'
    category = Column(String, index=True) # 'Fatura', 'Market', 'Maaş', 'Yatırım'
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    account = relationship("Account")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, index=True)
    account_type = Column(String, default="vadesiz_tl")
    balance = Column(Float)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="accounts")
    assets = relationship("Asset", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True) # e.g., 'GARAN', 'FROTO'
    quantity = Column(Float)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="assets")

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)