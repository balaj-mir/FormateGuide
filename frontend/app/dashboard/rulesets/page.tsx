"use client";

import { useEffect, useState } from "react";
import { BookOpen, Star, Download, Search, Building2, CheckCircle } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { useAuthStore } from "@/lib/store";

export default function RulesetsPage() {
  const [rulesets, setRulesets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const { user } = useAuthStore();

  useEffect(() => {
    fetchRulesets();
  }, []);

  const fetchRulesets = async () => {
    try {
      const response = await apiClient.get("/rulesets");
      setRulesets(response.data.rulesets || []);
    } catch (error) {
      toast.error("Failed to load rulesets");
    } finally {
      setLoading(false);
    }
  };

  const filteredRulesets = rulesets.filter(rs => 
    rs.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    (rs.description && rs.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="max-w-6xl mx-auto">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <h1 className="text-3xl font-outfit font-bold text-white mb-2">Rulesets Library</h1>
          <p className="text-slate-400">Browse university formatting guidelines and academic standards.</p>
        </div>
        
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input 
            type="text" 
            placeholder="Search guidelines..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full md:w-64 pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
          />
        </div>
      </header>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="glass-panel h-48 rounded-2xl"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRulesets.map((rs) => (
            <div key={rs.id} className="glass-panel p-6 rounded-2xl flex flex-col h-full hover:-translate-y-1 transition-transform duration-300">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 shrink-0">
                  <BookOpen className="w-6 h-6 text-indigo-400" />
                </div>
                {rs.is_verified && (
                  <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" />
                    Verified
                  </span>
                )}
              </div>
              
              <h3 className="text-lg font-bold text-white mb-2 line-clamp-1" title={rs.name}>{rs.name}</h3>
              <p className="text-sm text-slate-400 mb-6 flex-1 line-clamp-3" title={rs.description}>
                {rs.description || "No description provided."}
              </p>
              
              <div className="mt-auto pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500 font-medium">
                <div className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4" />
                  <span>{rs.institution_id || "Global Standard"}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1"><Download className="w-3 h-3" /> {rs.download_count}</span>
                  <span className="px-1.5 py-0.5 bg-slate-800 rounded">v{rs.version}</span>
                </div>
              </div>
            </div>
          ))}

          {filteredRulesets.length === 0 && (
            <div className="col-span-full py-12 text-center text-slate-400">
              No rulesets found matching "{searchTerm}".
            </div>
          )}
        </div>
      )}
    </div>
  );
}
