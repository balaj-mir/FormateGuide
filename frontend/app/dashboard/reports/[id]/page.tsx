"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle, AlertTriangle, Info, Download, FileEdit, Clock, ChevronDown, ChevronUp, Loader2, PlayCircle } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

export default function ReportPage() {
  const { id } = useParams();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("pending");
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    // Poll for status if not complete
    let pollInterval: NodeJS.Timeout;

    const fetchReport = async () => {
      try {
        const response = await apiClient.get(`/reports/${id}`);
        setReport(response.data);
        setStatus("complete");
        setLoading(false);
      } catch (error: any) {
        if (error.response?.status === 404) {
          // Check submission status instead
          try {
            const subRes = await apiClient.get(`/submissions/${id}`);
            setStatus(subRes.data.status);
            if (subRes.data.status === "failed") {
              setLoading(false);
            }
          } catch (e) {
            setLoading(false);
          }
        } else {
          setLoading(false);
        }
      }
    };

    fetchReport();

    if (status === "pending" || status === "processing") {
      pollInterval = setInterval(fetchReport, 3000);
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [id, status]);

  const toggleGroup = (groupName: string) => {
    setExpandedGroups(prev => ({ ...prev, [groupName]: !prev[groupName] }));
  };

  const handleApplyCorrections = async () => {
    setApplying(true);
    try {
      await apiClient.post(`/corrections/${id}/apply-all-critical`);
      toast.success("Critical corrections applied successfully");
      // Reload report to get new URL
      const response = await apiClient.get(`/reports/${id}`);
      setReport(response.data);
    } catch (error) {
      toast.error("Failed to apply corrections");
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="h-[80vh] flex flex-col items-center justify-center">
        <Loader2 className="w-12 h-12 text-indigo-500 animate-spin mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Analyzing Document...</h2>
        <p className="text-slate-400">Parsing XML, checking margins, fonts, and citations.</p>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="h-[80vh] flex flex-col items-center justify-center max-w-md mx-auto text-center">
        <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-6 border border-red-500/20">
          <AlertTriangle className="w-8 h-8 text-red-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Processing Failed</h2>
        <p className="text-slate-400 mb-6">We encountered an error while analyzing your document. It might be corrupted or in an unsupported format.</p>
        <button 
          onClick={() => window.location.href = '/dashboard/upload'}
          className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
        >
          Try Another Document
        </button>
      </div>
    );
  }

  if (!report) return null;

  // Group violations by severity
  const critical = report.violations.filter((v: any) => v.severity === "critical");
  const warnings = report.violations.filter((v: any) => v.severity === "warning");
  const suggestions = report.violations.filter((v: any) => v.severity === "suggestion");

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-amber-400";
    return "text-red-400";
  };

  return (
    <div className="max-w-6xl mx-auto pb-12">
      {/* Header Area */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-outfit font-bold text-white">Compliance Report</h1>
            <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full text-xs font-bold uppercase tracking-wider">
              Score: {report.compliance_score}%
            </span>
          </div>
          <p className="text-slate-400 text-sm">
            Analyzed {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {report.report_pdf_url && (
            <a 
              href={report.report_pdf_url} 
              target="_blank" 
              rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-medium transition-colors text-sm"
            >
              <Download className="w-4 h-4" />
              Report PDF
            </a>
          )}
          {report.corrected_doc_url ? (
            <a 
              href={report.corrected_doc_url} 
              target="_blank" 
              rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)] text-sm"
            >
              <Download className="w-4 h-4" />
              Download Corrected
            </a>
          ) : (
            <button 
              onClick={handleApplyCorrections}
              disabled={applying || critical.length === 0}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors text-sm ${
                critical.length > 0
                  ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_15px_rgba(79,70,229,0.3)]"
                  : "bg-slate-800 text-slate-500 cursor-not-allowed"
              }`}
            >
              {applying ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileEdit className="w-4 h-4" />}
              Auto-Fix Critical ({critical.length})
            </button>
          )}
        </div>
      </div>

      {/* Top Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="glass-panel p-4 rounded-xl flex items-center gap-4 border-l-4 border-l-emerald-500">
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white leading-none mb-1">{report.total_elements_checked - report.total_violations}</div>
            <div className="text-xs text-slate-400 font-medium">Passed Checks</div>
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl flex items-center gap-4 border-l-4 border-l-red-500">
          <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white leading-none mb-1">{report.critical_count}</div>
            <div className="text-xs text-slate-400 font-medium">Critical Errors</div>
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl flex items-center gap-4 border-l-4 border-l-amber-500">
          <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center shrink-0">
            <Info className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white leading-none mb-1">{report.warning_count}</div>
            <div className="text-xs text-slate-400 font-medium">Warnings</div>
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl flex items-center gap-4 border-l-4 border-l-indigo-500">
          <div className="w-10 h-10 rounded-full bg-indigo-500/10 flex items-center justify-center shrink-0">
            <Clock className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white leading-none mb-1">{report.estimated_fix_time_minutes}m</div>
            <div className="text-xs text-slate-400 font-medium">Est. Fix Time</div>
          </div>
        </div>
      </div>

      {/* Violations List */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold font-outfit text-white mb-2">Detailed Findings</h2>
        
        {report.violations.length === 0 ? (
          <div className="glass-panel p-12 text-center rounded-2xl">
            <CheckCircle className="w-16 h-16 text-emerald-400 mx-auto mb-4 opacity-50" />
            <h3 className="text-xl font-medium text-white mb-2">Perfect Score!</h3>
            <p className="text-slate-400">Your document perfectly matches the formatting guidelines. No corrections needed.</p>
          </div>
        ) : (
          <>
            <ViolationGroup 
              title="Critical Violations" 
              icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
              violations={critical}
              color="red"
              expanded={expandedGroups["critical"] !== false}
              onToggle={() => toggleGroup("critical")}
            />
            <ViolationGroup 
              title="Warnings" 
              icon={<Info className="w-5 h-5 text-amber-400" />}
              violations={warnings}
              color="amber"
              expanded={expandedGroups["warnings"]}
              onToggle={() => toggleGroup("warnings")}
            />
            <ViolationGroup 
              title="Suggestions" 
              icon={<PlayCircle className="w-5 h-5 text-indigo-400" />}
              violations={suggestions}
              color="indigo"
              expanded={expandedGroups["suggestions"]}
              onToggle={() => toggleGroup("suggestions")}
            />
          </>
        )}
      </div>
    </div>
  );
}

function ViolationGroup({ title, icon, violations, color, expanded, onToggle }: any) {
  if (!violations || violations.length === 0) return null;

  return (
    <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800">
      <div 
        className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          {icon}
          <h3 className="font-semibold text-white">{title}</h3>
          <span className={`px-2 py-0.5 rounded-full text-xs font-bold bg-${color}-500/10 text-${color}-400`}>
            {violations.length}
          </span>
        </div>
        {expanded ? <ChevronUp className="w-5 h-5 text-slate-500" /> : <ChevronDown className="w-5 h-5 text-slate-500" />}
      </div>
      
      {expanded && (
        <div className="border-t border-slate-800 divide-y divide-slate-800/50">
          {violations.map((v: any) => (
            <div key={v.id} className="p-6 hover:bg-slate-900/30 transition-colors">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-white">{v.rule_name}</span>
                    {v.is_auto_fixable && (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-emerald-500/10 text-emerald-400 rounded border border-emerald-500/20">
                        Auto-Fixable
                      </span>
                    )}
                    {v.fix_applied && (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-indigo-500/10 text-indigo-400 rounded border border-indigo-500/20">
                        Fixed
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-slate-400 mb-3">
                    Found in <span className="text-slate-300 font-medium">{v.element_type}</span> {v.page_number ? `on page ${v.page_number}` : ''}
                    {v.affected_count > 1 && ` (and ${v.affected_count - 1} other places)`}
                  </div>
                  
                  {v.context_excerpt && (
                    <div className="bg-slate-900/80 rounded-lg p-3 text-xs text-slate-500 font-mono border border-slate-800 break-all mb-3">
                      "...{v.context_excerpt}..."
                    </div>
                  )}
                  
                  <div className="flex flex-wrap items-center gap-4 text-sm mt-2">
                    <div className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
                      <span className="text-slate-500 mr-2">Found:</span>
                      <span className="text-red-400 line-through">{v.current_value}</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-600" />
                    <div className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
                      <span className="text-slate-500 mr-2">Required:</span>
                      <span className="text-emerald-400 font-medium">{v.expected_value}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
