'use client';

import { useState } from 'react';
import { predictTransaction } from '@/lib/api';

import { CheckCircle2, PlusCircle, List, Send, XCircle, Loader2 } from 'lucide-react';

export default function TransactionPage() {
  const [form, setForm] = useState({
    age: '', transaction_amount: '', account_balance: '',
    num_transactions_today: '', is_foreign_transaction: 0,
    transaction_hour: '', prev_fraud_flag: 0,
    merchant_distance_km: '', merchant_risk_score: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const [txId, setTxId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {
        age: parseFloat(form.age),
        transaction_amount: parseFloat(form.transaction_amount),
        account_balance: parseFloat(form.account_balance),
        num_transactions_today: parseInt(form.num_transactions_today),
        is_foreign_transaction: form.is_foreign_transaction,
        transaction_hour: parseInt(form.transaction_hour),
        prev_fraud_flag: form.prev_fraud_flag,
        merchant_distance_km: parseFloat(form.merchant_distance_km),
        merchant_risk_score: parseFloat(form.merchant_risk_score),
      };
      const res = await predictTransaction(payload);
      setTxId(res.transaction_id);
      setSubmitted(true);
    } catch (err) {
      setError(err.message || 'Terjadi kesalahan');
    } finally {
      setLoading(false);
    }
  };

  const handleNewTransaction = () => {
    setForm({
      age: '', transaction_amount: '', account_balance: '',
      num_transactions_today: '', is_foreign_transaction: 0,
      transaction_hour: '', prev_fraud_flag: 0,
      merchant_distance_km: '', merchant_risk_score: '',
    });
    setSubmitted(false);
    setTxId(null);
    setError('');
  };

  // ===== Tampilan setelah berhasil submit =====
  if (submitted) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Pengajuan Berhasil</h1>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: 48, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ color: 'var(--success)', marginBottom: 16 }}>
            <CheckCircle2 size={64} />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>
            Transaksi Berhasil Diajukan
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 15, marginBottom: 8 }}>
            Nomor Transaksi: <strong style={{ color: 'var(--accent)' }}>#{txId}</strong>
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, maxWidth: 400, margin: '0 auto 28px' }}>
            Transaksi Anda sedang dalam proses review oleh pihak bank.
            Anda dapat memantau statusnya di halaman <strong>Status Transaksi</strong>.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={handleNewTransaction} style={{ gap: 8 }}>
              <PlusCircle size={18} /> Ajukan Transaksi Baru
            </button>
            <a href="/status" className="btn btn-ghost" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <List size={18} /> Lihat Status
            </a>
          </div>
        </div>
      </div>
    );
  }

  // ===== Tampilan Form =====
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Pengajuan Transaksi Baru</h1>
        <p className="page-subtitle">Lengkapi data transaksi Anda untuk diproses</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Usia</label>
              <input className="form-input" type="number" min="17" max="120" step="1"
                placeholder="Contoh: 35" value={form.age}
                onChange={e => handleChange('age', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Jumlah Transaksi (Rp)</label>
              <input className="form-input" type="number" min="0" step="1"
                placeholder="Contoh: 500000" value={form.transaction_amount}
                onChange={e => handleChange('transaction_amount', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Saldo Rekening (Rp)</label>
              <input className="form-input" type="number" step="0.01"
                placeholder="Contoh: 15000000" value={form.account_balance}
                onChange={e => handleChange('account_balance', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Jumlah Transaksi Hari Ini</label>
              <input className="form-input" type="number" min="0" step="1"
                placeholder="Contoh: 3" value={form.num_transactions_today}
                onChange={e => handleChange('num_transactions_today', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Jam Transaksi (0-23)</label>
              <input className="form-input" type="number" min="0" max="23" step="1"
                placeholder="Contoh: 14" value={form.transaction_hour}
                onChange={e => handleChange('transaction_hour', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Jarak ke Merchant (km)</label>
              <input className="form-input" type="number" min="0" step="0.1"
                placeholder="Contoh: 5.2" value={form.merchant_distance_km}
                onChange={e => handleChange('merchant_distance_km', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Skor Risiko Merchant (0-10)</label>
              <input className="form-input" type="number" min="0" max="10" step="0.1"
                placeholder="Contoh: 3.5" value={form.merchant_risk_score}
                onChange={e => handleChange('merchant_risk_score', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Transaksi Luar Negeri</label>
              <div className="toggle-group">
                <button type="button" className={`toggle ${form.is_foreign_transaction ? 'active' : ''}`}
                  onClick={() => handleChange('is_foreign_transaction', form.is_foreign_transaction ? 0 : 1)} />
                <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                  {form.is_foreign_transaction ? 'Ya' : 'Tidak'}
                </span>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Riwayat Fraud Sebelumnya</label>
              <div className="toggle-group">
                <button type="button" className={`toggle ${form.prev_fraud_flag ? 'active' : ''}`}
                  onClick={() => handleChange('prev_fraud_flag', form.prev_fraud_flag ? 0 : 1)} />
                <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                  {form.prev_fraud_flag ? 'Ya' : 'Tidak'}
                </span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <button className="btn btn-primary" type="submit" disabled={loading}
              style={{ padding: '14px 48px', fontSize: 16, gap: 8 }}>
              {loading ? <><Loader2 size={20} className="spin" /> Mengirim...</> : <><Send size={20} /> Ajukan Transaksi</>}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 12 }}>
          <XCircle size={20} style={{ color: 'var(--danger)' }} />
          <p style={{ color: 'var(--danger)', margin: 0 }}>{error}</p>
        </div>
      )}
    </div>
  );
}
