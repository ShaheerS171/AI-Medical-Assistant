import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Download, AlertCircle } from 'lucide-react';
import client from '../api/client';
import UploadZone from '../components/UploadZone';
import ReactMarkdown from 'react-markdown';

const stagger = { animate: { transition: { staggerChildren: 0.08 } } };
const child = { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 } };

export default function KidneyUltrasoundPage() {
    const [longFile, setLongFile] = useState(null);
    const [transFile, setTransFile] = useState(null);
    const [form, setForm] = useState({
        name: 'Jane Doe', id: 'PAT-KID-0001', age: 45, sex: 'Female',
        history: 'Flank pain and haematuria for 2 weeks. Suspected renal pathology for further evaluation.'
    });
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');

    const handleRun = async (e) => {
        e.preventDefault();
        if (!longFile || !transFile) {
            setError('Please upload both the longitudinal and transverse ultrasound images.');
            return;
        }
        setError(''); setLoading(true); setResults(null);
        try {
            const fd = new FormData();
            fd.append('longitudinal', longFile);
            fd.append('transverse', transFile);
            const { data } = await client.post('/predict/kidney-ultrasound', fd);
            setResults({ ...data, report: buildReport(data, form) });
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    const buildReport = (data, info) => {
        const { length_cm, width_cm, thickness_cm } = data;
        const vol = ((4 / 3) * Math.PI * (length_cm / 2) * (width_cm / 2) * (thickness_cm / 2)).toFixed(1);
        return `## RADIOLOGICAL REPORT — KIDNEY ULTRASOUND (B-MODE)

**Patient:** ${info.name}  |  **ID:** ${info.id}  |  **Age:** ${info.age}  |  **Sex:** ${info.sex}

**Clinical History:** ${info.history}

---

### MORPHOMETRIC MEASUREMENTS

| Dimension | Measurement |
|-----------|-------------|
| **Length** | ${length_cm.toFixed(2)} cm |
| **Width**  | ${width_cm.toFixed(2)} cm |
| **Thickness** | ${thickness_cm.toFixed(2)} cm |
| **Estimated Volume** | ~${vol} cm³ |

### REFERENCE RANGES (Adult)
- Normal kidney length: 9–12 cm
- Normal kidney width: 4–6 cm
- Normal kidney thickness: 3–5 cm

### FINDINGS

DeepLabV3+ segmentation model analysis of bilateral kidney morphometry:
- **Length:** ${length_cm.toFixed(2)} cm ${length_cm < 9 ? '⚠️ Below normal range' : length_cm > 12 ? '⚠️ Above normal range' : '✅ Within normal range'}
- **Width:** ${width_cm.toFixed(2)} cm ${width_cm < 4 ? '⚠️ Below normal range' : width_cm > 6 ? '⚠️ Above normal range' : '✅ Within normal range'}
- **Thickness:** ${thickness_cm.toFixed(2)} cm ${thickness_cm < 3 ? '⚠️ Below normal range' : thickness_cm > 5 ? '⚠️ Above normal range' : '✅ Within normal range'}

### IMPRESSION

Automated segmentation yielded morphometric measurements as documented above.
${length_cm < 9 || width_cm < 4 ? 'Measurements suggest possible renal atrophy or hypoplasia. Clinical correlation with renal function tests (eGFR, creatinine) recommended.' : 'Measurements are within acceptable physiologic range.'}

### DISCLAIMER

⚠️ This report is an **AI-generated decision-support draft** (DeepLabV3+ model). All measurements and findings require verification by a licensed sonographer or nephrologist before clinical use.`;
    };

    const downloadPDF = async () => {
        if (!results || !longFile || !transFile) return;
        try {
            const getBase64 = (file) => new Promise((resolve) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result.split(',')[1]);
            });

            const longB64 = await getBase64(longFile);
            const transB64 = await getBase64(transFile);

            const req = {
                patient_name: form.name,
                patient_id: form.id,
                patient_age: form.age,
                patient_sex: form.sex,
                patient_history: form.history,
                report_text: results.report,
                scan_type: "Kidney Ultrasound Segmentation",
                original_img_b64: longB64,
                overlay_img_b64: transB64,
                metrics: {
                    "Kidney Length": `${results.length_cm?.toFixed(2)} cm`,
                    "Kidney Width": `${results.width_cm?.toFixed(2)} cm`,
                    "Thickness": `${results.thickness_cm?.toFixed(2)} cm`
                }
            };

            const res = await client.post('/export/pdf', req, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `kidney_report_${form.id}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (err) {
            setError(err?.response?.data?.detail || 'PDF Export Failed');
        }
    };


    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <h1><Activity size={22} style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />Kidney Ultrasound Morphometry</h1>
                <p>DeepLabV3+ Segmentation · Length / Width / Thickness · LLM Draft Report</p>
            </div>

            {error && (
                <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: '#f87171', marginBottom: '1.25rem', display: 'flex', gap: 8, alignItems: 'center' }}>
                    <AlertCircle size={16} /> {error}
                </div>
            )}

            <form onSubmit={handleRun}>
                {/* Image uploads */}
                <div className="two-col" style={{ marginBottom: '1.25rem' }}>
                    <div className="card">
                        <div className="card-title">1. Longitudinal View (Length)</div>
                        <UploadZone
                            label="Upload longitudinal kidney ultrasound (PNG / JPG)"
                            onFile={setLongFile}
                            file={longFile}
                        />
                    </div>
                    <div className="card">
                        <div className="card-title">2. Transverse View (Width & Thickness)</div>
                        <UploadZone
                            label="Upload transverse kidney ultrasound (PNG / JPG)"
                            onFile={setTransFile}
                            file={transFile}
                        />
                    </div>
                </div>

                {/* Patient Form */}
                <div className="card" style={{ marginBottom: '1.25rem' }}>
                    <div className="card-title">3. Patient Intake Form</div>
                    <div className="two-col">
                        <div>
                            <div className="form-group">
                                <label className="form-label">Patient Full Name</label>
                                <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Patient ID</label>
                                <input className="form-input" value={form.id} onChange={e => setForm({ ...form, id: e.target.value })} />
                            </div>
                        </div>
                        <div>
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
                </div>

                <motion.button
                    className="btn btn-primary btn-full"
                    type="submit"
                    disabled={loading}
                    whileTap={{ scale: 0.98 }}
                    style={{ padding: '0.85rem' }}
                >
                    {loading ? '⚡ Running kidney segmentation...' : '🫘 Run Segmentation & Generate Report'}
                </motion.button>
            </form>

            <AnimatePresence>
                {loading && (
                    <motion.div className="spinner-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <div className="spinner" />
                        <p className="spinner-text">DeepLabV3+ segmentation & morphometric calculation in progress...</p>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {results && (
                    <motion.div className="results-section" variants={stagger} initial="initial" animate="animate">
                        <div className="section-divider" />
                        <motion.div variants={child} className="section-title">🫘 Segmentation Overlays</motion.div>

                        <motion.div variants={child} className="image-pair" style={{ marginBottom: '1.5rem' }}>
                            <div className="image-card">
                                {longFile && <img src={URL.createObjectURL(longFile)} alt="Longitudinal" />}
                                <div className="image-caption">Longitudinal View — Length Axis</div>
                            </div>
                            <div className="image-card">
                                {transFile && <img src={URL.createObjectURL(transFile)} alt="Transverse" />}
                                <div className="image-caption">Transverse View — Width & Thickness Axes</div>
                            </div>
                        </motion.div>

                        <motion.div variants={child} className="three-col" style={{ marginBottom: '1.5rem' }}>
                            {[
                                { label: 'Kidney Length', value: `${results.length_cm?.toFixed(2)} cm` },
                                { label: 'Kidney Width', value: `${results.width_cm?.toFixed(2)} cm` },
                                { label: 'Thickness', value: `${results.thickness_cm?.toFixed(2)} cm` },
                            ].map(({ label, value }) => (
                                <div className="metric-card" key={label}>
                                    <div className="metric-label">{label}</div>
                                    <div className="metric-value accent">{value}</div>
                                </div>
                            ))}
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
