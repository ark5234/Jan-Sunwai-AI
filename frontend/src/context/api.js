/**
 * Shared axios instance for new components/pages.
 * Uses secure cookie-based auth transport with credentials included.
 */
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

// Ensure every axios call in the app includes cookies for auth.
axios.defaults.withCredentials = true;
const api = axios.create({ baseURL: API_BASE_URL, withCredentials: true });

let global401InterceptorInstalled = false;

const AUTH_ENDPOINT_SEGMENTS = [
  "/users/login",
  "/users/register",
  "/users/forgot-password",
  "/users/reset-password",
];

function isAuthEndpoint(url = "") {
  return AUTH_ENDPOINT_SEGMENTS.some((segment) => url.includes(segment));
}

function clearSessionAndRedirectToLogin() {
  // Attempt backend logout so cookie is cleared server-side too.
  fetch(`${API_BASE_URL}/users/logout`, { method: "POST", credentials: "include" }).catch(() => {
    // no-op
  });

  const currentPath = window.location.pathname || "";
  const isAlreadyOnAuthPage = ["/login", "/register", "/forgot-password", "/reset-password"].some(
    (path) => currentPath.startsWith(path)
  );
  if (!isAlreadyOnAuthPage) {
    window.location.href = "/login";
  }
}

export function installGlobalAxios401Interceptor() {
  if (global401InterceptorInstalled) {
    return;
  }

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      const statusCode = error?.response?.status;
      const requestUrl = String(error?.config?.url || "");
      if (statusCode === 401 && !isAuthEndpoint(requestUrl)) {
        clearSessionAndRedirectToLogin();
      }
      return Promise.reject(error);
    }
  );

  global401InterceptorInstalled = true;
}

export default api;
