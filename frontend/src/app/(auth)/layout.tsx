import { Activity } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-background text-foreground selection:bg-primary/20">
      {/* Left side - Brand / Aesthetic */}
      <div className="hidden lg:flex flex-1 flex-col justify-between bg-primary relative overflow-hidden text-primary-foreground p-12 lg:w-1/2">
        {/* Abstract Background pattern */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/80 to-blue-900/40 z-0"></div>
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-white/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>

        <div className="relative z-10 flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-white/20 backdrop-blur-md shadow-inner border border-white/10">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <span className="font-display font-semibold text-xl tracking-tight">
            Clinical AI Platform
          </span>
        </div>

        <div className="relative z-10 max-w-lg mb-8">
          <h1 className="text-4xl lg:text-5xl font-display font-medium leading-tight mb-6">
            Intelligent Evidence Retrieval & Synthesis
          </h1>
          <p className="text-primary-foreground/80 text-lg leading-relaxed font-sans">
            Access, synthesize, and chat with authoritative guidelines from the WHO and CDC instantly. Designed for modern healthcare professionals.
          </p>
        </div>

        <div className="relative z-10 flex items-center gap-4 text-sm font-medium text-primary-foreground/60">
          <span>Enterprise Grade Security</span>
          <span className="w-1.5 h-1.5 rounded-full bg-primary-foreground/60"></span>
          <span>HIPAA Compliance Ready</span>
        </div>
      </div>

      {/* Right side - Forms container */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 lg:p-12 w-full lg:w-1/2 relative bg-card/50 backdrop-blur-xl">
        <main className="w-full max-w-sm">
          {children}
        </main>
      </div>
    </div>
  );
}
