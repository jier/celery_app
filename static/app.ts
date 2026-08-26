declare const supabase: any;

const SUPABASE_URL = "http://127.0.0.1:54321";
const SUPABASE_ANON_KEY = "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH";
const API_BASE = window.location.origin;

const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

type Page = "login" | "signup" | "upload" | "jobs" | "products";

let currentPage: Page = "login";
let session: { access_token: string } | null = null;

const main = document.getElementById("main")!;
const nav = document.getElementById("nav")!;

// --- Init ---

sb.auth.getSession().then((res: any) => {
  if (res.data.session) {
    session = res.data.session;
    renderNav();
    showPage("jobs");
  } else {
    renderNav();
    showPage("login");
  }
});

sb.auth.onAuthStateChange((_event: string, newSession: any) => {
  session = newSession;
  if (newSession) renderLoggedInNav(); else renderNav();
  if (!newSession) showPage("login");
});

// --- Navigation ---

function renderNav() {
  if (session) renderLoggedInNav();
  else renderGuestNav();
}

function renderGuestNav() {
  nav.innerHTML = "";
  addNavButton("Login", "login");
  addNavButton("Sign Up", "signup");
  activateNav();
}

function renderLoggedInNav() {
  nav.innerHTML = "";
  addNavButton("Upload", "upload");
  addNavButton("Jobs", "jobs");
  addNavButton("Products", "products");
  const logoutBtn = document.createElement("button");
  logoutBtn.className = "btn btn-secondary";
  logoutBtn.textContent = "Logout";
  logoutBtn.onclick = () => { sb.auth.signOut(); };
  nav.appendChild(logoutBtn);
  activateNav();
}

function addNavButton(label: string, page: Page) {
  const btn = document.createElement("button");
  btn.textContent = label;
  btn.dataset.page = page;
  btn.onclick = () => showPage(page);
  nav.appendChild(btn);
}

function activateNav() {
  nav.querySelectorAll("button[data-page]").forEach((b) => {
    const el = b as HTMLButtonElement;
    el.classList.toggle("active", el.dataset.page === currentPage);
  });
}

function showPage(page: Page) {
  currentPage = page;
  activateNav();
  main.innerHTML = "";
  switch (page) {
    case "login": renderAuth("login"); break;
    case "signup": renderAuth("signup"); break;
    case "upload": renderUpload(); break;
    case "jobs": renderJobs(); break;
    case "products": renderProducts(); break;
  }
}

// --- Auth ---

function renderAuth(mode: "login" | "signup") {
  const html = `
    <div class="card">
      <h2>${mode === "login" ? "Login" : "Create Account"}</h2>
      <div class="form-group">
        <label>Email</label>
        <input type="email" id="auth-email" placeholder="demo@example.com" />
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" id="auth-password" placeholder="Password (min 8 chars)" />
      </div>
      <div id="auth-error"></div>
      <button class="btn btn-primary" id="auth-submit">${mode === "login" ? "Login" : "Sign Up"}</button>
      <div class="auth-toggle">
        ${mode === "login"
          ? 'No account? <a id="auth-switch">Create one</a>'
          : 'Have an account? <a id="auth-switch">Login</a>'}
      </div>
    </div>
  `;
  main.innerHTML = html;

  document.getElementById("auth-switch")!.onclick = () => showPage(mode === "login" ? "signup" : "login");
  document.getElementById("auth-submit")!.onclick = async () => {
    const email = (document.getElementById("auth-email") as HTMLInputElement).value;
    const password = (document.getElementById("auth-password") as HTMLInputElement).value;
    const errEl = document.getElementById("auth-error")!;
    errEl.innerHTML = "";

    const res = mode === "login"
      ? await sb.auth.signInWithPassword({ email, password })
      : await sb.auth.signUp({ email, password });

    if (res.error) {
      errEl.innerHTML = `<div class="error">${res.error.message}</div>`;
      return;
    }
    if (res.data.user && !res.data.session) {
      errEl.innerHTML = `<div class="success">Check your email for a confirmation link (local dev skips this).</div>`;
    }
  };
}

// --- Upload ---

