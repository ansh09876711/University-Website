let total = 0;
let present = 0;
let absent = 0;

document.addEventListener("DOMContentLoaded", () => {
    total = document.querySelectorAll(".student-box").length;
    updateSummary();
});

function toggleStatus(box) {
    const status = box.querySelector(".status");

    if (status.innerText === "Absent") {
        status.innerText = "Present";
        box.classList.add("present");
        box.classList.remove("absent");
    } else {
        status.innerText = "Absent";
        box.classList.add("absent");
        box.classList.remove("present");
    }

    calculate();
}

function calculate() {
    present = document.querySelectorAll(".student-box.present").length;
    absent = total - present;

    updateSummary();
}

function updateSummary() {
    document.getElementById("total").innerText = total;
    document.getElementById("present").innerText = present;
    document.getElementById("absent").innerText = absent;

    const percent = total ? ((present / total) * 100).toFixed(1) : 0;
    document.getElementById("percent").innerText = percent + "%";
}

function saveAttendance() {
    alert("✅ Attendance Saved Successfully (Demo Mode)");
}
