import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = (import.meta.env.VITE_SUPABASE_URL as string | undefined)?.trim() || "";
const anon = (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined)?.trim() || "";

export const supabase: SupabaseClient | null =
  url && anon ? createClient(url, anon) : null;

export function supabaseConfigured(): boolean {
  return supabase !== null;
}

export async function getAccessToken(): Promise<string | null> {
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

/** 邮件确认 / 重置密码要能在手机打开，不能指回 127.0.0.1。 */
export function authRedirectTo(): string {
  const configured = (import.meta.env.VITE_SITE_URL as string | undefined)?.trim();
  if (configured) return configured.replace(/\/$/, "");
  if (typeof window !== "undefined") {
    const origin = window.location.origin;
    if (!/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(origin)) {
      return origin;
    }
  }
  return "https://heal-companion.onrender.com";
}
