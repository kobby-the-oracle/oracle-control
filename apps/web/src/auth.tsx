/// <reference types="vite/client" />
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
  const [loading, setLoading] = React.useState(true);
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [showFounderSetup, setShowFounderSetup] = React.useState(false);
  const [founderEmail, setFounderEmail] = React.useState("fordjourmicheal379@gmail.com");
  const [bootstrapKey, setBootstrapKey] = React.useState("");
  const [setupMessage, setSetupMessage] = React.useState("");

  React.useEffect(() => {
    if (!supabase) { setLoading(false); return; }
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

  if (!supabase) return <main className="auth-shell"><section className="auth-card"><div className="auth-brand"><span className="auth-mark">O</span><div><b>ORACLE CONTROL</b><small>SECURE WORKSPACE</small></div></div><div className="auth-eyebrow">SETUP REQUIRED</div><h1>Workspace access is not configured.</h1><p className="auth-copy">The sign-in service is unavailable because its public project settings are missing. Access is blocked until configuration is completed.</p><p className="auth-error">Contact your platform administrator. No unauthenticated access is permitted.</p></section></main>;
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
  async function inviteFounder(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setSetupMessage(""); setError("");
    try {
      const response = await fetch("https://oracle-control-api-ok8v.onrender.com/v1/admin/users/invite-founder", {
        method: "POST", headers: { "Content-Type": "application/json", "X-API-Key": bootstrapKey },
        body: JSON.stringify({ email: founderEmail.trim(), redirect_to: window.location.origin + "/app" }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Founder invitation could not be sent.");
      setSetupMessage("Invitation sent to " + founderEmail.trim() + ". Open that email, accept the invitation, and set your password. Then return here to sign in.");
      setShowFounderSetup(false); setBootstrapKey("");
    } catch (err) { setSetupMessage(err instanceof Error ? err.message : "Founder setup failed."); }
    finally { setBusy(false); }
  }
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
{setupMessage && <p className="auth-error" role="status">{setupMessage}</p>}
<button className="auth-reset" onClick={()=>{setShowFounderSetup(v=>!v);setSetupMessage("");}}>First-time Founder setup</button>
{showFounderSetup && <form onSubmit={inviteFounder} className="auth-form auth-setup">
<p className="auth-copy">Send the first administrator invitation. Enter the existing administrator API key saved in your Render environment. Never share it in chat.</p>
<label htmlFor="founder-email">Founder sign-in email</label><input id="founder-email" type="email" value={founderEmail} onChange={e=>setFounderEmail(e.target.value)} required/>
<label htmlFor="bootstrap-key">Administrator API key</label><input id="bootstrap-key" type="password" autoComplete="off" value={bootstrapKey} onChange={e=>setBootstrapKey(e.target.value)} required/>
<button className="auth-submit" type="submit" disabled={busy}>{busy?"Sending invitation…":"Send Founder invitation"}</button>
</form>}
<footer>Protected access · Evidence first. Conclusions with proof.</footer>
  </section></main>;
  return <>{React.isValidElement(children) ? React.cloneElement(children as React.ReactElement<{accessToken?:string;onSignOut?:()=>void}>, {accessToken:session.access_token,onSignOut:signOut}) : children}</>;
}
