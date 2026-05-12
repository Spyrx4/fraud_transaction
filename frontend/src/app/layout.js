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
              <div className="role-select-screen" data-theme={theme}>
                <div className="role-select-container">
                  <div className="sidebar-logo" style={{ width: 64, height: 64, fontSize: 28, margin: '0 auto 24px' }}>FD</div>
                  <h1 className="hero-title" style={{ fontSize: 32 }}>Fraud Detection<br/>Monitoring System</h1>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 16, marginBottom: 40, maxWidth: 420, margin: '0 auto 40px' }}>
                    Pilih peran Anda untuk melanjutkan
                  </p>

                  <div className="role-cards">
                    {/* Nasabah Card */}
                    <button className="role-card" onClick={() => selectRole('nasabah')}>
                      <div className="role-card-icon">👤</div>
                      <h2 className="role-card-title">Nasabah / Debitur</h2>
                      <p className="role-card-desc">
                        Ajukan transaksi dan pantau status persetujuan secara real-time.
                      </p>
                      <ul className="role-card-features">
                        <li>📝 Form pengajuan transaksi</li>
                        <li>📋 Pantau status transaksi</li>
                        <li>📊 Lihat hasil analisis fraud</li>
                      </ul>
                      <span className="btn btn-primary" style={{ marginTop: 16, width: '100%' }}>
                        Masuk sebagai Nasabah →
                      </span>
                    </button>

                    {/* Bank Card */}
                    <button className="role-card" onClick={() => selectRole('bank')}>
                      <div className="role-card-icon">🏦</div>
                      <h2 className="role-card-title">Kreditur / Bank</h2>
                      <p className="role-card-desc">
                        Dashboard analitik, monitoring transaksi, dan AI assistant.
                      </p>
                      <ul className="role-card-features">
                        <li>📊 Dashboard analitik lengkap</li>
                        <li>🔍 Monitoring & review transaksi</li>
                        <li>🤖 AI Chatbot assistant</li>
                      </ul>
                      <span className="btn btn-primary" style={{ marginTop: 16, width: '100%' }}>
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
