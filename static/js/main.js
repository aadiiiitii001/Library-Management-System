/* --------------------------------------------------
   MAIN.JS — Premium UI Script
   Neon Dark + AJAX + Toast + Validation
-------------------------------------------------- */

// ------------------------------
// 1. Toast Notification System
// ------------------------------

function showToast(message, type = "info") {
    const toastContainer = document.getElementById("toastContainer");

    const toast = document.createElement("div");
    toast.classList.add("toast-custom");

    // Colors based on type
    let colorMap = {
        success: "#0aff9d",
        error: "#ff4e78",
        warning: "#ffcb47",
        info: "#3ea6ff"
    };

    toast.style.borderColor = colorMap[type] || colorMap.info;
    toast.style.color = colorMap[type] || colorMap.info;

    toast.innerText = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 400);
    }, 2500);
}

// Show toast if ?msg= exists in URL
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get("msg")) {
    showToast(urlParams.get("msg"), "success");
}



// ------------------------------
// 2. Button Ripple Effect
// ------------------------------
document.addEventListener("click", function (e) {
    if (e.target.classList.contains("btn")) {
        let ripple = document.createElement("span");
        ripple.classList.add("ripple");
        
        const rect = e.target.getBoundingClientRect();
        ripple.style.left = `${e.clientX - rect.left}px`;
        ripple.style.top = `${e.clientY - rect.top}px`;

        e.target.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }
});



// ------------------------------
// 3. Live Search (AJAX)
// ------------------------------
const searchBox = document.getElementById("searchBox");
const searchResults = document.getElementById("searchResults");

if (searchBox) {
    searchBox.addEventListener("keyup", function () {
        const query = searchBox.value.trim();

        if (query.length === 0) {
            searchResults.style.display = "none";
            return;
        }

        fetch(`/search?q=${query}&partial=1`)
            .then(res => res.text())
            .then(html => {
                searchResults.innerHTML = html;
                searchResults.style.display = "block";
            })
            .catch(err => console.error("Search Error:", err));
    });
}



// ------------------------------
// 4. Form Validation
// ------------------------------

function validateForm(formId, fields) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener("submit", function (e) {
        let valid = true;

        fields.forEach(field => {
            const input = document.getElementById(field);
            if (input && input.value.trim() === "") {
                valid = false;
                input.style.borderColor = "var(--danger)";
                showToast(`${field} is required`, "error");
            } else if (input) {
                input.style.borderColor = "var(--neon-blue)";
            }
        });

        if (!valid) e.preventDefault();
    });
}

// Example usage (you can add more)
validateForm("addBookForm", ["title"]);
validateForm("addMemberForm", ["name", "email"]);



// ------------------------------
// 5. Theme Toggle (Dark / Light)
// ------------------------------

const themeToggle = document.getElementById("themeToggle");

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        document.body.classList.toggle("light-mode");

        if (document.body.classList.contains("light-mode")) {
            themeToggle.innerText = "🌙";
            showToast("Light Mode Activated", "info");
        } else {
            themeToggle.innerText = "☀️";
            showToast("Dark Mode Activated", "info");
        }
    });
}



// ------------------------------
// 6. Smooth Page Fade-In
// ------------------------------
document.body.style.opacity = 0;

window.onload = () => {
    document.body.style.transition = "opacity 0.6s ease";
    document.body.style.opacity = 1;
};
