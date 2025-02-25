document.addEventListener("DOMContentLoaded", function () {
    const menuItems = document.querySelectorAll(".sidebar a");

    menuItems.forEach(item => {
        item.addEventListener("mouseover", function () {
            this.style.transform = "scale(1.1)";
        });

        item.addEventListener("mouseout", function () {
            this.style.transform = "scale(1)";
        });
    });
});
