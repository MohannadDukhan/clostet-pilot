import axios from "axios";

// if you ever change ports, update here
export const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});
