'use client';

import { useState, useEffect } from 'react';
import { getDashboardStats, getTransactions } from '@/lib/api';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  ArcElement, Tooltip, Legend
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

import { Activity, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [s, t] = await Promise.all([
        getDashboardStats(),
        getTransactions(null, 10, 0),
      ]);
      setStats(s);
      setRecent(t.transactions || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <p style={{ color: 'var(--text-secondary)' }}>Memuat data...</p>;
  if (!stats) return <p style={{ color: 'var(--danger)' }}>Gagal memuat data. Pastikan backend berjalan.</p>;

  /* --- Chart: Fraud by Hour --- */
  const hourlyLabels = stats.hourly_distribution?.map(h => `${h.hour}:00`) || [];
  const hourlyData = {
    labels: hourlyLabels,
    datasets: [
      {
        label: 'Total Transaksi',
        data: stats.hourly_distribution?.map(h => h.count) || [],
        backgroundColor: 'rgba(99,102,241,0.5)',
        borderColor: 'var(--accent)',
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: 'High Risk',
        data: stats.hourly_distribution?.map(h => h.fraud_count) || [],
        backgroundColor: 'rgba(239,68,68,0.5)',
        borderColor: 'var(--danger)',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { labels: { color: 'var(--text-secondary)', font: { family: 'Inter' } } }
    },
    scales: {
      x: { ticks: { color: 'var(--text-muted)' }, grid: { color: 'var(--border)' } },
      y: { ticks: { color: 'var(--text-muted)' }, grid: { color: 'var(--border)' } },
    },
  };

  /* --- Chart: Risk Distribution --- */
  const riskData = {
    labels: ['Tinggi', 'Sedang', 'Rendah'],
    datasets: [{
      data: [stats.total_high_risk, stats.total_medium_risk, stats.total_low_risk],
      backgroundColor: ['rgba(239,68,68,0.7)', 'rgba(245,158,11,0.7)', 'rgba(34,197,94,0.7)'],
      borderWidth: 0,
    }],
  };

  const doughnutOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'bottom', labels: { color: 'var(--text-secondary)', font: { family: 'Inter' }, padding: 16 } }
    },
  };

  const riskClass = (level) => {
    if (!level) return '';
    return level === 'HIGH' ? 'row-high' : level === 'MEDIUM' ? 'row-medium' : 'row-low';
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Ringkasan analitik fraud detection — auto-refresh setiap 30 detik</p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon accent"><Activity size={20} /></div>
          <div className="kpi-info">
            <div className="kpi-label">Total Transaksi</div>
            <div className="kpi-value">{Math.round(stats.total_transactions)}</div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon danger"><AlertTriangle size={20} /></div>
          <div className="kpi-info">
            <div className="kpi-label">Rata-rata Fraud</div>
            <div className="kpi-value">{stats.avg_fraud_pct}%</div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon success"><CheckCircle2 size={20} /></div>
          <div className="kpi-info">
            <div className="kpi-label">Disetujui</div>
            <div className="kpi-value">{Math.round(stats.total_approved)}</div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon warning"><Clock size={20} /></div>
          <div className="kpi-info">
            <div className="kpi-label">Menunggu</div>
            <div className="kpi-value">{Math.round(stats.total_pending)}</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-title">Distribusi Transaksi per Jam</div>
          {hourlyLabels.length > 0
            ? <Bar data={hourlyData} options={chartOptions} />
            : <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Belum ada data</p>
          }
        </div>
        <div className="chart-card">
          <div className="chart-title">Distribusi Level Risiko</div>
          {stats.total_transactions > 0
            ? <div style={{ maxWidth: 280, margin: '0 auto' }}><Doughnut data={riskData} options={doughnutOptions} /></div>
            : <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Belum ada data</p>
          }
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="card">
        <div className="chart-title" style={{ marginBottom: 12 }}>Transaksi Terbaru</div>
        {recent.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Belum ada transaksi</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Jumlah</th><th>Probabilitas</th><th>Risiko</th><th>Status</th><th>Waktu</th>
                </tr>
              </thead>
              <tbody>
                {recent.map(tx => (
                  <tr key={tx.id} className={riskClass(tx.risk_level)}>
                    <td>#{tx.id}</td>
                    <td>{Number(tx.transaction_amount).toLocaleString('id-ID')}</td>
                    <td>{(tx.fraud_probability * 100).toFixed(1)}%</td>
                    <td><span className={`badge badge-${tx.risk_level?.toLowerCase()}`}>{tx.risk_level}</span></td>
                    <td><span className={`badge badge-${tx.status}`}>{tx.status === 'pending' ? 'Menunggu' : tx.status === 'approved' ? 'Disetujui' : 'Ditolak'}</span></td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{new Date(tx.created_at).toLocaleString('id-ID')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
