'use client';

import { useState, useEffect } from 'react';
import { getTransactions } from '@/lib/api';

import { Clock, CheckCircle2, XCircle, Inbox, Wallet } from 'lucide-react';

export default function StatusPage() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTransactions(null, 50, 0)
      .then(res => setTransactions(res.transactions || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const statusConfig = {
    pending:  { label: 'Menunggu Review', color: 'var(--timeline-done)', icon: <Clock size={14} /> },
    approved: { label: 'Disetujui', color: 'var(--semantic-success)', icon: <CheckCircle2 size={14} /> },
    rejected: { label: 'Ditolak', color: 'var(--semantic-error)', icon: <XCircle size={14} /> },
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Status Transaksi</h1>
        <p className="page-subtitle">Pantau status pengajuan transaksi Anda</p>
      </div>

      {loading ? (
        <p style={{ color: 'var(--muted)' }}>Memuat data...</p>
      ) : transactions.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 64, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ marginBottom: 24, color: 'var(--hairline-strong)' }}><Inbox size={48} /></div>
          <h3 style={{ color: 'var(--ink)', marginBottom: 12, fontWeight: 500 }}>Belum Ada Transaksi</h3>
          <p style={{ color: 'var(--body)', fontSize: 14, maxWidth: 300 }}>
            Ajukan transaksi baru melalui menu "Ajukan Transaksi" di sidebar.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {transactions.map(tx => {
            const st = statusConfig[tx.status] || statusConfig.pending;
            return (
              <div key={tx.id} className="card" style={{ padding: '20px 24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                      <strong style={{ fontSize: 16, color: 'var(--ink)', fontWeight: 600 }}>Transaksi #{tx.id}</strong>
                      <span className={`badge badge-${tx.status}`} style={{ gap: 6, fontWeight: 600 }}>
                        {st.icon} {st.label}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap', fontSize: 14, color: 'var(--body)' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Wallet size={16} style={{ color: 'var(--muted)' }} /> Rp {Number(tx.transaction_amount).toLocaleString('id-ID')}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Clock size={16} style={{ color: 'var(--muted)' }} /> {new Date(tx.created_at).toLocaleString('id-ID')}
                      </span>
                    </div>
                  </div>
                  <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    <div style={{ color: st.color }}>
                      {tx.status === 'approved' ? <CheckCircle2 size={32} /> : tx.status === 'rejected' ? <XCircle size={32} /> : <Clock size={32} />}
                    </div>
                    <div style={{ fontSize: 11, color: st.color, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {tx.status === 'approved' ? 'Disetujui' : tx.status === 'rejected' ? 'Ditolak' : 'Menunggu'}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
