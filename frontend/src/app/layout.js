'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import "./globals.css";
import Sidebar from '@/components/Sidebar';
import ChatWidget from '@/components/ChatWidget';

export default function RootLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [theme, setTheme] = useState('dark');
  const [role, setRole] = useState(null); // null = belum pilih, 'nasabah', 'bank'
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const savedCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    const savedRole = localStorage.getItem('role');
    setTheme(savedTheme);
    setCollapsed(savedCollapsed);
    setRole(savedRole);
    document.documentElement.setAttribute('data-theme', savedTheme);
    setMounted(true);
  }, []);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  const toggleCollapse = () => {
    setCollapsed(!collapsed);
    localStorage.setItem('sidebar-collapsed', String(!collapsed));
  };

  const switchRole = () => {
    const next = role === 'bank' ? 'nasabah' : 'bank';
    setRole(next);
    localStorage.setItem('role', next);
    router.push('/');
  };

  const selectRole = (r) => {
    setRole(r);
    localStorage.setItem('role', r);
    if (r === 'nasabah') router.push('/transaction');
    else router.push('/dashboard');
  };

  return (
    <html lang="id" data-theme={theme}>
      <head>
        <title>Fraud Detection Monitoring System</title>
        <meta name="description" content="Sistem monitoring transaksi berbasis Machine Learning untuk deteksi fraud" />
      </head>
      <body>
        {mounted && (
          <>
            {!role ? (
              /* ====== Role Selection Screen ====== */
              <div className="role-select-screen">
                <div className="role-select-container" style={{ maxWidth: 800, padding: '0 24px' }}>
                  <div className="sidebar-logo" style={{ width: 64, height: 64, fontSize: 28, margin: '0 auto 32px' }}>FD</div>
                  <h1 className="hero-title" style={{ marginBottom: 16 }}>Fraud Detection<br/>Monitoring System</h1>
                  <p style={{ color: 'var(--body)', fontSize: 18, marginBottom: 64, maxWidth: 500, margin: '0 auto 64px' }}>
                    Pilih peran Anda untuk melanjutkan ke platform monitoring berbasis AI.
                  </p>

                  <div className="role-cards" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
                    {/* Nasabah Card */}
                    <button className="role-card" onClick={() => selectRole('nasabah')}>
                      <div className="role-card-icon" style={{ fontSize: 40, marginBottom: 20 }}>👤</div>
                      <h2 className="card-title" style={{ fontSize: 22, marginBottom: 12 }}>Nasabah / Debitur</h2>
                      <p style={{ color: 'var(--body)', fontSize: 15, marginBottom: 24, lineHeight: 1.6 }}>
                        Ajukan transaksi dan pantau status persetujuan secara real-time.
                      </p>
                      <ul className="role-card-features" style={{ listStyle: 'none', padding: 0, marginBottom: 32, textAlign: 'left', fontSize: 14, color: 'var(--body)' }}>
                        <li style={{ marginBottom: 8 }}>📝 Form pengajuan transaksi</li>
                        <li style={{ marginBottom: 8 }}>📋 Pantau status transaksi</li>
                        <li>📊 Lihat hasil analisis fraud</li>
                      </ul>
                      <span className="btn btn-primary" style={{ width: '100%' }}>
                        Masuk sebagai Nasabah →
                      </span>
                    </button>

                    {/* Bank Card */}
                    <button className="role-card" onClick={() => selectRole('bank')}>
                      <div className="role-card-icon" style={{ fontSize: 40, marginBottom: 20 }}>🏦</div>
                      <h2 className="card-title" style={{ fontSize: 22, marginBottom: 12 }}>Kreditur / Bank</h2>
                      <p style={{ color: 'var(--body)', fontSize: 15, marginBottom: 24, lineHeight: 1.6 }}>
                        Dashboard analitik, monitoring transaksi, dan AI assistant.
                      </p>
                      <ul className="role-card-features" style={{ listStyle: 'none', padding: 0, marginBottom: 32, textAlign: 'left', fontSize: 14, color: 'var(--body)' }}>
                        <li style={{ marginBottom: 8 }}>📊 Dashboard analitik lengkap</li>
                        <li style={{ marginBottom: 8 }}>🔍 Monitoring & review transaksi</li>
                        <li>🤖 AI Chatbot assistant</li>
                      </ul>
                      <span className="btn btn-primary" style={{ width: '100%' }}>
                        Masuk sebagai Bank →
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* ====== Main App Layout ====== */
              <div className={`app-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
                <Sidebar
                  collapsed={collapsed}
                  onToggle={toggleCollapse}
                  theme={theme}
                  onThemeToggle={toggleTheme}
                  role={role}
                  onRoleChange={switchRole}
                />
                <main className="main-content">
                  {children}
                </main>
                {/* ChatWidget hanya muncul untuk Bank */}
                {role === 'bank' && <ChatWidget />}
              </div>
            )}
          </>
        )}
      </body>
    </html>
  );
}
