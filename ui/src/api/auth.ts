import { BASE_URL } from "./client";
import type { User, AuthResponse } from "../types";

export interface RegisterPayload {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  company?: string;
}

export async function registerUser(payload: RegisterPayload): Promise<User> {
  const response = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Register failed (${response.status}): ${text}`);
  }
  return response.json() as Promise<User>;
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Login failed (${response.status}): ${text}`);
  }
  return response.json() as Promise<AuthResponse>;
}
