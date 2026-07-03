import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Login | FormatGuard",
  description: "Sign in to FormatGuard.",
};

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-950">
      <div className="hidden md:flex w-1/2 bg-slate-900 relative overflow-hidden items-center justify-center p-12">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/40 via-slate-900 to-slate-900 z-0" />
        <div className="relative z-10 max-w-md">
          <h2 className="text-4xl font-outfit font-bold text-white mb-6">
            Stop Fighting Format.<br />Start Creating.
          </h2>
          <p className="text-slate-400 text-lg">
            Join thousands of students and faculty using FormatGuard to ensure perfect document compliance every time.
          </p>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-6 md:p-12 relative">
        {/* Glow effect behind the form */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-indigo-500/20 blur-[100px] rounded-full z-0 pointer-events-none" />
        <div className="relative z-10 w-full max-w-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
