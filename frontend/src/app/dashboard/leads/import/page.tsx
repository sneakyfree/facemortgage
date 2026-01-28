'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api/client';
import { Upload, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';

export default function LeadImportPage() {
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<{
        success: boolean;
        imported: number;
        failed: number;
        errors: string[];
    } | null>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            if (!selectedFile.name.endsWith('.csv')) {
                alert('Please select a CSV file');
                return;
            }
            setFile(selectedFile);
            setResult(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            const { data } = await apiClient.post('/leads/import', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setResult({
                success: true,
                imported: data.imported_count || 0,
                failed: data.failed_count || 0,
                errors: data.errors || [],
            });
        } catch (err: any) {
            setResult({
                success: false,
                imported: 0,
                failed: 0,
                errors: [err.response?.data?.detail || 'Upload failed'],
            });
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4">
            <div className="max-w-2xl mx-auto">
                <div className="mb-8">
                    <button
                        onClick={() => router.back()}
                        className="text-gray-600 hover:text-gray-900 flex items-center gap-2 mb-4"
                    >
                        ← Back to Leads
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900">Import Leads</h1>
                    <p className="mt-2 text-gray-600">
                        Upload a CSV file to import leads in bulk.
                    </p>
                </div>

                {/* CSV Format Guide */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8">
                    <h3 className="font-semibold text-blue-900 mb-2">CSV Format Requirements</h3>
                    <p className="text-sm text-blue-700 mb-3">
                        Your CSV file should include the following columns:
                    </p>
                    <div className="bg-white rounded-lg p-3 font-mono text-xs text-gray-700 overflow-x-auto">
                        contact_name,contact_email,contact_phone,loan_purpose,estimated_loan_amount
                    </div>
                    <p className="text-sm text-blue-600 mt-3">
                        <a href="/templates/leads_import_template.csv" className="underline hover:no-underline">
                            Download sample template
                        </a>
                    </p>
                </div>

                {/* Upload area */}
                <div className="bg-white rounded-xl border p-8 mb-6">
                    <div
                        onClick={() => fileInputRef.current?.click()}
                        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${file ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                            }`}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".csv"
                            onChange={handleFileSelect}
                            className="hidden"
                        />

                        {file ? (
                            <div className="flex items-center justify-center gap-3">
                                <FileText className="w-8 h-8 text-blue-600" />
                                <div className="text-left">
                                    <p className="font-medium text-gray-900">{file.name}</p>
                                    <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                                </div>
                                <button
                                    onClick={(e) => { e.stopPropagation(); setFile(null); setResult(null); }}
                                    className="ml-4 p-1 hover:bg-gray-100 rounded"
                                >
                                    <X className="w-5 h-5 text-gray-400" />
                                </button>
                            </div>
                        ) : (
                            <>
                                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                <p className="text-gray-900 font-medium mb-1">
                                    Click to upload or drag and drop
                                </p>
                                <p className="text-sm text-gray-500">CSV files only, max 5MB</p>
                            </>
                        )}
                    </div>

                    <button
                        onClick={handleUpload}
                        disabled={!file || uploading}
                        className="w-full mt-6 py-3 px-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {uploading ? 'Importing...' : 'Import Leads'}
                    </button>
                </div>

                {/* Result display */}
                {result && (
                    <div className={`rounded-xl p-6 ${result.success && result.failed === 0 ? 'bg-green-50 border border-green-200' :
                            result.success && result.failed > 0 ? 'bg-yellow-50 border border-yellow-200' :
                                'bg-red-50 border border-red-200'
                        }`}>
                        <div className="flex items-start gap-4">
                            {result.success && result.failed === 0 ? (
                                <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                            ) : (
                                <AlertCircle className={`w-6 h-6 flex-shrink-0 ${result.success ? 'text-yellow-600' : 'text-red-600'
                                    }`} />
                            )}
                            <div className="flex-1">
                                <h3 className={`font-semibold ${result.success && result.failed === 0 ? 'text-green-900' :
                                        result.success ? 'text-yellow-900' : 'text-red-900'
                                    }`}>
                                    {result.success && result.failed === 0 ? 'Import Successful!' :
                                        result.success ? 'Import Complete with Errors' : 'Import Failed'}
                                </h3>

                                {result.success && (
                                    <p className={`text-sm mt-1 ${result.failed > 0 ? 'text-yellow-700' : 'text-green-700'
                                        }`}>
                                        {result.imported} leads imported successfully
                                        {result.failed > 0 && `, ${result.failed} failed`}
                                    </p>
                                )}

                                {result.errors.length > 0 && (
                                    <div className="mt-3">
                                        <p className="text-sm font-medium text-gray-700 mb-1">Errors:</p>
                                        <ul className="text-sm text-gray-600 list-disc list-inside">
                                            {result.errors.slice(0, 5).map((error, i) => (
                                                <li key={i}>{error}</li>
                                            ))}
                                            {result.errors.length > 5 && (
                                                <li>...and {result.errors.length - 5} more</li>
                                            )}
                                        </ul>
                                    </div>
                                )}

                                {result.success && (
                                    <button
                                        onClick={() => router.push('/dashboard/leads')}
                                        className="mt-4 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 text-sm font-medium"
                                    >
                                        View Imported Leads
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
