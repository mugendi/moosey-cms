(function () {
  var config = window.mooseyListConfig || {};
  var prefix = config.prefix || "admin";
  var subpath = config.subpath || "";
  var entryList = null;

  function requestJson(url, options, fallbackMessage) {
    return fetch(url, options).then(function (response) {
      if (response.ok) return response.json();
      return response.json().then(function (data) {
        throw new Error(data.detail || fallbackMessage);
      });
    });
  }

  window.openNewFileModal = function () {
    var input = document.getElementById("new-file-name");
    var directory = document.getElementById("new-file-directory");
    input.value = "";
    directory.textContent = subpath ? subpath + "/" : "/";
    directory.title = directory.textContent;
    document.getElementById("new-file-modal").classList.remove("hidden");
    input.focus();
  };

  window.openNewDirModal = function () {
    var input = document.getElementById("new-dir-name");
    var directory = document.getElementById("new-dir-directory");
    input.value = "";
    directory.textContent = subpath ? subpath + "/" : "/";
    directory.title = directory.textContent;
    document.getElementById("new-dir-modal").classList.remove("hidden");
    input.focus();
  };

  window.closeModal = function (id) {
    document.getElementById(id).classList.add("hidden");
  };

  function entryIcon(entry) {
    if (entry.type === "directory") {
      return '<svg class="w-5 h-5 text-moose-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>';
    }
    if (entry.name.endsWith(".md")) {
      return '<svg class="w-5 h-5 text-moose-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>';
    }
    return '<svg class="w-5 h-5 text-moose-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/></svg>';
  }

  function entryName(entry) {
    var link = document.createElement("a");
    link.className =
      "entry-name text-moose-800 hover:text-moose-600 font-medium transition-colors";
    if (entry.type === "directory") {
      var path = subpath ? subpath + "/" + entry.name : entry.name;
      link.href = "/" + prefix + "/browse/" + path;
      link.textContent = entry.name + "/";
    } else {
      link.href = "/" + prefix + "/edit/" + entry.path;
      link.textContent = entry.name;
    }
    return link;
  }
  function directoriesFirstSort(itemA, itemB, options) {
    var valuesA = itemA.values();
    var valuesB = itemB.values();
    var typeA = Number(valuesA["entry-size"]) === -1 ? 0 : 1;
    var typeB = Number(valuesB["entry-size"]) === -1 ? 0 : 1;

    if (typeA !== typeB) {
      // List.js reverses custom comparator results for descending sorts.
      return (typeA - typeB) * (options.order === "desc" ? -1 : 1);
    }

    var valueA = valuesA[options.valueName];
    var valueB = valuesB[options.valueName];
    if (options.valueName !== "entry-name") {
      return Number(valueA) - Number(valueB);
    }
    return String(valueA).localeCompare(String(valueB), undefined, {
      numeric: true,
      sensitivity: "base",
    });
  }

  function sortEntries(valueName, order) {
    entryList.sort(valueName, {
      order: order,
      sortFunction: directoriesFirstSort,
    });
  }

  function refreshEntryList() {
    if (typeof List === "undefined") return;

    if (!entryList) {
      entryList = new List("content-list", {
        listClass: "list",
        page: 20,
        pagination: true,
        valueNames: [
          "entry-name",
          "entry-title",
          { name: "entry-size", attr: "data-sort-value" },
          { name: "entry-modified", attr: "data-sort-value" },
        ],
        fuzzySearch: {
          searchClass: "fuzzy-search",
          threshold: 0.4,
          multiSearch: true,
        },
      });
    } else {
      entryList.reIndex();
    }

    var selection = document.getElementById("content-sort").value.split(":");
    sortEntries(selection[0], selection[1]);
  }

  function renderEntries(entries) {
    var tbody = document.getElementById("entries-body");
    tbody.replaceChildren();

    if (!entries || entries.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="4" class="px-5 py-6 text-center text-moose-400">This directory is empty.</td></tr>';
      return;
    }

    entries.forEach(function (entry) {
      var row = document.createElement("tr");
      var modified = Date.parse(entry.modified) || 0;
      var size = entry.type === "directory" ? -1 : entry.size;
      row.className = "hover:bg-moose-50 transition-colors";
      row.innerHTML =
        '<td class="px-5 py-3"><div class="flex items-center gap-3">' +
        entryIcon(entry) +
        '<div data-entry-name></div></div></td>' +
        '<td class="entry-size px-5 py-3 text-right text-moose-400" data-sort-value="' +
        size +
        '">' +
        (entry.type === "directory" ? "—" : formatSize(entry.size)) +
        '</td><td class="entry-modified px-5 py-3 text-right text-moose-400" data-sort-value="' +
        modified +
        '">' +
        timeAgo(entry.modified) +
        '</td><td class="px-5 py-3 text-right"><button type="button" class="text-moose-400 hover:text-red-600 transition-colors" title="Delete"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg></button></td>';

      var nameContainer = row.querySelector("[data-entry-name]");
      nameContainer.appendChild(entryName(entry));
      if (entry.title && entry.type !== "directory") {
        var title = document.createElement("span");
        title.className = "entry-title block text-xs text-moose-400";
        title.textContent = entry.title;
        nameContainer.appendChild(title);
      }
      row.querySelector("button").addEventListener("click", function () {
        openDeleteModal(entry.path, entry.type, entry.name);
      });
      tbody.appendChild(row);
    });

    refreshEntryList();
  }

  window.openDeleteModal = function (path, type, name) {
    document.getElementById("delete-target-path").value = path;
    document.getElementById("delete-target-type").value = type;
    document.getElementById("delete-target-name").textContent = name;
    document.getElementById("delete-modal").classList.remove("hidden");
  };

  window.confirmDelete = function () {
    var path = document.getElementById("delete-target-path").value;
    var type = document.getElementById("delete-target-type").value;
    var endpoint = type === "directory" ? "/dir/" : "/file/";
    requestJson("/" + prefix + endpoint + path, { method: "DELETE" }, "Delete failed")
      .then(function () {
        showFlash("Deleted " + path, "success");
        closeModal("delete-modal");
        loadDirectory(subpath);
      })
      .catch(function (error) {
        showFlash(error.message, "error");
      });
  };

  window.createFile = function () {
    var name = document.getElementById("new-file-name").value.trim();
    if (!name) return showFlash("Enter a file name", "error");
    if (/[\\/]/.test(name))
      return showFlash("Enter a file name without folders", "error");
    name = name.replace(/(?:\.md)+$/i, "").trim();
    if (!name || name === "." || name === "..")
      return showFlash("Enter a valid file name", "error");
    name += ".md";
    var path = subpath ? subpath + "/" + name : name;
    requestJson(
      "/" + prefix + "/file/" + path,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frontmatter: {}, body: "" }),
      },
      "Create failed"
    )
      .then(function () {
        showFlash("Created " + name, "success");
        closeModal("new-file-modal");
        loadDirectory(subpath);
      })
      .catch(function (error) {
        showFlash(error.message, "error");
      });
  };

  window.createDir = function () {
    var name = document.getElementById("new-dir-name").value.trim();
    if (!name) return showFlash("Enter a folder name", "error");
    if (/[\\/]/.test(name))
      return showFlash("Enter a folder name without parent folders", "error");
    if (name === "." || name === "..")
      return showFlash("Enter a valid folder name", "error");
    var path = subpath ? subpath + "/" + name : name;
    requestJson("/" + prefix + "/dir/" + path, { method: "POST" }, "Create failed")
      .then(function () {
        showFlash("Created folder " + name, "success");
        closeModal("new-dir-modal");
        loadDirectory(subpath);
      })
      .catch(function (error) {
        showFlash(error.message, "error");
      });
  };

  function loadDirectory(path) {
    var url = path ? "/" + prefix + "/list/" + path : "/" + prefix + "/list";
    requestJson(url, undefined, "Failed to load directory")
      .then(function (data) {
        renderEntries(data.entries);
      })
      .catch(function (error) {
        showFlash("Failed to load directory: " + error.message, "error");
      });
  }

  window.loadDirectory = loadDirectory;
  document
    .getElementById("new-file-name")
    .addEventListener("keydown", function (event) {
      if (event.key !== "Enter") return;
      event.preventDefault();
      window.createFile();
    });
  document
    .getElementById("new-dir-name")
    .addEventListener("keydown", function (event) {
      if (event.key !== "Enter") return;
      event.preventDefault();
      window.createDir();
    });
  document
    .getElementById("content-sort")
    .addEventListener("change", function (event) {
      if (!entryList) return;
      var selection = event.target.value.split(":");
      sortEntries(selection[0], selection[1]);
    });
  document
    .getElementById("content-page-size")
    .addEventListener("change", function (event) {
      if (!entryList) return;
      entryList.page = Number(event.target.value);
      entryList.show(1, entryList.page);
    });
  loadDirectory(subpath);
})();
