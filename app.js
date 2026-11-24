(function () {
  let selectedQueueIdx = -1;
  let foundPatientId = null;
  const DOCTORS_DATA = [
    { name: "Dr. Ibrahim Ashraf", field: "General Medicine", status: "Available" },
    { name: "Dr. Shawal Nadeem", field: "Cardiology", status: "Available" },
    { name: "Dr. Abubakar Naveed", field: "Orthopedics", status: "Available" },
    { name: "Dr. Aibtasam Ali", field: "Pediatrics", status: "Available" },
    { name: "Dr. Bisma Iqbal", field: "Neurology", status: "On Duty" },
    { name: "Dr. Ibrahim Ali", field: "ENT & Dermatology", status: "On Duty" },
  ];
  const appState = {
    kpis: {
      totalPatients: 0,
      waitingQueue: 0,
      activeAdmissions: 0,
      availableDoctors: 4,
    },
    doctors: DOCTORS_DATA,
    queue: [],
    patients: [],
    status: "Call Next Patient: Ready. Add Patient, Book Appointment, or Search by ID.",
  };
  function esc(v) {
    return String(v ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function updateClockDisplay() {
    const now = new Date();
    const d = now.toLocaleDateString("en-US", {
      month: "long",
      day: "2-digit",
      year: "numeric",
    });
    const t =
      now.toLocaleDateString("en-US", { weekday: "long" }) +
      ", " +
      now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    const el = document.getElementById("clockDisplay");
    if (el) el.innerHTML = `${d}<br>${t}`;
  }
  function getStatusPill(status) {
    if (status === "Completed") return `<span class="pill-status pill-completed">Completed</span>`;
    if (status === "Waiting") return `<span class="pill-status pill-waiting">Waiting</span>`;
    return `<span class="pill-status pill-progress">In Progress</span>`;
  }
  function setOutputText(msg) {
    const el = document.getElementById("outputMessage");
    if (!el) return;
    const i = msg.indexOf(":");
    if (i !== -1) {
      el.innerHTML = `<strong>${esc(msg.slice(0, i + 1))}</strong>${esc(msg.slice(i + 1))}`;
    } else {
      el.textContent = msg;
    }
  }
  function selectDoctorFromList(docObj) {
    if (!docObj) return;
    const selAdd = document.getElementById("selDoctor");
    const selAppt = document.getElementById("selApptDoctor");
    [selAdd, selAppt].forEach((sel) => {
      if (!sel) return;
      for (let i = 0; i < sel.options.length; i++) {
        const optVal = sel.options[i].value;
        if (optVal.indexOf(docObj.name) === 0 || optVal.indexOf(`${docObj.name} — ${docObj.field}`) === 0) {
          sel.selectedIndex = i;
          break;
        }
      }
    });
    appState.status = `Doctor Selected: ${docObj.name} — ${docObj.field} (${docObj.status})`;
    renderAll();
  }
  function renderAll() {
    const availDocsCount = (appState.doctors || DOCTORS_DATA).filter((d) => d.status === "Available").length;
    document.getElementById("statTotal").textContent = appState.kpis.totalPatients;
    document.getElementById("statQueue").textContent = appState.kpis.waitingQueue;
    document.getElementById("statAdmissions").textContent = appState.kpis.activeAdmissions;
    document.getElementById("statDoctors").textContent = availDocsCount || appState.kpis.availableDoctors;
    const docsBox = document.getElementById("doctorsListBox");
    const docs = appState.doctors && appState.doctors.length ? appState.doctors : DOCTORS_DATA;
    docsBox.innerHTML = docs
      .map((d, idx) => {
        const stCls = d.status === "On Duty" ? "doc-badge-duty" : "doc-badge-avail";
        return `<button type="button" class="doc-badge ${stCls}" data-didx="${idx}">${esc(d.name)} — ${esc(d.field)} (${esc(d.status)})</button>`;
      })
      .join("");
    docsBox.querySelectorAll(".doc-badge[data-didx]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = Number(btn.getAttribute("data-didx"));
        selectDoctorFromList(docs[idx]);
      });
    });

    const dl = document.getElementById("patientNameList");
    if (dl) {
      dl.innerHTML = appState.patients.map((p) => `<option value="${esc(p.name)}"></option>`).join("");
    }
    const qBox = document.getElementById("queueContainer");
    if (!appState.queue.length) {
      qBox.innerHTML = `<div class="queue-item"><span class="queue-meta">No appointments in queue</span></div>`;
      selectedQueueIdx = -1;
    } else {
      if (selectedQueueIdx >= appState.queue.length) selectedQueueIdx = -1;
      qBox.innerHTML = appState.queue
        .map((item, idx) => {
          const activeCls = idx === selectedQueueIdx ? "active-item" : "";
          return `
            <div class="queue-item ${activeCls}" data-qidx="${idx}">
              <span>${esc(item.name)}</span>
              <span class="queue-meta">${esc(item.wait)}</span>
            </div>
          `;
        })
        .join("");
      qBox.querySelectorAll(".queue-item[data-qidx]").forEach((row) => {
        row.addEventListener("click", () => {
          selectedQueueIdx = Number(row.getAttribute("data-qidx"));
          renderAll();
        });
      });
    }
    const tbody = document.getElementById("patientsBody");
    if (!appState.patients.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; color:#64748b; padding:22px;">
            No patients added yet. Fill "1. Add Patient" and click Add Patient.
          </td>
        </tr>
      `;
    } else {
      tbody.innerHTML = appState.patients
        .map((p) => {
          const hi = foundPatientId === p.id ? "found-row" : "";
          const docCol = p.field ? `${p.doctor} (${p.field})` : p.doctor;
          return `
            <tr class="${hi}" data-pid="${p.id}">
              <td>${esc(p.id)}</td>
              <td>${esc(p.name)}</td>
              <td>${esc(p.age)}</td>
              <td>${esc(p.disease)}</td>
              <td>${esc(docCol)}</td>
              <td>${getStatusPill(p.status)}</td>
              <td>${esc(p.prescription || "—")}</td>
            </tr>
          `;
        })
        .join("");
      tbody.querySelectorAll("tr[data-pid]").forEach((tr) => {
        tr.addEventListener("click", () => {
          const pid = Number(tr.getAttribute("data-pid"));
          foundPatientId = pid;
          const p = appState.patients.find((item) => item.id === pid);
          if (p) {
            const addrStr = p.address ? ` | Address: ${p.address}` : "";
            appState.status = `Selected Patient: Patient ID ${p.id} | ${p.name} (${p.age}y)${addrStr} — ${p.disease} | ${p.doctor} (${p.field || "General"})`;
          }
          renderAll();
        });
      });
    }
    if (appState.status) {
      setOutputText(appState.status);
    }
  }
  function sendToServer(endpoint, payload) {
    fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!d) return;
        if (d.kpis) appState.kpis = d.kpis;
        if (Array.isArray(d.patients)) appState.patients = d.patients;
        if (Array.isArray(d.queue)) appState.queue = d.queue;
        if (Array.isArray(d.doctors) && d.doctors.length) appState.doctors = d.doctors;
        if (d.status) appState.status = d.status;
        renderAll();
      })
      .catch(() => {});
  }
  function onAddPatientClick() {
    const rawId = document.getElementById("inpId").value.trim();
    const name = document.getElementById("inpName").value.trim();
    const rawAge = document.getElementById("inpAge").value.trim();
    const address = document.getElementById("inpRate").value.trim();
    const disease = document.getElementById("inpDisease").value.trim();
    const docChoice = document.getElementById("selDoctor").value;
    if (!rawId || !name || !rawAge || !disease) {
      appState.status = "Add Patient: Please fill Patient ID, Patient Name, Age, and Disease.";
      renderAll();
      return;
    }
    const pid = Number(rawId);
    const age = Number(rawAge);
    const splitDoc = docChoice.split(" (");
    const docName = splitDoc[0] || "Dr. Ibrahim Ashraf";
    const docField = splitDoc[1] ? splitDoc[1].replace(")", "") : "General Medicine";
    const record = {
      id: pid,
      name,
      age,
      disease,
      doctor: docName,
      field: docField,
      address,
      rate: address,
      status: "In Progress",
      prescription: `${docField} Care`,
    };
    const existing = appState.patients.findIndex((p) => p.id === pid);
    if (existing >= 0) {
      appState.patients[existing] = record;
    } else {
      appState.patients.push(record);
      appState.kpis.activeAdmissions += 1;
    }
    appState.kpis.totalPatients = appState.patients.length;
    foundPatientId = pid;
    const addrStr = address ? ` | Address: ${address}` : "";
    appState.status = `Add Patient: Patient ID ${pid} | Name: ${name} | Age: ${age}${addrStr} | Disease: ${disease} | ${docName} (${docField})`;
    document.getElementById("inpId").value = "";
    document.getElementById("inpName").value = "";
    document.getElementById("inpAge").value = "";
    document.getElementById("inpRate").value = "";
    document.getElementById("inpDisease").value = "";
    renderAll();
    sendToServer("/api/add-patient", { id: pid, name, age, address, rate: address, disease, doctor: docChoice });
  }
  function onBookApptClick() {
    const input = document.getElementById("inpApptName");
    const name = input.value.trim();
    const docChoice = document.getElementById("selApptDoctor").value;
    if (!name) {
      appState.status = "Book Appt: Please type a patient name first.";
      renderAll();
      return;
    }
    appState.queue.push({ name, wait: "" });
    appState.queue = appState.queue.map((item, idx) => ({
      name: item.name,
      wait: idx === 0 ? "Next Up" : `#${idx + 1} in line`,
    }));
    appState.kpis.waitingQueue = appState.queue.length;
    appState.status = `Book Appt: Booked appointment for ${name} (${docChoice}) | Waiting Queue: ${appState.queue.length}`;
    input.value = "";
    renderAll();
    sendToServer("/api/book-appointment", { name, doctor: docChoice });
  }
  function onCallNextClick() {
    if (!appState.queue.length) {
      appState.status = "Call Next Patient: No pending appointments in queue.";
      renderAll();
      return;
    }
    const nextItem = appState.queue.shift();
    appState.queue = appState.queue.map((item, idx) => ({
      name: item.name,
      wait: idx === 0 ? "Next Up" : `#${idx + 1} in line`,
    }));
    appState.kpis.waitingQueue = appState.queue.length;

    appState.patients.forEach((p) => {
      if (p.name.toLowerCase() === nextItem.name.toLowerCase()) {
        p.status = "Completed";
      }
    });
    appState.status = `Call Next Patient: Now attending ${nextItem.name} | Remaining in queue: ${appState.queue.length}`;
    renderAll();
    sendToServer("/api/call-next", {});
  }
  function onCancelApptClick() {
    if (selectedQueueIdx < 0 || selectedQueueIdx >= appState.queue.length) {
      appState.status = "Cancel Appointment: Please click an appointment in the queue first.";
      renderAll();
      return;
    }
    const targetIdx = selectedQueueIdx;
    const removed = appState.queue.splice(targetIdx, 1)[0];
    selectedQueueIdx = -1;
    appState.queue = appState.queue.map((item, idx) => ({
      name: item.name,
      wait: idx === 0 ? "Next Up" : `#${idx + 1} in line`,
    }));
    appState.kpis.waitingQueue = appState.queue.length;
    appState.status = `Cancel Appointment: Cancelled appointment for ${removed.name}.`;
    renderAll();
    sendToServer("/api/cancel-appointment", { index: targetIdx });
  }
  function onSearchClick() {
    const raw = document.getElementById("inpSearchId").value.trim();
    if (!raw) {
      appState.status = "Search Patient: Please enter a Patient ID.";
      renderAll();
      return;
    }
    const pid = Number(raw);
    const found = appState.patients.find((p) => p.id === pid);
    if (found) {
      foundPatientId = found.id;
      const addrStr = found.address ? ` | Address: ${found.address}` : "";
      appState.status = `Search Patient: Found -> Patient ID ${found.id} | ${found.name} (${found.age}y)${addrStr} | ${found.disease} | ${found.doctor} (${found.field || "General"})`;
    } else {
      foundPatientId = null;
      appState.status = `Search Patient: Patient with ID ${pid} not found.`;
    }
    renderAll();
    sendToServer("/api/search-patient", { id: pid });
  }
  function onClearSearchClick() {
    const sInp = document.getElementById("inpSearchId");
    if (sInp) sInp.value = "";
    foundPatientId = null;
    appState.status = "Search Patient: Cleared search filter and row highlight.";
    renderAll();
  }
  function init() {
    document.getElementById("btnAddPatient")?.addEventListener("click", onAddPatientClick);
    document.getElementById("btnBookAppt")?.addEventListener("click", onBookApptClick);
    document.getElementById("btnCallNextSide")?.addEventListener("click", onCallNextClick);
    document.getElementById("btnCallNextQueue")?.addEventListener("click", onCallNextClick);
    document.getElementById("btnCancelAppt")?.addEventListener("click", onCancelApptClick);
    document.getElementById("btnSearchPatient")?.addEventListener("click", onSearchClick);
    document.getElementById("btnClearSearch")?.addEventListener("click", onClearSearchClick);
    document.getElementById("btnSearchIcon")?.addEventListener("click", onSearchClick);
    const sInp = document.getElementById("inpSearchId");
    if (sInp) {
      sInp.addEventListener("keydown", (e) => {
        if (e.key === "Enter") onSearchClick();
      });
    }
    updateClockDisplay();
    setInterval(updateClockDisplay, 30000);
    renderAll();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
(function setupAgeNumberOnlyNotice() {
      var ageInput = document.getElementById("inpAge");
      var ageError = document.getElementById("ageErrorMsg");
      if (!ageInput || !ageError) return;

      var hideTimer = null;

      function showOnlyNumberAllowed() {
        ageError.classList.add("show");
        if (hideTimer) clearTimeout(hideTimer);
        hideTimer = setTimeout(function () {
          ageError.classList.remove("show");
        }, 2000);
      }

      function hideOnlyNumberAllowed() {
        ageError.classList.remove("show");
        if (hideTimer) {
          clearTimeout(hideTimer);
          hideTimer = null;
        }
      }

      ageInput.addEventListener("keydown", function (e) {
        if (e.ctrlKey || e.metaKey || e.altKey) return;
        var controlKeys = [
          "Backspace", "Delete", "Tab", "Escape", "Enter",
          "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"
        ];
        if (controlKeys.indexOf(e.key) !== -1) return;

        if (!/^[0-9]$/.test(e.key)) {
          e.preventDefault();
          showOnlyNumberAllowed();
        } else {
          hideOnlyNumberAllowed();
        }
      });

      ageInput.addEventListener("paste", function (e) {
        var pasted = (e.clipboardData || window.clipboardData).getData("text") || "";
        if (!/^[0-9]+$/.test(pasted.trim())) {
          e.preventDefault();
          showOnlyNumberAllowed();
        } else {
          hideOnlyNumberAllowed();
        }
      });

      ageInput.addEventListener("input", function () {
        if (/^[0-9]*$/.test(ageInput.value)) {
          hideOnlyNumberAllowed();
        } else {
          ageInput.value = ageInput.value.replace(/[^0-9]/g, "");
          showOnlyNumberAllowed();
        }
      });

      ageInput.addEventListener("blur", hideOnlyNumberAllowed);
    })();

(function setupPatientIdAndNameValidationNotice() {
  var idInput = document.getElementById("inpId");
  var idError = document.getElementById("idErrorMsg");
  var nameInput = document.getElementById("inpName");
  var nameError = document.getElementById("nameErrorMsg");

  function bindNotice(inputEl, errorEl, matcher, sanitizer, msg, ms) {
    if (!inputEl || !errorEl) return;
    var timer = null;
    function show() {
      errorEl.textContent = msg;
      errorEl.classList.add("show");
      inputEl.classList.add("input-invalid");
      if (timer) clearTimeout(timer);
      timer = setTimeout(function () {
        errorEl.classList.remove("show");
      }, ms || 2200);
    }
    function hide() {
      errorEl.classList.remove("show");
      inputEl.classList.remove("input-invalid");
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
    }
    inputEl.addEventListener("keydown", function (e) {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      var navKeys = [
        "Backspace", "Delete", "Tab", "Escape", "Enter",
        "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"
      ];
      if (navKeys.indexOf(e.key) !== -1) return;
      if (!matcher.test(e.key)) {
        e.preventDefault();
        show();
      } else {
        hide();
      }
    });
    inputEl.addEventListener("paste", function (e) {
      var pasted = ((e.clipboardData || window.clipboardData).getData("text") || "").trim();
      if (!pasted || !sanitizer(pasted)) {
        e.preventDefault();
        show();
      } else {
        hide();
      }
    });
    inputEl.addEventListener("input", function () {
      if (sanitizer(inputEl.value)) {
        hide();
      } else {
        inputEl.value = inputEl.value.replace(new RegExp(matcher.source.replace(/^\^|\$$/g, ""), "g"), "");
        show();
      }
    });
    inputEl.addEventListener("blur", hide);
  }

  bindNotice(
    idInput,
    idError,
    /^[0-9]$/,
    function (v) { return /^[0-9]*$/.test(v); },
    "Only number allowed",
    2000
  );

  bindNotice(
    nameInput,
    nameError,
    /^[A-Za-z ]$/,
    function (v) { return /^[A-Za-z ]*$/.test(v); },
    "Only put alphabetic not numeric value",
    2200
  );
})();
(function setupAuthGate() {
    var AUTH_USERS_KEY = "hms_auth_users_v1";
    var AUTH_SESSION_KEY = "hms_auth_session_v1";

    function loadUsers() {
      var defaults = [
        {
          name: "HMS Administrator",
          identifier: "admin@hms.local",
          username: "admin",
          password: "password123"
        }
      ];
      try {
        var raw = localStorage.getItem(AUTH_USERS_KEY);
        if (!raw) return defaults;
        var parsed = JSON.parse(raw);
        return Array.isArray(parsed) && parsed.length ? parsed : defaults;
      } catch (e) {
        return defaults;
      }
    }

    function saveUsers(users) {
      try {
        localStorage.setItem(AUTH_USERS_KEY, JSON.stringify(users));
      } catch (e) {}
    }

    function getSession() {
      try {
        var raw = localStorage.getItem(AUTH_SESSION_KEY);
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    }

    function setSession(user) {
      try {
        if (user) {
          localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(user));
        } else {
          localStorage.removeItem(AUTH_SESSION_KEY);
        }
      } catch (e) {}
    }

    function setAuthError(elId, msg) {
      var el = document.getElementById(elId);
      if (!el) return;
      el.textContent = msg;
      el.classList.add("show");
    }

    function clearAuthError(elId) {
      var el = document.getElementById(elId);
      if (!el) return;
      el.classList.remove("show");
    }

    function syncAuthUI() {
      var session = getSession();
      var badge = document.getElementById("activeUserBadge");
      var logoutBtn = document.getElementById("btnLogout");
      if (session && (session.name || session.identifier)) {
        document.body.classList.remove("auth-locked");
        if (badge) {
          badge.textContent = session.name || session.identifier;
          badge.style.display = "inline-flex";
        }
        if (logoutBtn) {
          logoutBtn.style.display = "inline-flex";
        }
      } else {
        document.body.classList.add("auth-locked");
        if (badge) badge.style.display = "none";
        if (logoutBtn) logoutBtn.style.display = "none";
      }
    }

    window.switchAuthMode = function (mode) {
      var isSignUp = mode === "signup";
      document.getElementById("tabSignIn").classList.toggle("active", !isSignUp);
      document.getElementById("tabSignUp").classList.toggle("active", isSignUp);
      document.getElementById("formSignIn").classList.toggle("active", !isSignUp);
      document.getElementById("formSignUp").classList.toggle("active", isSignUp);
      clearAuthError("loginErrorMsg");
      clearAuthError("signupErrorMsg");
    };

    window.handleSignIn = function (event) {
      if (event) event.preventDefault();
      clearAuthError("loginErrorMsg");
      var idInput = document.getElementById("loginEmail").value.trim().toLowerCase();
      var passInput = document.getElementById("loginPassword").value;
      if (!idInput || !passInput) {
        setAuthError("loginErrorMsg", "Please enter email/username and password");
        return;
      }
      var users = loadUsers();
      var matched = users.find(function (u) {
        var uId = String(u.identifier || "").toLowerCase();
        var uName = String(u.username || "").toLowerCase();
        return (uId === idInput || uName === idInput) && u.password === passInput;
      });
      if (!matched) {
        setAuthError("loginErrorMsg", "Invalid credentials (Default: admin@hms.local / password123)");
        return;
      }
      setSession({ name: matched.name, identifier: matched.identifier });
      document.getElementById("loginPassword").value = "";
      syncAuthUI();
      setOutput("Signed In", "Welcome, " + matched.name);
    };

    window.handleSignUp = function (event) {
      if (event) event.preventDefault();
      clearAuthError("signupErrorMsg");
      var nameVal = document.getElementById("signupName").value.trim();
      var emailVal = document.getElementById("signupEmail").value.trim();
      var passVal = document.getElementById("signupPassword").value;
      if (!nameVal || !/^[A-Za-z ]+$/.test(nameVal)) {
        setAuthError("signupErrorMsg", "Only put alphabetic not numeric value");
        return;
      }
      if (!emailVal) {
        setAuthError("signupErrorMsg", "Please enter email or username");
        return;
      }
      if (!passVal || passVal.length < 6) {
        setAuthError("signupErrorMsg", "Password must be at least 6 characters");
        return;
      }
      var users = loadUsers();
      var duplicate = users.some(function (u) {
        return String(u.identifier || "").toLowerCase() === emailVal.toLowerCase();
      });
      if (duplicate) {
        setAuthError("signupErrorMsg", "Account with this email/username already exists");
        return;
      }
      var newUser = {
        name: nameVal,
        identifier: emailVal,
        username: emailVal.split("@")[0],
        password: passVal
      };
      users.push(newUser);
      saveUsers(users);
      setSession({ name: newUser.name, identifier: newUser.identifier });
      document.getElementById("signupPassword").value = "";
      syncAuthUI();
      setOutput("Account Created", "Signed in as " + newUser.name);
    };

    window.logoutNow = function () {
      setSession(null);
      syncAuthUI();
      window.switchAuthMode("signin");
    };

    // Block any global function call if user is not signed in
    var guardedFns = [
      "addPatientNow", "bookApptNow", "callNextNow", "cancelApptNow",
      "searchPatientNow", "clearSearchNow", "runAiChatbot", "runAiAppointment",
      "runAiReportSummary", "runAiDoctorAssistant", "runAiAnalytics",
      "runDsPriorityBook", "runDsPriorityCall", "runDsBstLookup",
      "runDsHashLookup", "runDsSortByAge", "runDsStackTop", "runDsWardGraph"
    ];
    guardedFns.forEach(function (fnName) {
      var orig = window[fnName];
      if (typeof orig === "function") {
        window[fnName] = function () {
          if (!getSession()) {
            syncAuthUI();
            return;
          }
          return orig.apply(this, arguments);
        };
      }
    });

    syncAuthUI();
  })();