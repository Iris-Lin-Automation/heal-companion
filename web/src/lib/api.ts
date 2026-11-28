import { getAccessToken } from "./supabaseClient";

/** 所有产品接口都带上当前登录的 access token，不传本地 user_id。 */
export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = await getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(input, { ...init, headers });
}
