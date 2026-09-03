import { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Brain, Bone, MessageSquare, Activity,
    ChevronRight, LogOut, Menu, X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
    { id: 'brain', label: 'Brain MRI', sub: 'Tumor Detection', icon: Brain },
    { id: 'knee', label: 'Knee X-Ray', sub: 'Osteoarthritis', icon: Bone },
    { id: 'chat', label: 'Medical Consultation', sub: 'Chat & Doctor Finder', icon: MessageSquare },
    { id: 'kidney', label: 'Kidney Ultrasound', sub: 'Morphometry', icon: Activity },
];

export default function Sidebar({ activePage, setActivePage }) {
    const { user, signOut } = useAuth();
    const [mobileOpen, setMobileOpen] = useState(false);

    return (
        <>
            {/* Sidebar */}
            <div className="sidebar">
                {/* Logo */}
                <div className="sidebar-logo">
                    <img src="/image.png" alt="Logo" className="sidebar-logo-icon" style={{ border: 'none', background: 'transparent', boxShadow: 'none' }} />
                    <div className="sidebar-logo-text">
                        <h2>AI Medical</h2>
                        <p>Clinical Support System</p>
                    </div>
                </div>

                <div className="sidebar-label">Diagnostic Modules</div>

                {/* Nav Items */}
                <nav className="sidebar-nav">
                    {NAV_ITEMS.map(({ id, label, sub, icon: Icon }) => (
                        <motion.button
                            key={id}
                            className={`nav-item ${activePage === id ? 'active' : ''}`}
                            onClick={() => { setActivePage(id); setMobileOpen(false); }}
                            whileTap={{ scale: 0.97 }}
                            style={{ background: 'none', border: activePage === id ? '1px solid var(--border)' : '1px solid transparent', width: '100%', textAlign: 'left', cursor: 'pointer' }}
                        >
                            <Icon size={17} className="nav-icon" />
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ fontSize: '0.82rem', fontWeight: 600, lineHeight: 1.2 }}>{label}</div>
                                <div style={{ fontSize: '0.67rem', color: 'var(--text-dim)', marginTop: 1 }}>{sub}</div>
                            </div>
                            {activePage === id && <ChevronRight size={14} />}
                        </motion.button>
                    ))}
                </nav>

                {/* Footer */}
                <div className="sidebar-footer">
                    <div className="sidebar-disclaimer">
                        💡 <strong>Clinical Support:</strong> AI outputs require review by a licensed healthcare professional.
                    </div>

                    {user && (
                        <div className="user-card">
                            <div className="user-avatar">
                                {(user.email || 'U').charAt(0).toUpperCase()}
                            </div>
                            <div className="user-info">
                                <div className="user-email">{user.email}</div>
                            </div>
                            <button className="btn-signout" onClick={signOut} title="Sign out">
                                <LogOut size={14} />
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Mobile hamburger — only shown via CSS on small screens */}
            <motion.button
                onClick={() => setMobileOpen(o => !o)}
                whileTap={{ scale: 0.9 }}
                className="mobile-menu-btn"
                style={{
                    position: 'fixed', top: 12, left: 12, zIndex: 200,
                    background: 'var(--bg-card)', border: '1px solid var(--border-dim)',
                    borderRadius: 8, padding: 6, cursor: 'pointer', color: 'var(--text-primary)',
                    display: 'none'
                }}
            >
                {mobileOpen ? <X size={18} /> : <Menu size={18} />}
            </motion.button>
        </>
    );
}
