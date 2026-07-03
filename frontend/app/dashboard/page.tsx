"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { FileText, ArrowRight, Clock, CheckCircle, AlertTriangle, UploadCloud } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { apiClient } from "@/lib/api-client";
import { formatDistanceToNow } from "date-fns";

export default function DashboardOverview() {
  const { user } = useAuthStore();
  const [recentSubmissions, setRecentSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await apiClient.get("/submissions?limit=3");
        setRecentSubmissions(response.data.submissions || []);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

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
    <div className="max-w-5xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-outfit font-bold text-white mb-2">Welcome back, {user?.full_name?.split(' ')[0] || 'User'}</h1>
        <p className="text-slate-400">Here's what's happening with your documents today.</p>
      </header>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-6 rounded-2xl relative overflow-hidden group cursor-pointer"
          onClick={() => window.location.href = '/dashboard/upload'}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10 flex items-start justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center mb-4 border border-indigo-500/20">
                <UploadCloud className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">New Upload</h3>
              <p className="text-sm text-slate-400">Check a new document against your university guidelines.</p>
            </div>
            <ArrowRight className="w-5 h-5 text-indigo-400 transform group-hover:translate-x-1 transition-transform" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel p-6 rounded-2xl relative overflow-hidden group cursor-pointer"
          onClick={() => window.location.href = '/dashboard/rulesets'}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10 flex items-start justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center mb-4 border border-cyan-500/20">
                <FileText className="w-6 h-6 text-cyan-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">Browse Rulesets</h3>
              <p className="text-sm text-slate-400">Find the right formatting guidelines for your next paper.</p>
            </div>
            <ArrowRight className="w-5 h-5 text-cyan-400 transform group-hover:translate-x-1 transition-transform" />
          </div>
        </motion.div>
      </div>

      {/* Recent Activity */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold font-outfit text-white">Recent Submissions</h2>
          <Link href="/dashboard/submissions" className="text-sm text-indigo-400 hover:text-indigo-300 font-medium">
            View All
          </Link>
        </div>

        <div className="glass-panel rounded-2xl overflow-hidden">
          {loading ? (
            <div className="p-8 flex justify-center">
              <Clock className="w-6 h-6 animate-spin text-slate-500" />
            </div>
          ) : recentSubmissions.length > 0 ? (
            <div className="divide-y divide-slate-800/50">
              {recentSubmissions.map((sub: any) => (
                <div key={sub.id} className="p-4 md:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-800/30 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5 text-slate-400" />
                    </div>
                    <div>
                      <h4 className="font-medium text-white mb-1 truncate max-w-[200px] md:max-w-xs" title={sub.original_filename}>
                        {sub.original_filename}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-slate-400">
                        <span>{formatDistanceToNow(new Date(sub.created_at), { addSuffix: true })}</span>
                        <span>•</span>
                        <span>{Math.round(sub.file_size_bytes / 1024)} KB</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between md:justify-end gap-6 w-full md:w-auto pl-14 md:pl-0">
                    {getStatusBadge(sub.status)}
                    <Link 
                      href={`/dashboard/reports/${sub.id}`}
                      className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm font-medium text-white transition-colors"
                    >
                      View Report
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-slate-500" />
              </div>
              <h3 className="text-lg font-medium text-white mb-2">No submissions yet</h3>
              <p className="text-slate-400 mb-6">Upload your first document to see the magic happen.</p>
              <Link 
                href="/dashboard/upload"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors"
              >
                <UploadCloud className="w-4 h-4" />
                Upload Document
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
