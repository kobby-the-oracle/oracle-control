import React from "react";
import { createClient, type Session } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;
const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    })
  : null;

export function AuthGate({ children }: { children: React.ReactNode }) {
  const [session, setSession] = React.useState<Session | null>(null);
  const [loading, setLoading] = React.useState(Boolean(supabase));
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data, error: sessionError }) => {
      if (sessionError) setError(sessionError.message);
      setSession(data.session);
      setLoading(false);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      setLoading(false);
    });
    return () => listener.subscription.unsubscribe();
  }, []);

  if (!supabase) return <>{children}</>;
  async function signIn(event: React.FormEvent) {
    event.preventDefault();
    if (!supabase) return;
    setBusy(true); setError("");
    const { error: signInError } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
    if (signInError) setError(signInError.message);
    setBusy(false);
  }
  async function resetPassword() {
    if (!supabase || !email.trim()) { setError("Enter your email address first."); return; }
    setBusy(true); setError("");
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: window.location.origin + "/app",
    });
    if (resetError) setError(resetError.message);
    else setError("If this account exists, a password-reset email has been sent.");
    setBusy(false);
  }
  async function signOut() { await supabase?.auth.signOut(); }
  if (loading) return <div className="auth-shell"><div className="auth-card"><span className="auth-mark">O</span><p>Restoring your secure session…</p></div></div>;
  if (!session) return <main className="auth-shell"><section className="auth-card">
    <div className="auth-brand"><span className="auth-mark">O</span><div><b>ORACLE CONTROL</b><small>FORENSIC INTELLIGENCE PLATFORM</small></div></div>
    <div className="auth-eyebrow">SECURE WORKSPACE ACCESS</div><h1>Welcome back.</h1>
    <p className="auth-copy">Sign in to access your organisation’s investigation workspace.</p>
    <form onSubmit={signIn} className="auth-form">
      <label htmlFor="auth-email">Work email</label><input id="auth-email" type="email" autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@organisation.com" required/>
      <label htmlFor="auth-password">Password</label><input id="auth-password" type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Your password" required/>
      <button className="auth-submit" type="submit" disabled={busy}>{busy?"Please wait…":"Sign in securely"}</button>
    </form>
    <button className="auth-reset" onClick={resetPassword} disabled={busy}>Forgot your password?</button>
    {error&&<p className="auth-error" role="alert">{error}</p>}
    <div className="auth-note"><span>INVITE-ONLY ACCESS</span><p>Accounts are provisioned by your organisation administrator. Public self-registration is disabled.</p></div>
    <footer>Protected access · Evidence first. Conclusions with proof.</footer>
  </section></main>;
  return <>{React.isValidElement(children) ? React.cloneElement(children as React.ReactElement<{accessToken?:string;onSignOut?:()=>void}>, {accessToken:session.access_token,onSignOut:signOut}) : children}</>;
}
