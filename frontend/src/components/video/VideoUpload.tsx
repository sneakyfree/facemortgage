'use client';

import { useState, useRef, useCallback } from 'react';
import { Upload, X, Check, AlertCircle, Video } from 'lucide-react';
import { apiClient } from '@/lib/api/client';

interface VideoUploadProps {
    onUploadComplete?: (videoUrl: string) => void;
    maxSizeMB?: number;
    acceptedFormats?: string[];
}

export default function VideoUpload({
    onUploadComplete,
    maxSizeMB = 100,
    acceptedFormats = ['video/mp4', 'video/webm', 'video/quicktime'],
}: VideoUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const validateFile = (file: File): string | null => {
        if (!acceptedFormats.includes(file.type)) {
            return `Invalid format. Accepted: ${acceptedFormats.map(f => f.split('/')[1]).join(', ')}`;
        }
        if (file.size > maxSizeMB * 1024 * 1024) {
            return `File too large. Maximum size: ${maxSizeMB}MB`;
        }
        return null;
    };

    const handleFile = (file: File) => {
        setError(null);
        setSuccess(false);

        const validationError = validateFile(file);
        if (validationError) {
            setError(validationError);
            return;
        }

        setFile(file);
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);

        if (e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    }, []);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setProgress(0);
        setError(null);

        const formData = new FormData();
        formData.append('video', file);

        try {
            // Simulate progress for demo (real implementation would use XMLHttpRequest or fetch with progress)
            const progressInterval = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);

            const response = await apiClient.post('/videos/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            clearInterval(progressInterval);
            setProgress(100);
            setSuccess(true);

            if (onUploadComplete && response.data.video_url) {
                onUploadComplete(response.data.video_url);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Upload failed. Please try again.');
            setProgress(0);
        } finally {
            setUploading(false);
        }
    };

    const reset = () => {
        setFile(null);
        setProgress(0);
        setError(null);
        setSuccess(false);
        if (inputRef.current) {
            inputRef.current.value = '';
        }
    };

    return (
        <div className="w-full max-w-xl mx-auto">
            {/* Drop Zone */}
            <div
                onDrop={handleDrop}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${dragActive
                        ? 'border-blue-500 bg-blue-50'
                        : error
                            ? 'border-red-300 bg-red-50'
                            : success
                                ? 'border-green-300 bg-green-50'
                                : 'border-gray-300 hover:border-gray-400'
                    }`}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept={acceptedFormats.join(',')}
                    onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    disabled={uploading}
                />

                {success ? (
                    <div className="py-4">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Check className="w-8 h-8 text-green-600" />
                        </div>
                        <p className="text-lg font-medium text-green-800 mb-2">Upload Complete!</p>
                        <button
                            onClick={reset}
                            className="text-sm text-green-600 hover:underline"
                        >
                            Upload another video
                        </button>
                    </div>
                ) : file ? (
                    <div className="py-4">
                        <div className="flex items-center justify-center gap-3 mb-4">
                            <Video className="w-8 h-8 text-blue-600" />
                            <div className="text-left">
                                <p className="font-medium text-gray-900 truncate max-w-[200px]">{file.name}</p>
                                <p className="text-sm text-gray-500">
                                    {(file.size / 1024 / 1024).toFixed(1)} MB
                                </p>
                            </div>
                            <button
                                onClick={(e) => { e.preventDefault(); reset(); }}
                                className="p-1 hover:bg-gray-100 rounded"
                            >
                                <X className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>

                        {/* Progress Bar */}
                        {uploading && (
                            <div className="mb-4">
                                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-blue-600 transition-all duration-300"
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                                <p className="text-sm text-gray-500 mt-2">{progress}% uploaded</p>
                            </div>
                        )}

                        <button
                            onClick={handleUpload}
                            disabled={uploading}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
                        >
                            {uploading ? 'Uploading...' : 'Upload Video'}
                        </button>
                    </div>
                ) : (
                    <div className="py-4">
                        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-lg font-medium text-gray-900 mb-1">
                            Drag and drop your video here
                        </p>
                        <p className="text-sm text-gray-500 mb-4">
                            or click to browse
                        </p>
                        <p className="text-xs text-gray-400">
                            Accepted formats: MP4, WebM, MOV • Max size: {maxSizeMB}MB
                        </p>
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="mt-4 flex items-center gap-2 justify-center text-red-600">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm">{error}</span>
                    </div>
                )}
            </div>
        </div>
    );
}
