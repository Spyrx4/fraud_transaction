"""
main.py - FastAPI Application Entry Point

Konsep REST API:
================
REST API adalah cara standar agar frontend (browser/app) bisa berkomunikasi 
dengan backend (Python/model ML). Komunikasi menggunakan HTTP:

  Frontend                    Backend (FastAPI)
  --------                    -----------------
  POST /api/predict  ----->   Terima data, predict, simpan, return hasil
  GET  /api/dashboard ----->  Query database, return statistik
  GET  /api/transactions -->  Return daftar transaksi
  PATCH /api/transactions/5 > Update status transaksi ID=5

HTTP Methods:
  GET    = Ambil data (read-only)
  POST   = Kirim data baru (create)
  PATCH  = Update sebagian data (update)
  DELETE = Hapus data

Konsep Pydantic:
================
Pydantic memvalidasi data yang masuk SEBELUM sampai ke handler function.
Jika nasabah mengirim age="abc", Pydantic akan otomatis menolak dengan
error 422 (Unprocessable Entity). Ini melindungi model dari input sampah.

Cara menjalankan:
  cd ml-service
  py -m uvicorn app.main:app --reload --port 8000

  --reload : auto-restart saat code berubah (development mode)
  --port   : port yang digunakan

Setelah jalan, buka browser:
  http://localhost:8000/docs  → Swagger UI (interactive API docs)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from contextlib import asynccontextmanager

# Import module kita
from app.database import init_db, insert_transaction, get_transactions, update_transaction_status, get_dashboard_stats
from app.model_loader import load_model, predict_fraud
from app.agent import process_chat



# ============================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================
# Ini mendefinisikan BENTUK data yang boleh masuk & keluar API.
# Field(...) = required, Field(default) = optional
# ge/le = greater/less than or equal (validasi range)
# ============================================================

class TransactionInput(BaseModel):
    """
    Schema untuk input transaksi dari nasabah.
    Setiap field punya validasi agar data yang masuk masuk akal.
    """
    age: float = Field(..., ge=17, le=120, description="Usia pemilik akun (0-120)")
    transaction_amount: float = Field(..., ge=0, description="Nominal transaksi")
    account_balance: float = Field(..., description="Saldo akun saat ini")
    num_transactions_today: int = Field(..., ge=0, description="Jumlah transaksi hari ini")
    is_foreign_transaction: int = Field(..., ge=0, le=1, description="0=Domestik, 1=Luar negeri")
    transaction_hour: int = Field(..., ge=0, le=23, description="Jam transaksi (0-23)")
    prev_fraud_flag: int = Field(..., ge=0, le=1, description="0=Tidak pernah fraud, 1=Pernah")
    merchant_distance_km: float = Field(..., ge=0, description="Jarak ke merchant (km)")
    merchant_risk_score: float = Field(..., ge=0, le=10, description="Risk score merchant (0-10)")


class TransactionResponse(BaseModel):
    """Schema untuk response setelah prediksi."""
    transaction_id: int
    fraud_probability: float
    risk_level: str
    prediction: int
    status: str


class StatusUpdate(BaseModel):
    """Schema untuk update status transaksi."""
    status: str = Field(..., pattern="^(approved|rejected|pending)$")


class ChatRequest(BaseModel):
    """Schema untuk pesan chat ke AI Agent."""
    message: str = Field(..., description="Pesan atau perintah teks dari user")


# ============================================================
# Application Lifecycle
# ============================================================
# asynccontextmanager digunakan untuk kode yang perlu jalan
# SEBELUM server siap menerima request (startup) dan
# SETELAH server shutdown (cleanup).
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: Load model & init database.
    Ini jalan SEKALI saat server mulai.
    """
    print("Starting up...")
    init_db()       # Buat tabel jika belum ada
    load_model()    # Load pipeline ke memori
    print("Server ready!")
    yield           # Server berjalan di sini
    print("Shutting down...")


