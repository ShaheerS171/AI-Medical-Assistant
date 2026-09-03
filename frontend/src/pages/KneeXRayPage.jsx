import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bone, Download, AlertCircle } from 'lucide-react';
import client from '../api/client';
import UploadZone from '../components/UploadZone';
import ReactMarkdown from 'react-markdown';

const stagger = { animate: { transition: { staggerChildren: 0.08 } } };
const child = { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 } };

const KL_LABELS = {
    0: 'Normal — No articular changes',
    1: 'Doubtful — Possible osteophytes',
    2: 'Mild — Definite osteophytes',
    3: 'Moderate — Moderate joint space loss',
    4: 'Severe — Large osteophytes, complete loss',
};

export default function KneeXRayPage() {
    const [file, setFile] = useState(null);
    const [form, setForm] = useState({ name: 'John Smith', id: 'PAT-XRAY-4920', age: 64, sex: 'Male', history: 'Worsening right knee stiffness during weight-bearing activities over 6 months.' });
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');

    const handleRun = async (e) => {
        e.preventDefault();
        if (!file) { setError('Please upload a Knee X-Ray scan first.'); return; }
        setError(''); setLoading(true); setResults(null);
        try {
            const fd = new FormData();
            fd.append('file', file);
            const { data } = await client.post('/predict/knee-xray', fd);
            setResults({ ...data, report: buildReport(data, form) });
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    const buildReport = (data, info) => {
        const conf = (data.confidence * 100).toFixed(1);
        const gradeDesc = KL_LABELS[data.predicted_grade] || 'Unknown';
        return `## RADIOLOGICAL REPORT — KNEE X-RAY

**Patient:** ${info.name}  |  **ID:** ${info.id}  |  **Age:** ${info.age}  |  **Sex:** ${info.sex}

**Clinical History:** ${info.history}

---

### FINDINGS

**Kellgren-Lawrence Grade:** KL Grade ${data.predicted_grade}
**Grade Description:** ${gradeDesc}
**Model Confidence:** ${conf}%
**Calibration Status:** ${data.calibrated ? 'Calibrated (Temperature Scaling Active)' : 'Uncalibrated'}

### IMPRESSION

The knee radiograph demonstrates **KL Grade ${data.predicted_grade}** osteoarthritis findings.
${gradeDesc}. Model confidence is ${conf}%.

${data.predicted_grade >= 3 ? '⚠️ Moderate to severe osteoarthritis detected. Orthopedic consultation recommended.' : '✅ Mild osteoarthritis findings. Conservative management and follow-up advised.'}

### DISCLAIMER

⚠️ This is an **AI-generated decision-support draft**. Formal clinical interpretation must be performed by a licensed radiologist or orthopedic surgeon.`;
    };

    const downloadPDF = async () => {
        if (!results || !file) return;
        try {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = async () => {
                try {
                    const req = {
                        patient_name: form.name,
                        patient_id: form.id,
                        patient_age: form.age,
                        patient_sex: form.sex,
                        patient_history: form.history,
                        report_text: results.report,
                        scan_type: "Knee X-Ray Scan",
                        original_img_b64: reader.result.split(',')[1] || reader.result,
                        overlay_img_b64: results.gradcam_b64 || "",
                        metrics: {
                            "Severity Score": `KL Grade ${results.predicted_grade}`,
                            "Confidence": `${(results.confidence * 100).toFixed(1)}%`,
                            "Calibration": results.calibrated ? 'Calibrated' : 'Uncalibrated'
                        }
                    };

                    const res = await client.post('/export/pdf', req, { responseType: 'blob' });
                    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `knee_xray_report_${form.id}.pdf`);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                } catch (err) {
                    setError(err.response?.data?.detail || 'PDF Generation failed.');
                }
            };
        } catch (err) {
            setError('Could not process image for PDF.');
        }
    };

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <h1><Bone size={22} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />Knee Radiograph (X-Ray) Analysis</h1>
                <p>Kellgren-Lawrence Ordinal Grading · Grad-CAM Heatmap · Draft Clinical Report</p>
            </div>

            {error && (
                <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: '#f87171', marginBottom: '1.25rem', display: 'flex', gap: 8, alignItems: 'center' }}>
                    <AlertCircle size={16} /> {error}
                </div>
            )}

            <form onSubmit={handleRun}>
                <div className="two-col">
                    <div className="card">
                        <div className="card-title">Upload Knee X-Ray</div>
                        <UploadZone label="Drop Knee X-Ray scan here (JPG / PNG)" onFile={setFile} file={file} />
                    </div>

                    <div className="card">
                        <div className="card-title">Patient Intake Form</div>
                        <div className="form-group">
                            <label className="form-label">Patient Full Name</label>
                            <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Patient ID</label>
                            <input className="form-input" value={form.id} onChange={e => setForm({ ...form, id: e.target.value })} />
                        </div>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Age</label>
                                <input className="form-input" type="number" min={1} max={120} value={form.age} onChange={e => setForm({ ...form, age: +e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Biological Sex</label>
                                <select className="form-select form-input" value={form.sex} onChange={e => setForm({ ...form, sex: e.target.value })}>
                                    <option>Male</option><option>Female</option><option>Other</option>
                                </select>
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Clinical Complaints & History</label>
                            <textarea className="form-textarea form-input" value={form.history} onChange={e => setForm({ ...form, history: e.target.value })} />
                        </div>
                    </div>
                </div>

                <motion.button
                    className="btn btn-primary btn-full"
                    type="submit"
                    disabled={loading}
                    whileTap={{ scale: 0.98 }}
                    style={{ marginTop: '1.25rem', padding: '0.85rem' }}
                >
                    {loading ? '⚡ Grading osteoarthritis severity...' : '🦴 Run Analysis & Generate Report'}
                </motion.button>
            </form>

            <AnimatePresence>
                {loading && (
                    <motion.div className="spinner-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <div className="spinner" />
                        <p className="spinner-text">Running KL-grade classification & Grad-CAM overlay...</p>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {results && (
                    <motion.div className="results-section" variants={stagger} initial="initial" animate="animate">
                        <div className="section-divider" />
                        <motion.div variants={child} className="section-title">🦴 Vision Model Findings</motion.div>

                        <motion.div variants={child} className="image-pair" style={{ marginBottom: '1.5rem' }}>
                            <div className="image-card">
                                {file && <img src={URL.createObjectURL(file)} alt="Original X-Ray" />}
                                <div className="image-caption">Original X-Ray Input</div>
                            </div>
                            <div className="image-card">
                                {results.gradcam_b64 ? (
                                    <>
                                        <img src={`data:image/png;base64,${results.gradcam_b64}`} alt="Grad-CAM Cartilage Overlay" />
                                        <div className="image-caption">Grad-CAM Cartilage Overlay</div>
                                    </>
                                ) : (
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--accent-dim)', minHeight: 200, height: '100%' }}>
                                        <div style={{ textAlign: 'center', padding: '1rem' }}>
                                            <Bone size={36} style={{ color: 'var(--accent)', marginBottom: 8 }} />
                                            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Overlay unavailable</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>

                        <motion.div variants={child} className="three-col" style={{ marginBottom: '1.5rem' }}>
                            {[
                                { label: 'Severity Score', value: `KL Grade ${results.predicted_grade}` },
                                { label: 'Grade Confidence', value: `${(results.confidence * 100).toFixed(1)}%` },
                                { label: 'Calibration', value: results.calibrated ? 'Calibrated ✓' : 'Uncalibrated' },
                            ].map(({ label, value }) => (
                                <div className="metric-card" key={label}>
                                    <div className="metric-label">{label}</div>
                                    <div className="metric-value accent">{value}</div>
                                </div>
                            ))}
                        </motion.div>

                        {/* KL Grade description */}
                        <motion.div variants={child}>
                            <div className="card" style={{ marginBottom: '1rem', borderColor: 'var(--border)' }}>
                                <div className="card-title">Grade Interpretation</div>
                                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                                    {KL_LABELS[results.predicted_grade] || 'Grade description unavailable'}
                                </p>
                            </div>
                        </motion.div>

                        <div className="section-divider" />
                        <motion.div variants={child} className="section-title">📄 Radiological Report Preview</motion.div>
                        <motion.div variants={child} className="report-box">
                            <ReactMarkdown>{results.report}</ReactMarkdown>
                        </motion.div>

                        <motion.div variants={child} style={{ marginTop: '1rem' }}>
                            <button className="btn btn-secondary btn-full" onClick={downloadPDF} type="button">
                                <Download size={16} /> Download PDF Report
                            </button>
                        </motion.div>

                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
