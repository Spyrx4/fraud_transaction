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
    <div className="hero" style={{ textAlign: 'center', padding: 'var(--space-section) 24px', maxWidth: 900, margin: '0 auto' }}>
      <div className="sidebar-logo" style={{ width: 48, height: 48, fontSize: 20, margin: '0 auto 32px' }}>FD</div>
      <h1 className="hero-title" style={{ whiteSpace: 'pre-line', marginBottom: 24 }}>
        {isBank ? 'Dashboard\nFraud Monitoring' : 'Platform Keamanan\nTransaksi Digital'}
      </h1>
      <p className="hero-desc" style={{ fontSize: 20, color: 'var(--body)', maxWidth: 600, margin: '0 auto 64px', lineHeight: 1.5 }}>
        {isBank
          ? 'Pantau aktivitas transaksi, analisis risiko fraud, dan kelola persetujuan secara real-time dengan asisten AI.'
          : 'Ajukan transaksi dengan aman. Sistem kami menggunakan Machine Learning canggih untuk memastikan keamanan setiap transaksi Anda.'}
      </p>

      {stats && (
        <div className="hero-stats" style={{ display: 'flex', justifyContent: 'center', gap: 64, flexWrap: 'wrap', borderTop: '1px solid var(--hairline)', paddingTop: 64 }}>
          <div className="hero-stat">
            <div className="hero-stat-value" style={{ fontSize: 48, fontWeight: 400, color: 'var(--ink)', letterSpacing: '-0.03em' }}>
              {Math.round(stats.total_transactions)}
            </div>
            <div className="caption-uppercase">Total Transaksi</div>
          </div>
          {isBank && (
            <>
              <div className="hero-stat">
                <div className="hero-stat-value" style={{ fontSize: 48, fontWeight: 400, color: 'var(--primary)', letterSpacing: '-0.03em' }}>
                  {stats.avg_fraud_pct}%
                </div>
                <div className="caption-uppercase">Rata-rata Fraud</div>
              </div>
            </>
          )}
          <div className="hero-stat">
            <div className="hero-stat-value" style={{ fontSize: 48, fontWeight: 400, color: 'var(--timeline-done)', letterSpacing: '-0.03em' }}>
              {Math.round(stats.total_pending)}
            </div>
            <div className="caption-uppercase">Menunggu</div>
          </div>
        </div>
      )}
    </div>
  );
}
