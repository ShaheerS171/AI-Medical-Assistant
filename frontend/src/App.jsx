import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import BrainMRIPage from './pages/BrainMRIPage';
import KneeXRayPage from './pages/KneeXRayPage';
import ChatbotPage from './pages/ChatbotPage';
import KidneyUltrasoundPage from './pages/KidneyUltrasoundPage';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const PAGE_MAP = {
  brain: BrainMRIPage,
  knee: KneeXRayPage,
  chat: ChatbotPage,
  kidney: KidneyUltrasoundPage,
};

function AppInner() {
  const { user, loading } = useAuth();
  const [activePage, setActivePage] = useState('brain');

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: '1rem'
      }}>
        <div className="spinner" style={{ width: 52, height: 52 }} />
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Initialising AI Medical Assistant...</p>
      </div>
    );
  }

  if (!user) return <LoginPage />;

  const ActivePage = PAGE_MAP[activePage] || BrainMRIPage;

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={activePage}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            <ActivePage />
          </motion.div>
        </AnimatePresence>
      </main>

      <ToastContainer
        position="bottom-right"
        theme="dark"
        toastStyle={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-dim)',
          color: 'var(--text-primary)'
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
