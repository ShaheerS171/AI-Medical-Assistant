import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, MapPin, Send, Paperclip, Trash2, Building2, AlertCircle } from 'lucide-react';
import client from '../api/client';
import ReactMarkdown from 'react-markdown';

const stagger = { animate: { transition: { staggerChildren: 0.06 } } };
const child = { initial: { opacity: 0, x: -10 }, animate: { opacity: 1, x: 0 } };

function UrgencyBadge({ urgency }) {
    const map = {
        high: { cls: 'badge-red', label: '🔴 HIGH URGENCY' },
        medium: { cls: 'badge-yellow', label: '🟡 MEDIUM URGENCY' },
        low: { cls: 'badge-green', label: '🟢 LOW URGENCY' },
    };
    const { cls, label } = map[urgency?.toLowerCase()] || { cls: 'badge-gray', label: `⚪ ${(urgency || '').toUpperCase()}` };
    return <span className={`badge ${cls}`}>{label}</span>;
}

function CitationsPanel({ citations }) {
    const [open, setOpen] = useState(false);
    if (!citations?.length) return null;
    return (
        <div>
            <button className="citations-btn" onClick={() => setOpen(o => !o)}>
                📚 {open ? 'Hide' : 'View'} {citations.length} source(s)
            </button>
            <AnimatePresence>
                {open && (
                    <motion.div
                        className="citations-panel"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                    >
                        {citations.map((c, i) => (
                            <div className="citation-card" key={i}>
                                <strong>[{i + 1}]</strong> {c.authors}{c.year ? ` (${c.year})` : ''}. {' '}
                                <a href={c.url} target="_blank" rel="noopener noreferrer">{c.title}</a>
                                {c.journal ? ` — ${c.journal}` : ''}.{' '}
                                <small>PMID: {c.pmid}</small>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default function ChatbotPage() {
    const [activeTab, setActiveTab] = useState('chat');
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [attachFile, setAttachFile] = useState(null);
    const [loading, setLoading] = useState(false);

    // Doctor finder state
    const [location, setLocation] = useState('');
    const [specialty, setSpecialty] = useState('');
    const [radius, setRadius] = useState(15);
    const [doctors, setDoctors] = useState([]);
    const [docLoading, setDocLoading] = useState(false);
    const [docError, setDocError] = useState('');

    const messagesEnd = useRef(null);

    useEffect(() => {
        messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async () => {
        const text = input.trim();
        if (!text && !attachFile) return;

        const userMsg = { role: 'user', content: text || '(attached file)', file: attachFile?.name };
        setMessages(m => [...m, userMsg]);
        setInput(''); setAttachFile(null);
        setLoading(true);

        try {
            const fd = new FormData();
            fd.append('symptoms', text);
            if (attachFile) fd.append('file', attachFile);

            const { data } = await client.post('/consult', fd);

            const urgency = data.urgency || 'unknown';
            const advice = data.advice || '';
            const specialist = data.recommended_specialist;
            const disclaimer = data.disclaimer || '';
            const citations = data.citations || [];

            let md = `${advice}`;
            if (specialist) md += `\n\n🩺 **Recommended Specialist:** ${specialist}`;
            md += `\n\n---\n⚠️ *${disclaimer}*`;

            setMessages(m => [...m, { role: 'assistant', content: md, urgency, citations }]);
        } catch (err) {
            setMessages(m => [...m, { role: 'assistant', content: `❌ Consultation failed: ${err.response?.data?.detail || err.message}`, urgency: 'unknown', citations: [] }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKey = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    };

    const findDoctors = async () => {
        if (!location) { setDocError('Please enter a location.'); return; }
        setDocError(''); setDocLoading(true); setDoctors([]);
        try {
            const { data } = await client.get('/find-doctors', { params: { location, specialty, radius_km: radius } });
            setDoctors(data.results || []);
        } catch (err) {
            setDocError(err.response?.data?.detail || err.message || 'Facility lookup failed.');
        } finally {
            setDocLoading(false);
        }
    };

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <h1><MessageSquare size={22} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />Medical Consultation & Doctor Locator</h1>
                <p>RAG-grounded symptom triage powered by Mistral AI + live PubMed citations</p>
            </div>

            {/* Tabs */}
            <div className="tab-list">
                <button className={`tab-item ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
                    💬 AI Medical Chat
                </button>
                <button className={`tab-item ${activeTab === 'find' ? 'active' : ''}`} onClick={() => setActiveTab('find')}>
                    📍 Find Nearby Specialist
                </button>
            </div>

            {/* ── Chat Tab ── */}
            {activeTab === 'chat' && (
                <div className="chat-container">
                    <div className="chat-messages">
                        {messages.length === 0 && (
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}
                            >
                                <MessageSquare size={40} style={{ margin: '0 auto 0.75rem', color: 'var(--accent)', display: 'block' }} />
                                <p style={{ fontSize: '0.9rem' }}>Describe your symptoms to begin your consultation</p>
                                <p style={{ fontSize: '0.75rem', marginTop: 4 }}>e.g. "I have had a headache and fever for 3 days"</p>
                            </motion.div>
                        )}

                        <AnimatePresence initial={false}>
                            {messages.map((msg, i) => (
                                <motion.div
                                    key={i}
                                    className={`chat-bubble ${msg.role}`}
                                    initial={{ opacity: 0, y: 12 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.25 }}
                                >
                                    <div className={`bubble-avatar ${msg.role === 'user' ? 'user' : 'ai'}`}>
                                        {msg.role === 'user' ? 'U' : '🤖'}
                                    </div>
                                    <div>
                                        {msg.role === 'assistant' && msg.urgency && (
                                            <div style={{ marginBottom: 6 }}><UrgencyBadge urgency={msg.urgency} /></div>
                                        )}
                                        <div className="bubble-content">
                                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                                            {msg.file && (
                                                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>
                                                    📎 {msg.file}
                                                </div>
                                            )}
                                        </div>
                                        {msg.citations && <CitationsPanel citations={msg.citations} />}
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>

                        {loading && (
                            <motion.div className="chat-bubble" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                <div className="bubble-avatar ai">🤖</div>
                                <div className="bubble-content" style={{ display: 'flex', gap: 6, alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                                    <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                                    Consulting medical knowledge base & PubMed...
                                </div>
                            </motion.div>
                        )}
                        <div ref={messagesEnd} />
                    </div>

                    {/* Input area */}
                    <div className="chat-input-area">
                        {attachFile && (
                            <div style={{ fontSize: '0.73rem', color: 'var(--accent)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Paperclip size={12} /> {attachFile.name}
                                <button onClick={() => setAttachFile(null)} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', marginLeft: 4, display: 'flex' }}>
                                    ✕
                                </button>
                            </div>
                        )}
                        <div className="chat-input-wrapper">
                            <label className="chat-attach-label">
                                <Paperclip size={14} />
                                <input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={e => setAttachFile(e.target.files?.[0] || null)} />
                            </label>
                            <textarea
                                className="chat-textarea"
                                rows={1}
                                placeholder="Describe your symptoms (e.g. headache, fever for 3 days)..."
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyDown={handleKey}
                            />
                            <motion.button
                                whileTap={{ scale: 0.9 }}
                                onClick={sendMessage}
                                disabled={loading}
                                style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent2))', border: 'none', borderRadius: 8, width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}
                            >
                                <Send size={15} color="#fff" />
                            </motion.button>
                        </div>
                        {messages.length > 0 && (
                            <button
                                className="btn btn-danger"
                                style={{ marginTop: '0.5rem', fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                                onClick={() => setMessages([])}
                            >
                                <Trash2 size={13} /> Clear Chat
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* ── Doctor Finder Tab ── */}
            {activeTab === 'find' && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <div className="card" style={{ marginBottom: '1.5rem' }}>
                        <div className="card-title"><MapPin size={14} /> Search Healthcare Facilities</div>

                        <div className="form-row" style={{ marginBottom: '1rem' }}>
                            <div className="form-group" style={{ gridColumn: 'span 1' }}>
                                <label className="form-label">Location / City</label>
                                <input className="form-input" placeholder="e.g. Rawalpindi, Pakistan" value={location} onChange={e => setLocation(e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Specialist Search Term</label>
                                <input className="form-input" placeholder="e.g. neurologist, orthopedist" value={specialty} onChange={e => setSpecialty(e.target.value)} />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label">Search Radius: <strong style={{ color: 'var(--accent)' }}>{radius} km</strong></label>
                            <input
                                type="range" min={5} max={100} value={radius}
                                onChange={e => setRadius(+e.target.value)}
                                style={{ width: '100%', accentColor: 'var(--accent)' }}
                            />
                        </div>

                        {docError && (
                            <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '0.6rem 0.875rem', fontSize: '0.8rem', color: '#f87171', marginBottom: '1rem', display: 'flex', gap: 8, alignItems: 'center' }}>
                                <AlertCircle size={14} /> {docError}
                            </div>
                        )}

                        <button className="btn btn-primary" onClick={findDoctors} disabled={docLoading}>
                            {docLoading ? '🔍 Searching...' : '📍 Locate Facilities'}
                        </button>
                    </div>

                    {docLoading && (
                        <div className="spinner-overlay"><div className="spinner" /><p className="spinner-text">Locating facilities within {radius} km...</p></div>
                    )}

                    <AnimatePresence>
                        {doctors.length > 0 && (
                            <motion.div variants={stagger} initial="initial" animate="animate">
                                <div className="section-title" style={{ marginBottom: '1rem' }}>
                                    🏥 Found {doctors.length} Facilities
                                </div>
                                {doctors.map((doc, i) => (
                                    <motion.div key={i} variants={child} className="doctor-card" style={{ marginBottom: '0.75rem' }}>
                                        <div className="doctor-icon"><Building2 size={20} /></div>
                                        <div className="doctor-info">
                                            <h4>{doc.name}</h4>
                                            {doc.address && <p>📍 {doc.address}</p>}
                                            {doc.distance_km != null && <p>📏 {doc.distance_km} km away</p>}
                                        </div>
                                    </motion.div>
                                ))}
                            </motion.div>
                        )}
                        {!docLoading && doctors.length === 0 && location && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)', fontSize: '0.875rem' }}>
                                No matching healthcare facilities found within {radius} km.
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            )}
        </motion.div>
    );
}
