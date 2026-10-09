
(function () {
    "use strict";

    const translations = {
        ar: {
            welcome: "ماذا تريد أن تتعلم اليوم؟",
            search: "🔎 ابحث عن درس أو مادة...",
            button: "بحث",
            cards: [
                ["المساعد الذكي", "اسأل Study AI"],
                ["الدروس", "تصفح الكتب والدروس"],
                ["الاختبارات", "اختبر معلوماتك"],
                ["نتائج المسابقات الموريتانية", "تابع نتائج المسابقات والامتحانات"],
                ["الإعدادات", "خصص تجربة Study AI"]
            ]
        },
        en: {
            welcome: "What would you like to learn today?",
            search: "🔎 Search for a lesson or subject...",
            button: "Search",
            cards: [
                ["AI Assistant", "Ask Study AI"],
                ["Lessons", "Browse books and lessons"],
                ["Quizzes", "Test your knowledge"],
                ["Mauritanian Exam Results", "Check exam results"],
                ["Settings", "Customize Study AI"]
            ]
        },
        fr: {
            welcome: "Que souhaitez-vous apprendre aujourd'hui ?",
            search: "🔎 Rechercher une leçon ou une matière...",
            button: "Rechercher",
            cards: [
                ["Assistant IA", "Posez vos questions à Study AI"],
                ["Leçons", "Parcourir les livres et les leçons"],
                ["Quiz", "Testez vos connaissances"],
                ["Résultats des concours mauritaniens", "Consultez les résultats"],
                ["Paramètres", "Personnalisez Study AI"]
            ]
        }
    };

    function applyHomeLanguage() {
        const lang = localStorage.getItem("language") || "ar";
        const t = translations[lang] || translations.ar;

        document.documentElement.lang = lang;
        document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

        const welcome = document.getElementById("welcomeText");
        if (welcome) welcome.textContent = t.welcome;

        const input = document.querySelector('.search input[name="q"]');
        if (input) input.placeholder = t.search;

        const button = document.querySelector(".search button");
        if (button) button.textContent = t.button;

        const paths = ["/chat", "/lessons", "/quizzes", "/results", "/settings"];

        paths.forEach((path, i) => {
            const card = document.querySelector('.card[href="' + path + '"]');
            if (!card) return;

            const title = card.querySelector("h2");
            const description = card.querySelector("p");

            if (title) title.textContent = t.cards[i][0];
            if (description) description.textContent = t.cards[i][1];
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", applyHomeLanguage);
    } else {
        applyHomeLanguage();
    }
})();
