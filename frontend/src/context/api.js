/**
 * Shared axios instance for new components/pages.
 * Automatically injects the JWT token from localStorage.
 */
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const api = axios.create({ baseURL: API_BASE_URL });

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
  try {
    localStorage.removeItem("jan_sunwai_user");
  } catch {
    // no-op in edge cases
  }

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

api.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem("jan_sunwai_user");
    if (raw) {
      const { access_token } = JSON.parse(raw);
      if (access_token) config.headers.Authorization = `Bearer ${access_token}`;
    }
  } catch (_) {
    // ignore parse errors
  }
  return config;
});

export default api;
