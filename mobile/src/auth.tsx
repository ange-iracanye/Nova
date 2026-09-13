import React, { createContext, useContext, useEffect, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import { api, setApiSession, Session, User } from './api';

type AuthValue = { user: User | null; loading: boolean; signIn: (email: string, password: string) => Promise<void>; signUp: (email: string, password: string) => Promise<void>; signOut: () => Promise<void> };
const AuthContext = createContext<AuthValue | null>(null);
const TOKEN_KEY = 'nova.mobile.session';

async function persistSession(session?: Session) {
  if (!session?.token) throw new Error('Nova did not return a valid session.');
  setApiSession(session.token);
  await SecureStore.setItemAsync(TOKEN_KEY, session.token);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    (async () => {
      try {
        const token = await SecureStore.getItemAsync(TOKEN_KEY);
        if (!token) return;
        setApiSession(token);
        const result = await api.me();
        if (result.authenticated && result.user) setUser(result.user);
        else { setApiSession(null); await SecureStore.deleteItemAsync(TOKEN_KEY); }
      } catch { setApiSession(null); await SecureStore.deleteItemAsync(TOKEN_KEY).catch(() => undefined); }
      finally { setLoading(false); }
    })();
  }, []);

  const authenticate = async (action: 'login' | 'register', email: string, password: string) => {
    const result = await api[action](email.trim().toLowerCase(), password);
    if (!result.success || !result.session || !result.user) throw new Error(result.message || 'Authentication failed.');
    await persistSession(result.session);
    setUser(result.user);
  };
  const signOut = async () => { try { await api.logout(); } finally { setApiSession(null); setUser(null); await SecureStore.deleteItemAsync(TOKEN_KEY).catch(() => undefined); } };
  return <AuthContext.Provider value={{ user, loading, signIn: (e,p) => authenticate('login',e,p), signUp: (e,p) => authenticate('register',e,p), signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('useAuth must be used inside AuthProvider'); return value; }
