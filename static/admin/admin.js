/* ================================================================
   admin.js — Shared JavaScript utilities for Moosey CMS admin UI.
   Included in base.html; available to all admin templates.
   ================================================================ */

/* -----------------------------------------------------------
   toggleSidebar() — open / close the mobile sidebar drawer.
   Works by toggling the translate class and overlay visibility.
   ----------------------------------------------------------- */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;

    const isOpen = !sidebar.classList.contains('-translate-x-full');
    if (isOpen) {
        sidebar.classList.add('-translate-x-full');
        overlay && overlay.classList.add('hidden');
    } else {
        sidebar.classList.remove('-translate-x-full');
        overlay && overlay.classList.remove('hidden');
    }
}

/* -----------------------------------------------------------
   showFlash(message, type, duration) — display a toast-style
   notification in the flash container.

   type: 'success' | 'error' | 'info'  (default: 'info')
   duration: milliseconds to show (default: 3000)
   ----------------------------------------------------------- */
function showFlash(message, type, duration, action) {
    type = type || 'info';
    duration = duration || 4500;

    const container = document.getElementById('flash-container');
    if (!container) return;

    const growlMeta = {
        success: { title: 'Success', icon: '✓' },
        error:   { title: 'Error', icon: '!' },
        warning: { title: 'Warning', icon: '!' },
        info:    { title: 'Moosey CMS', icon: 'i' },
    };
    const meta = growlMeta[type] || growlMeta.info;

    const el = document.createElement('div');
    el.className = 'moose-growl';
    el.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const icon = document.createElement('div');
    icon.className = 'moose-growl__icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = meta.icon;

    const copy = document.createElement('div');
    const title = document.createElement('p');
    title.className = 'moose-growl__title';
    title.textContent = meta.title;
    const text = document.createElement('p');
    text.className = 'moose-growl__message';
    text.textContent = String(message);
    copy.append(title, text);

    if (action && typeof action.onClick === 'function') {
        const actionButton = document.createElement('button');
        actionButton.type = 'button';
        actionButton.className = 'moose-growl__action';
        actionButton.textContent = action.label || 'Undo';
        actionButton.addEventListener('click', function () {
            action.onClick();
            dismiss();
        });
        copy.appendChild(actionButton);
    }

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'moose-growl__close';
    close.setAttribute('aria-label', 'Dismiss notification');
    close.textContent = '×';

    let timer;
    function dismiss() {
        if (!el.isConnected || el.classList.contains('is-leaving')) return;
        clearTimeout(timer);
        el.classList.add('is-leaving');
        el.addEventListener('animationend', function () { el.remove(); }, { once: true });
        setTimeout(function () { el.remove(); }, 300);
    }
    close.addEventListener('click', dismiss);
    el.addEventListener('mouseenter', function () { clearTimeout(timer); });
    el.addEventListener('mouseleave', function () { timer = setTimeout(dismiss, duration); });

    el.append(icon, copy, close);
    container.prepend(el);
    timer = setTimeout(dismiss, duration);
}

/* -----------------------------------------------------------
   Escape key handler — close any open modal when Escape is
   pressed.  Modals must have the class 'modal-overlay'.
   ----------------------------------------------------------- */
document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('.modal-overlay').forEach(function (m) {
        m.classList.add('hidden');
    });
});
