import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScanHeart, Download, AlertCircle } from 'lucide-react';
import client from '../api/client';
import UploadZone from '../components/UploadZone';
import ReactMarkdown from 'react-markdown';

const stagger = { animate: { transition: { staggerChildren: 0.08 } } };
const child = { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 } };

export default function TuberculosisPage() {
    const [file, setFile] = useState(null);
    const [form, setForm] = useState({
        name: 'Jane Doe',
        id: 'PAT-TB-1042',
        age: 38,
        sex: 'Female',
        history: 'Persistent productive cough for 4 weeks, nocturnal diaphoresis, low-grade pyrexia, and unintentional 5kg weight loss.'
    });
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');

    const handleRun = async (e) => {
        e.preventDefault();
        if (!file) {
            setError('Please upload a Chest X-Ray scan first.');
            return;
        }
        setError('');
        setLoading(true);
        setResults(null);

        try {
            const fd = new FormData();
            fd.append('file', file);
            fd.append('age', form.age);
            fd.append('sex', form.sex);

            const { data } = await client.post('/predict/tb-xray', fd);

            // Generate report using AI Explainability Engine (DeepSeek / LLM)
            let report = '';
            try {
                const repRes = await client.post('/generate/report', {
                    modality: 'tb-xray',
                    patient_info: form,
                    prediction_data: data
                });
                report = repRes.data.report;
            } catch (llmErr) {
                console.warn('AI LLM report generation failed, using structured template fallback:', llmErr);
                report = buildReport(data, form);
            }

            setResults({ ...data, report });
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    const buildReport = (data, info) => {
        const conf = (data.confidence * 100).toFixed(1);
        const isTB = data.predicted_class === 'Tuberculosis';
        const normProb = data.probabilities?.Normal ? (data.probabilities.Normal * 100).toFixed(1) : 'N/A';
        const tbProb = data.probabilities?.Tuberculosis ? (data.probabilities.Tuberculosis * 100).toFixed(1) : 'N/A';

        return `## RADIOLOGICAL REPORT — CHEST X-RAY (TB SCREENING)

**Patient:** ${info.name}  |  **ID:** ${info.id}  |  **Age:** ${info.age}  |  **Sex:** ${info.sex}

**Clinical History:** ${info.history}

---

### FINDINGS

**Classification:** ${data.predicted_class?.toUpperCase()}
**Model Confidence:** ${conf}%
**Class Probabilities:** Normal: ${normProb}% | Tuberculosis: ${tbProb}%

### TECHNIQUE & VISUAL OBSERVATIONS
Posteroanterior (PA) chest projection reviewed. DenseNet121 neural architecture with Grad-CAM activation mapping evaluated for focal parenchymal abnormalities.

### DETAILED RADIOLOGICAL FINDINGS
${isTB 
    ? 'The automated thoracic analysis identifies focal parenchymal opacities, apical consolidation, and attention patterns consistent with active pulmonary tuberculosis infection.' 
    : 'The chest radiograph demonstrates clear lung fields bilaterally without focal consolidation, cavitation, or hilar enlargement indicative of active tuberculosis.'}

### IMPRESSION & RECOMMENDATIONS

**Impression:** ${isTB ? 'Radiological features suspicious for Pulmonary Tuberculosis.' : 'No definite radiographical signs of active Pulmonary Tuberculosis.'}
Confidence: ${conf}%.

${isTB 
    ? '⚠️ Urgent acid-fast bacilli (AFB) sputum smear & culture, GeneXpert MTB/RIF assay, thoracic CT, airborne precautions, and pulmonary/infectious disease consultation recommended.' 
    : '✅ Routine clinical follow-up advised. Re-evaluate if respiratory symptoms persist.'}

### DISCLAIMER

⚠️ This is an **AI-generated decision-support draft**. Formal clinical interpretation and diagnosis must be verified by a certified radiologist or pulmonologist.`;
    };

    const downloadPDF = async () => {
        if (!results || !file) return;
        try {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = async () => {
                try {
                    const normProb = results.probabilities?.Normal ? `${(results.probabilities.Normal * 100).toFixed(1)}%` : 'N/A';
                    const tbProb = results.probabilities?.Tuberculosis ? `${(results.probabilities.Tuberculosis * 100).toFixed(1)}%` : 'N/A';

                    const req = {
                        patient_name: form.name,
                        patient_id: form.id,
                        patient_age: Number(form.age),
                        patient_sex: form.sex,
                        patient_history: form.history,
                        report_text: results.report,
                        scan_type: "Chest X-Ray (Tuberculosis Screening)",
                        original_img_b64: reader.result.split(',')[1] || reader.result,
                        overlay_img_b64: results.gradcam_b64 || "",
                        metrics: {
                            "Diagnosis": results.predicted_class,
                            "Confidence": `${(results.confidence * 100).toFixed(1)}%`,
                            "Probabilities": `TB: ${tbProb} | Normal: ${normProb}`
                        }
                    };

                    const res = await client.post('/export/pdf', req, { responseType: 'blob' });
                    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `tb_xray_report_${form.id}.pdf`);
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

    const isTB = results?.predicted_class === 'Tuberculosis';

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <h1>
                    <ScanHeart size={22} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle', color: 'var(--accent)' }} />
                    Chest X-Ray — Tuberculosis Screening
                </h1>
                <p>DenseNet121 Multimodal Classifier · Grad-CAM Saliency Overlay · AI Radiological Report</p>
            </div>

            {error && (
                <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: '#f87171', marginBottom: '1.25rem', display: 'flex', gap: 8, alignItems: 'center' }}>
                    <AlertCircle size={16} /> {error}
                </div>
            )}

            <form onSubmit={handleRun}>
                <div className="two-col">
                    <div className="card">
                        <div className="card-title">Upload Chest X-Ray</div>
                        <UploadZone label="Drop Chest X-Ray image here (JPG / PNG)" onFile={setFile} file={file} />
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
                                    <option value="Female">Female</option>
                                    <option value="Male">Male</option>
                                    <option value="Other">Other / Unknown</option>
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
                    {loading ? '⚡ Analyzing Chest X-Ray...' : '🫁 Run Analysis & Generate Report'}
                </motion.button>
            </form>

            <AnimatePresence>
                {loading && (
                    <motion.div className="spinner-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <div className="spinner" />
                        <p className="spinner-text">Running DenseNet121 inference & Grad-CAM overlay...</p>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {results && (
                    <motion.div className="results-section" variants={stagger} initial="initial" animate="animate">
                        <div className="section-divider" />
                        <motion.div variants={child} className="section-title">🫁 Vision Model Findings</motion.div>

                        <motion.div variants={child} className="image-pair" style={{ marginBottom: '1.5rem' }}>
                            <div className="image-card">
                                {file && <img src={URL.createObjectURL(file)} alt="Original Chest X-Ray" />}
                                <div className="image-caption">Original Chest X-Ray Input</div>
                            </div>
                            <div className="image-card">
                                {results.gradcam_b64 ? (
                                    <>
                                        <img src={`data:image/png;base64,${results.gradcam_b64}`} alt="Grad-CAM Activation Overlay" />
                                        <div className="image-caption">Grad-CAM Saliency Heatmap</div>
                                    </>
                                ) : (
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--accent-dim)', minHeight: 200, height: '100%' }}>
                                        <div style={{ textAlign: 'center', padding: '1rem' }}>
                                            <ScanHeart size={36} style={{ color: 'var(--accent)', marginBottom: 8 }} />
                                            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Overlay unavailable</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>

                        <motion.div variants={child} className="three-col" style={{ marginBottom: '1.5rem' }}>
                            {[
                                { 
                                    label: 'Diagnosis', 
                                    value: results.predicted_class, 
                                    color: isTB ? '#ef4444' : '#10b981' 
                                },
                                { 
                                    label: 'Confidence', 
                                    value: `${(results.confidence * 100).toFixed(1)}%`, 
                                    color: 'var(--accent)' 
                                },
                                { 
                                    label: 'TB Probability', 
                                    value: results.probabilities?.Tuberculosis ? `${(results.probabilities.Tuberculosis * 100).toFixed(1)}%` : 'N/A', 
                                    color: isTB ? '#ef4444' : 'var(--text-primary)' 
                                },
                            ].map(({ label, value, color }) => (
                                <div className="metric-card" key={label}>
                                    <div className="metric-label">{label}</div>
                                    <div className="metric-value" style={{ color }}>{value}</div>
                                </div>
                            ))}
                        </motion.div>

                        {/* Probability breakdown card */}
                        <motion.div variants={child}>
                            <div className="card" style={{ marginBottom: '1rem', borderColor: 'var(--border)' }}>
                                <div className="card-title">Class Probabilities</div>
                                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginTop: 8 }}>
                                    <div>
                                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Normal: </span>
                                        <strong style={{ fontSize: '0.95rem' }}>
                                            {results.probabilities?.Normal ? `${(results.probabilities.Normal * 100).toFixed(1)}%` : '0%'}
                                        </strong>
                                    </div>
                                    <div>
                                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Tuberculosis: </span>
                                        <strong style={{ fontSize: '0.95rem', color: isTB ? '#ef4444' : 'inherit' }}>
                                            {results.probabilities?.Tuberculosis ? `${(results.probabilities.Tuberculosis * 100).toFixed(1)}%` : '0%'}
                                        </strong>
                                    </div>
                                </div>
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
