"""
agent.py - AI Agent Logic for Fraud Detection System

Menggunakan OpenAI API untuk memproses pesan natural language dari user
dan mengubahnya menjadi pemanggilan fungsi (Function Calling / Tool Calling).
"""

import os
import json
from openai import OpenAI
from app.database import bulk_update_by_risk, get_agent_summary, get_daily_report
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Inisialisasi OpenAI client
# Pastikan OPENAI_API_KEY ada di dalam file .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# Definisi Tools (Buku Panduan untuk LLM)
# ============================================================
# Ini adalah skema JSON yang memberitahu OpenAI tentang
# fungsi apa saja yang tersedia dan parameter apa yang dibutuhkan.

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bulk_approve",
            "description": "Menyetujui (approve) banyak transaksi yang masih pending secara massal berdasarkan batas maksimal risk_score (fraud_probability).",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_risk_score": {
                        "type": "number",
                        "description": "Batas maksimal fraud probability (0.0 sampai 1.0). Transaksi di bawah batas ini akan di-approve."
                    }
                },
                "required": ["max_risk_score"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bulk_reject",
            "description": "Menolak (reject) banyak transaksi yang masih pending secara massal berdasarkan batas minimal risk_score (fraud_probability).",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_risk_score": {
                        "type": "number",
                        "description": "Batas minimal fraud probability (0.0 sampai 1.0). Transaksi di atas batas ini akan di-reject."
                    }
                },
                "required": ["min_risk_score"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_database_stats",
            "description": "Mengambil ringkasan kondisi database saat ini, seperti total transaksi pending, disetujui, dan ditolak."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_daily_report",
            "description": "Menghasilkan laporan harian transaksi hari ini, mencakup total transaksi, fraud yang dicegah, dan volume transaksi."
        }
    }
]

# ============================================================
# Pemetaan Nama Fungsi ke Fungsi Python Sebenarnya
# ============================================================
def execute_tool(tool_name: str, arguments: dict) -> str:
    """Mengeksekusi fungsi lokal berdasarkan permintaan LLM."""
    try:
        if tool_name == "bulk_approve":
            max_risk = arguments.get("max_risk_score")
            affected = bulk_update_by_risk(threshold_risk=max_risk, condition='<', status='approved')
            return f"Berhasil menyetujui (approve) {affected} transaksi yang memiliki risk score di bawah {max_risk}."
            
        elif tool_name == "bulk_reject":
            min_risk = arguments.get("min_risk_score")
            affected = bulk_update_by_risk(threshold_risk=min_risk, condition='>', status='rejected')
            return f"Berhasil menolak (reject) {affected} transaksi yang memiliki risk score di atas {min_risk}."
            
        elif tool_name == "get_database_stats":
            stats = get_agent_summary()
            return stats
            
        elif tool_name == "generate_daily_report":
            report = get_daily_report()
            # Format report as JSON string so LLM can read and summarize it
            return f"Data Laporan Harian: {json.dumps(report)}. Tolong sampaikan data ini dalam format laporan yang rapi ke user."
            
        else:
            return f"Error: Fungsi {tool_name} tidak ditemukan."
            
    except Exception as e:
        return f"Error saat mengeksekusi {tool_name}: {str(e)}"

# ============================================================
# Fungsi Utama Agent
# ============================================================
def process_chat(user_message: str) -> str:
    """
    1. Kirim pesan ke LLM.
    2. Cek apakah LLM ingin memanggil fungsi (tool_calls).
    3. Jika ya, jalankan fungsi lokal, kembalikan hasilnya ke LLM.
    4. Minta LLM merangkum hasil akhirnya untuk user.
    """
    
    # Jika tidak ada API key, fallback (agar aplikasi tidak crash)
    if not os.getenv("OPENAI_API_KEY"):
        return "Maaf, API Key OpenAI belum dikonfigurasi di backend. Silakan tambahkan OPENAI_API_KEY di file .env"

    system_prompt = (
        "Anda adalah Fraud Detection Assistant, asisten cerdas untuk sistem perbankan. "
        "Anda dapat menjawab pertanyaan tentang transaksi, memberikan laporan harian, dan mengambil tindakan "
        "seperti menerima (approve) atau menolak (reject) transaksi. "
        "Jawab dengan singkat, profesional, dan gunakan Bahasa Indonesia."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    try:
        # Langkah 1: Kirim permintaan awal ke OpenAI beserta daftar tools
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Gunakan gpt-4o-mini untuk efisiensi harga dan kecepatan
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Langkah 2: Cek apakah LLM ingin memanggil tools
        if tool_calls:
            messages.append(response_message) # Tambahkan balasan asisten (yang berisi instruksi pemanggilan tool) ke history
            
            # Eksekusi semua tool yang diminta oleh LLM
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"[Agent] Memanggil tool: {function_name} dengan argumen {function_args}")
                
                # Jalankan fungsi lokal
                function_response = execute_tool(function_name, function_args)
                
                # Berikan hasil fungsi kembali ke LLM
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

            # Langkah 3: Minta respons final dari LLM setelah fungsi dijalankan
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            
            return final_response.choices[0].message.content

        else:
            # Jika LLM tidak memanggil alat, langsung return balasannya
            return response_message.content

    except Exception as e:
        return f"Terjadi kesalahan pada AI Agent: {str(e)}"
