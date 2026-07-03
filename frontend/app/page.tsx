"use client";

import React, { useRef, useState, useEffect } from "react";
import Link from "next/link";
import { motion, useScroll, useTransform, useSpring, useMotionValue, useMotionValueEvent, AnimatePresence } from "framer-motion";
import { FileCheck, Shield, Zap, ArrowRight, UploadCloud, GraduationCap, Code } from "lucide-react";

// ---------------------------------------------------------
// Subcomponents for Interactive Effects
// ---------------------------------------------------------

const MagneticButton = ({ children, className, href }: { children: React.ReactNode, className: string, href?: string }) => {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 150, damping: 15, mass: 0.1 });
  const springY = useSpring(y, { stiffness: 150, damping: 15, mass: 0.1 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const distanceX = e.clientX - centerX;
    const distanceY = e.clientY - centerY;
    
    if (Math.abs(distanceX) < 80 && Math.abs(distanceY) < 80) {
      x.set(distanceX * 0.3);
      y.set(distanceY * 0.3);
    } else {
      x.set(0);
      y.set(0);
    }
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const content = (
    <motion.div
      ref={ref}
      style={{ x: springX, y: springY }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative inline-block ${className}`}
    >
      {children}
    </motion.div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
};

const BentoCard = ({ children, className, delay = 0 }: { children: React.ReactNode, className: string, delay?: number }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.5, delay, ease: [0.4, 0, 0.2, 1] }}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      className={`bento-card ${className}`}
    >
      <div 
        className="bento-card-glow"
        style={{
          opacity: isHovering ? 1 : 0,
          background: `radial-gradient(300px circle at ${mousePosition.x}px ${mousePosition.y}px, var(--accent-cyan-glow), transparent 70%)`
        }}
      />
      <div className="relative z-10 h-full flex flex-col">
        {children}
      </div>
    </motion.div>
  );
};

// ---------------------------------------------------------
// Main Landing Page
// ---------------------------------------------------------

export default function LandingPage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const { scrollY } = useScroll();

  useMotionValueEvent(scrollY, "change", (latest) => {
    setIsScrolled(latest > 60);
  });

  // Parallax Mockup
  const yMockup = useTransform(scrollY, [0, 600], [0, -100]);
  const rotateXMockup = useTransform(scrollY, [0, 600], [8, 0]);
  const scaleMockup = useTransform(scrollY, [0, 600], [1, 1.02]);

  return (
    <>
      <div className="bg-grid" />
      <div className="noise-overlay" />

      {/* Animated Orbs */}
      <motion.div 
        className="fixed top-[10%] left-[20%] w-[600px] h-[600px] rounded-full bg-[var(--accent-cyan)] opacity-[0.15] blur-[120px] pointer-events-none -z-10"
        animate={{ x: [0, 100, 0], y: [0, 50, 0] }}
        transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
      />
      <motion.div 
        className="fixed top-[40%] right-[10%] w-[800px] h-[800px] rounded-full bg-[var(--accent-violet)] opacity-[0.12] blur-[120px] pointer-events-none -z-10"
        animate={{ x: [0, -150, 0], y: [0, -100, 0] }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
      />

      {/* Navbar */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className={`fixed top-0 w-full z-50 transition-all duration-300 ${isScrolled ? 'backdrop-blur-xl bg-black/40 border-b border-[var(--border)]' : 'bg-transparent'}`}
      >
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-display font-bold text-xl tracking-tight">
            <Shield className="w-5 h-5 text-[var(--accent-cyan)]" />
            <span>Format<span className="heading-gradient">Guard</span></span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[var(--text-secondary)]">
            <Link href="#features" className="hover:text-[var(--accent-cyan)] transition-colors relative group">
              Features
              <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-[var(--accent-cyan)] opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
            <Link href="#how-it-works" className="hover:text-[var(--accent-cyan)] transition-colors relative group">
              How it Works
              <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-[var(--accent-cyan)] opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium text-[var(--text-primary)] hover:text-[var(--accent-cyan)] transition-colors">
              Sign In
            </Link>
            <MagneticButton href="/register" className="btn-primary text-sm px-6 py-2">
              Get Started
            </MagneticButton>
          </div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <section className="pt-40 pb-20 md:pt-48 md:pb-32 container mx-auto px-6 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--accent-cyan)] text-xs font-mono mb-8 backdrop-blur-md"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent-cyan)] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--accent-cyan)]"></span>
            </span>
            FormatGuard Engine v2.0
          </motion.div>

          <h1 className="text-5xl md:text-7xl lg:text-[80px] font-display font-bold tracking-tighter mb-8 leading-[1.1]">
            <motion.div className="overflow-hidden inline-block" initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4 }}>Stop</motion.div>{' '}
            <motion.div className="overflow-hidden inline-block" initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.48 }}>fighting</motion.div>{' '}
            <motion.div className="overflow-hidden inline-block" initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.56 }}>Word</motion.div>{' '}
            <motion.div className="overflow-hidden inline-block" initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.64 }}>formatting.</motion.div>
            <br />
            <motion.div className="overflow-hidden inline-block" initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.72 }}>
              <span className="heading-gradient">Start Graduating.</span>
            </motion.div>
          </h1>

          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.8 }}
            className="text-lg md:text-xl text-[var(--text-secondary)] mb-10 max-w-2xl mx-auto leading-relaxed"
          >
            The world's first automated compliance platform for university thesis and reports. Instantly detect and auto-correct formatting violations.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.9, type: "spring" }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <MagneticButton href="/register" className="btn-primary w-full sm:w-auto flex items-center justify-center gap-2 group">
              Start Free Trial
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </MagneticButton>
            <MagneticButton href="#demo" className="btn-ghost w-full sm:w-auto flex items-center justify-center gap-2">
              View Example Report
            </MagneticButton>
          </motion.div>
        </div>
      </section>

      {/* Floating Dashboard Mockup */}
      <section id="demo" className="container mx-auto px-6 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1, duration: 0.8, ease: "easeOut" }}
          style={{ y: yMockup, rotateX: rotateXMockup, scale: scaleMockup, perspective: 1200 }}
          className="max-w-5xl mx-auto"
        >
          <div className="mockup-container">
            <div className="mockup-header">
              <div className="flex gap-1.5">
                <div className="mockup-dot bg-rose-500" />
                <div className="mockup-dot bg-amber-500" />
                <div className="mockup-dot bg-emerald-500" />
              </div>
              <div className="ml-4 flex-1 h-6 bg-black/40 rounded-md border border-[var(--border)] flex items-center justify-center text-[10px] font-mono text-[var(--text-muted)]">
                app.formatguard.com/report/a38f
              </div>
            </div>
            <div className="mockup-body bg-[var(--bg-base)]">
              {/* Fake Sidebar */}
              <div className="w-64 border-r border-[var(--border)] pr-4 flex flex-col gap-4">
                <div className="h-4 w-24 bg-[var(--border)] rounded" />
                <div className="p-3 border-l-2 border-[var(--accent-error)] bg-[var(--accent-error)]/10 rounded-r-md">
                  <div className="text-xs font-mono text-[var(--accent-error)] mb-1">MARGIN ERROR</div>
                  <div className="text-sm">Left margin is 1.0", expected 1.5"</div>
                </div>
                <div className="p-3 border-l-2 border-[var(--accent-cyan)] bg-[var(--accent-cyan)]/10 rounded-r-md">
                  <div className="text-xs font-mono text-[var(--accent-cyan)] mb-1">FONT ERROR</div>
                  <div className="text-sm">Heading 1 uses Calibri, expected Times New Roman</div>
                </div>
              </div>
              {/* Fake Document */}
              <div className="flex-1 bg-white/5 rounded-md border border-[var(--border)] p-8 relative overflow-hidden">
                <div className="w-full h-8 bg-[var(--border)] rounded mb-4 w-3/4" />
                <div className="w-full h-2 bg-[var(--border)] rounded mb-2" />
                <div className="w-full h-2 bg-[var(--border)] rounded mb-2" />
                <div className="w-full h-2 bg-[var(--border)] rounded mb-2 w-5/6" />
                {/* Scanner Line */}
                <motion.div 
                  className="absolute left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[var(--accent-cyan)] to-transparent shadow-[0_0_10px_var(--accent-cyan)]"
                  animate={{ top: ["0%", "100%", "0%"] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                />
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Bento Box Features */}
      <section id="features" className="py-32 container mx-auto px-6 relative z-10">
        <div className="text-center mb-20">
          <h2 className="text-4xl md:text-5xl font-display font-bold mb-4">Precision Engineering for Documents</h2>
          <p className="text-[var(--text-secondary)] max-w-xl mx-auto text-lg">We parse Word documents at the XML level to guarantee 100% compliance with strict institutional guidelines.</p>
        </div>

        <div className="bento-grid">
          <BentoCard className="bento-hero group" delay={0.1}>
            <div className="flex-1">
              <div className="w-12 h-12 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <FileCheck className="w-6 h-6 text-[var(--accent-cyan)]" />
              </div>
              <h3 className="text-2xl font-display font-bold mb-3">Instant Compliance</h3>
              <p className="text-[var(--text-secondary)] text-lg max-w-md">Checks margins, fonts, spacing, citations, and headers against your university's exact rulebook.</p>
            </div>
            <div className="absolute right-0 bottom-0 w-2/3 h-2/3 bg-gradient-to-tl from-[var(--bg-elevated)] to-transparent border-t border-l border-[var(--border)] rounded-tl-2xl translate-x-4 translate-y-4 group-hover:translate-x-2 group-hover:translate-y-2 transition-transform p-6">
              <div className="font-mono text-xs text-[var(--accent-cyan)] mb-2">{"<w:pPr>"}</div>
              <div className="font-mono text-xs text-[var(--text-secondary)] pl-4">{"<w:spacing w:line=\"480\" w:lineRule=\"auto\"/>"}</div>
              <div className="font-mono text-xs text-[var(--text-secondary)] pl-4">{"<w:ind w:left=\"2160\"/>"}</div>
              <div className="font-mono text-xs text-[var(--accent-cyan)] mt-2">{"</w:pPr>"}</div>
            </div>
          </BentoCard>

          <BentoCard className="bento-top-right group" delay={0.2}>
            <div className="w-10 h-10 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center mb-4 group-hover:rotate-12 transition-transform">
              <Zap className="w-5 h-5 text-[var(--accent-violet)]" />
            </div>
            <h3 className="text-xl font-display font-bold mb-2">1-Click Auto-Fix</h3>
            <p className="text-[var(--text-secondary)] text-sm">Don't just find the errors. FormatGuard rewrites the underlying XML to fix them automatically.</p>
          </BentoCard>

          <BentoCard className="bento-mid-right group" delay={0.3}>
            <div className="w-10 h-10 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center mb-4 group-hover:-rotate-12 transition-transform">
              <GraduationCap className="w-5 h-5 text-[var(--accent-success)]" />
            </div>
            <h3 className="text-xl font-display font-bold mb-2">Institution Rulesets</h3>
            <p className="text-[var(--text-secondary)] text-sm">Pre-loaded with verified guidelines for NUST, FAST, COMSATS, IEEE, APA, Harvard, and more.</p>
          </BentoCard>
        </div>
      </section>

      {/* How it Works Section */}
      <section id="how-it-works" className="py-20 container mx-auto px-6 relative z-10 border-t border-[var(--border)]">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">How it Works</h2>
          <p className="text-[var(--text-secondary)] max-w-xl mx-auto">Three simple steps to perfect formatting.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto text-center">
          <div className="p-6">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center text-2xl font-bold text-[var(--accent-cyan)] mx-auto mb-6 shadow-[0_0_20px_var(--accent-cyan-glow)]">1</div>
            <h3 className="text-xl font-display font-bold mb-3">Upload Document</h3>
            <p className="text-[var(--text-secondary)]">Drag and drop your raw Word (.docx) file into our secure portal.</p>
          </div>
          <div className="p-6">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center text-2xl font-bold text-[var(--accent-violet)] mx-auto mb-6 shadow-[0_0_20px_var(--accent-violet-glow)]">2</div>
            <h3 className="text-xl font-display font-bold mb-3">Select Ruleset</h3>
            <p className="text-[var(--text-secondary)]">Choose your university or target journal from our pre-loaded guidelines.</p>
          </div>
          <div className="p-6">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center text-2xl font-bold text-[var(--accent-success)] mx-auto mb-6 shadow-[0_0_20px_rgba(0,212,170,0.25)]">3</div>
            <h3 className="text-xl font-display font-bold mb-3">Auto-Correct</h3>
            <p className="text-[var(--text-secondary)]">Review the compliance report and click 'Fix All' to download the perfect document.</p>
          </div>
        </div>
      </section>

      {/* Institutions Section */}
      <section id="institutions" className="py-20 container mx-auto px-6 relative z-10 border-t border-[var(--border)]">
        <div className="max-w-4xl mx-auto text-center bg-[var(--bg-elevated)] border border-[var(--border)] rounded-3xl p-12 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-b from-[var(--accent-cyan-glow)] to-transparent opacity-0 group-hover:opacity-10 transition-opacity" />
          <h2 className="text-3xl md:text-4xl font-display font-bold mb-4 relative z-10">Built for Universities</h2>
          <p className="text-[var(--text-secondary)] max-w-2xl mx-auto mb-8 text-lg relative z-10">
            Stop wasting faculty time manually checking margins and font sizes. FormatGuard provides a centralized dashboard to track student compliance and manage institutional rulesets.
          </p>
          <MagneticButton href="/register" className="btn-primary relative z-10">
            Setup Institutional Portal
          </MagneticButton>
        </div>
      </section>
    </>
  );
}
