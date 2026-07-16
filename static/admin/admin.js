/* ================================================================
   admin.js — Shared JavaScript utilities for Moosey CMS admin UI.
   Included in base.html; available to all admin templates.
   ================================================================ */

const sidebarBreakpoint = window.matchMedia("(min-width: 768px)");
const sidebarStorageKey = "moosey-admin-sidebar-collapsed";

function updateSidebarToggle(expanded) {
  const toggle = document.getElementById("sidebar-toggle");
  if (!toggle) return;
  toggle.setAttribute("aria-expanded", String(expanded));
  toggle.setAttribute(
    "aria-label",
    expanded ? "Collapse sidebar" : "Expand sidebar"
  );
}

function setMobileSidebarOpen(open) {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  if (!sidebar) return;

  sidebar.classList.toggle("-translate-x-full", !open);
  overlay && overlay.classList.toggle("hidden", !open);
  document.body.classList.toggle("overflow-hidden", open);
  updateSidebarToggle(open);
}

function setDesktopSidebarCollapsed(collapsed, persist) {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  sidebar.dataset.collapsed = String(collapsed);
  sidebar.querySelectorAll("[data-sidebar-label]").forEach(function (label) {
    label.classList.toggle("md:hidden", collapsed);
  });

  const header = sidebar.querySelector("[data-sidebar-header]");
  const nav = sidebar.querySelector("[data-sidebar-nav]");
  header && header.classList.toggle("md:justify-center", collapsed);
  header && header.classList.toggle("md:px-2", collapsed);
  nav && nav.classList.toggle("md:px-2", collapsed);

  updateSidebarToggle(!collapsed);
  if (persist !== false) {
    try {
      localStorage.setItem(sidebarStorageKey, String(collapsed));
    } catch (error) {
      // Storage may be unavailable in privacy-restricted contexts.
    }
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  if (sidebarBreakpoint.matches) {
    setDesktopSidebarCollapsed(sidebar.dataset.collapsed !== "true");
  } else {
    setMobileSidebarOpen(sidebar.classList.contains("-translate-x-full"));
  }
}

function getStoredSidebarCollapsed() {
  try {
    return localStorage.getItem(sidebarStorageKey) === "true";
  } catch (error) {
    return false;
  }
}

function syncSidebarToBreakpoint() {
  const overlay = document.getElementById("sidebar-overlay");
  document.body.classList.remove("overflow-hidden");
  overlay && overlay.classList.add("hidden");

  if (sidebarBreakpoint.matches) {
    setDesktopSidebarCollapsed(getStoredSidebarCollapsed(), false);
  } else {
    setMobileSidebarOpen(false);
  }
}

function initializeSidebar() {
  syncSidebarToBreakpoint();

  const sidebar = document.getElementById("sidebar");
  sidebar &&
    sidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (!sidebarBreakpoint.matches) setMobileSidebarOpen(false);
      });
    });
}

document.addEventListener("DOMContentLoaded", initializeSidebar);
if (sidebarBreakpoint.addEventListener) {
  sidebarBreakpoint.addEventListener("change", syncSidebarToBreakpoint);
} else {
  sidebarBreakpoint.addListener(syncSidebarToBreakpoint);
}

function formatSize(bytes) {
  if (bytes === null || bytes === undefined) return "—";
  if (bytes === 0) return "0 B";
  var units = ["B", "KB", "MB", "GB"];
  var i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return bytes.toFixed(i ? 1 : 0) + " " + units[i];
}

function timeAgo(isoStr) {
  if (!isoStr) return "—";
  var diff = (Date.now() - new Date(isoStr).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return Math.floor(diff / 60) + "m ago";
  if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
  return Math.floor(diff / 86400) + "d ago";
}

/* -----------------------------------------------------------
   showFlash(message, type, duration) — display a toast-style
   notification in the flash container.

   type: 'success' | 'error' | 'info'  (default: 'info')
   duration: milliseconds to show (default: 3000)
   ----------------------------------------------------------- */
function showFlash(message, type, duration, action) {
  type = type || "info";
  duration = duration || 4500;

  const container = document.getElementById("flash-container");
  if (!container) return;

  const growlMeta = {
    success: { title: "Success", icon: "✓" },
    error: { title: "Error", icon: "!" },
    warning: { title: "Warning", icon: "!" },
    info: {
      title: document.body.dataset.adminBrand || "CMS",
      icon: "i",
    },
  };
  const meta = growlMeta[type] || growlMeta.info;

  const el = document.createElement("div");
  el.className = "moose-growl";
  el.setAttribute("role", type === "error" ? "alert" : "status");

  const icon = document.createElement("div");
  icon.className = "moose-growl__icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = meta.icon;

  const copy = document.createElement("div");
  const title = document.createElement("p");
  title.className = "moose-growl__title";
  title.textContent = meta.title;
  const text = document.createElement("p");
  text.className = "moose-growl__message";
  text.textContent = String(message);
  copy.append(title, text);

  if (action && typeof action.onClick === "function") {
    const actionButton = document.createElement("button");
    actionButton.type = "button";
    actionButton.className = "moose-growl__action";
    actionButton.textContent = action.label || "Undo";
    actionButton.addEventListener("click", function () {
      action.onClick();
      dismiss();
    });
    copy.appendChild(actionButton);
  }

  const close = document.createElement("button");
  close.type = "button";
  close.className = "moose-growl__close";
  close.setAttribute("aria-label", "Dismiss notification");
  close.textContent = "×";

  let timer;
  function dismiss() {
    if (!el.isConnected || el.classList.contains("is-leaving")) return;
    clearTimeout(timer);
    el.classList.add("is-leaving");
    el.addEventListener(
      "animationend",
      function () {
        el.remove();
      },
      { once: true }
    );
    setTimeout(function () {
      el.remove();
    }, 300);
  }
  close.addEventListener("click", dismiss);
  el.addEventListener("mouseenter", function () {
    clearTimeout(timer);
  });
  el.addEventListener("mouseleave", function () {
    timer = setTimeout(dismiss, duration);
  });

  el.append(icon, copy, close);
  container.prepend(el);
  timer = setTimeout(dismiss, duration);
}


/* -----------------------------------------------------------
   Escape key handler — close any open modal when Escape is
   pressed.  Modals must have the class 'modal-overlay'.
   ----------------------------------------------------------- */
document.addEventListener("keydown", function (e) {
  if (e.key !== "Escape") return;
  if (!sidebarBreakpoint.matches) setMobileSidebarOpen(false);
  document.querySelectorAll(".modal-overlay").forEach(function (m) {
    m.classList.add("hidden");
  });
});
