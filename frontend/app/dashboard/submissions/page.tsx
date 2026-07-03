"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Clock, CheckCircle, AlertTriangle, MoreVertical, Trash2, Download } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { formatBytes } from "@/lib/utils";

export default function SubmissionsPage() {
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const fetchSubmissions = async () => {
    try {
      const response = await apiClient.get("/submissions");
      setSubmissions(response.data.submissions || []);
    } catch (error) {
      toast.error("Failed to load submissions");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this submission?")) return;
    try {
      await apiClient.delete(`/submissions/${id}`);
      setSubmissions(submissions.filter(s => s.id !== id));
      toast.success("Submission deleted");
    } catch (error) {
      toast.error("Failed to delete submission");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "complete":
        return <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><CheckCircle className="w-3 h-3" /> Complete</span>;
      case "processing":
        return <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"><Clock className="w-3 h-3 animate-spin" /> Processing</span>;
      case "failed":
        return <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20"><AlertTriangle className="w-3 h-3" /> Failed</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">Pending</span>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <header className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-outfit font-bold text-white mb-2">My Submissions</h1>
          <p className="text-slate-400">History of all your uploaded documents and compliance reports.</p>
        </div>
        <Link 
          href="/dashboard/upload"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors shadow-[0_0_15px_rgba(79,70,229,0.3)]"
        >
          New Upload
        </Link>
      </header>

      <div className="glass-panel rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 flex justify-center">
            <Clock className="w-8 h-8 animate-spin text-slate-500" />
          </div>
        ) : submissions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/50 border-b border-slate-800">
                  <th className="py-4 px-6 text-xs font-medium text-slate-400 uppercase tracking-wider">Document</th>
                  <th className="py-4 px-6 text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="py-4 px-6 text-xs font-medium text-slate-400 uppercase tracking-wider">Date</th>
                  <th className="py-4 px-6 text-xs font-medium text-slate-400 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {submissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center shrink-0">
                          <FileText className="w-5 h-5 text-slate-400" />
                        </div>
                        <div>
                          <div className="font-medium text-white mb-0.5">{sub.original_filename}</div>
                          <div className="text-xs text-slate-500">{formatBytes(sub.file_size_bytes)}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6">{getStatusBadge(sub.status)}</td>
                    <td className="py-4 px-6 text-sm text-slate-400">
                      {formatDistanceToNow(new Date(sub.created_at), { addSuffix: true })}
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center justify-end gap-3">
                        <Link 
                          href={`/dashboard/reports/${sub.id}`}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-md text-sm font-medium transition-colors"
                        >
                          View Report
                        </Link>
                        <button 
                          onClick={() => handleDelete(sub.id)}
                          className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-md transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-16 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-slate-500" />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">No submissions found</h3>
            <p className="text-slate-400">You haven't uploaded any documents yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
