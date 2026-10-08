async function askAI() {
    const input = document.getElementById("question");
    const chat = document.getElementById("chat");

    const question = input.value.trim();

    if (!question) {
        return;
    }

    chat.innerHTML += `
        <div class="message user">
            <div class="avatar">👤</div>
            <div>${question}</div>
        </div>
    `;

    input.value = "";

    const loadingId = "loading-" + Date.now();

    chat.innerHTML += `
        <div class="message ai" id="${loadingId}">
            <div class="avatar">🤖</div>
            <div>جاري التفكير...</div>
        </div>
    `;

    chat.scrollTop = chat.scrollHeight;

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        const data = await response.json();

        const loading = document.getElementById(loadingId);

        if (loading) {
            loading.outerHTML = `
                <div class="message ai">
                    <div class="avatar">🤖</div>
                    <div>${data.answer}</div>
                </div>
            `;
        }

    } catch (error) {

        const loading = document.getElementById(loadingId);

        if (loading) {
            loading.outerHTML = `
                <div class="message ai">
                    <div class="avatar">⚠️</div>
                    <div>حدث خطأ في الاتصال بالخادم.</div>
                </div>
            `;
        }
    }

    chat.scrollTop = chat.scrollHeight;
}
