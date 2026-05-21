'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, FileText, ClipboardList, LayoutDashboard, 
  Search, User, Building2, RefreshCcw, 
  Sun, Moon, ChevronLeft, ChevronRight 
} from 'lucide-react';

const nasabahNav = [
  { href: '/', label: 'Beranda', icon: <Home size={18} /> },
  { href: '/transaction', label: 'Ajukan Transaksi', icon: <FileText size={18} /> },
  { href: '/status', label: 'Status Transaksi', icon: <ClipboardList size={18} /> },
];

const bankNav = [
  { href: '/', label: 'Beranda', icon: <Home size={18} /> },
  { href: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
  { href: '/monitoring', label: 'Monitoring', icon: <Search size={18} /> },
];

export default function Sidebar({ collapsed, onToggle, theme, onThemeToggle, role, onRoleChange }) {
  const pathname = usePathname();
  const navItems = role === 'bank' ? bankNav : nasabahNav;
  const roleLabel = role === 'bank' ? 'Kreditur / Bank' : 'Nasabah / Debitur';
  const RoleIcon = role === 'bank' ? Building2 : User;

  return (
    <aside className="sidebar">
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">FD</div>
        <span className="sidebar-title">Fraud Detection</span>
      </div>

      {/* Role Indicator */}
      <div className="role-indicator" style={{ padding: '0 8px', marginBottom: 24 }}>
        <div style={{
          background: 'var(--canvas-soft)',
          border: '1px solid var(--hairline)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 12px',
          fontSize: 11,
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: 'var(--ink)',
          textAlign: collapsed ? 'center' : 'left',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          gap: 8
        }}>
          <RoleIcon size={14} style={{ color: 'var(--primary)' }} />
          {!collapsed && <span>{roleLabel}</span>}
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item ${pathname === item.href ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        {/* Switch Role */}
        <button className="theme-toggle" onClick={onRoleChange}>
          <span className="nav-icon"><RefreshCcw size={16} /></span>
          <span className="nav-label">Ganti ke {role === 'bank' ? 'Nasabah' : 'Bank'}</span>
        </button>

        {/* Theme Toggle */}
        <button className="theme-toggle" onClick={onThemeToggle}>
          <span className="nav-icon">{theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}</span>
          <span className="nav-label">{theme === 'dark' ? 'Mode Terang' : 'Mode Gelap'}</span>
        </button>

        {/* Collapse Toggle */}
        <button className="collapse-btn" onClick={onToggle}>
          <span className="nav-icon">{collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}</span>
          <span className="nav-label">Tutup Sidebar</span>
        </button>
      </div>
    </aside>
  );
}
