(function () {
    var prefix   = '{{ admin_config.prefix }}';
    var filePath = '{{ file_path | default("") }}';
    var isNew    = !filePath;
    

    var tuiEditor = null;      /* TUI Editor instance */
    var guifierInstance = null; /* Guifier instance */
    var guifierSnapshot = null; /* Last metadata state, used for deletion undo */
    var guifierObserver = null;
    var guifierCheckTimer = null;
    var suppressGuifierObserver = false;
    var frontmatterData = {};   /* Current frontmatter data */
    var activeTab = 'content';  /* Current active tab */
    var previewStyle = 'vertical'; /* Split-screen by default */
    var isSaving = false;

    /* ================================================================
       Dynamic editor height — fill viewport after header
       ================================================================ */
    function calcEditorHeight() {
        var container = document.getElementById('tui-editor');
        if (!container) return '500px';
        var rect = container.getBoundingClientRect();
        var available = window.innerHeight - rect.top - 16; /* 16px bottom padding */
        return Math.max(available, 300) + 'px'; /* minimum 300px */
    }

    function applyEditorHeight() {
        var h = calcEditorHeight();
        if (tuiEditor) {
            tuiEditor.setHeight(h);
        }
        var guifierEl = document.getElementById('guifier-container');
        if (guifierEl) {
            guifierEl.style.minHeight = h;
        }
    }

    /* ================================================================
       Tab switching
       ================================================================ */
    window.switchTab = function (tabName) {
        activeTab = tabName;

        /* Update tab buttons */
        document.querySelectorAll('.tab-button').forEach(function(btn) {
            btn.classList.remove('active', 'border-moose-700', 'text-moose-900', 'bg-moose-50');
            btn.classList.add('border-transparent', 'text-moose-500');
        });

        var activeBtn = document.getElementById('tab-' + tabName);
        activeBtn.classList.add('active', 'border-moose-700', 'text-moose-900', 'bg-moose-50');
        activeBtn.classList.remove('border-transparent', 'text-moose-500');

        /* Update tab panels */
        document.querySelectorAll('.tab-panel').forEach(function(panel) {
            panel.classList.add('hidden');
        });

        var activePanel = document.getElementById('panel-' + tabName);
        activePanel.classList.remove('hidden');

        /* Refresh TUI Editor when switching to content tab */
        if (tabName === 'content' && tuiEditor) {
            applyEditorHeight();
        }
    };

    window.togglePreviewStyle = function () {
        if (!tuiEditor) return;

        previewStyle = previewStyle === 'tab' ? 'tab' : 'vertical';
        tuiEditor.changePreviewStyle(previewStyle);

        var toggle = document.getElementById('preview-style-toggle');
        var label = document.getElementById('preview-style-label');
        var isTabbed = previewStyle === 'tab';
        if (toggle) {
            toggle.setAttribute('aria-pressed', String(isTabbed));
            toggle.title = isTabbed ? 'Switch to split preview' : 'Switch to tabbed preview';
        }
        if (label) label.textContent = isTabbed ? 'Tabbed' : 'Split';
    };

    /* ================================================================
       TUI Editor initialization
       ================================================================ */
    function initTuiEditor() {
        var container = document.getElementById('tui-editor');
        var fallback  = document.getElementById('fallback-editor');

        if (typeof toastui !== 'undefined' && toastui.Editor) {
            try {
                function makeToolbarButton(name, tooltip, svg, handler) {
                    var button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'toastui-editor-toolbar-icons';
                    button.style.backgroundImage = 'none';
                    button.style.cursor = 'pointer';
                    button.setAttribute('aria-label', tooltip);
                    button.innerHTML = svg;
                    button.addEventListener('click', handler);
                    return { name: name, tooltip: tooltip, el: button };
                }

                function changeLineIndent(outdent) {
                    if (!tuiEditor || !tuiEditor.isMarkdownMode()) {
                        showFlash('Indent and outdent are available in Markdown mode', 'info');
                        return;
                    }

                    var selection = tuiEditor.getSelection();
                    var lines = tuiEditor.getMarkdown().split('\n');
                    var startLine = selection[0][0];
                    var endLine = selection[1][0];
                    if (selection[1][1] === 0 && endLine > startLine) endLine -= 1;

                    var selectedLines = lines.slice(startLine, endLine + 1);
                    var changed = selectedLines.map(function(line) {
                        return outdent ? line.replace(/^(\t| {1,4})/, '') : '    ' + line;
                    }).join('\n');
                    var rangeStart = [startLine, 0];
                    var rangeEnd = [endLine, lines[endLine].length];

                    tuiEditor.replaceSelection(changed, rangeStart, rangeEnd);
                    tuiEditor.setSelection(rangeStart, [endLine, changed.split('\n').pop().length]);
                    tuiEditor.focus();
                }

                var indentIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M9 12h12M9 18h12M3 9l3 3-3 3"/></svg>';
                var outdentIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M9 12h12M9 18h12M6 9l-3 3 3 3"/></svg>';

                var toolbar = [
                    ['heading', 'bold', 'italic', 'strike'],
                    ['hr', 'quote'],
                    ['ul', 'ol', 'task'],
                    ['table', 'link'],
                    ['code', 'codeblock'],
                    [
                        makeToolbarButton('indent', 'Indent selected lines', indentIcon, function() { changeLineIndent(false); }),
                        makeToolbarButton('outdent', 'Outdent selected lines', outdentIcon, function() { changeLineIndent(true); })
                    ]
                ];

                // Add custom "Add File" button (only if static dir is configured)
                var fpModal = document.getElementById('file-picker-modal');
                if (fpModal) {
                    var fpBtn = document.createElement('button');
                    fpBtn.className = 'toastui-editor-toolbar-icons !-mx-1 !my-0 !pl-1';
                    fpBtn.style.cursor = 'pointer';
                    fpBtn.style.backgroundImage = 'none';
                    fpBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>';
                    fpBtn.addEventListener('click', function() {
                        openFilePickerModal();
                    });
                    toolbar[toolbar.length - 1].push({
                        name: 'addFile',
                        tooltip: 'Add file (image, PDF, video, etc.)',
                        el: fpBtn
                    });
                }

                var availablePlugins = [
                    toastui.Editor.plugin.chart,
                    toastui.Editor.plugin.codeSyntaxHighlight,
                    toastui.Editor.plugin.colorSyntax,
                    toastui.Editor.plugin.tableMergedCell,
                    toastui.Editor.plugin.uml
                ].filter(function(plugin) { return typeof plugin === 'function'; });

                tuiEditor = new toastui.Editor({
                    el: container,
                    height: calcEditorHeight(),
                    initialEditType: 'markdown',
                    previewStyle: previewStyle,
                    usageStatistics: false,
                    toolbarItems: toolbar,
                    plugins: availablePlugins
                });

                fallback.classList.add('hidden');
                container.classList.remove('hidden');
                return;
            } catch (e) {
                console.warn('TUI Editor init failed, falling back to textarea:', e);
            }
        }

        /* Fallback: plain textarea */
        container.classList.add('hidden');
        fallback.classList.remove('hidden');
        var previewToggle = document.getElementById('preview-style-toggle');
        if (previewToggle) previewToggle.disabled = true;
    }

    /* ================================================================
       Guifier — date detection & data pre-processing
       Guifier uses lodash.isDate() which only recognises Date instances.
       ISO date strings like "2024-01-15" must be converted to Date
       objects before Guifier sees them, otherwise they render as text.
       ================================================================ */
    function looksLikeDate(v) {
        return typeof v === 'string' && /^\d{4}-\d{2}-\d{2}(T|\s)/.test(v);
    }

    function prepareForGuifier(obj) {
        if (obj === null || typeof obj !== 'object') {
            return looksLikeDate(obj) ? new Date(obj) : obj;
        }
        if (Array.isArray(obj)) return obj.map(prepareForGuifier);
        var out = {};
        for (var k in obj) { out[k] = prepareForGuifier(obj[k]); }
        return out;
    }

    function metadataFieldPath(id, field) {
        return String(field.path || id).split('.');
    }

    function hasMetadataPath(data, path) {
        var current = data;
        for (var i = 0; i < path.length; i++) {
            if (!current || typeof current !== 'object' || !(path[i] in current)) return false;
            current = current[path[i]];
        }
        return true;
    }

    function metadataDefault(field) {
        if (field.default_factory === 'today') {
            var now = new Date();
            var local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
            return local.toISOString().slice(0, 10);
        }
        return cloneData(field.default === undefined ? '' : field.default);
    }

    function setMetadataPath(data, path, value, replaceScalarParent) {
        var current = data;
        for (var i = 0; i < path.length - 1; i++) {
            if (current[path[i]] === undefined) current[path[i]] = {};
            if (replaceScalarParent && (current[path[i]] === null || typeof current[path[i]] !== 'object' || Array.isArray(current[path[i]]))) {
                current[path[i]] = {};
            }
            if (!current[path[i]] || typeof current[path[i]] !== 'object' || Array.isArray(current[path[i]])) return false;
            current = current[path[i]];
        }
        current[path[path.length - 1]] = value;
        return true;
    }

    function highlightAddedMetadataField(path, attempt) {
        attempt = attempt || 0;
        var container = document.getElementById('guifier-container');
        var key = path[path.length - 1];
        var walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
        var textNode;
        var target = null;
        while ((textNode = walker.nextNode())) {
            if (textNode.nodeValue.trim() !== key) continue;
            var candidate = textNode.parentElement;
            for (var i = 0; candidate && candidate !== container && i < 5; i++, candidate = candidate.parentElement) {
                var rect = candidate.getBoundingClientRect();
                if (candidate.querySelector('input, textarea, select, button') && rect.height >= 28 && rect.height <= 320) {
                    target = candidate;
                    break;
                }
            }
            if (target) break;
        }
        if (!target && attempt < 12) {
            setTimeout(function() { highlightAddedMetadataField(path, attempt + 1); }, 50);
            return;
        }
        if (!target) return;
        target.classList.remove('moose-field-added');
        void target.offsetWidth;
        target.classList.add('moose-field-added');
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(function() { target.classList.remove('moose-field-added'); }, 1500);
    }

    window.addMetadataField = function (id) {
        var field = (frontmatterRegistry.fields || {})[id];
        if (!field || field.hidden) return;
        var data = readGuifierData() || cloneData(frontmatterData);
        var path = metadataFieldPath(id, field);
        if (hasMetadataPath(data, path)) {
            showFlash((field.label || id) + ' already exists', 'info');
            return;
        }
        if (!setMetadataPath(data, path, metadataDefault(field), field.replace_scalar_parent === true)) {
            showFlash('Cannot add ' + (field.label || id) + ': its parent is not an object', 'error');
            return;
        }
        setFrontmatter(data);
        closeMetadataFieldMenu(false);
        highlightAddedMetadataField(path);
        renderMetadataFieldMenu(document.getElementById('metadata-field-search').value);
        showFlash((field.label || id) + ' added', 'success');
    };

    window.renderMetadataFieldMenu = function (query) {
        var list = document.getElementById('metadata-field-list');
        if (!list) return;
        var data = readGuifierData() || frontmatterData || {};
        var needle = String(query || '').trim().toLowerCase();
        var grouped = {};
        Object.keys(frontmatterRegistry.fields || {}).forEach(function(id) {
            var field = frontmatterRegistry.fields[id];
            if (field.hidden) return;
            var haystack = [id, field.label, field.description, field.group].join(' ').toLowerCase();
            if (needle && haystack.indexOf(needle) === -1) return;
            var group = field.group || 'Other';
            (grouped[group] = grouped[group] || []).push({ id: id, field: field });
        });
        list.innerHTML = '';
        Object.keys(grouped).forEach(function(group) {
            var heading = document.createElement('p');
            heading.className = 'px-2 pb-1 pt-2 text-xs font-bold uppercase tracking-wide text-moose-500';
            heading.textContent = group;
            list.appendChild(heading);
            grouped[group].forEach(function(item) {
                var exists = hasMetadataPath(data, metadataFieldPath(item.id, item.field));
                var button = document.createElement('button');
                button.type = 'button';
                button.disabled = exists;
                button.className = 'mb-1 block w-full rounded-lg px-3 py-2 text-left hover:bg-moose-100 disabled:cursor-not-allowed disabled:opacity-45';
                var label = document.createElement('span');
                label.className = 'block text-sm font-semibold text-moose-900';
                label.textContent = item.field.label || item.id;
                var detail = document.createElement('span');
                detail.className = 'block text-xs text-moose-500';
                detail.textContent = (item.field.path || item.id) + ' · ' + (exists ? 'Already added' : item.field.description || item.field.type);
                button.append(label, detail);
                button.addEventListener('click', function() { window.addMetadataField(item.id); });
                list.appendChild(button);
            });
        });
        if (!list.children.length) list.innerHTML = '<p class="p-4 text-center text-sm text-moose-500">No supported fields found.</p>';
    };

    function closeMetadataFieldMenu(returnFocus) {
        var menu = document.getElementById('metadata-field-menu');
        var toggle = document.getElementById('metadata-field-toggle');
        if (!menu || !toggle || menu.classList.contains('hidden')) return;
        menu.classList.add('hidden');
        toggle.setAttribute('aria-expanded', 'false');
        if (returnFocus) toggle.focus();
    }

    window.toggleMetadataFieldMenu = function () {
        var menu = document.getElementById('metadata-field-menu');
        var toggle = document.getElementById('metadata-field-toggle');
        var opening = menu.classList.contains('hidden');
        menu.classList.toggle('hidden', !opening);
        toggle.setAttribute('aria-expanded', String(opening));
        if (opening) {
            renderMetadataFieldMenu('');
            setTimeout(function() { document.getElementById('metadata-field-search').focus(); }, 0);
        }
    };

    function cloneData(value) {
        return JSON.parse(JSON.stringify(value === undefined ? {} : value));
    }

    function readGuifierData() {
        if (!guifierInstance) return null;
        try {
            return JSON.parse(guifierInstance.getData('json'));
        } catch (e) {
            return null;
        }
    }

    function countDataNodes(value) {
        if (value === null || typeof value !== 'object') return 1;
        if (Array.isArray(value)) {
            return 1 + value.reduce(function(total, item) { return total + countDataNodes(item); }, 0);
        }
        return 1 + Object.keys(value).reduce(function(total, key) {
            return total + 1 + countDataNodes(value[key]);
        }, 0);
    }

    function restoreGuifierSnapshot(snapshot) {
        if (!guifierInstance) return;
        suppressGuifierObserver = true;
        guifierSnapshot = cloneData(snapshot);
        frontmatterData = cloneData(snapshot);
        guifierInstance.setData(prepareForGuifier(snapshot), 'js');
        setTimeout(function () { suppressGuifierObserver = false; }, 0);
        showFlash('Metadata deletion undone', 'success');
    }

    function checkGuifierForDeletion() {
        if (suppressGuifierObserver) return;
        var current = readGuifierData();
        if (current === null) return;

        if (guifierSnapshot !== null && countDataNodes(current) < countDataNodes(guifierSnapshot)) {
            var previous = cloneData(guifierSnapshot);
            showFlash('A metadata item was removed', 'info', 7000, {
                label: 'Undo',
                onClick: function () { restoreGuifierSnapshot(previous); }
            });
        }
        guifierSnapshot = cloneData(current);
        frontmatterData = cloneData(current);
    }

    function observeGuifier(container) {
        if (guifierObserver) guifierObserver.disconnect();
        guifierObserver = new MutationObserver(function () {
            clearTimeout(guifierCheckTimer);
            guifierCheckTimer = setTimeout(checkGuifierForDeletion, 40);
        });
        guifierObserver.observe(container, { childList: true, subtree: true, characterData: true });
    }

    /* ================================================================
       Guifier initialization
       ================================================================ */
    function initGuifier(data) {
        var container = document.getElementById('guifier-container');

        if (typeof Guifier !== 'undefined') {
            try {
                guifierInstance = new Guifier({
                    elementSelector: '#guifier-container',
                    data: prepareForGuifier(data || {}),
                    dataType: 'js'
                });
                guifierSnapshot = cloneData(data || {});
                observeGuifier(container);
                return;
            } catch (e) {
                console.warn('Guifier init failed:', e);
            }
        }

        /* Fallback: simple key-value editor */
        container.innerHTML = '<p class="text-moose-400 text-sm italic">Guifier not loaded. Using basic editor.</p>';
    }

    /* ================================================================
       Editor helpers
       ================================================================ */
    function getEditorValue() {
        if (tuiEditor) return tuiEditor.getMarkdown();
        return document.getElementById('fallback-editor').value;
    }

    function setEditorValue(text) {
        if (tuiEditor) {
            tuiEditor.setMarkdown(text || '');
        } else {
            document.getElementById('fallback-editor').value = text || '';
        }
    }

    function getFrontmatter() {
        if (guifierInstance) {
            try {
                var jsonString = guifierInstance.getData('json');
                return JSON.parse(jsonString);
            } catch (e) {
                console.warn('Guifier getData failed:', e);
            }
        }
        return frontmatterData;
    }

    function setFrontmatter(data) {
        frontmatterData = data || {};
        guifierSnapshot = cloneData(frontmatterData);
        if (guifierInstance) {
            try {
                suppressGuifierObserver = true;
                guifierInstance.setData(prepareForGuifier(frontmatterData), 'js');
                setTimeout(function () { suppressGuifierObserver = false; }, 0);
                renderMetadataFieldMenu(document.getElementById('metadata-field-search').value);
            } catch (e) {
                console.warn('Guifier setData failed:', e);
            }
        }
    }

    /* ================================================================
       Load file content
       ================================================================ */
    var _frontmatterRaw = null;  // raw YAML text from original file (preserves comments)

    function loadFile(path) {
        if (!path) return;

        fetch('/' + prefix + '/file/' + path)
            .then(function (r) {
                if (!r.ok) throw new Error('File not found');
                return r.json();
            })
            .then(function (data) {
                setEditorValue(data.body || '');
                setFrontmatter(data.frontmatter || {});
                _frontmatterRaw = data.frontmatter_raw || null;
            })
            .catch(function (err) {
                showFlash('Could not load file: ' + err.message, 'error');
            });
    }

    /* ================================================================
       Save file
       ================================================================ */
    function setSaveState(saving) {
        isSaving = saving;
        var button = document.getElementById('btn-save');
        var label = document.getElementById('save-label');
        var icon = document.getElementById('save-icon');
        var spinner = document.getElementById('save-spinner');
        if (button) {
            button.disabled = saving;
            button.setAttribute('aria-busy', String(saving));
        }
        if (label) label.textContent = saving ? 'Saving…' : 'Save';
        if (icon) icon.classList.toggle('hidden', saving);
        if (spinner) spinner.classList.toggle('hidden', !saving);
    }

    window.saveFile = function () {
        if (isSaving) return;
        var savePath = filePath;
        if (isNew) {
            var input = document.getElementById('file-path-input');
            savePath = input ? input.value.trim() : '';
            if (!savePath) { showFlash('Enter a file path', 'error'); return; }
        }

        var body = getEditorValue();
        var meta = getFrontmatter();

        var payload = { frontmatter: meta, body: body };
        /* Send original raw YAML back so server preserves comments */
        if (_frontmatterRaw) {
            payload.frontmatter_raw = _frontmatterRaw;
        }

        var method = isNew ? 'POST' : 'PUT';
        setSaveState(true);

        fetch('/' + prefix + '/file/' + savePath, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(function (r) {
            if (!r.ok) return r.json().then(function (d) { throw new Error(d.detail || 'Save failed'); });
            return r.json();
        })
        .then(function (result) {
            showFlash('Saved!', 'success');
            if (isNew && result.path) {
                /* Update URL so subsequent saves use PUT */
                filePath = result.path;
                isNew = false;
                window.history.replaceState({}, '', '/' + prefix + '/edit/' + result.path);
                /* Reload to get frontmatter_raw for the newly created file */
                loadFile(result.path);
            }
        })
        .catch(function (err) {
            showFlash('Save failed: ' + err.message, 'error');
        })
        .finally(function () {
            setSaveState(false);
        });
    };

    /* ================================================================
       Utility
       ================================================================ */
    function escHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    /* ================================================================
       File Picker
       ================================================================ */
    var fpCurrentPath = '';
    var fpSelectedFile = null;  // { name, path, url, mime_type }
    var fpStaticRoute = '{{ admin_config._static_route | default("/static") }}';

    window.openFilePickerModal = function() {
        if (!document.getElementById('file-picker-modal')) return;
        fpCurrentPath = '';
        fpSelectedFile = null;
        document.getElementById('file-picker-modal').classList.remove('hidden');
        document.getElementById('fp-preview').classList.add('hidden');
        fpLoadDirectory('');
    };

    window.closeFilePicker = function() {
        document.getElementById('file-picker-modal').classList.add('hidden');
        fpSelectedFile = null;
    };

    window.fpNavigate = function(path) {
        fpCurrentPath = path;
        fpSelectedFile = null;
        document.getElementById('fp-preview').classList.add('hidden');
        fpLoadDirectory(path);
    };

    function fpLoadDirectory(subpath) {
        var url = '/' + prefix + fpStaticRoute + (subpath ? '/' + subpath : '');
        fetch(url)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                fpRenderBreadcrumbs(data.path);
                fpRenderGrid(data.entries);
            })
            .catch(function(err) {
                showFlash('Could not load files: ' + err.message, 'error');
            });
    }

    function fpRenderBreadcrumbs(pathStr) {
        var container = document.getElementById('fp-breadcrumbs');
        var parts = pathStr ? pathStr.split('/').filter(Boolean) : [];
        var html = '<span class="cursor-pointer hover:text-moose-900" onclick="fpNavigate(\'\')">Root</span>';
        var accumulated = '';
        for (var i = 0; i < parts.length; i++) {
            accumulated += (accumulated ? '/' : '') + parts[i];
            var p = accumulated;
            html += ' <span class="text-moose-300">/</span> ';
            html += '<span class="cursor-pointer hover:text-moose-900" onclick="fpNavigate(\'' + p + '\')">' + escHtml(parts[i]) + '</span>';
        }
        html += ' <span class="text-moose-300">/</span>';
        container.innerHTML = html;
    }

    function fpRenderGrid(entries) {
        var grid = document.getElementById('fp-grid');
        var empty = document.getElementById('fp-empty');

        if (entries.length === 0) {
            grid.innerHTML = '';
            empty.classList.remove('hidden');
            return;
        }
        empty.classList.add('hidden');

        var html = '';
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i];

            html += '<div class="fp-card border border-moose-200 rounded-lg p-3 cursor-pointer hover:border-moose-500 hover:shadow transition-all" ';
            html += 'data-path="' + escHtml(e.path) + '" ';
            html += 'data-url="' + escHtml(e.url || '') + '" ';
            html += 'data-type="' + e.type + '" ';
            html += 'data-mime="' + escHtml(e.mime_type || '') + '" ';
            html += 'data-name="' + escHtml(e.name) + '" ';
            html += 'data-size="' + e.size + '" ';
            html += 'onclick="fpSelect(this)" ondblclick="fpSelect(this);fpInsertSelected()">';

            if (e.type === 'directory') {
                html += '<div class="text-3xl text-center mb-2">📁</div>';
            } else if (e.mime_type && e.mime_type.indexOf('image/') === 0 && e.url) {
                html += '<div class="aspect-square mb-2 overflow-hidden rounded bg-moose-100 flex items-center justify-center">';
                html += '<img src="' + escHtml(e.url) + '" alt="" class="max-h-full max-w-full object-contain" loading="lazy">';
                html += '</div>';
            } else {
                // File icon — render emoji placeholder, async-update with file-icons
                html += '<div class="fp-icon text-3xl text-center mb-2">📄</div>';
            }

            html += '<div class="text-xs text-moose-700 truncate text-center" title="' + escHtml(e.name) + '">' + escHtml(e.name) + '</div>';
            html += '</div>';
        }
        grid.innerHTML = html;

        // Async-update file icons (FileIcons.getClass is async)
        if (typeof FileIcons !== 'undefined') {
            var cards = grid.querySelectorAll('.fp-card[data-type="file"]:not([data-mime^="image/"])');
            cards.forEach(function(card) {
                var name = card.getAttribute('data-name');
                var iconEl = card.querySelector('.fp-icon');
                if (iconEl) {
                    FileIcons.getClass(name).then(function(cls) {
                        iconEl.innerHTML = '<i class="' + cls + '"></i>';
                    });
                }
            });
        }
    }

    window.fpSelect = function(el) {
        // Deselect previous
        document.querySelectorAll('.fp-card').forEach(function(c) {
            c.classList.remove('border-moose-600', 'bg-moose-50');
        });
        // Select this one
        el.classList.add('border-moose-600', 'bg-moose-50');

        var type = el.getAttribute('data-type');
        var url = el.getAttribute('data-url');
        var name = el.getAttribute('data-name');
        var mime = el.getAttribute('data-mime');
        var path = el.getAttribute('data-path');
        var size = parseInt(el.getAttribute('data-size'), 10);

        fpSelectedFile = { name: name, path: path, url: url, mime_type: mime, size: size };

        if (type === 'directory') {
            fpNavigate(path);
            return;
        }

        fpShowPreview(fpSelectedFile);
    };

    function fpShowPreview(file) {
        var panel = document.getElementById('fp-preview');
        var content = document.getElementById('fp-preview-content');
        var info = document.getElementById('fp-preview-info');
        panel.classList.remove('hidden');

        var html = '';
        if (file.mime_type && file.mime_type.indexOf('image/') === 0) {
            html = '<img src="' + escHtml(file.url) + '" alt="' + escHtml(file.name) + '" class="max-w-full rounded">';
        } else if (file.mime_type === 'application/pdf') {
            html = '<iframe src="' + escHtml(file.url) + '" class="w-full h-64 rounded border border-moose-200"></iframe>';
        } else if (file.mime_type && file.mime_type.indexOf('video/') === 0) {
            html = '<video src="' + escHtml(file.url) + '" controls class="w-full rounded"></video>';
        } else if (file.mime_type && file.mime_type.indexOf('audio/') === 0) {
            html = '<audio src="' + escHtml(file.url) + '" controls class="w-full"></audio>';
        } else {
            html = '<div id="fp-preview-icon" class="text-center py-8 text-4xl">📄</div>';
        }
        content.innerHTML = html;

        // Async-update preview icon
        if (typeof FileIcons !== 'undefined') {
            var iconEl = document.getElementById('fp-preview-icon');
            if (iconEl) {
                FileIcons.getClass(file.name).then(function(cls) {
                    iconEl.innerHTML = '<i class="' + cls + '" style="font-size: 48px;"></i>';
                });
            }
        }

        var sizeStr = file.size > 1024 * 1024
            ? (file.size / (1024 * 1024)).toFixed(1) + ' MB'
            : file.size > 1024
                ? (file.size / 1024).toFixed(1) + ' KB'
                : file.size + ' B';
        info.innerHTML = '<p class="font-medium text-moose-900">' + escHtml(file.name) + '</p>'
            + '<p>' + escHtml(file.mime_type || 'Unknown type') + '</p>'
            + '<p>' + sizeStr + '</p>';
    }

    window.fpInsertSelected = function() {
        if (!fpSelectedFile || !fpSelectedFile.url) return;
        var file = fpSelectedFile;
        var markdown;

        if (file.mime_type && file.mime_type.indexOf('image/') === 0) {
            markdown = '![' + file.name + '](' + file.url + ')';
        } else {
            markdown = '[' + file.name + '](' + file.url + ')';
        }

        if (tuiEditor) {
            tuiEditor.insertText(markdown);
        } else {
            var ta = document.getElementById('fallback-editor');
            var start = ta.selectionStart;
            var end = ta.selectionEnd;
            ta.value = ta.value.substring(0, start) + markdown + ta.value.substring(end);
            ta.selectionStart = ta.selectionEnd = start + markdown.length;
            ta.focus();
        }

        closeFilePicker();
    };

    window.fpUploadFiles = async function(fileList) {
        var path = fpCurrentPath;
        for (var i = 0; i < fileList.length; i++) {
            var file = fileList[i];
            var uploadPath = path ? path + '/' + file.name : file.name;
            var formData = new FormData();
            formData.append('file', file);

            try {
                var resp = await fetch('/' + prefix + fpStaticRoute + '/upload/' + uploadPath, {
                    method: 'POST',
                    body: formData,
                });
                if (!resp.ok) {
                    var msg;
                    try { var err = await resp.json(); msg = err.detail || 'Upload failed'; } catch(e) { msg = 'Upload failed'; }
                    showFlash('Upload failed: ' + msg, 'error');
                }
            } catch (e) {
                showFlash('Upload failed: ' + e.message, 'error');
            }
        }
        document.getElementById('fp-upload-input').value = '';
        fpLoadDirectory(fpCurrentPath);
    }

    window.fpCreateFolder = function() {
        var name = prompt('Folder name:');
        if (!name) return;
        var createPath = fpCurrentPath ? fpCurrentPath + '/' + name : name;

        fetch('/' + prefix + fpStaticRoute + '/mkdir/' + createPath, { method: 'POST' })
            .then(function(r) {
                if (!r.ok) return r.json().then(function(d) { throw new Error(d.detail || 'Failed'); });
                return r.json();
            })
            .then(function() {
                fpLoadDirectory(fpCurrentPath);
            })
            .catch(function(err) {
                showFlash('Create folder failed: ' + err.message, 'error');
            });
    };

    /* ================================================================
       Init — deferred CDN scripts (TUI Editor, Guifier) execute
       before DOMContentLoaded, so globals are available here.
       ================================================================ */
    document.addEventListener('DOMContentLoaded', function () {
        initTuiEditor();
        initGuifier({});

        if (filePath) {
            loadFile(filePath);
        }

        /* Apply dynamic height after init */
        applyEditorHeight();

        /* Recalculate on window resize */
        window.addEventListener('resize', function () {
            applyEditorHeight();
        });

        document.addEventListener('pointerdown', function(e) {
            var menu = document.getElementById('metadata-field-menu');
            var toggle = document.getElementById('metadata-field-toggle');
            if (menu && toggle && !menu.contains(e.target) && !toggle.contains(e.target)) {
                closeMetadataFieldMenu(false);
            }
        });

        document.getElementById('panel-metadata').addEventListener('focusout', function() {
            setTimeout(function() {
                var menu = document.getElementById('metadata-field-menu');
                var toggle = document.getElementById('metadata-field-toggle');
                if (menu && toggle && !menu.contains(document.activeElement) && !toggle.contains(document.activeElement)) {
                    closeMetadataFieldMenu(false);
                }
            }, 0);
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeMetadataFieldMenu(true);
                var modal = document.getElementById('file-picker-modal');
                if (modal && !modal.classList.contains('hidden')) {
                    closeFilePicker();
                }
            }
        });
    });
})();
