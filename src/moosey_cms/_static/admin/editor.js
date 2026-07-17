(function () {
  var isNew = !filePath;
  var tuiEditor = null; /* TUI Editor instance */
  var guifierInstance = null; /* Guifier instance */
  var guifierSnapshot = null; /* Last metadata state, used for deletion undo */
  var guifierObserver = null;
  var guifierCheckTimer = null;
  var suppressGuifierObserver = false;
  var frontmatterData = {}; /* Current frontmatter data */
  var activeTab = "content"; /* Current active tab */
  var previewStyle = "tab"; /* Split-screen by default */
  var isSaving = false;
  var savedBody = null;
  var savedFrontmatter = null;
  var toggle = document.getElementById("preview-style-toggle");

  /* ================================================================
       Dynamic editor height — fill viewport after header
       ================================================================ */
  function calcEditorHeight() {
    var container = document.getElementById("tui-editor");
    if (!container) return "500px";
    var rect = container.getBoundingClientRect();
    var available =
      window.innerHeight - rect.top - 16; /* 16px bottom padding */
    return Math.max(available, 300) + "px"; /* minimum 300px */
  }

  function applyEditorHeight() {
    if (tuiEditor) {
      var editorEl = document.getElementById("content-editor");
      var contentLoadingEl = document.getElementById("content-loading");
      contentLoadingEl.classList.add("hidden");
      editorEl.classList.remove("hidden");

      var h = calcEditorHeight();

      tuiEditor.setHeight(h);
      // show button
      toggle.classList.remove("hidden");
      toggle.classList.add("inline-flex");
    }
    var guifierEl = document.getElementById("guifier-container");
    if (guifierEl) {
      guifierEl.style.minHeight = h;
    }
  }

  /* ================================================================
       Tab switching
       ================================================================ */
  var editorTabs = ["content", "metadata", "history"];

  function activeTabStorageKey() {
    return "moosey-editor-tab:" + prefix + ":" + (filePath || "new");
  }

  function persistActiveTab() {
    try {
      sessionStorage.setItem(activeTabStorageKey(), activeTab);
    } catch (error) {
      // Storage may be unavailable in privacy-restricted browser contexts.
    }
  }

  function restoreActiveTab() {
    var storedTab;
    try {
      storedTab = sessionStorage.getItem(activeTabStorageKey());
    } catch (error) {
      return;
    }
    if (editorTabs.indexOf(storedTab) === -1) return;
    if (storedTab === "history" && !filePath) return;
    window.switchTab(storedTab);
  }

  window.switchTab = function (tabName) {
    activeTab = tabName;
    persistActiveTab();

    /* Update tab buttons */
    document.querySelectorAll(".tab-button").forEach(function (btn) {
      btn.classList.remove(
        "active",
        "border-moose-700",
        "text-moose-900",
        "bg-moose-50"
      );
      btn.classList.add("border-transparent", "text-moose-500");
    });

    var activeBtn = document.getElementById("tab-" + tabName);
    activeBtn.classList.add(
      "active",
      "border-moose-700",
      "text-moose-900",
      "bg-moose-50"
    );
    activeBtn.classList.remove("border-transparent", "text-moose-500");

    /* Update tab panels */
    document.querySelectorAll(".tab-panel").forEach(function (panel) {
      panel.classList.add("hidden");
    });

    var activePanel = document.getElementById("panel-" + tabName);
    activePanel.classList.remove("hidden");

    /* Refresh TUI Editor when switching to content tab */
    if (tabName === "content" && tuiEditor) {
      applyEditorHeight();
    }

    /* Load history when switching to history tab */
    if (tabName === "history") {
      loadHistory();
    }
  };

  window.togglePreviewStyle = function () {
    if (!tuiEditor) return;
    previewStyle = previewStyle === "tab" ? "vertical" : "tab";

    tuiEditor.changePreviewStyle(previewStyle);

    var label = document.getElementById("preview-style-label");
    var splitIcon = document.getElementById("preview-style-split-icon");
    var tabbedIcon = document.getElementById("preview-style-tabbed-icon");
    var isTabbed = previewStyle === "tab";
    if (toggle) {
      toggle.setAttribute("aria-pressed", String(isTabbed));
      toggle.title = isTabbed
        ? "Switch to split preview"
        : "Switch to tabbed preview";
    }
    if (label) label.textContent = isTabbed ? "Split View" : "Tabbed View";
    if (splitIcon) splitIcon.classList.toggle("hidden", !isTabbed);
    if (tabbedIcon) tabbedIcon.classList.toggle("hidden", isTabbed);
  };

  /* ================================================================
       TUI Editor initialization
       ================================================================ */
  function initTuiEditor() {
    var container = document.getElementById("tui-editor");
    var fallback = document.getElementById("fallback-editor");

    if (typeof toastui !== "undefined" && toastui.Editor) {
      try {
        function makeToolbarButton(name, tooltip, svg, handler) {
          var button = document.createElement("button");
          button.type = "button";
          button.className = "toastui-editor-toolbar-icons";
          button.style.backgroundImage = "none";
          button.style.cursor = "pointer";
          button.setAttribute("aria-label", tooltip);
          button.innerHTML = svg;
          button.addEventListener("click", handler);
          return { name: name, tooltip: tooltip, el: button };
        }

        function changeLineIndent(outdent) {
          if (!tuiEditor || !tuiEditor.isMarkdownMode()) {
            showFlash(
              "Indent and outdent are available in Markdown mode",
              "info"
            );
            return;
          }

          var selection = tuiEditor.getSelection();
          var lines = tuiEditor.getMarkdown().split("\n");
          var startLine = selection[0][0];
          var endLine = selection[1][0];
          if (selection[1][1] === 0 && endLine > startLine) endLine -= 1;

          var selectedLines = lines.slice(startLine, endLine + 1);
          var changed = selectedLines
            .map(function (line) {
              return outdent ? line.replace(/^(\t| {1,4})/, "") : "    " + line;
            })
            .join("\n");
          var rangeStart = [startLine, 0];
          var rangeEnd = [endLine, lines[endLine].length];

          tuiEditor.replaceSelection(changed, rangeStart, rangeEnd);
          tuiEditor.setSelection(rangeStart, [
            endLine,
            changed.split("\n").pop().length,
          ]);
          tuiEditor.focus();
        }

        // Add custom "Add File" button (only if static dir is configured)
        var fpModal = document.getElementById("file-picker-modal");
        if (fpModal) {
          var fpBtn = document.createElement("button");
          fpBtn.className = "toastui-editor-toolbar-icons !-mx-1 !my-0 !pl-1";
          fpBtn.style.cursor = "pointer";
          fpBtn.style.backgroundImage = "none";
          fpBtn.innerHTML =
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>';
          fpBtn.addEventListener("click", function () {
            openFilePickerModal();
          });
          //   toolbar[toolbar.length - 1].push(
          //     {
          //     name: "addFile",
          //     tooltip: "Add file (image, PDF, video, etc.)",
          //     el: fpBtn,
          //   }
          // );
        }

        var toolbar = [
          ["heading", "bold", "italic", "strike"],
          
          ["ul", "ol", "task", "indent", "outdent"],
          [
            {
              name: "addFile",
              tooltip: "Add file (image, PDF, video, etc.)",
              el: fpBtn,
            },
            "table",
            "link",
          ],
          ["hr", "quote"],
          ["code", "codeblock"],
        ];

        var availablePlugins = [
          toastui.Editor.plugin.chart,
          toastui.Editor.plugin.codeSyntaxHighlight,
          toastui.Editor.plugin.colorSyntax,
          toastui.Editor.plugin.tableMergedCell,
          toastui.Editor.plugin.uml,
        ].filter(function (plugin) {
          return typeof plugin === "function";
        });

        tuiEditor = new toastui.Editor({
          el: container,
          height: calcEditorHeight(),
          initialEditType: "markdown",
          previewStyle: previewStyle,
          usageStatistics: false,
          toolbarItems: toolbar,
          plugins: availablePlugins,
        });

        fallback.classList.add("hidden");
        container.classList.remove("hidden");
        return;
      } catch (e) {
        console.warn("TUI Editor init failed, falling back to textarea:", e);
      }
    }

    /* Fallback: plain textarea */
    container.classList.add("hidden");
    fallback.classList.remove("hidden");
    var previewToggle = document.getElementById("preview-style-toggle");
    if (previewToggle) previewToggle.disabled = true;
  }



  function prepareForGuifier(obj) {
    if (obj === null || typeof obj !== "object") {
      val = typecast(obj)
      return val
    }
    if (Array.isArray(obj)) return obj.map(prepareForGuifier);
    var out = {};
    for (var k in obj) {
      out[k] = prepareForGuifier(obj[k]);
    }
    return out;
  }

  function metadataFieldPath(id, field) {
    return String(field.path || id).split(".");
  }

  function hasMetadataPath(data, path) {
    var current = data;
    for (var i = 0; i < path.length; i++) {
      if (!current || typeof current !== "object" || !(path[i] in current))
        return false;
      current = current[path[i]];
    }
    return true;
  }

  function metadataDefault(field) {
    if (field.default_factory === "today") {
      var now = new Date();
      var local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
      return local.toISOString().slice(0, 10);
    }
    return cloneData(field.default === undefined ? "" : field.default);
  }

  function setMetadataPath(
    data,
    path,
    value,
    replaceScalarParent,
    scalarParentKey
  ) {
    var current = data;
    for (var i = 0; i < path.length - 1; i++) {
      if (current[path[i]] === undefined) current[path[i]] = {};
      if (
        replaceScalarParent &&
        (current[path[i]] === null ||
          typeof current[path[i]] !== "object" ||
          Array.isArray(current[path[i]]))
      ) {
        var parentValue = current[path[i]];
        current[path[i]] = {};
        if (
          scalarParentKey &&
          parentValue !== null &&
          parentValue !== undefined &&
          typeof parentValue !== "object"
        ) {
          current[path[i]][scalarParentKey] = parentValue;
        }
      }
      if (
        !current[path[i]] ||
        typeof current[path[i]] !== "object" ||
        Array.isArray(current[path[i]])
      )
        return false;
      current = current[path[i]];
    }
    current[path[path.length - 1]] = value;
    return true;
  }

  function highlightAddedMetadataField(path, attempt) {
    attempt = attempt || 0;
    var container = document.getElementById("guifier-container");
    var key = path[path.length - 1];
    var walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    var textNode;
    var target = null;
    while ((textNode = walker.nextNode())) {
      if (textNode.nodeValue.trim() !== key) continue;
      var candidate = textNode.parentElement;
      for (
        var i = 0;
        candidate && candidate !== container && i < 5;
        i++, candidate = candidate.parentElement
      ) {
        var rect = candidate.getBoundingClientRect();
        if (
          candidate.querySelector("input, textarea, select, button") &&
          rect.height >= 28 &&
          rect.height <= 320
        ) {
          target = candidate;
          break;
        }
      }
      if (target) break;
    }
    if (!target && attempt < 12) {
      setTimeout(function () {
        highlightAddedMetadataField(path, attempt + 1);
      }, 50);
      return;
    }
    if (!target) return;
    target.classList.remove("moose-field-added");
    void target.offsetWidth;
    target.classList.add("moose-field-added");
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(function () {
      target.classList.remove("moose-field-added");
    }, 1500);
  }

  function encodePath(path) {
    return String(path || "")
      .split("/")
      .map(encodeURIComponent)
      .join("/");
  }

  function applyFileIcon(iconElement, className, fontSize) {
    var tokens = String(className || "")
      .split(/\s+/)
      .filter(function (token) {
        return /^[a-zA-Z0-9_-]+$/.test(token);
      });
    if (!tokens.length) return;
    var icon = document.createElement("i");
    icon.classList.add.apply(icon.classList, tokens);
    if (fontSize) icon.style.fontSize = fontSize;
    iconElement.replaceChildren(icon);
  }

  function fpLoadDirectory(subpath) {
    var url =
      "/" +
      prefix +
      fpStaticRoute +
      (subpath ? "/" + encodePath(subpath) : "");
    fetch(url)
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        fpRenderGrid(data.entries);
      })
      .catch(function (error) {
        showFlash("Could not load files: " + error.message, "error");
      });
  }

  function fpRenderGrid(entries) {
    var grid = document.getElementById("fp-grid");
    var empty = document.getElementById("fp-empty");
    grid.replaceChildren();

    if (!entries || entries.length === 0) {
      empty.classList.remove("hidden");
      return;
    }
    empty.classList.add("hidden");

    entries.forEach(function (entry) {
      var card = document.createElement("div");
      var type = entry.type === "directory" ? "directory" : "file";
      var mime = String(entry.mime_type || "");
      var name = String(entry.name || "");
      var path = String(entry.path || "");
      var assetUrl =
        "/" + prefix + fpStaticRoute + "/" + encodePath(path);
      card.className =
        "fp-card border border-moose-200 rounded-lg p-3 cursor-pointer hover:border-moose-500 hover:shadow transition-all";
      card.dataset.path = path;
      card.dataset.url = type === "directory" ? "" : assetUrl;
      card.dataset.type = type;
      card.dataset.mime = mime;
      card.dataset.name = name;
      card.dataset.size = String(Number(entry.size) || 0);
      card.addEventListener("click", function () {
        window.fpSelect(card);
      });
      card.addEventListener("dblclick", function () {
        window.fpSelect(card);
        window.fpInsertSelected();
      });

      if (type === "directory") {
        var folderIcon = document.createElement("div");
        folderIcon.className = "text-3xl text-center mb-2";
        folderIcon.textContent = "📁";
        card.appendChild(folderIcon);
      } else if (mime.indexOf("image/") === 0) {
        var imageWrapper = document.createElement("div");
        imageWrapper.className =
          "aspect-square mb-2 overflow-hidden rounded bg-moose-100 flex items-center justify-center";
        var image = document.createElement("img");
        image.src = assetUrl;
        image.alt = "";
        image.className = "max-h-full max-w-full object-contain";
        image.loading = "lazy";
        imageWrapper.appendChild(image);
        card.appendChild(imageWrapper);
      } else {
        var fileIcon = document.createElement("div");
        fileIcon.className = "fp-icon text-3xl text-center mb-2";
        fileIcon.textContent = "📄";
        card.appendChild(fileIcon);
        if (typeof FileIcons !== "undefined") {
          FileIcons.getClass(name).then(function (className) {
            applyFileIcon(fileIcon, className);
          });
        }
      }

      var label = document.createElement("div");
      label.className = "text-xs text-moose-700 truncate text-center";
      label.title = name;
      label.textContent = name;
      card.appendChild(label);
      grid.appendChild(card);
    });
  }


  window.addMetadataField = function (id) {
    var field = (frontmatterRegistry.fields || {})[id];
    if (!field || field.hidden) return;
    var data = readGuifierData() || cloneData(frontmatterData);
    var path = metadataFieldPath(id, field);
    
    if (hasMetadataPath(data, path)) {
      showFlash((field.label || id) + " already exists", "info");
      return;
    }
    if (
      !setMetadataPath(
        data,
        path,
        metadataDefault(field),
        field.replace_scalar_parent === true,
        field.scalar_parent_key
      )
    ) {
      showFlash(
        "Cannot add " + (field.label || id) + ": its parent is not an object",
        "error"
      );
      return;
    }
    setFrontmatter(data);
    closeMetadataFieldMenu(false);
    highlightAddedMetadataField(path);
    renderMetadataFieldMenu(
      document.getElementById("metadata-field-search").value
    );
    showFlash((field.label || id) + " added", "success");
  };

  window.renderMetadataFieldMenu = function (query) {
    var list = document.getElementById("metadata-field-list");
    if (!list) return;
    var data = readGuifierData() || frontmatterData || {};
    var needle = String(query || "")
      .trim()
      .toLowerCase();
    var grouped = {};
    Object.keys(frontmatterRegistry.fields || {})
      .sort(function (left, right) {
        var leftField = frontmatterRegistry.fields[left];
        var rightField = frontmatterRegistry.fields[right];
        var leftOrder = Number(leftField.order);
        var rightOrder = Number(rightField.order);
        if (!Number.isFinite(leftOrder)) leftOrder = 9007199254740991;
        if (!Number.isFinite(rightOrder)) rightOrder = 9007199254740991;
        if (leftOrder !== rightOrder) return leftOrder - rightOrder;
        return String(leftField.label || left).localeCompare(
          String(rightField.label || right)
        );
      })
      .forEach(function (id) {
      var field = frontmatterRegistry.fields[id];
      if (field.hidden) return;
      var haystack = [id, field.label, field.description, field.group]
        .join(" ")
        .toLowerCase();
      if (needle && haystack.indexOf(needle) === -1) return;
      var group = field.group || "Other";
      (grouped[group] = grouped[group] || []).push({ id: id, field: field });
      });
    list.innerHTML = "";
    Object.keys(grouped).forEach(function (group) {
      var heading = document.createElement("p");
      heading.className =
        "px-2 pb-1 pt-2 text-xs font-bold uppercase tracking-wide text-moose-500";
      heading.textContent = group;
      list.appendChild(heading);
      grouped[group].forEach(function (item) {
        var exists = hasMetadataPath(
          data,
          metadataFieldPath(item.id, item.field)
        );
        var button = document.createElement("button");
        button.type = "button";
        button.disabled = exists;
        button.className =
          "mb-1 block w-full rounded-lg px-3 py-2 text-left hover:bg-moose-100 disabled:cursor-not-allowed disabled:opacity-45";
        var label = document.createElement("span");
        label.className = "block text-sm font-semibold text-moose-900";
        label.textContent = item.field.label || item.id;
        var detail = document.createElement("span");
        detail.className = "block text-xs text-moose-500";
        detail.textContent =
          (item.field.path || item.id) +
          " · " +
          (exists
            ? "Already added"
            : item.field.description || item.field.type);
        button.append(label, detail);
        button.addEventListener("click", function () {
          window.addMetadataField(item.id);
        });
        list.appendChild(button);
      });
    });
    if (!list.children.length)
      list.innerHTML =
        '<p class="p-4 text-center text-sm text-moose-500">No supported fields found.</p>';
  };

  function closeMetadataFieldMenu(returnFocus) {
    var menu = document.getElementById("metadata-field-menu");
    var toggle = document.getElementById("metadata-field-toggle");
    if (!menu || !toggle || menu.classList.contains("hidden")) return;
    menu.classList.add("hidden");
    toggle.setAttribute("aria-expanded", "false");
    if (returnFocus) toggle.focus();
  }

  window.toggleMetadataFieldMenu = function () {
    var menu = document.getElementById("metadata-field-menu");
    var toggle = document.getElementById("metadata-field-toggle");
    var opening = menu.classList.contains("hidden");
    menu.classList.toggle("hidden", !opening);
    toggle.setAttribute("aria-expanded", String(opening));
    if (opening) {
      renderMetadataFieldMenu("");
      setTimeout(function () {
        document.getElementById("metadata-field-search").focus();
      }, 0);
    }
  };

  function cloneData(value) {
    return JSON.parse(JSON.stringify(value === undefined ? {} : value));
  }

  function readGuifierData() {
    if (!guifierInstance) return null;
    try {
      return JSON.parse(guifierInstance.getData("json"));
    } catch (e) {
      return null;
    }
  }

  function countDataNodes(value) {
    if (value === null || typeof value !== "object") return 1;
    if (Array.isArray(value)) {
      return (
        1 +
        value.reduce(function (total, item) {
          return total + countDataNodes(item);
        }, 0)
      );
    }
    return (
      1 +
      Object.keys(value).reduce(function (total, key) {
        return total + 1 + countDataNodes(value[key]);
      }, 0)
    );
  }

  function restoreGuifierSnapshot(snapshot) {
    if (!guifierInstance) return;
    suppressGuifierObserver = true;
    guifierSnapshot = cloneData(snapshot);
    frontmatterData = cloneData(snapshot);
    guifierInstance.setData(prepareForGuifier(snapshot), "js");
    setTimeout(function () {
      suppressGuifierObserver = false;
    }, 0);
    showFlash("Metadata deletion undone", "success");
  }

  function checkGuifierForDeletion() {
    if (suppressGuifierObserver) return;
    var current = readGuifierData();
    if (current === null) return;

    if (
      guifierSnapshot !== null &&
      countDataNodes(current) < countDataNodes(guifierSnapshot)
    ) {
      var previous = cloneData(guifierSnapshot);
      showFlash("A metadata item was removed", "info", 7000, {
        label: "Undo",
        onClick: function () {
          restoreGuifierSnapshot(previous);
        },
      });
    }
    guifierSnapshot = cloneData(current);
    frontmatterData = cloneData(current);
    updateStats();
  }

  function observeGuifier(container) {
    if (guifierObserver) guifierObserver.disconnect();
    guifierObserver = new MutationObserver(function () {
      clearTimeout(guifierCheckTimer);
      guifierCheckTimer = setTimeout(checkGuifierForDeletion, 40);
    });
    guifierObserver.observe(container, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  /* ================================================================
       Guifier initialization
       ================================================================ */
  function initGuifier(data) {
    var container = document.getElementById("guifier-container");

    if (typeof Guifier !== "undefined") {
      try {
        guifierInstance = new Guifier({
          elementSelector: "#guifier-container",
          data: prepareForGuifier(data || {}),
          dataType: "js",
        });
        guifierSnapshot = cloneData(data || {});
        observeGuifier(container);
        return;
      } catch (e) {
        console.warn("Guifier init failed:", e);
      }
    }

    /* Fallback: simple key-value editor */
    container.innerHTML =
      '<p class="text-moose-400 text-sm italic">Guifier not loaded. Using basic editor.</p>';
  }

  /* ================================================================
       Editor helpers
       ================================================================ */
  function getEditorValue() {
    if (tuiEditor) return tuiEditor.getMarkdown();
    return document.getElementById("fallback-editor").value;
  }

  function updateStats() {
    var contentCount = document.getElementById("content-char-count");
    var metadataCount = document.getElementById("metadata-prop-count");
    if (contentCount) contentCount.textContent = getEditorValue().length;
    var metadata = readGuifierData();
    if (metadata === null) metadata = frontmatterData;
    if (metadataCount) metadataCount.textContent = Object.keys(metadata || {}).length;
    updateSaveButton();
  }

  function serializedFrontmatter() {
    return JSON.stringify(getFrontmatter() || {});
  }

  function rememberSavedState() {
    savedBody = getEditorValue();
    savedFrontmatter = serializedFrontmatter();
    updateSaveButton();
  }

  function updateSaveButton() {
    var buttons = document.querySelectorAll('[id^="btn-save"]');
    if (!buttons.length) return;
    var changed =
      savedBody !== null &&
      (getEditorValue() !== savedBody ||
        serializedFrontmatter() !== savedFrontmatter);
    buttons.forEach(function (button) {
      button.disabled = isSaving || !changed;
    });
  }

  function setEditorValue(text) {
    if (tuiEditor) {
      tuiEditor.setMarkdown(text || "");
    } else {
      document.getElementById("fallback-editor").value = text || "";
    }
    updateStats();
  }

  function getFrontmatter() {
    if (guifierInstance) {
      try {
        var jsonString = guifierInstance.getData("json");
        return JSON.parse(jsonString);
      } catch (e) {
        console.warn("Guifier getData failed:", e);
      }
    }
    return frontmatterData;
  }

  function setFrontmatter(data) {
    frontmatterData = data || {};
    guifierSnapshot = cloneData(frontmatterData);
    setApproximateHistoryCount(frontmatterData.version);
    if (guifierInstance) {
      try {
        suppressGuifierObserver = true;
        guifierInstance.setData(prepareForGuifier(frontmatterData), "js");
        setTimeout(function () {
          suppressGuifierObserver = false;
        }, 0);
        renderMetadataFieldMenu(
          document.getElementById("metadata-field-search").value
        );
      } catch (e) {
        console.warn("Guifier setData failed:", e);
      }
    }
    updateStats();
  }

  /* ================================================================
       Load file content
       ================================================================ */
  var _frontmatterRaw = null; // raw YAML text from original file (preserves comments)

  function loadFile(path) {
    if (!path) return;

    fetch("/" + prefix + "/file/" + encodePath(path))
      .then(function (r) {
        if (!r.ok) throw new Error("File not found");
        return r.json();
      })
      .then(function (data) {
        setEditorValue(data.body || "");
        setFrontmatter(data.frontmatter || {});
        _frontmatterRaw = data.frontmatter_raw || null;
        rememberSavedState();
      })
      .catch(function (err) {
        showFlash("Could not load file: " + err.message, "error");
      });
  }

  /* ================================================================
       Save file
       ================================================================ */
  function setSaveState(saving) {
    isSaving = saving;
    updateSaveButton();
    document.querySelectorAll('[id^="btn-save"]').forEach(function (button) {
      button.setAttribute("aria-busy", String(saving));
    });
    document.querySelectorAll('[id^="save-label"]').forEach(function (label) {
      label.textContent = saving ? "Saving…" : "Save";
    });
    document.querySelectorAll('[id^="save-icon"]').forEach(function (icon) {
      icon.classList.toggle("hidden", saving);
    });
    document.querySelectorAll('[id^="save-spinner"]').forEach(function (spinner) {
      spinner.classList.toggle("hidden", !saving);
    });
  }

  window.saveFile = function () {
    if (isSaving) return;
    var savePath = filePath;
    if (isNew) {
      var input = document.getElementById("file-path-input");
      savePath = input ? input.value.trim() : "";
      if (!savePath) {
        showFlash("Enter a file path", "error");
        return;
      }
    }

    var body = getEditorValue();
    var meta = getFrontmatter();

    var payload = { frontmatter: meta, body: body };
    /* Send original raw YAML back so server preserves comments */
    if (_frontmatterRaw) {
      payload.frontmatter_raw = _frontmatterRaw;
    }

    var method = isNew ? "POST" : "PUT";
    setSaveState(true);

    fetch("/" + prefix + "/file/" + encodePath(savePath), {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) {
        if (!r.ok)
          return r.json().then(function (d) {
            throw new Error(d.detail || "Save failed");
          });
        return r.json();
      })
      .then(function (result) {
        showFlash("Saved!", "success");
        rememberSavedState();
        historyCountIsExact = false;
        setApproximateHistoryCount(result.version);
        if (isNew && result.path) {
          /* Update URL so subsequent saves use PUT */
          filePath = result.path;
          persistActiveTab();
          isNew = false;
          enableHistoryTab();
          window.history.replaceState(
            {},
            "",
            "/" + prefix + "/edit/" + encodePath(result.path)
          );
          /* Reload to get frontmatter_raw for the newly created file */
          loadFile(result.path);
        }
      })
      .catch(function (err) {
        showFlash("Save failed: " + err.message, "error");
      })
      .finally(function () {
        setSaveState(false);
      });
  };

  /* ================================================================
       Version History
       ================================================================ */
  var historyData = [];
  var historyCountIsExact = false;

  function setApproximateHistoryCount(version) {
    if (historyCountIsExact) return;
    var numericVersion = Number(version);
    if (!Number.isInteger(numericVersion) || numericVersion < 1) return;
    var count = document.getElementById("history-count");
    if (count) count.textContent = "~" + numericVersion;
  }

  function enableHistoryTab() {
    var btn = document.getElementById("tab-history");
    if (btn) {
      btn.disabled = false;
      btn.removeAttribute("title");
    }
  }

  function loadHistory() {
    if (!filePath) return;
    var loading = document.getElementById("history-loading");
    var empty = document.getElementById("history-empty");
    var list = document.getElementById("history-list");

    if (loading) loading.classList.remove("hidden");
    if (empty) empty.classList.add("hidden");
    if (list) list.replaceChildren();
    var limitNote = document.getElementById("history-limit-note");
    if (limitNote) limitNote.classList.add("hidden");

    fetch("/" + prefix + "/file-history/" + encodePath(filePath))
      .then(function (r) {
        if (!r.ok) throw new Error("Failed to load history");
        return r.json();
      })
      .then(function (data) {
        historyData = data.history || [];
        historyCountIsExact = true;
        renderHistory();
      })
      .catch(function (err) {
        if (loading) loading.classList.add("hidden");
        showFlash("Could not load history: " + err.message, "error");
      });
  }

  function renderHistory() {
    var loading = document.getElementById("history-loading");
    var empty = document.getElementById("history-empty");
    var list = document.getElementById("history-list");
    var count = document.getElementById("history-count");

    if (loading) loading.classList.add("hidden");
    if (count) count.textContent = historyData.length;

    if (!historyData.length) {
      if (empty) empty.classList.remove("hidden");
      if (list) list.replaceChildren();
      return;
    }

    if (empty) empty.classList.add("hidden");
    if (!list) return;
    list.replaceChildren();

    historyData.forEach(function (history, index) {
      var date = new Date(history.date);
      var shortHash = String(history.hash || "").substring(0, 7);
      var isCurrent = index === 0;
      var item = document.createElement("div");
      item.className =
        "flex items-start justify-between gap-3 rounded-lg border border-moose-200 p-3 hover:bg-moose-50 transition-colors";

      var details = document.createElement("div");
      details.className = "min-w-0 flex-1";
      var heading = document.createElement("div");
      heading.className = "flex items-center gap-2 mb-1";
      if (isCurrent) {
        var current = document.createElement("span");
        current.className =
          "inline-flex items-center rounded-full bg-moose-200 px-2 py-0.5 text-xs font-medium uppercase text-green-600";
        current.textContent = "current";
        heading.appendChild(current);
      }
      var message = document.createElement("span");
      message.className =
        "text-sm font-medium text-moose-900 truncate";
      message.textContent = history.message || "";
      heading.appendChild(message);

      var metadata = document.createElement("div");
      metadata.className =
        "flex items-center gap-3 text-xs text-moose-500";
      var timestamp = document.createElement("span");
      timestamp.title = date.toLocaleString();
      timestamp.textContent = formatTimeAgo(date);
      var hash = document.createElement("span");
      hash.className = "font-mono text-moose-400";
      hash.textContent = shortHash;
      metadata.append(timestamp, hash);
      details.append(heading, metadata);
      item.appendChild(details);

      if (!isCurrent) {
        var revertButton = document.createElement("button");
        revertButton.type = "button";
        revertButton.className =
          "shrink-0 text-xs bg-white border border-moose-300 hover:bg-moose-100 hover:border-moose-400 text-moose-700 px-3 py-1.5 rounded-lg transition-colors font-medium";
        revertButton.textContent = "Preview";
        revertButton.addEventListener("click", function () {
          window.openHistoryPreview(history.hash, shortHash);
        });
        item.appendChild(revertButton);
      }
      list.appendChild(item);
    });

    /* Show limit note when at max */
    var limitNote = document.getElementById("history-limit-note");
    if (limitNote) {
      if (historyData.length >= 50) {
        limitNote.classList.remove("hidden");
      } else {
        limitNote.classList.add("hidden");
      }
    }
  }

  function renderHistoryDiff(diff) {
    var target = document.getElementById("history-preview-diff");
    target.replaceChildren();

    if (!diff) {
      var empty = document.createElement("p");
      empty.className = "p-4 text-sm text-moose-500";
      empty.textContent = "No content changes from the current file.";
      target.appendChild(empty);
      return;
    }

    if (typeof Diff2HtmlUI === "undefined") {
      var fallback = document.createElement("pre");
      fallback.className = "overflow-auto whitespace-pre-wrap p-4 text-xs";
      fallback.textContent = diff;
      target.appendChild(fallback);
      return;
    }

    var diffUi = new Diff2HtmlUI(target, diff, {
      drawFileList: false,
      fileContentToggle: false,
      matching: "lines",
      outputFormat: window.matchMedia("(min-width: 900px)").matches
        ? "side-by-side"
        : "line-by-line",
      synchronisedScroll: true,
      highlight: true,
      stickyFileHeaders: true,
      renderNothingWhenEmpty: false,
    });
    diffUi.draw();
    diffUi.highlightCode();
  }

  var historyPreviewHash = "";
  var historyPreviewShortHash = "";

  window.openHistoryPreview = function (hash, shortHash) {
    if (!filePath) return;
    historyPreviewHash = hash;
    historyPreviewShortHash = shortHash;

    var modal = document.getElementById("history-preview-modal");
    var loading = document.getElementById("history-preview-loading");
    var content = document.getElementById("history-preview-content");
    var revertButton = document.getElementById("history-preview-revert");
    document.getElementById("history-preview-summary").textContent =
      filePath + " at " + shortHash;
    document.getElementById("history-preview-diff").replaceChildren();
    document.getElementById("history-preview-file").textContent = "";
    document.getElementById("history-preview-current-version").textContent = "—";
    document.getElementById("history-preview-target-version").textContent = "—";
    loading.textContent = "Loading version…";
    loading.classList.remove("hidden");
    content.classList.add("hidden");
    revertButton.disabled = true;
    modal.classList.remove("hidden");

    fetch(
      "/" +
        prefix +
        "/file-version/" +
        encodePath(filePath) +
        "?commit=" +
        encodeURIComponent(hash)
    )
      .then(function (response) {
        if (!response.ok)
          return response.json().then(function (data) {
            throw new Error(data.detail || "Version preview failed");
          });
        return response.json();
      })
      .then(function (data) {
        if (historyPreviewHash !== hash) return;
        var currentVersion =
          data.current_version === null || data.current_version === undefined
            ? "unknown"
            : String(data.current_version);
        var targetVersion =
          data.target_version === null || data.target_version === undefined
            ? "unknown"
            : String(data.target_version);
        document.getElementById("history-preview-current-version").textContent =
          currentVersion;
        document.getElementById("history-preview-target-version").textContent =
          targetVersion;
        document.getElementById("history-preview-direction-text").textContent =
          "You are reverting this file from version " +
          currentVersion +
          " (current) to version " +
          targetVersion +
          " (selected).";
        renderHistoryDiff(data.diff);
        document.getElementById("history-preview-file").textContent =
          data.content || "";
        loading.classList.add("hidden");
        content.classList.remove("hidden");
        revertButton.disabled = false;
        revertButton.onclick = function () {
          window.revertToVersion(historyPreviewHash, historyPreviewShortHash);
        };
      })
      .catch(function (error) {
        loading.textContent = "Could not load preview: " + error.message;
      });
  };

  window.closeHistoryPreview = function () {
    document.getElementById("history-preview-modal").classList.add("hidden");
    historyPreviewHash = "";
    historyPreviewShortHash = "";
  };


  window.revertToVersion = function (hash, shortHash) {
    if (!filePath) return;
    if (!confirm("Revert to version " + shortHash + "? Current changes will be overwritten.")) {
      return;
    }
    closeHistoryPreview();

    fetch("/" + prefix + "/rollback/" + encodePath(filePath), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ commit: hash }),
    })
      .then(function (r) {
        if (!r.ok)
          return r.json().then(function (d) {
            throw new Error(d.detail || "Rollback failed");
          });
        return r.json();
      })
      .then(function (result) {
        showFlash("Reverted to " + shortHash + " (v" + result.version + ")", "success");
        loadFile(filePath);
        loadHistory();
      })
      .catch(function (err) {
        showFlash("Rollback failed: " + err.message, "error");
      });
  };

  function formatTimeAgo(date) {
    var now = new Date();
    var diff = Math.floor((now - date) / 1000);
    if (diff < 60) return "just now";
    if (diff < 3600) return Math.floor(diff / 60) + "m ago";
    if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
    if (diff < 604800) return Math.floor(diff / 86400) + "d ago";
    return date.toLocaleDateString();
  }

  /* ================================================================
       File Picker
       ================================================================ */
  var fpCurrentPath = "";
  var fpSelectedFile = null; 

  window.openFilePickerModal = function () {
    if (!document.getElementById("file-picker-modal")) return;
    fpCurrentPath = "";
    fpSelectedFile = null;
    document.getElementById("file-picker-modal").classList.remove("hidden");
    document.getElementById("fp-preview").classList.add("hidden");
    fpLoadDirectory("");
  };

  window.closeFilePicker = function () {
    document.getElementById("file-picker-modal").classList.add("hidden");
    fpSelectedFile = null;
  };

  window.fpNavigate = function (path) {
    fpCurrentPath = path;
    fpSelectedFile = null;
    document.getElementById("fp-preview").classList.add("hidden");
    fpLoadDirectory(path);
  };

  window.fpSelect = function (el) {
    // Deselect previous
    document.querySelectorAll(".fp-card").forEach(function (c) {
      c.classList.remove("border-moose-600", "bg-moose-50");
    });
    // Select this one
    el.classList.add("border-moose-600", "bg-moose-50");

    var type = el.getAttribute("data-type");
    var url = el.getAttribute("data-url");
    var name = el.getAttribute("data-name");
    var mime = el.getAttribute("data-mime");
    var path = el.getAttribute("data-path");
    var size = parseInt(el.getAttribute("data-size"), 10);

    fpSelectedFile = {
      name: name,
      path: path,
      url: url,
      mime_type: mime,
      size: size,
    };

    if (type === "directory") {
      fpNavigate(path);
      return;
    }

    fpShowPreview(fpSelectedFile);
  };

  function fpShowPreview(file) {
    var panel = document.getElementById("fp-preview");
    var content = document.getElementById("fp-preview-content");
    var info = document.getElementById("fp-preview-info");
    panel.classList.remove("hidden");
    content.replaceChildren();

    var preview;
    if (file.mime_type && file.mime_type.indexOf("image/") === 0) {
      preview = document.createElement("img");
      preview.src = file.url;
      preview.alt = file.name;
      preview.className = "max-w-full rounded";
    } else if (file.mime_type === "application/pdf") {
      preview = document.createElement("iframe");
      preview.src = file.url;
      preview.title = "Preview of " + file.name;
      preview.className = "w-full h-64 rounded border border-moose-200";
      preview.setAttribute("sandbox", "");
    } else if (file.mime_type && file.mime_type.indexOf("video/") === 0) {
      preview = document.createElement("video");
      preview.src = file.url;
      preview.controls = true;
      preview.className = "w-full rounded";
    } else if (file.mime_type && file.mime_type.indexOf("audio/") === 0) {
      preview = document.createElement("audio");
      preview.src = file.url;
      preview.controls = true;
      preview.className = "w-full";
    } else {
      preview = document.createElement("div");
      preview.id = "fp-preview-icon";
      preview.className = "text-center py-8 text-4xl";
      preview.textContent = "📄";
      if (typeof FileIcons !== "undefined") {
        FileIcons.getClass(file.name).then(function (className) {
          applyFileIcon(preview, className, "48px");
        });
      }
    }
    content.appendChild(preview);

    var sizeStr =
      file.size > 1024 * 1024
        ? (file.size / (1024 * 1024)).toFixed(1) + " MB"
        : file.size > 1024
          ? (file.size / 1024).toFixed(1) + " KB"
          : file.size + " B";
    var name = document.createElement("p");
    name.className = "font-medium text-moose-900";
    name.textContent = file.name;
    var mime = document.createElement("p");
    mime.textContent = file.mime_type || "Unknown type";
    var size = document.createElement("p");
    size.textContent = sizeStr;
    info.replaceChildren(name, mime, size);
  }

  window.fpInsertSelected = function () {
    if (!fpSelectedFile || !fpSelectedFile.url) return;
    var file = fpSelectedFile;
    var markdown;

    if (file.mime_type && file.mime_type.indexOf("image/") === 0) {
      markdown = "![" + file.name + "](" + file.url + ")";
    } else {
      markdown = "[" + file.name + "](" + file.url + ")";
    }

    if (tuiEditor) {
      tuiEditor.insertText(markdown);
    } else {
      var ta = document.getElementById("fallback-editor");
      var start = ta.selectionStart;
      var end = ta.selectionEnd;
      ta.value =
        ta.value.substring(0, start) + markdown + ta.value.substring(end);
      ta.selectionStart = ta.selectionEnd = start + markdown.length;
      ta.focus();
    }

    closeFilePicker();
  };

  window.fpUploadFiles = async function (fileList) {
    var path = fpCurrentPath;
    for (var i = 0; i < fileList.length; i++) {
      var file = fileList[i];
      var uploadPath = path ? path + "/" + file.name : file.name;
      var formData = new FormData();
      formData.append("file", file);

      try {
        var resp = await fetch(
          "/" + prefix + fpStaticRoute + "/upload/" + encodePath(uploadPath),
          {
            method: "POST",
            body: formData,
          }
        );
        if (!resp.ok) {
          var msg;
          try {
            var err = await resp.json();
            msg = err.detail || "Upload failed";
          } catch (e) {
            msg = "Upload failed";
          }
          showFlash("Upload failed: " + msg, "error");
        }
      } catch (e) {
        showFlash("Upload failed: " + e.message, "error");
      }
    }
    document.getElementById("fp-upload-input").value = "";
    fpLoadDirectory(fpCurrentPath);
  };

  window.fpCreateFolder = function () {
    var name = prompt("Folder name:");
    if (!name) return;
    var createPath = fpCurrentPath ? fpCurrentPath + "/" + name : name;

    fetch("/" + prefix + fpStaticRoute + "/mkdir/" + encodePath(createPath), {
      method: "POST",
    })
      .then(function (r) {
        if (!r.ok)
          return r.json().then(function (d) {
            throw new Error(d.detail || "Failed");
          });
        return r.json();
      })
      .then(function () {
        fpLoadDirectory(fpCurrentPath);
      })
      .catch(function (err) {
        showFlash("Create folder failed: " + err.message, "error");
      });
  };

  /* ================================================================
       Init — deferred CDN scripts (TUI Editor, Guifier) execute
       before DOMContentLoaded, so globals are available here.
       ================================================================ */
  document.addEventListener("DOMContentLoaded", function () {
    initTuiEditor();
    initGuifier({});
    updateStats();

    if (tuiEditor) tuiEditor.on("change", updateStats);
    document.getElementById("fallback-editor").addEventListener("input", updateStats);
    document.getElementById("panel-metadata").addEventListener("input", updateStats);
    document.getElementById("panel-metadata").addEventListener("change", updateStats);

    if (!filePath) rememberSavedState();

    if (filePath) {
      loadFile(filePath);
      enableHistoryTab();
    }
    restoreActiveTab();

    /* Apply dynamic height after init */
    applyEditorHeight();

    /* Recalculate on window resize */
    window.addEventListener("resize", function () {
      applyEditorHeight();
    });

    document.addEventListener("pointerdown", function (e) {
      var menu = document.getElementById("metadata-field-menu");
      var toggle = document.getElementById("metadata-field-toggle");
      if (
        menu &&
        toggle &&
        !menu.contains(e.target) &&
        !toggle.contains(e.target)
      ) {
        closeMetadataFieldMenu(false);
      }
    });

    document
      .getElementById("panel-metadata")
      .addEventListener("focusout", function () {
        setTimeout(function () {
          var menu = document.getElementById("metadata-field-menu");
          var toggle = document.getElementById("metadata-field-toggle");
          if (
            menu &&
            toggle &&
            !menu.contains(document.activeElement) &&
            !toggle.contains(document.activeElement)
          ) {
            closeMetadataFieldMenu(false);
          }
        }, 0);
      });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        closeMetadataFieldMenu(true);
        var modal = document.getElementById("file-picker-modal");
        if (modal && !modal.classList.contains("hidden")) {
          closeFilePicker();
        }
        var historyModal = document.getElementById("history-preview-modal");
        if (historyModal && !historyModal.classList.contains("hidden")) {
          closeHistoryPreview();
        }
      }
    });
  });
})();
