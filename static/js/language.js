(function () {
    const savedLanguage = localStorage.getItem("language") || "ar";

    document.documentElement.lang = savedLanguage;

    if (savedLanguage === "ar") {
        document.documentElement.dir = "rtl";
    } else {
        document.documentElement.dir = "ltr";
    }

    window.currentLanguage = savedLanguage;
})();
