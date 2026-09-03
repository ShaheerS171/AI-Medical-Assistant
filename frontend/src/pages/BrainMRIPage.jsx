import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Radio, Download, AlertCircle, Upload } from 'lucide-react';
import client from '../api/client';
import UploadZone from '../components/UploadZone';
import ReactMarkdown from 'react-markdown';

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } },
};

const stagger = {
    animate: { transition: { staggerChildren: 0.08 } }
};
const child = {
    initial: { opacity: 0, y: 14 },
    animate: { opacity: 1, y: 0 }
};

export default function BrainMRIPage() {
    const [file, setFile] = useState(null);
    const [overlay, setOverlay] = useState('Grad-CAM Heatmap');
    const [form, setForm] = useState({ name: 'Jane Doe', id: 'PAT-MRI-8841', age: 52, sex: 'Female', history: 'Acute onset morning headaches associated with nausea and focal weakness.' });
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');

    const handleRun = async (e) => {
        e.preventDefault();
        if (!file) { setError('Please upload a Brain MRI scan first.'); return; }
        setError(''); setLoading(true); setResults(null);
        try {
            const fd = new FormData();
            fd.append('file', file);
            const { data } = await client.post('/predict/brain-mri', fd);

            // generate a basic report from returned data
            const report = buildReport(data, form);
            setResults({ ...data, report });
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    const buildReport = (data, info) => {
        const conf = (data.confidence * 100).toFixed(1);
        const area = data.tumor_area_mm2 ? `${data.tumor_area_mm2.toFixed(1)} mm²` : 'N/A';
        return `## RADIOLOGICAL REPORT — BRAIN MRI

**Patient:** ${info.name}  |  **ID:** ${info.id}  |  **Age:** ${info.age}  |  **Sex:** ${info.sex}

**Clinical History:** ${info.history}

---

### FINDINGS

**Classification:** ${data.predicted_class?.toUpperCase()}
**Model Confidence:** ${conf}%
**Estimated Lesion Area:** ${area}

### IMPRESSION

AI model has classified the MRI scan as **${data.predicted_class}** with ${conf}% confidence.
${data.tumor_area_mm2 ? `An estimated lesion area of ${area} was detected on the ROI.` : 'No measurable lesion area detected.'}

### DISCLAIMER

⚠️ This report is an **AI-generated decision-support draft** and must be reviewed by a licensed radiologist or neurologist before clinical use. It does not constitute a formal medical diagnosis.`;
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
                        scan_type: "Brain MRI Scan",
                        original_img_b64: reader.result.split(',')[1] || reader.result,
                        overlay_img_b64: (overlay === 'Grad-CAM Heatmap' ? results.gradcam_b64 : results.overlay_b64) || "",
                        metrics: {
                            "Predicted Category": results.predicted_class?.toUpperCase(),
                            "Confidence Level": `${(results.confidence * 100).toFixed(1)}%`,
                            "Estimated Lesion Area": results.tumor_area_mm2 ? `${results.tumor_area_mm2.toFixed(1)} mm²` : 'N/A'
                        }
                    };

                    const res = await client.post('/export/pdf', req, { responseType: 'blob' });
                    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `brain_mri_report_${form.id}.pdf`);
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


    const confidencePct = results ? (results.confidence * 100).toFixed(1) : null;
    const areaDisp = results?.tumor_area_mm2 ? `${results.tumor_area_mm2.toFixed(1)} mm²` : 'N/A';

    return (
        <motion.div variants={pageVariants} initial="initial" animate="animate">
            {/* Header */}
            <div className="page-header">
                <h1><Brain size={22} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />Brain MRI Scan Analysis</h1>
                <p>Classification · YOLO Segmentation Area Measurement · LLM Draft Report</p>
            </div>

            {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: '#f87171', marginBottom: '1.25rem', display: 'flex', gap: 8, alignItems: 'center' }}>
                    <AlertCircle size={16} /> {error}
                </motion.div>
            )}

            <form onSubmit={handleRun}>
                <div className="two-col">
                    {/* Upload */}
                    <div className="card">
                        <div className="card-title"><Upload size={14} /> Upload Imaging Scan</div>
                        <UploadZone label="Drop Brain MRI scan here (JPG / PNG)" onFile={setFile} file={file} />

                        <div className="form-group" style={{ marginTop: '1rem' }}>
                            <label className="form-label">Explainability Overlay</label>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                {['Grad-CAM Heatmap', 'YOLO Bounding Box'].map(v => (
                                    <button
                                        key={v} type="button"
                                        className={`btn ${overlay === v ? 'btn-primary' : 'btn-secondary'}`}
                                        style={{ fontSize: '0.78rem', padding: '0.4rem 0.9rem' }}
                                        onClick={() => setOverlay(v)}
                                    >{v}</button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Patient Form */}
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
                                    <option>Female</option><option>Male</option><option>Other</option>
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
                    {loading ? '⚡ Processing Vision Models & Generating Report...' : '🔬 Run Analysis & Generate Report'}
                </motion.button>
            </form>

            {/* Loading */}
            <AnimatePresence>
                {loading && (
                    <motion.div className="spinner-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <div className="spinner" />
                        <p className="spinner-text">Running tumor classification & GradCAM analysis...</p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Results */}
            <AnimatePresence>
                {results && (
                    <motion.div
                        className="results-section"
                        variants={stagger} initial="initial" animate="animate"
                    >
                        <div className="section-divider" />

                        <motion.div variants={child} className="section-title">
                            🧬 Vision Model Findings
                        </motion.div>

                        {/* Image pair */}
                        <motion.div variants={child} className="image-pair" style={{ marginBottom: '1.5rem' }}>
                            <div className="image-card">
                                {file && <img src={URL.createObjectURL(file)} alt="Original MRI" />}
                                <div className="image-caption">Original MRI Input</div>
                            </div>
                            <div className="image-card">
                                {overlay === 'Grad-CAM Heatmap' && results.gradcam_b64 ? (
                                    <>
                                        <img src={`data:image/png;base64,${results.gradcam_b64}`} alt="Grad-CAM Heatmap" />
                                        <div className="image-caption">Grad-CAM Activation Heatmap</div>
                                    </>
                                ) : overlay === 'YOLO Bounding Box' && results.overlay_b64 ? (
                                    <>
                                        <img src={`data:image/png;base64,${results.overlay_b64}`} alt="YOLO Detection Overlay" />
                                        <div className="image-caption">YOLO Tumor Detection Overlay</div>
                                    </>
                                ) : (
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--accent-dim)', minHeight: 200, flex: 1 }}>
                                        <div style={{ textAlign: 'center', padding: '1rem' }}>
                                            <Radio size={36} style={{ color: 'var(--accent)', marginBottom: 8 }} />
                                            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                                {overlay === 'YOLO Bounding Box' ? 'No tumor region detected' : 'Overlay unavailable'}
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>

                        {/* Metrics */}
                        <motion.div variants={child} className="three-col" style={{ marginBottom: '1.5rem' }}>
                            {[
                                { label: 'Predicted Category', value: results.predicted_class?.toUpperCase() },
                                { label: 'Confidence Level', value: `${confidencePct}%` },
                                { label: 'Estimated Lesion Area', value: areaDisp },
                            ].map(({ label, value }) => (
                                <div className="metric-card" key={label}>
                                    <div className="metric-label">{label}</div>
                                    <div className="metric-value accent">{value}</div>
                                </div>
                            ))}
                        </motion.div>

                        {/* Report */}
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
