(function () {
    "use strict";

    const root = document.documentElement;

    function applyPreferences() {
        const darkMode = localStorage.getItem("darkMode") === "true";
        const language = localStorage.getItem("language") || "ar";

        document.body.classList.toggle("dark", darkMode);
        root.lang = language;
        root.dir = language === "ar" ? "rtl" : "ltr";
        root.dataset.theme = darkMode ? "dark" : "light";
    }

    function start() {
        applyPreferences();

        window.addEventListener("storage", function (event) {
            if (event.key === "darkMode" || event.key === "language") {
                applyPreferences();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
