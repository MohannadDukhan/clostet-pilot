// src/api.js
import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const API = axios.create({
  baseURL,
});

// Attach token to every request
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("cp:token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear auth state and redirect to login
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("cp:token");
      localStorage.removeItem("cp:user");
      if (window.location.pathname !== "/login" && window.location.pathname !== "/signup") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// AUTH
export async function signup(payload) {
  const { data } = await API.post("/auth/signup", payload);
  return data; // { token, user }
}

export async function login(payload) {
  const { data } = await API.post("/auth/login", payload);
  return data; // { token, user }
}

export async function getMe() {
  const { data } = await API.get("/users/me");
  return data;
}

// USERS
export async function createUser(payload) {
  const body = typeof payload === "string" ? { name: payload } : payload || {};
  const { data } = await API.post("/users", body);
  return data;
}

export async function listUsers() {
  const { data } = await API.get("/users");
  return data;
}

export async function updateUser(userId, payload) {
  const { data } = await API.put(`/users/${userId}`, payload);
  return data;
}

// USER-SCOPED ITEMS
export async function listUserItems(userId) {
  const { data } = await API.get(`/users/${userId}/items`);
  return data;
}
export async function uploadUserItem(userId, { file, name, allowDuplicate = false }) {
  const form = new FormData();
  if (file) form.append("file", file);
  if (name) form.append("name", name);

  const { data } = await API.post(
    `/users/${userId}/items?allow_duplicate=${allowDuplicate ? "true" : "false"}`,
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return data;
}

// ITEM OPS
export async function classifyItem(itemId) {
  const { data } = await API.post(`/items/${itemId}/classify`);
  return data;
}
export async function patchItem(itemId, patch) {
  const { data } = await API.patch(`/items/${itemId}`, patch);
  return data;
}
export async function deleteItem(itemId) {
  await API.delete(`/items/${itemId}`);
}

export async function suggestOutfit(userId, params = {}) {
  const q = new URLSearchParams(params).toString();
  const { data } = await API.get(`/users/${userId}/outfits/suggest${q ? `?${q}` : ""}`);
  return data;
}

export async function scoreOutfit(userId, payload) {
  const { data } = await API.post(`/users/${userId}/outfits/score`, payload);
  return data;
}

// LIKED COLOUR COMBOS
export async function likeCombo(userId, colorFingerprint) {
  const { data } = await API.post(`/users/${userId}/liked-combos`, { color_fingerprint: colorFingerprint });
  return data;
}
export async function unlikeCombo(userId, colorFingerprint) {
  const { data } = await API.delete(`/users/${userId}/liked-combos`, { data: { color_fingerprint: colorFingerprint } });
  return data;
}
export async function dislikeCombo(userId, colorFingerprint) {
  const { data } = await API.post(`/users/${userId}/disliked-combos`, { color_fingerprint: colorFingerprint });
  return data;
}
export async function undislikeCombo(userId, colorFingerprint) {
  const { data } = await API.delete(`/users/${userId}/disliked-combos`, { data: { color_fingerprint: colorFingerprint } });
  return data;
}
export async function listDislikedCombos(userId) {
  const { data } = await API.get(`/users/${userId}/disliked-combos`);
  return data;
}

// Supports full URLs, "/storage/..." paths, or just filenames.
export function imageSrc(it) {
  const raw =
    it?.image_url ||
    it?.imagePath ||
    it?.path ||
    it?.filename ||
    it?.file;

  if (!raw) return null;

  if (/^https?:\/\//i.test(raw)) return raw;
  if (raw.startsWith("/")) return API.defaults.baseURL + raw;

  return `${API.defaults.baseURL}/storage/${raw}`;
}
