function toggleMenu() {
    let menu = document.getElementById("sideMenu");
    menu.style.right = (menu.style.right === "0px") ? "-100%" : "0px";
}

function openLogin() {
    document.getElementById("loginModal").style.display = "block";
}

function closeLogin() {
    document.getElementById("loginModal").style.display = "none";
}

function openStudy() {
    document.getElementById("studyModal").style.display = "block";
}

function closeStudy() {
    document.getElementById("studyModal").style.display = "none";
}
function toggleMenu() {
    document.getElementById("sideMenu").classList.toggle("open");
}
function filterCompany(name) {
    document.querySelectorAll('.company').forEach(div => {
        if (name === 'all' || div.classList.contains(name)) {
            div.style.display = "block";
        } else {
            div.style.display = "none";
        }
    });
}
fetch("/attendance/save", { ... })
fetch("/attendance/load")
