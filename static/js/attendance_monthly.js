function toggleAttendance(student, date, cell) {

    let status = "present";

    if (cell.classList.contains("present")) {
        status = "absent";
    }

    fetch("/toggle-attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            student: student,
            date: date,
            status: status
        })
    });

    cell.classList.remove("present", "absent", "empty");

    if (status === "present") {
        cell.classList.add("present");
        cell.innerHTML = "✔";
    } else {
        cell.classList.add("absent");
        cell.innerHTML = "✖";
    }
}
