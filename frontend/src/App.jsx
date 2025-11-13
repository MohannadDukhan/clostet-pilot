import { Toaster } from "react-hot-toast";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import RootLayout from "./layouts/RootLayout";

import Home from "./pages/Home";
import About from "./pages/About";
import CreateUser from "./pages/CreateUser";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import NotFound from "./pages/NotFound";
import GenerateOutfit from "./pages/GenerateOutfit";


export default function App() {
<<<<<<< HEAD
  return (
    <BrowserRouter>
      <Toaster position="top-center" />
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="create-user" element={<CreateUser />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="upload" element={<Upload />} />
          <Route path="*" element={<NotFound />} />
          <Route path="generate" element={<GenerateOutfit />} />
        </Route>
      </Routes>
    </BrowserRouter>
=======
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

  // show/hide user edit form
  const [showEditUser, setShowEditUser] = useState(false);

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
            outfit_part: it.outfit_part || "",
            category: it.category || "",
            primary_color: it.primary_color || "",
            secondary_color: it.secondary_color || "",
            formality: it.formality || "",
            season: it.season || "",
            is_graphic: it.is_graphic || false,
            target_gender: it.target_gender || "",
            gender_source: it.gender_source || "",
            gender_confidence: it.gender_confidence || "",
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
      const { data } = await API.post("/users", { name: newUserName.trim(), gender: "male", city: "London" });
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
        [data.id]: {
          outfit_part: data.outfit_part || "",
          category: data.category || "",
          primary_color: data.primary_color || "",
          secondary_color: data.secondary_color || "",
          formality: data.formality || "",
          season: data.season || "",
          is_graphic: data.is_graphic || false,
          target_gender: data.target_gender || "",
          gender_source: data.gender_source || "",
          gender_confidence: data.gender_confidence || "",
          verified: data.verified || false,
        },
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
              <option key={u.id} value={u.id}>{u.name} (id {u.id})</option>
            ))}
          </select>
        </div>

        {/* user edit form toggle */}
        {userId && (
          <>
            <button
              onClick={() => setShowEditUser((v) => !v)}
              style={{ ...btnStyle, marginBottom: 10 }}
            >
              {showEditUser ? "close edit user" : "edit user"}
            </button>
            {showEditUser && (
              <div style={{ ...cardStyle, marginBottom: 20, marginTop: -8 }}>
                <h2 style={h2Style}>edit user</h2>
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                  <TextBox label="name" value={users.find(u => u.id === userId)?.name || ""} onChange={(v) => {
                    setUsers(us => us.map(u => u.id === userId ? { ...u, name: v } : u));
                  }} />
                  <TextBox label="gender" value={users.find(u => u.id === userId)?.gender || ""} onChange={(v) => {
                    setUsers(us => us.map(u => u.id === userId ? { ...u, gender: v } : u));
                  }} />
                  <TextBox label="city" value={users.find(u => u.id === userId)?.city || ""} onChange={(v) => {
                    setUsers(us => us.map(u => u.id === userId ? { ...u, city: v } : u));
                  }} />
                  <TextBox label="style_preferences" value={users.find(u => u.id === userId)?.style_preferences || ""} onChange={(v) => {
                    setUsers(us => us.map(u => u.id === userId ? { ...u, style_preferences: v } : u));
                  }} />
                  <button onClick={async () => {
                    const u = users.find(u => u.id === userId);
                    if (!u) return;
                    setBusy(true);
                    try {
                      const { data } = await API.patch(`/users/${userId}`, u);
                      setUsers(us => us.map(x => x.id === userId ? data : x));
                      setMessage("user updated");
                    } catch (e) {
                      setMessage("failed to update user");
                    } finally {
                      setBusy(false);
                    }
                  }} disabled={busy} style={btnStyle}>save</button>
                </div>
              </div>
            )}
          </>
        )}


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
                  outfit_part: "",
                  category: "",
                  primary_color: "",
                  secondary_color: "",
                  formality: "",
                  season: "",
                  is_graphic: false,
                  target_gender: "",
                  gender_source: "",
                  gender_confidence: "",
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
                          <TextBox label="outfit_part" value={form.outfit_part} onChange={(v) => updateEdit(it.id, "outfit_part", v)} />
                          <TextBox label="category" value={form.category} onChange={(v) => updateEdit(it.id, "category", v)} />
                          <TextBox label="primary_color" value={form.primary_color} onChange={(v) => updateEdit(it.id, "primary_color", v)} />
                          <TextBox label="secondary_color" value={form.secondary_color} onChange={(v) => updateEdit(it.id, "secondary_color", v)} />
                          <TextBox label="formality" value={form.formality} onChange={(v) => updateEdit(it.id, "formality", v)} />
                          <TextBox label="season" value={form.season} onChange={(v) => updateEdit(it.id, "season", v)} />
                          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14 }}>
                            <input
                              type="checkbox"
                              checked={form.is_graphic || false}
                              onChange={(e) => updateEdit(it.id, "is_graphic", e.target.checked)}
                            />
                            is_graphic
                          </label>
                          <TextBox label="target_gender" value={form.target_gender} onChange={(v) => updateEdit(it.id, "target_gender", v)} />
                          <TextBox label="gender_source" value={form.gender_source} onChange={(v) => updateEdit(it.id, "gender_source", v)} />
                          <TextBox label="gender_confidence" value={form.gender_confidence} onChange={(v) => updateEdit(it.id, "gender_confidence", v)} />
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
                          <FieldLine label="outfit_part" value={it.outfit_part} />
                          <FieldLine label="category" value={it.category} />
                          <FieldLine label="primary_color" value={it.primary_color} />
                          <FieldLine label="secondary_color" value={it.secondary_color} />
                          <FieldLine label="formality" value={it.formality} />
                          <FieldLine label="season" value={it.season} />
                          <FieldLine label="is_graphic" value={it.is_graphic ? "yes" : "no"} />
                          <FieldLine label="target_gender" value={it.target_gender} />
                          <FieldLine label="gender_source" value={it.gender_source} />
                          <FieldLine label="gender_confidence" value={it.gender_confidence} />

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
>>>>>>> dca7839e8ed1124303e3a3f3197617979d8bb027
  );
}
