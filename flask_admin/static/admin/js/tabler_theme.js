/*
Tabler theme switcher for Flask-Admin.

Applies the user's light/dark choice (via the `?theme=` switcher links in
the navbar) as `data-bs-theme` on `<html>` and persists it in localStorage
so the choice survives navigation.
*/
(function() {
    'use strict';

    var STORAGE_KEY = 'fa-tabler-theme';

    function currentTheme() {
        try {
            var fromUrl = new URLSearchParams(window.location.search).get('theme');
            if (fromUrl === 'dark' || fromUrl === 'light') {
                return fromUrl;
            }
            return window.localStorage.getItem(STORAGE_KEY) || 'light';
        } catch (e) {
            return 'light';
        }
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        try {
            window.localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) {
            /* storage unavailable (e.g. private mode) — theme still applies */
        }
    }

    applyTheme(currentTheme());
})();
