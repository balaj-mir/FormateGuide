"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { motion } from "framer-motion";
import { UploadCloud, FileText, X, ShieldCheck, Loader2, AlertCircle, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import { formatBytes } from "@/lib/utils";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [rulesets, setRulesets] = useState<any[]>([]);
  const [selectedRuleset, setSelectedRuleset] = useState("");
  const [uploading, setUploading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchRulesets = async () => {
      try {
        const response = await apiClient.get("/rulesets/prebuilt");
        setRulesets(response.data.rulesets || []);
      } catch (error) {
        toast.error("Failed to load rulesets");
      }
    };
    fetchRulesets();
  }, []);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const selected = acceptedFiles[0];
    if (selected) {
      if (!selected.name.endsWith('.docx')) {
        toast.error("Only .docx files are supported");
        return;
      }
      setFile(selected);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleUpload = async () => {
    if (!file) return toast.error("Please select a file first");
    if (!selectedRuleset) return toast.error("Please select a ruleset");

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("ruleset_id", selectedRuleset);

    try {
      const response = await apiClient.post("/submissions/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      
      toast.success("Document uploaded successfully");
      router.push(`/dashboard/reports/${response.data.id}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-outfit font-bold text-white mb-2">Upload Document</h1>
        <p className="text-slate-400">Select your Word document and the formatting guidelines to check against.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* File Upload Area */}
          <div className="glass-panel rounded-2xl overflow-hidden p-6">
            <h2 className="text-lg font-semibold text-white mb-4">1. Select Document (.docx)</h2>
            
            {!file ? (
              <div 
                {...getRootProps()} 
                className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                  isDragActive 
                    ? "border-indigo-500 bg-indigo-500/10" 
                    : "border-slate-700 hover:border-indigo-400/50 hover:bg-slate-800/50"
                }`}
              >
                <input {...getInputProps()} />
                <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
                  <UploadCloud className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-medium text-white mb-1">Drag & drop your document here</h3>
                <p className="text-sm text-slate-400 mb-4">or click to browse from your computer</p>
                <div className="text-xs text-slate-500 flex items-center justify-center gap-4">
                  <span>Word (.docx) only</span>
                  <span>•</span>
                  <span>Max 10MB</span>
                </div>
              </div>
            ) : (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="border border-indigo-500/30 bg-indigo-500/5 rounded-xl p-6 relative"
              >
                <button 
                  onClick={() => setFile(null)}
                  className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
                    <FileText className="w-6 h-6 text-white" />
                  </div>
                  <div className="overflow-hidden">
                    <h3 className="text-lg font-medium text-white truncate" title={file.name}>{file.name}</h3>
                    <p className="text-sm text-slate-400">{formatBytes(file.size)}</p>
                  </div>
                </div>
                <div className="mt-6 flex items-center gap-2 text-sm text-emerald-400 bg-emerald-400/10 px-3 py-2 rounded-lg border border-emerald-400/20">
                  <ShieldCheck className="w-4 h-4" />
                  <span>File is ready for processing</span>
                </div>
              </motion.div>
            )}
          </div>

          {/* Ruleset Selection */}
          <div className="glass-panel rounded-2xl overflow-hidden p-6">
            <h2 className="text-lg font-semibold text-white mb-4">2. Select Guidelines</h2>
            
            <div className="grid gap-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {rulesets.map((rs) => (
                <label 
                  key={rs.id}
                  className={`flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedRuleset === rs.id 
                      ? "border-indigo-500 bg-indigo-500/10" 
                      : "border-slate-700 bg-slate-800/50 hover:border-slate-600"
                  }`}
                >
                  <div className="pt-0.5">
                    <input 
                      type="radio" 
                      name="ruleset" 
                      value={rs.id}
                      checked={selectedRuleset === rs.id}
                      onChange={(e) => setSelectedRuleset(e.target.value)}
                      className="w-4 h-4 text-indigo-600 bg-slate-900 border-slate-600 focus:ring-indigo-500 focus:ring-offset-slate-900"
                    />
                  </div>
                  <div>
                    <h4 className="font-medium text-white mb-1">{rs.name}</h4>
                    <p className="text-xs text-slate-400">{rs.description}</p>
                    <div className="flex gap-3 mt-2 text-[10px] uppercase font-bold tracking-wider text-slate-500">
                      <span>v{rs.version}</span>
                      <span>•</span>
                      <span>{rs.institution_id || "Global"}</span>
                    </div>
                  </div>
                </label>
              ))}
              {rulesets.length === 0 && (
                <div className="text-center p-6 text-slate-500 flex flex-col items-center">
                  <Loader2 className="w-6 h-6 animate-spin mb-2" />
                  <span>Loading rulesets...</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Panel */}
        <div className="lg:col-span-1">
          <div className="glass-panel rounded-2xl p-6 sticky top-24">
            <h3 className="font-semibold text-white mb-4">Summary</h3>
            
            <div className="space-y-4 mb-6 text-sm">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Document</span>
                <span className="text-white font-medium max-w-[150px] truncate" title={file?.name}>
                  {file ? file.name : "None selected"}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Ruleset</span>
                <span className="text-white font-medium">
                  {selectedRuleset ? "Selected" : "Required"}
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400">Cost</span>
                <span className="text-emerald-400 font-medium">1 Check</span>
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || !selectedRuleset || uploading}
              className={`w-full py-3 px-4 rounded-xl font-medium flex items-center justify-center gap-2 transition-all ${
                !file || !selectedRuleset || uploading
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_20px_rgba(79,70,229,0.4)]"
              }`}
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Start Analysis
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>

            <div className="mt-4 flex items-start gap-2 text-xs text-slate-500">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <p>Your document will be encrypted and processed securely. We do not store your intellectual property.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
