import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
    const { signIn, signUp } = useAuth();
    const [tab, setTab] = useState('login');   // 'login' | 'register'
    const [email, setEmail] = useState('');
    const [pass, setPass] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [info, setInfo] = useState('');

    const handle = async (e) => {
        e.preventDefault();
        setError(''); setInfo('');
        setBusy(true);
        try {
            if (tab === 'login') {
                await signIn(email, pass);
            } else {
                await signUp(email, pass);
                setInfo('Account created! Check your inbox to confirm your email, then sign in.');
                setTab('login');
            }
        } catch (err) {
            setError(err.message || 'Authentication failed. Please try again.');
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="auth-wall">
            <motion.div
                className="auth-card"
                initial={{ opacity: 0, y: 30, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            >
                {/* Logo */}
                <div className="auth-logo">
                    <div className="icon-wrap">🏥</div>
                    <h1>AI Medical Assistant</h1>
                    <p>Clinical Diagnostic Support System</p>
                </div>

                {/* Tabs */}
                <div className="auth-tabs">
                    <button className={`auth-tab ${tab === 'login' ? 'active' : ''}`} onClick={() => setTab('login')}>
                        Sign In
                    </button>
                    <button className={`auth-tab ${tab === 'register' ? 'active' : ''}`} onClick={() => setTab('register')}>
                        Register
                    </button>
                </div>

                {error && <div className="auth-error">⚠ {error}</div>}
                {info && (
                    <div style={{
                        background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)',
                        borderRadius: 8, padding: '0.65rem 0.875rem', fontSize: '0.8rem',
                        color: '#34d399', marginBottom: '1rem'
                    }}>
                        ✓ {info}
                    </div>
                )}

                <form onSubmit={handle}>
                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <input
                            className="form-input"
                            type="email"
                            placeholder="doctor@clinic.com"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            className="form-input"
                            type="password"
                            placeholder="••••••••"
                            value={pass}
                            onChange={e => setPass(e.target.value)}
                            required
                        />
                    </div>

                    <motion.button
                        className="btn btn-primary btn-full"
                        type="submit"
                        disabled={busy}
                        whileTap={{ scale: 0.97 }}
                        style={{ marginTop: '0.5rem' }}
                    >
                        {busy ? '⏳ Please wait...' : tab === 'login' ? '→ Sign In' : '→ Create Account'}
                    </motion.button>
                </form>

                <p style={{ textAlign: 'center', fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '1.25rem' }}>
                    🔒 Secured with Supabase Authentication
                </p>
            </motion.div>
        </div>
    );
}
