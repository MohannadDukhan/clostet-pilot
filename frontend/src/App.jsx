import { useEffect, useMemo, useState } from "react";
import { API } from "./api";

export default function App() {
  // users / current user
  const [users, setUsers] = useState([]);
  const [newUserName, setNewUserName] = useState("");
  const [userId, setUserId] = useState(null);

  // items
  const [items, setItems] = useState([]);
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  // edit + expand state per item
  const [editMap, setEditMap] = useState({});     // { [itemId]: {...} }
  const [expandMap, setExpandMap] = useState({}); // { [itemId]: boolean }

  const imagesBase = useMemo(() => `${API.defaults.baseURL}/images/`, []);

  // load users on boot
  useEffect(() => {
    (async () => {
      try {
        const { data } = await API.get("/users");
        setUsers(data);
        if (!userId && data.length > 0) setUserId(data[0].id);
      } catch (e) {
        console.error(e);
        setMessage("failed to load users");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // load items when user changes
  useEffect(() => {
    if (!userId) {
      setItems([]);
      setEditMap({});
      setExpandMap({});
      return;
    }
    (async () => {
      try {
        const { data } = await API.get(`/users/${userId}/items`);
        setItems(data);

        const fresh = {};
        const collapsed = {};
        for (const it of data) {
          fresh[it.id] = {
            category: it.category || "",
            color: it.color || "",
            season: it.season || "",
            formality: it.formality || "",
            notes: it.notes || "",
            verified: it.verified || false,
          };
          collapsed[it.id] = false; // start collapsed
        }
        setEditMap(fresh);
        setExpandMap(collapsed);
      } catch (e) {
        console.error(e);
        setMessage("failed to load items");
      }
    })();
  }, [userId]);

  // handlers
  async function createUser() {
    if (!newUserName.trim()) return;
    setBusy(true);
    try {
      const { data } = await API.post("/users", { display_name: newUserName.trim() });
      setUsers((u) => [data, ...u]);
      setUserId(data.id);
      setNewUserName("");
      setMessage("user created");
    } catch (e) {
      console.error(e);
      setMessage("failed to create user");
    } finally {
      setBusy(false);
    }
  }

  async function uploadItem() {
    if (!userId || !file) return;
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await API.post(`/users/${userId}/items`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setItems((prev) => [data, ...prev]);
      setEditMap((m) => ({
        ...m,
        [data.id]: { category: "", color: "", season: "", formality: "", notes: "", verified: false },
      }));
      setExpandMap((m) => ({ ...m, [data.id]: true })); // open editor for new upload
      setFile(null);
      setMessage("uploaded");
    } catch (e) {
      console.error(e);
      setMessage("failed to upload");
    } finally {
      setBusy(false);
    }
  }

  async function saveItem(itemId) {
    const patch = editMap[itemId];
    if (!patch) return;
    setBusy(true);
    try {
      const { data } = await API.patch(`/items/${itemId}`, patch);
      setItems((list) => list.map((x) => (x.id === itemId ? data : x)));
      setExpandMap((m) => ({ ...m, [itemId]: false })); // collapse after save
      setMessage("saved");
    } catch (e) {
      console.error(e);
      setMessage("failed to save");
    } finally {
      setBusy(false);
    }
  }

  async function removeItem(itemId) {
    setBusy(true);
    try {
      await API.delete(`/items/${itemId}`);
      setItems((list) => list.filter((x) => x.id !== itemId));
      setEditMap((m) => {
        const copy = { ...m };
        delete copy[itemId];
        return copy;
      });
      setExpandMap((m) => {
        const copy = { ...m };
        delete copy[itemId];
        return copy;
      });
      setMessage("deleted");
    } catch (e) {
      console.error(e);
      setMessage("failed to delete");
    } finally {
      setBusy(false);
    }
  }

  function updateEdit(itemId, field, value) {
    setEditMap((m) => ({
      ...m,
      [itemId]: { ...m[itemId], [field]: value },
    }));
  }

  return (
    <div style={pageStyle}>
      {/* centered main container */}
      <div style={containerStyle}>
        <h1 style={{ fontSize: 28, marginBottom: 6 }}>closet pilot</h1>
        <p style={{ opacity: 0.8, marginBottom: 24 }}>
          upload your clothes, build your wardrobe. “make outfit” coming soon.
        </p>

        {/* top bar: user creation + picker */}
        <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16, flexWrap: "wrap" }}>
          <input
            value={newUserName}
            onChange={(e) => setNewUserName(e.target.value)}
            placeholder="new user name"
            style={inputStyle}
          />
          <button onClick={createUser} disabled={busy || !newUserName.trim()} style={btnStyle}>
            create user
          </button>

          <span style={{ opacity: 0.6, marginLeft: 8 }}>or select:</span>
          <select
            value={userId || ""}
            onChange={(e) => setUserId(Number(e.target.value))}
            style={selectStyle}
          >
            <option value="" disabled>choose user…</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.display_name} (id {u.id})</option>
            ))}
          </select>
        </div>

        {/* upload */}
        <div style={cardStyle}>
          <h2 style={h2Style}>upload item</h2>
          <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <button onClick={uploadItem} disabled={busy || !userId || !file} style={btnStyle}>
              upload
            </button>
            {!userId && <span style={{ opacity: 0.6 }}>select or create a user first</span>}
          </div>
        </div>

        {/* wardrobe (first) */}
        <div style={{ ...cardStyle, paddingTop: 4 }}>
          <h2 style={h2Style}>wardrobe</h2>

          {items.length === 0 ? (
            <p style={{ opacity: 0.7, marginTop: 8 }}>no items yet.</p>
          ) : (
            <div style={gridStyle}>
              {items.map((it) => {
                const form = editMap[it.id] || {
                  category: "",
                  color: "",
                  season: "",
                  formality: "",
                  notes: "",
                  verified: false,
                };
                const expanded = !!expandMap[it.id];

                return (
                  <div key={it.id} style={itemCardStyle}>
                    <div style={imageWrapStyle}>
                      <img
                        src={imagesBase + it.stored_path}
                        alt={it.original_filename}
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                      />
                    </div>

                    <div style={{ marginTop: 10, fontSize: 13, opacity: 0.8 }}>{it.original_filename}</div>

                    {expanded ? (
                      <>
                        <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                          <TextBox label="category" value={form.category} onChange={(v) => updateEdit(it.id, "category", v)} />
                          <TextBox label="color" value={form.color} onChange={(v) => updateEdit(it.id, "color", v)} />
                          <TextBox label="season" value={form.season} onChange={(v) => updateEdit(it.id, "season", v)} />
                          <TextBox label="formality" value={form.formality} onChange={(v) => updateEdit(it.id, "formality", v)} />
                          <TextArea label="notes" value={form.notes} onChange={(v) => updateEdit(it.id, "notes", v)} />
                          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14 }}>
                            <input
                              type="checkbox"
                              checked={form.verified || false}
                              onChange={(e) => updateEdit(it.id, "verified", e.target.checked)}
                            />
                            verified
                          </label>
                        </div>

                        <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                          <button onClick={() => saveItem(it.id)} disabled={busy} style={btnStyle}>save</button>
                          <button onClick={() => setExpandMap((m) => ({ ...m, [it.id]: false }))} disabled={busy} style={btnSecondary}>cancel</button>
                          <button onClick={() => removeItem(it.id)} disabled={busy} style={{ ...btnStyle, background: "#2a1a1a", borderColor: "#563c3c" }}>delete</button>
                        </div>
                      </>
                    ) : (
                      <>
                        <div style={{ display: "grid", gap: 6, marginTop: 10, fontSize: 14 }}>
                          <FieldLine label="category" value={it.category} />
                          <FieldLine label="color" value={it.color} />
                          <FieldLine label="season" value={it.season} />
                          <FieldLine label="formality" value={it.formality} />
                          {it.notes ? <FieldLine label="notes" value={it.notes} /> : null}
                          <div style={{ opacity: 0.75 }}>{it.verified ? "verified ✅" : "not verified"}</div>
                        </div>

                        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                          <button onClick={() => setExpandMap((m) => ({ ...m, [it.id]: true }))} disabled={busy} style={btnStyle}>edit</button>
                          <button onClick={() => removeItem(it.id)} disabled={busy} style={{ ...btnStyle, background: "#2a1a1a", borderColor: "#563c3c" }}>delete</button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* make outfit placeholder (below wardrobe) */}
        <div style={cardStyle}>
          <h2 style={h2Style}>make outfit (coming soon)</h2>
          <button disabled style={{ ...btnStyle, opacity: 0.5, cursor: "not-allowed" }}>generate outfit</button>
          <p style={{ opacity: 0.7, marginTop: 8, fontSize: 14 }}>
            this will call an LLM with your wardrobe + request (e.g., “semi-formal dinner”), then propose a combo.
          </p>
        </div>

        {!!message && <div style={{ marginTop: 14, fontSize: 13, opacity: 0.75 }}>{message}</div>}
      </div>
    </div>
  );
}

/* small components */
function TextBox({ label, value, onChange }) {
  return (
    <label style={{ display: "grid", gap: 6, fontSize: 13 }}>
      <span style={{ opacity: 0.8 }}>{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={label} style={inputStyle} />
    </label>
  );
}

function TextArea({ label, value, onChange }) {
  return (
    <label style={{ display: "grid", gap: 6, fontSize: 13 }}>
      <span style={{ opacity: 0.8 }}>{label}</span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={label}
        rows={3}
        style={{ ...inputStyle, resize: "vertical" }}
      />
    </label>
  );
}

function FieldLine({ label, value }) {
  return (
    <div>
      <span style={{ opacity: 0.6, marginRight: 6 }}>{label}:</span>
      <span>{value || "—"}</span>
    </div>
  );
}

/* styles */
const pageStyle = {
  minHeight: "100vh",
  background: "#0f131c", // single color background
  color: "#eaeaea",
};

const containerStyle = {
  maxWidth: 1080,       // widen container; change to 1400 if you want even wider
  margin: "0 auto",     // center horizontally
  padding: 24,
};

const h2Style = { fontSize: 18, margin: 0, marginBottom: 8, opacity: 0.9 };

const btnStyle = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #2f3645",
  background: "#1b212e",
  color: "#eaeaea",
  cursor: "pointer",
};

const btnSecondary = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #2f3a55",
  background: "#1a2130",
  color: "#eaeaea",
  cursor: "pointer",
};

const inputStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid #2a2f3a",
  background: "#141821",
  color: "#eaeaea",
  minWidth: 200,
};

const selectStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid #2a2f3a",
  background: "#141821",
  color: "#eaeaea",
};

const cardStyle = {
  border: "1px solid #232938",
  background: "#11161f", // match page color family so page reads as one color
  borderRadius: 14,
  padding: 16,
  marginBottom: 16,
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", // fill available width
  gap: 16,
};

const itemCardStyle = {
  border: "1px solid #232938",
  background: "#0f131c",
  borderRadius: 14,
  padding: 12,
};

const imageWrapStyle = {
  width: "100%",
  aspectRatio: "1 / 1",
  overflow: "hidden",
  borderRadius: 12,
  background: "#11141b",
  border: "1px solid #232938",
};
