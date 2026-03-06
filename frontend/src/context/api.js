/**
 * Shared axios instance for new components/pages.
 * Automatically injects the JWT token from localStorage.
 */
import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000" });

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
