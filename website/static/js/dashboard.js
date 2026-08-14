let history = JSON.parse(localStorage.getItem("nova_history") || "[]");

document.getElementById("questions").innerText = history.length;

document.getElementById("xp").innerText = history.length * 10 + " XP";

const chats = document.getElementById("recentChats");

history.slice(-5).reverse().forEach(chat => {

    const div = document.createElement("div");

    div.className = "card";

    div.innerHTML = "<b>You:</b> " + chat.user;

    chats.appendChild(div);

});