# ============================================================
# FastAPI App Instance
# ============================================================
app = FastAPI(
    title="Fraud Detection API",
    description="API untuk prediksi fraud transaksi menggunakan XGBoost ML Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================
# CORS Middleware
# ============================================================
# CORS (Cross-Origin Resource Sharing) diperlukan karena:
# Frontend (Next.js) jalan di localhost:3000
# Backend (FastAPI) jalan di localhost:8000
#
# Tanpa CORS, browser akan BLOCK request dari frontend ke backend
# karena berbeda "origin" (port berbeda = origin berbeda).
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.65:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    """Health check endpoint. Berguna untuk monitoring uptime."""
    return {"status": "online", "service": "Fraud Detection API"}


@app.post("/api/predict", response_model=TransactionResponse)
async def predict_transaction(transaction: TransactionInput):
    """
    Endpoint utama: Terima data transaksi, prediksi fraud, simpan ke DB.
    
    Alur:
    1. Pydantic validasi input (otomatis, kita tidak perlu kode)
    2. Konversi ke dict untuk pipeline
    3. Pipeline predict (clean → impute → feature eng → scale → classify)
    4. Simpan ke database
    5. Return hasil ke frontend
    
    Jika terjadi error di pipeline, kita tangkap dan return HTTP 500.
    """
    try:
        # .model_dump() konversi Pydantic model ke dict Python
        data = transaction.model_dump()
        
        # Jalankan prediksi
        result = predict_fraud(data)
        
        # Simpan ke database
        tx_id = insert_transaction(data, result['fraud_probability'], result['risk_level'])
        
        return TransactionResponse(
            transaction_id=tx_id,
            fraud_probability=result['fraud_probability'],
            risk_level=result['risk_level'],
            prediction=result['prediction'],
            status="pending"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/api/transactions")
async def list_transactions(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    Ambil daftar transaksi.
    
    Query parameters (opsional):
      ?status=pending     → filter by status
      ?limit=20&offset=0  → pagination
    
    Query parameters dikirim di URL, bukan di body:
      GET /api/transactions?status=pending&limit=20
    """
    transactions = get_transactions(status=status, limit=limit, offset=offset)
    return {"transactions": transactions, "count": len(transactions)}


@app.patch("/api/transactions/{transaction_id}")
async def update_status(transaction_id: int, update: StatusUpdate):
    """
    Update status transaksi.
    
    Path parameter {transaction_id} otomatis di-extract dari URL:
      PATCH /api/transactions/5  →  transaction_id = 5
    """
    success = update_transaction_status(transaction_id, update.status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Transaction ID {transaction_id} not found")
    return {"message": f"Transaction {transaction_id} updated to {update.status}"}


@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """
    Statistik untuk dashboard bank.
    Semua perhitungan dilakukan di SQL (efisien) bukan di Python.
    """
    stats = get_dashboard_stats()
    return stats


@app.post("/api/predict/batch")
async def predict_batch(transactions: List[TransactionInput]):
    """
    Batch prediction: Proses banyak transaksi sekaligus.

    Digunakan oleh kreditur/bank untuk:
    - Upload data nasabah yang mengajukan secara offline
    - Input dari channel lain (kantor cabang, call center, dll)

    Input: Array of TransactionInput
    Output: Hasil prediksi per transaksi + ringkasan agregat

    Contoh request body:
    [
        {"age": 25, "transaction_amount": 9500, ...},
        {"age": 45, "transaction_amount": 150, ...}
    ]
    """
    if len(transactions) == 0:
        raise HTTPException(status_code=400, detail="Minimal 1 transaksi diperlukan")
    if len(transactions) > 100:
        raise HTTPException(status_code=400, detail="Maksimal 100 transaksi per batch")

    results = []
    errors = []

    for i, tx in enumerate(transactions):
        try:
            data = tx.model_dump()
            result = predict_fraud(data)
            tx_id = insert_transaction(data, result['fraud_probability'], result['risk_level'])

            results.append({
                "index": i,
                "transaction_id": tx_id,
                "fraud_probability": result['fraud_probability'],
                "risk_level": result['risk_level'],
                "prediction": result['prediction'],
                "status": "pending"
            })
        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    # Hitung ringkasan
    total = len(results)
    fraud_count = sum(1 for r in results if r['prediction'] == 1)
    avg_prob = sum(r['fraud_probability'] for r in results) / total if total > 0 else 0

    return {
        "total_processed": total,
        "total_errors": len(errors),
        "fraud_detected": fraud_count,
        "normal_detected": total - fraud_count,
        "avg_fraud_probability": round(avg_prob, 4),
        "results": results,
        "errors": errors
    }


@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    """
    Endpoint untuk berkomunikasi dengan AI Agent.
    Menerima pesan dari frontend dan memprosesnya menggunakan OpenAI Function Calling.
    """
    try:
        reply = process_chat(request.message)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
