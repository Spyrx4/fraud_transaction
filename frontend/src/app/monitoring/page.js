'use client';

import { useState, useEffect, useCallback } from 'react';
import { getTransactions, updateTransactionStatus } from '@/lib/api';

import { RefreshCcw, Check, X, ChevronLeft, ChevronRight } from 'lucide-react';

export default function MonitoringPage() {
  const [transactions, setTransactions] = useState([]);
  const [statusFilter, setStatusFilter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [actionLoading, setActionLoading] = useState(null);
  const LIMIT = 15;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTransactions(statusFilter, LIMIT, page * LIMIT);
      setTransactions(res.transactions || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, page]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleAction = async (id, status) => {
    setActionLoading(id);
    try {
      await updateTransactionStatus(id, status);
      // Optimistic update — langsung ubah di UI tanpa re-fetch
      setTransactions(prev =>
        prev.map(tx => tx.id === id ? { ...tx, status } : tx)
      );
    } catch (e) {
      alert(`Gagal: ${e.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const filters = [
    { label: 'Semua', value: null },
    { label: 'Menunggu', value: 'pending' },
    { label: 'Disetujui', value: 'approved' },
    { label: 'Ditolak', value: 'rejected' },
  ];

  const riskClass = (level) => {
    if (!level) return '';
    return level === 'HIGH' ? 'row-high' : level === 'MEDIUM' ? 'row-medium' : 'row-low';
  };

  const statusLabel = (s) =>
    s === 'pending' ? 'Menunggu' : s === 'approved' ? 'Disetujui' : 'Ditolak';

  const riskLabel = (r) =>
    r === 'HIGH' ? 'TINGGI' : r === 'MEDIUM' ? 'SEDANG' : 'RENDAH';

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Monitoring Transaksi</h1>
        <p className="page-subtitle">Review dan ambil keputusan terhadap transaksi masuk</p>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div className="filter-tabs">
          {filters.map(f => (
            <button
              key={f.label}
              className={`filter-tab ${statusFilter === f.value ? 'active' : ''}`}
              onClick={() => { setStatusFilter(f.value); setPage(0); }}
            >
              {f.label}
            </button>
          ))}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={fetchData}>
          <RefreshCcw size={14} style={{ marginRight: 4 }} /> Refresh
        </button>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <p style={{ padding: 24, color: 'var(--text-secondary)' }}>Memuat data...</p>
        ) : transactions.length === 0 ? (
          <p style={{ padding: 24, color: 'var(--text-muted)' }}>Tidak ada transaksi ditemukan.</p>
        ) : (
          <div className="table-container" style={{ border: 'none' }}>
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Usia</th><th>Jumlah</th><th>Saldo</th>
                  <th>Probabilitas</th><th>Risiko</th><th>Status</th><th>Waktu</th><th>Aksi</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map(tx => (
                  <tr key={tx.id} className={riskClass(tx.risk_level)}>
                    <td><strong>#{tx.id}</strong></td>
                    <td>{tx.age}</td>
                    <td>{Number(tx.transaction_amount).toLocaleString('id-ID')}</td>
                    <td>{Number(tx.account_balance).toLocaleString('id-ID')}</td>
                    <td>
                      <strong style={{
                        color: tx.fraud_probability >= 0.8 ? 'var(--semantic-error)' :
                               tx.fraud_probability >= 0.5 ? 'var(--timeline-done)' : 'var(--semantic-success)',
                        fontWeight: 600
                      }}>
                        {(tx.fraud_probability * 100).toFixed(1)}%
                      </strong>
                    </td>
                    <td><span className={`badge badge-${tx.risk_level?.toLowerCase()}`}>{riskLabel(tx.risk_level)}</span></td>
                    <td><span className={`badge badge-${tx.status}`}>{statusLabel(tx.status)}</span></td>
                    <td style={{ color: 'var(--body)', fontSize: 13 }}>
                      {new Date(tx.created_at).toLocaleString('id-ID')}
                    </td>
                    <td>
                      {tx.status === 'pending' ? (
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            className="btn btn-success btn-sm"
                            style={{ padding: '6px' }}
                            onClick={() => handleAction(tx.id, 'approved')}
                            disabled={actionLoading === tx.id}
                          ><Check size={16} /></button>
                          <button
                            className="btn btn-danger btn-sm"
                            style={{ padding: '6px' }}
                            onClick={() => handleAction(tx.id, 'rejected')}
                            disabled={actionLoading === tx.id}
                          ><X size={16} /></button>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button onClick={() => setPage(p => p - 1)} disabled={page === 0} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <ChevronLeft size={16} /> Sebelumnya
        </button>
        <span className="page-info">Halaman {page + 1}</span>
        <button onClick={() => setPage(p => p + 1)} disabled={transactions.length < LIMIT} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          Selanjutnya <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
