"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Loader2, ArrowRight, ShieldAlert, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const { data: config, isLoading: isConfigLoading } = useQuery({
    queryKey: ["systemConfig"],
    queryFn: () => apiClient.getSystemConfig(),
  });

  const handleLogin = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      // If dev mode, we pass a dummy email, else the real one
      const loginEmail = config?.dev_mode ? "dev@example.com" : email;
      const res = await apiClient.login(loginEmail, password);
      localStorage.setItem("auth_token", res.token);
      router.push("/"); // redirect to home chat interface
    } catch (err: any) {
      setError(err.message || "Failed to sign in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isConfigLoading) {
    return (
      <div className="flex justify-center items-center h-48">
        <Loader2 className="w-8 h-8 animate-spin text-primary/50" />
      </div>
    );
  }

  const isDevMode = config?.dev_mode === true;

  return (
    <div className="w-full">
      <div className="mb-8 text-center lg:text-left">
        <h2 className="text-3xl font-display font-semibold tracking-tight text-foreground">
          Welcome back
        </h2>
        <p className="text-muted-foreground mt-2 font-sans">
          {isDevMode
            ? "Development mode is active. Quick login is available."
            : "Sign in to your account to continue."}
        </p>
      </div>

      <AnimatePresence mode="wait">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 flex items-start gap-3 text-destructive"
          >
            <ShieldAlert className="w-5 h-5 mt-0.5 shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {isDevMode ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="bg-primary/5 border border-primary/20 rounded-2xl p-6 text-center"
        >
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-primary/10 rounded-full text-primary">
              <CheckCircle2 className="w-8 h-8" />
            </div>
          </div>
          <h3 className="font-medium text-lg mb-2">Development Login</h3>
          <p className="text-sm text-muted-foreground mb-6">
            Bypass authentication to access the platform locally.
          </p>
          <button
            onClick={() => handleLogin()}
            disabled={isSubmitting}
            className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground py-2.5 rounded-lg font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                Continue as Dev User
                <ArrowRight className="w-4 h-4 ml-1" />
              </>
            )}
          </button>
        </motion.div>
      ) : (
        <motion.form
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, staggerChildren: 0.1 }}
          onSubmit={handleLogin}
          className="space-y-5"
        >
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Work Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2.5 rounded-lg bg-background border border-input focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-muted-foreground/50"
              placeholder="dr.smith@hospital.org"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-foreground">
                Password
              </label>
              <Link href="#" className="flex text-xs text-primary hover:underline font-medium">
                Forgot password?
              </Link>
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2.5 rounded-lg bg-background border border-input focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-muted-foreground/50"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !email || !password}
            className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground py-2.5 rounded-lg font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed mt-2"
          >
            {isSubmitting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              "Sign In"
            )}
          </button>
        </motion.form>
      )}

      {!isDevMode && (
        <p className="text-center text-sm text-muted-foreground mt-8">
          Don't have an account?{" "}
          <Link href="/signup" className="text-primary font-medium hover:underline">
            Request Access
          </Link>
        </p>
      )}
    </div>
  );
}
