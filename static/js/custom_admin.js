document.addEventListener("DOMContentLoaded", function () {
    // Add animations to sidebar links
    let sidebarLinks = document.querySelectorAll(".sidebar a");
    sidebarLinks.forEach(link => {
        link.addEventListener("mouseover", () => {
            link.classList.add("animate__animated", "animate__pulse");
        });
        link.addEventListener("mouseleave", () => {
            link.classList.remove("animate__animated", "animate__pulse");
        });
    });

    // Add smooth scrolling to top button
    let topButton = document.createElement("button");
    topButton.innerHTML = "⬆️";
    topButton.style.position = "fixed";
    topButton.style.bottom = "20px";
    topButton.style.right = "20px";
    topButton.style.background = "#BF1A1C";
    topButton.style.color = "white";
    topButton.style.border = "none";
    topButton.style.borderRadius = "50%";
    topButton.style.padding = "10px";
    topButton.style.cursor = "pointer";
    topButton.style.display = "none";

    document.body.appendChild(topButton);

    window.addEventListener("scroll", function () {
        if (window.scrollY > 300) {
            topButton.style.display = "block";
        } else {
            topButton.style.display = "none";
        }
    });

    topButton.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
});
