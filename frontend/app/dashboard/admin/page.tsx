"use client";

import { useEffect, useState } from "react";
import { Users, FileText, Activity, ShieldAlert, BarChart3, Clock, ArrowUpRight } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/lib/store";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

export default function AdminDashboard() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [recentUsers, setRecentUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Only fetch if admin
    if (user?.role !== "institutional_admin" && user?.role !== "super_admin") {
      setLoading(false);
      return;
    }

    const fetchAdminData = async () => {
      try {
        const [statsRes, usersRes] = await Promise.all([
          apiClient.get("/admin/analytics"),
          apiClient.get("/admin/users?limit=5")
        ]);
        setStats(statsRes.data);
        setRecentUsers(usersRes.data.users || []);
      } catch (error) {
        toast.error("Failed to load admin data");
      } finally {
        setLoading(false);
      }
    };

    fetchAdminData();
  }, [user]);

  if (user?.role !== "institutional_admin" && user?.role !== "super_admin") {
    return (
      <div className="h-[80vh] flex flex-col items-center justify-center text-center max-w-md mx-auto">
        <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-6 border border-red-500/20">
          <ShieldAlert className="w-8 h-8 text-red-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Access Denied</h2>
        <p className="text-slate-400">You do not have the required administrative privileges to view this page.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Clock className="w-8 h-8 animate-spin text-slate-500" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-outfit font-bold text-white mb-2">Institution Admin</h1>
        <p className="text-slate-400">Manage your university's users, rulesets, and view platform analytics.</p>
      </header>

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <StatCard 
          title="Total Submissions" 
          value={stats?.total_submissions || 0} 
          icon={<FileText className="w-5 h-5 text-indigo-400" />}
          trend="+12%"
          color="indigo"
        />
        <StatCard 
          title="Active Students" 
          value={stats?.active_users || 0} 
          icon={<Users className="w-5 h-5 text-cyan-400" />}
          trend="+5%"
          color="cyan"
        />
        <StatCard 
          title="Avg. Compliance" 
          value={`${stats?.avg_compliance_score || 0}%`} 
          icon={<Activity className="w-5 h-5 text-emerald-400" />}
          trend="+2.4%"
          color="emerald"
        />
        <StatCard 
          title="Published Rulesets" 
          value={stats?.published_rulesets || 0} 
          icon={<BookOpen className="w-5 h-5 text-amber-400" />}
          trend="0%"
          color="amber"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Users Table */}
        <div className="lg:col-span-2 glass-panel rounded-2xl overflow-hidden p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-white">Recent Users</h2>
            <button className="text-sm font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              View All <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-800 text-xs font-medium text-slate-500 uppercase tracking-wider">
                  <th className="pb-3 pr-4">User</th>
                  <th className="pb-3 px-4">Role</th>
                  <th className="pb-3 px-4 text-center">Checks Used</th>
                  <th className="pb-3 pl-4 text-right">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {recentUsers.map((u) => (
                  <tr key={u.id}>
                    <td className="py-4 pr-4">
                      <div className="font-medium text-white mb-0.5">{u.full_name || "Unknown"}</div>
                      <div className="text-xs text-slate-400">{u.email}</div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="px-2 py-1 rounded bg-slate-800 text-xs text-slate-300 font-medium capitalize">
                        {u.role.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-center text-sm font-medium text-white">
                      {u.monthly_checks_used}
                    </td>
                    <td className="py-4 pl-4 text-right text-xs text-slate-400">
                      {formatDistanceToNow(new Date(u.created_at), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {recentUsers.length === 0 && (
              <div className="text-center py-8 text-slate-500">No users found for your institution.</div>
            )}
          </div>
        </div>

        {/* Analytics Summary */}
        <div className="lg:col-span-1 glass-panel rounded-2xl overflow-hidden p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-white">Common Errors</h2>
            <BarChart3 className="w-5 h-5 text-slate-500" />
          </div>
          
          <div className="space-y-6">
            <ErrorItem name="Margin Spacing" count={142} percentage={85} color="bg-red-500" />
            <ErrorItem name="Citation Style" count={98} percentage={65} color="bg-amber-500" />
            <ErrorItem name="Font Size/Type" count={87} percentage={58} color="bg-indigo-500" />
            <ErrorItem name="Missing Headers" count={45} percentage={30} color="bg-cyan-500" />
            <ErrorItem name="Line Spacing" count={32} percentage={21} color="bg-emerald-500" />
          </div>
          
          <div className="mt-8 pt-6 border-t border-slate-800">
            <button className="w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm transition-colors">
              Download Full Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, trend, color }: any) {
  return (
    <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
      <div className={`absolute top-0 right-0 w-24 h-24 bg-${color}-500/10 blur-[30px] rounded-full -mr-10 -mt-10 pointer-events-none`} />
      <div className="flex items-start justify-between mb-4 relative z-10">
        <div className={`w-10 h-10 rounded-xl bg-${color}-500/10 flex items-center justify-center border border-${color}-500/20`}>
          {icon}
        </div>
        <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">{trend}</span>
      </div>
      <h3 className="text-slate-400 text-sm font-medium mb-1 relative z-10">{title}</h3>
      <div className="text-3xl font-bold text-white relative z-10">{value}</div>
    </div>
  );
}

function ErrorItem({ name, count, percentage, color }: any) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-300">{name}</span>
        <span className="text-xs font-bold text-slate-500">{count} issues</span>
      </div>
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

import { BookOpen } from "lucide-react";
