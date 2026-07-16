/**
 * Copyright (c) 2026 Anthony Mugendi
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

(function () {
  /* ── Helpers ── */
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

  function renderStats(group, stats) {
    var available = stats && stats.available !== false;
    document.getElementById(group + "-stat-files").textContent = available
      ? stats.file_count
      : "—";
    document.getElementById(group + "-stat-dirs").textContent = available
      ? stats.directory_count
      : "—";
    document.getElementById(group + "-stat-size").textContent = available
      ? formatSize(stats.total_size)
      : "—";
    document.getElementById(group + "-stat-modified").textContent = available
      ? timeAgo(stats.modified)
      : "Not configured";
  }

  /* ── Load recursive content and uploaded-file totals ── */
  fetch("/" + prefix + "/stats")
    .then(function (r) {
      if (!r.ok) throw new Error("Statistics request failed");
      return r.json();
    })
    .then(function (data) {
      renderStats("content", data.content);
      renderStats("uploads", data.uploads);
    })
    .catch(function (err) {
      showFlash("Failed to load statistics: " + err.message, "error");
    });

  /* ── Load root directory listing ── */
  fetch("/" + prefix + "/list")
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      var entries = data.entries || [];
      var files = entries.filter(function (e) {
        return e.type === "file";
      });
      /* Recent files list (max 5) */
      var recent = files
        .sort(function (a, b) {
          return new Date(b.modified || 0) - new Date(a.modified || 0);
        })
        .slice(0, 5);

      var container = document.getElementById("recent-list");
      if (recent.length === 0) {
        container.innerHTML =
          '<p class="px-5 py-4 text-sm text-moose-400">No files yet. Create your first file!</p>';
        return;
      }

      container.innerHTML = recent
        .map(function (e) {
          var editUrl = "/" + prefix + "/edit/" + e.path;
          return (
            '<a href="' +
            editUrl +
            '" class="flex items-center justify-between px-5 py-3 hover:bg-moose-50 transition-colors">' +
            "<div>" +
            '<p class="text-sm font-medium text-moose-800">' +
            (e.title || e.name) +
            "</p>" +
            '<p class="text-xs text-moose-400">' +
            e.path +
            "</p>" +
            "</div>" +
            '<span class="text-xs text-moose-400">' +
            timeAgo(e.modified) +
            "</span>" +
            "</a>"
          );
        })
        .join("");
    })
    .catch(function (err) {
      showFlash("Failed to load dashboard data: " + err.message, "error");
    });
})();
