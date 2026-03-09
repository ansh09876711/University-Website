// ===============================
// ATTENDANCE ANALYTICS (TEACHER)
// ===============================

// Safety check
if (typeof present === "undefined" || typeof absent === "undefined") {
    console.error("Attendance data not found");
}

// ---------- PIE CHART ----------
const pieCtx = document.getElementById("attendancePie");

if (pieCtx) {
    new Chart(pieCtx, {
        type: "pie",
        data: {
            labels: ["Present", "Absent"],
            datasets: [{
                data: [present, absent],
                backgroundColor: [
                    "#22c55e", // green
                    "#ef4444"  // red
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        font: { size: 14 }
                    }
                }
            }
        }
    });
}

// ---------- BAR CHART ----------
const barCtx = document.getElementById("attendanceBar");

if (barCtx) {
    new Chart(barCtx, {
        type: "bar",
        data: {
            labels: ["Present", "Absent"],
            datasets: [{
                label: "Students",
                data: [present, absent],
                backgroundColor: [
                    "#22c55e",
                    "#ef4444"
                ],
                borderRadius: 8,
                barThickness: 50
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}
