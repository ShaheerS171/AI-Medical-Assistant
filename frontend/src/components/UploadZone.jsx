import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, X, FileImage } from 'lucide-react';

export default function UploadZone({ label, accept = '.jpg,.jpeg,.png', onFile, file }) {
    const [dragging, setDragging] = useState(false);

    const onDrop = useCallback((e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer?.files?.[0];
        if (f) onFile(f);
    }, [onFile]);

    const preview = file ? URL.createObjectURL(file) : null;

    return (
        <div>
            {!file ? (
                <div
                    className={`upload-zone ${dragging ? 'drag-over' : ''}`}
                    onDragOver={e => { e.preventDefault(); setDragging(true); }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={onDrop}
                >
                    <input
                        type="file"
                        accept={accept}
                        onChange={e => e.target.files?.[0] && onFile(e.target.files[0])}
                    />
                    <div className="upload-icon"><FileImage size={32} /></div>
                    <p>{label || 'Drop image here or click to browse'}</p>
                    <small>JPG, PNG, JPEG supported</small>
                </div>
            ) : (
                <AnimatePresence>
                    <motion.div
                        className="upload-preview"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        <img src={preview} alt="preview" />
                        <div className="upload-filename">
                            <FileImage size={13} />
                            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {file.name}
                            </span>
                            <button
                                onClick={() => onFile(null)}
                                style={{ background: 'none', border: 'none', color: 'var(--red)', cursor: 'pointer', display: 'flex' }}
                            >
                                <X size={14} />
                            </button>
                        </div>
                    </motion.div>
                </AnimatePresence>
            )}
        </div>
    );
}
