async function loadStudents() {
    const cls = document.getElementById("classSelect").value;
    const list = document.getElementById("studentList");
    list.innerHTML = "";
    if (!cls) return;

    const res = await fetch(`/api/get-students/${cls}`);
    const data = await res.json();

    data.students.forEach(name => {
        const li = document.createElement("li");
        li.innerHTML = `
          ${name}
          <button onclick="removeStudent('${name}')">❌</button>
        `;
        list.appendChild(li);
    });
}

async function addStudent() {
    const cls = document.getElementById("classSelect").value;
    const name = document.getElementById("studentName").value.trim();

    if (!cls || !name) return alert("Fill all fields");

    await fetch("/api/add-student", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({class: cls, student: name})
    });

    document.getElementById("studentName").value = "";
    loadStudents();
}

async function removeStudent(name) {
    const cls = document.getElementById("classSelect").value;

    await fetch("/api/remove-student", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({class: cls, student: name})
    });

    loadStudents();
}
