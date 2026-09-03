import { createContext, useContext, useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_ANON = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

const supabase = SUPABASE_URL && SUPABASE_ANON
    ? createClient(SUPABASE_URL, SUPABASE_ANON)
    : null;

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!supabase) { setLoading(false); return; }

        supabase.auth.getSession().then(({ data }) => {
            const session = data?.session;
            if (session) {
                setUser(session.user);
                localStorage.setItem('auth_token', session.access_token);
            }
            setLoading(false);
        });

        const { data: listener } = supabase.auth.onAuthStateChange((_ev, session) => {
            if (session) {
                setUser(session.user);
                localStorage.setItem('auth_token', session.access_token);
            } else {
                setUser(null);
                localStorage.removeItem('auth_token');
            }
        });

        return () => listener?.subscription?.unsubscribe();
    }, []);

    const signIn = async (email, password) => {
        if (!supabase) throw new Error('Supabase not configured');
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        return data;
    };

    const signUp = async (email, password) => {
        if (!supabase) throw new Error('Supabase not configured');
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        return data;
    };

    const signOut = async () => {
        if (supabase) await supabase.auth.signOut();
        setUser(null);
        localStorage.removeItem('auth_token');
    };

    return (
        <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut, supabase }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
