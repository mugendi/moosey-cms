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
function showFlash(message, type, duration) {
    type = type || 'info';
    duration = duration || 3000;

    const container = document.getElementById('flash-container');
    if (!container) return;

    const colorMap = {
        success: 'bg-green-600',
        error:   'bg-red-600',
        info:    'bg-moose-700',
    };

    const el = document.createElement('div');
    el.className = colorMap[type] || colorMap.info
        + ' text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium'
        + ' flex items-center gap-2 transition-opacity duration-300';

    el.textContent = message;
    container.appendChild(el);

    setTimeout(function () {
        el.style.opacity = '0';
        setTimeout(function () { el.remove(); }, 300);
    }, duration);
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