function renderUpload() {
  main.innerHTML = `
    <div class="card">
      <h2>Upload Inventory CSV</h2>
      <p style="color:#666;margin-bottom:1rem;">CSV columns: sku, name, price, quantity</p>
      <input type="file" id="file-input" accept=".csv" />
      <div id="upload-error"></div>
      <div id="upload-success" style="display:none"></div>
      <button class="btn btn-primary" id="upload-btn" style="margin-top:0.75rem;">Upload &amp; Import</button>
      <div id="upload-progress" style="display:none;margin-top:0.75rem;color:#666;">Uploading...</div>
    </div>
  `;

  document.getElementById("upload-btn")!.onclick = async () => {
    const fileInput = document.getElementById("file-input") as HTMLInputElement;
    const errEl = document.getElementById("upload-error")!;
    const okEl = document.getElementById("upload-success")!;
    const progEl = document.getElementById("upload-progress")!;
    errEl.innerHTML = ""; okEl.style.display = "none";

    if (!fileInput.files?.length) {
      errEl.innerHTML = `<div class="error">Please select a CSV file.</div>`;
      return;
    }

    progEl.style.display = "block";
    const form = new FormData();
    form.append("file", fileInput.files[0]);

    const res = await fetch(`${API_BASE}/imports`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session!.access_token}` },
      body: form,
    });
    progEl.style.display = "none";

    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      errEl.innerHTML = `<div class="error">Upload failed: ${detail.detail || res.statusText}</div>`;
      return;
    }

    const job = await res.json();
    okEl.style.display = "block";
    okEl.innerHTML = `<div class="success">Import created! <a href="#" id="goto-job">View job ${job.id.slice(0, 8)}</a></div>`;
    document.getElementById("goto-job")!.onclick = (e) => { e.preventDefault(); showPage("jobs"); };
    fileInput.value = "";
  };
}

// --- Jobs ---

let jobUnsub: (() => void) | null = null;

async function renderJobs() {
  if (session === null) return;
  if (jobUnsub) { jobUnsub(); jobUnsub = null; }

  main.innerHTML = `
    <div class="card">
      <h2>Import Jobs</h2>
      <table><thead><tr><th>Filename</th><th>Status</th><th>Progress</th><th>Created</th></tr></thead>
      <tbody id="jobs-tbody"></tbody></table>
      <div id="jobs-empty" style="display:none;color:#666;margin-top:1rem;">No imports yet. Upload a CSV to get started.</div>
    </div>
  `;

  const load = async () => {
    const res = await fetch(`${API_BASE}/imports`, { headers: { Authorization: `Bearer ${session!.access_token}` } });
    // Note: GET /imports would need a list endpoint. For now we subscribe to Realtime.
  };

  // Subscribe to all import_jobs changes for this user
  sb
    .channel("import-jobs")
    .on("postgres_changes", { event: "*", schema: "public", table: "import_jobs" },
      () => loadAllJobs(),
    )
    .subscribe();

  jobUnsub = () => sb.removeChannel(sb.channel("import-jobs"));
  await loadAllJobs();
}

async function loadAllJobs() {
  if (session === null) return;
  const res = await fetch(`${API_BASE}/imports/list`, {
    headers: { Authorization: `Bearer ${session!.access_token}` },
  });
  if (!res.ok) return;
  const jobs: any[] = await res.json();
  const tbody = document.getElementById("jobs-tbody");
  const empty = document.getElementById("jobs-empty");
  if (!tbody || !empty) return;

  if (!jobs.length) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";
  tbody.innerHTML = jobs.map((j: any) => {
    const pct = j.total_rows > 0 ? Math.round((j.processed_rows / j.total_rows) * 100) : 0;
    return `<tr>
      <td>${escapeHtml(j.filename)}</td>
      <td><span class="status-badge status-${j.status}">${j.status}</span></td>
      <td>
        ${j.processed_rows}/${j.total_rows} (${j.failed_rows} failed)
        <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
      </td>
      <td>${j.created_at ? new Date(j.created_at).toLocaleString() : "—"}</td>
    </tr>`;
  }).join("");
}

// --- Products ---

async function renderProducts() {
  if (session === null) return;
  main.innerHTML = `<div class="card"><h2>Products</h2><div id="products-loading">Loading...</div></div>`;

  const res = await fetch(`${API_BASE}/imports/list`, {  // Placeholder: need a /products endpoint
    headers: { Authorization: `Bearer ${session!.access_token}` },
  });
  // For now, show a message that this is coming
  main.innerHTML = `
    <div class="card">
      <h2>Products</h2>
      <p style="color:#666;margin-top:0.5rem;">
        Your imported products will appear here. Upload a CSV and import it on the Jobs tab.
      </p>
      <p style="color:#666;">
        Products are upserted by SKU — re-uploading the same SKU updates quantity and price.
      </p>
    </div>
  `;
}

// --- Helpers ---

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}
