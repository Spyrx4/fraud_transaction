'use client';

import { useState, useEffect } from 'react';
import { getDashboardStats } from '@/lib/api';

export default function HomePage() {
  const [stats, setStats] = useState(null);
  const [role, setRole] = useState(null);

  useEffect(() => {
    setRole(localStorage.getItem('role'));
    getDashboardStats().then(setStats).catch(() => {});
  }, []);

  const isBank = role === 'bank';

  return (
    <div className="hero">
      <div className="sidebar-logo" style={{ width: 64, height: 64, fontSize: 28, marginBottom: 24 }}>FD</div>
      <h1 className="hero-title">
        {isBank ? 'Dashboard\nFraud Monitoring' : 'Selamat Datang'}
      </h1>
      <p className="hero-desc">
        {isBank
          ? 'Pantau aktivitas transaksi, analisis risiko fraud, dan kelola persetujuan secara real-time.'
          : 'Ajukan transaksi dengan aman. Sistem kami menggunakan Machine Learning untuk memastikan keamanan setiap transaksi Anda.'}
      </p>

      {stats && (
        <div className="hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-value">{Math.round(stats.total_transactions)}</div>
            <div className="hero-stat-label">Total Transaksi</div>
          </div>
          {isBank && (
            <>
              <div className="hero-stat">
                <div className="hero-stat-value">{stats.avg_fraud_pct}%</div>
                <div className="hero-stat-label">Rata-rata Fraud</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-value" style={{ color: 'var(--success)' }}>{Math.round(stats.total_approved)}</div>
                <div className="hero-stat-label">Disetujui</div>
              </div>
            </>
          )}
          <div className="hero-stat">
            <div className="hero-stat-value" style={{ color: 'var(--warning)' }}>{Math.round(stats.total_pending)}</div>
            <div className="hero-stat-label">Menunggu</div>
          </div>
        </div>
      )}
    </div>
  );
}
