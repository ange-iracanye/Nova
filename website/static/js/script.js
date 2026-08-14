const chat = document.getElementById("chat");
const input = document.getElementById("message");

function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = role;
    div.innerHTML = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

async function sendMessage() {

    const input = document.getElementById("message");
    const chat = document.getElementById("chat");

    const message = input.value.trim();

    if (!message) return;

    addMessage("user", message);

    input.value = "";

    const typing = document.createElement("div");
    typing.className = "nova";
    typing.id = "typing";
    typing.innerHTML = "Nova is thinking...";
    chat.appendChild(typing);

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        document.getElementById("typing").remove();

        addMessage(
            "nova",
            data.answer.replace(/\n/g, "<br>")
        );

    }

    catch (err) {

        document.getElementById("typing").remove();

        addMessage(
            "nova",
            "Connection error."
        );

        console.error(err);

    }

}

if (input) {
    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
}

function newChat() {
    chat.innerHTML = "";

    fetch("/new_chat", {
        method: "POST"
    }).catch(console.error);
}