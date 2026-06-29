import { jwtDecode } from "jwt-decode";

interface TokenPayload {
  exp: number;
  iat: number;
  sub: string;
  email: string;
  name: string;
  role?: string;
}

/**
 * Get the current access token from localStorage
 */
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("agentforge_token");
}

/**
 * Get the refresh token from localStorage
 */
export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("agentforge_refresh");
}

/**
 * Get the user object from localStorage
 */
export function getUser():
  | {
      id: string;
      email: string;
      name: string;
    }
  | null {
  if (typeof window === "undefined") return null;
  const user = localStorage.getItem("agentforge_user");
  return user ? JSON.parse(user) : null;
}

/**
 * Check if the user is authenticated (has a valid token)
 */
export function isAuthenticated(): boolean {
  const token = getAccessToken();
  if (!token) return false;

  try {
    const decoded = jwtDecode<TokenPayload>(token);
    const currentTime = Date.now() / 1000;
    return decoded.exp > currentTime;
  } catch {
    return false;
  }
}

/**
 * Get the expiration time of the current token
 */
export function getTokenExpiration(): number | null {
  const token = getAccessToken();
  if (!token) return null;

  try {
    const decoded = jwtDecode<TokenPayload>(token);
    return decoded.exp * 1000; // Convert to milliseconds
  } catch {
    return null;
  }
}

/**
 * Clear all authentication data from localStorage
 */
export function clearAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("agentforge_token");
  localStorage.removeItem("agentforge_refresh");
  localStorage.removeItem("agentforge_user");
}

/**
 * Save authentication data to localStorage
 */
export function setAuth(
  token: string,
  refreshToken: string,
  user: { id: string; email: string; name: string }
): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("agentforge_token", token);
  localStorage.setItem("agentforge_refresh", refreshToken);
  localStorage.setItem("agentforge_user", JSON.stringify(user));
}
