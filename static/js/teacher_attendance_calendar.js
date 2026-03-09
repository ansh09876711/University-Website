let current = new Date();

const calendar = document.getElementById("calendar");
const monthYear = document.getElementById("monthYear");

function renderCalendar() {
    calendar.innerHTML = "";

    const year = current.getFullYear();
    const month = current.getMonth();

    monthYear.innerText =
        current.toLocaleString("default", { month: "long" }) + " " + year;

    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // HEADER ROW
    const header = document.createElement("div");
    header.className = "calendar-row header";
    header.innerHTML = `<div class="name-col">Student</div>`;
    for (let d = 1; d <= daysInMonth; d++) {
        header.innerHTML += `<div>${d}</div>`;
    }
    calendar.appendChild(header);

    // STUDENT ROWS
    STUDENTS.forEach(s => {
        const row = document.createElement("div");
        row.className = "calendar-row";

        row.innerHTML = `<div class="name-col">${s.username}</div>`;

        for (let d = 1; d <= daysInMonth; d++) {
            const date =
                `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;

            const status = ATTENDANCE[s.username]?.[date];

            const cell = document.createElement("div");
            cell.className = "cell " + (status || "");

            cell.onclick = () => toggleAttendance(s.username, date, cell);

            row.appendChild(cell);
        }

        calendar.appendChild(row);
    });
}

function toggleAttendance(student, date, cell) {
    let newStatus = cell.classList.contains("present") ? "absent" : "present";

    fetch("/toggle-attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student, date, status: newStatus })
    });

    cell.classList.remove("present", "absent");
    cell.classList.add(newStatus);
}

function changeMonth(step) {
    current.setMonth(current.getMonth() + step);
    renderCalendar();
}
let current = new Date();

function renderCalendar() {
    const year = current.getFullYear();
    const month = current.getMonth();

    document.getElementById("monthYear").innerText =
        current.toLocaleString("default", { month: "long", year: "numeric" });

    const firstDay = new Date(year, month, 1).getDay();
    const totalDays = new Date(year, month + 1, 0).getDate();

    let html = `<table><tr>
        <th>Student</th>
        ${[...Array(totalDays)].map((_, i) => `<th>${i+1}</th>`).join("")}
    </tr>`;

    students.forEach(s => {
        html += `<tr><td>${s.username}</td>`;
        for (let d = 1; d <= totalDays; d++) {
            const date = `${year}-${month+1}-${d}`;
            html += `
                <td>
                    <button class="present" onclick="mark('${s.username}','${date}','present')">✔</button>
                    <button class="absent" onclick="mark('${s.username}','${date}','absent')">✖</button>
                </td>`;
        }
        html += "</tr>";
    });

    html += "</table>";
    document.getElementById("calendar").innerHTML = html;
}

function mark(student, date, status) {
    fetch("/toggle-attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student, date, status })
    });
}

function prevMonth() {
    current.setMonth(current.getMonth() - 1);
    renderCalendar();
}

function nextMonth() {
    current.setMonth(current.getMonth() + 1);
    renderCalendar();
}

renderCalendar();