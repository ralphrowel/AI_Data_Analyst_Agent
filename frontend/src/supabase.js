import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "";

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

// Built-in demo accounts for zero-config multi-tenant testing
export const demoAuthEnabled = import.meta.env.DEV && import.meta.env.VITE_ALLOW_DEMO_AUTH !== "false";
export const DEMO_ACCOUNTS = demoAuthEnabled ? [
  {
    id: "user_a_alice",
    token: "demo_user_a",
    email: "alice@visiq.ai",
    name: "Alice (Analyst)",
    role: "Senior Data Analyst",
    avatar: "A",
    color: "bg-indigo-500",
  },
  {
    id: "user_b_bob",
    token: "demo_user_b",
    email: "bob@visiq.ai",
    name: "Bob (Enterprise)",
    role: "Marketing Director",
    avatar: "B",
    color: "bg-emerald-500",
  },
] : [];
