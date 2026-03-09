const btn = document.getElementById("ai-chatbot-btn");
const popup = document.getElementById("ai-chatbot-popup");
const closeBtn = document.getElementById("chatbot-close");

// Toggle open
btn.addEventListener("click", (e) => {
    e.stopPropagation();
    popup.style.display = popup.style.display === "flex" ? "none" : "flex";
});

// Close button
closeBtn.addEventListener("click", () => {
    popup.style.display = "none";
});

// Click outside to close
document.addEventListener("click", (e) => {
    if (!popup.contains(e.target) && !btn.contains(e.target)) {
        popup.style.display = "none";
    }
});
