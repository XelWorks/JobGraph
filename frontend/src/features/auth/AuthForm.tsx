import React, { useState } from 'react';
import { Compass, Mail, Lock, User, AlertCircle, ArrowRight } from 'lucide-react';

interface AuthFormProps {
  onAuthSuccess: (token: string) => void;
}

export const AuthForm: React.FC<AuthFormProps> = ({ onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const meta = import.meta as unknown as { env?: { VITE_API_URL?: string } };
    const apiUrl = meta.env?.VITE_API_URL || 'http://localhost:8000';
    const trimmedEmail = email.trim().toLowerCase();

    if (!trimmedEmail || !password) {
      setError('Please fill in all required fields.');
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      setLoading(false);
      return;
    }

    try {
      if (isLogin) {
        // Handle Login
        const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: trimmedEmail, password }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || 'Invalid credentials');
        }

        const data = await response.json();
        if (data.access_token) {
          onAuthSuccess(data.access_token);
        } else {
          throw new Error('Missing token in response');
        }
      } else {
        // Handle Register
        const response = await fetch(`${apiUrl}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: trimmedEmail,
            password,
            first_name: firstName.trim() || null,
            last_name: lastName.trim() || null,
          }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || 'Registration failed');
        }

        // Auto-login upon successful registration
        const loginResp = await fetch(`${apiUrl}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: trimmedEmail, password }),
        });

        if (!loginResp.ok) {
          throw new Error('Registration succeeded, but auto-login failed. Please sign in manually.');
        }

        const data = await loginResp.json();
        if (data.access_token) {
          onAuthSuccess(data.access_token);
        } else {
          throw new Error('Missing token in response');
        }
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'An unexpected error occurred. Please try again.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-slate-950/40 p-8 rounded-2xl border border-slate-800 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-4 -mr-4 w-40 h-40 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        
        {/* Header Branding */}
        <div className="text-center relative z-10">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-sky-400">
              <Compass className="h-8 w-8 text-sky-400 animate-pulse" />
            </div>
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-white leading-tight">
            {isLogin ? 'Welcome back to JobGraph' : 'Create your account'}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            {isLogin ? "Don't have an account?" : 'Already registered?'}{' '}
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError(null);
              }}
              className="font-semibold text-sky-400 hover:text-sky-300 transition-colors focus:outline-none"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>

        {/* Error Banners */}
        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl flex gap-3 text-sm animate-fadeIn">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Auth Forms */}
        <form className="mt-8 space-y-5 relative z-10" onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400">First Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="John"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 focus:border-sky-500/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400">Last Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Doe"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 focus:border-sky-500/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
                  />
                </div>
              </div>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-400">Email Address <span className="text-rose-500">*</span></label>
            <div className="relative">
              <Mail className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
              <input
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 focus:border-sky-500/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-400">Password <span className="text-rose-500">*</span></label>
            <div className="relative">
              <Lock className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 focus:border-sky-500/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-6 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white font-bold text-sm shadow-[0_0_15px_-3px_rgba(14,165,233,0.3)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group focus:outline-none"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Processing...
              </span>
            ) : (
              <>
                {isLogin ? 'Sign In' : 'Create Account'}{' '}
                <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-800/40 text-center relative z-10 text-xs text-slate-500">
          JobGraph Platform • Single User Local-First Security
        </div>
      </div>
    </div>
  );
};
