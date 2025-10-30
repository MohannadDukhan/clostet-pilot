// src/api.js
import axios from "axios";

// change baseURL if your FastAPI runs elsewhere
export const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// USERS
export async function createUser(payload) {
  // Accept either a name string (backwards compat) or a full payload object
  const body = typeof payload === "string" ? { name: payload } : payload || {};
  const { data } = await API.post("/users", body);
  return data;
}
export async function listUsers() {
  const { data } = await API.get("/users");
  return data;
}

// USER-SCOPED ITEMS
export async function listUserItems(userId) {
  const { data } = await API.get(`/users/${userId}/items`);
  return data;
}
export async function uploadUserItem(userId, { file, name }) {
  const form = new FormData();
  if (file) form.append("file", file);
  if (name) form.append("name", name);
  const { data } = await API.post(`/users/${userId}/items`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
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


// Build a usable <img src> from whatever the backend returns.
// Supports full URLs, "/storage/..." paths, or just filenames.
export function imageSrc(it) {
  const raw =
    it?.image_url ||
    it?.imagePath ||
    it?.path ||
    it?.filename ||
    it?.file;

  if (!raw) return null;

  if (/^https?:\/\//i.test(raw)) return raw;            // already full URL
  if (raw.startsWith("/")) return API.defaults.baseURL + raw; // "/storage/abc.jpg"

  // common case: backend returns just "abc.jpg" stored under /storage
  return `${API.defaults.baseURL}/storage/${raw}`;
}
