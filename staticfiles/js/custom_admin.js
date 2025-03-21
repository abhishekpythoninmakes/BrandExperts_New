// custom_admin.js
document.addEventListener("DOMContentLoaded", function () {
    // Define color schemes for each app
    const appColors = {
        'dashboard': {
            main: '#BF1A1C',  // Red
            sub: '#FFD700'    // Gold
        },
        'auth': {
            main: '#2E7D32',  // Green
            sub: '#81C784'    // Light Green
        },
        'customers': {
            main: '#1976D2',  // Blue
            sub: '#64B5F6'    // Light Blue
        },
        'products_app': {
            main: '#7B1FA2',  // Purple
            sub: '#BA68C8'    // Light Purple
        }
    };

    // Select all sidebar menu items
    const menuItems = document.querySelectorAll(".sidebar .app-list > .app-item");

    menuItems.forEach(appItem => {
        // Get the app name from the class (assuming Jazzmin adds app-name- prefixed classes)
        const appClass = Array.from(appItem.classList).find(cls => cls.startsWith('app-name-'));
        const appName = appClass ? appClass.replace('app-name-', '') : '';

        // Find the submenu (model list) within this app
        const submenu = appItem.querySelector('.model-list');

        if (submenu) {
            // Create dropdown toggle functionality
            const appLink = appItem.querySelector('a:first-child');

            // Add dropdown class and styling
            appItem.classList.add('has-dropdown');
            submenu.style.display = 'none'; // Initially hidden

            // Set main color for app
            const colors = appColors[appName] || { main: '#BF1A1C', sub: '#FFD700' };
            appLink.style.backgroundColor = colors.main;

            // Style submenu items
            const submenuItems = submenu.querySelectorAll('a');
            submenuItems.forEach(item => {
                item.style.backgroundColor = colors.sub;
            });

            // Toggle dropdown on click
            appLink.addEventListener('click', function(e) {
                e.preventDefault();
                const isVisible = submenu.style.display === 'block';

                // Hide all other submenus
                document.querySelectorAll('.sidebar .model-list').forEach(otherMenu => {
                    otherMenu.style.display = 'none';
                });

                // Toggle current submenu
                submenu.style.display = isVisible ? 'none' : 'block';
            });

            // Hover effects
            appLink.addEventListener("mouseover", function () {
                this.style.transform = "scale(1.05)";
                this.style.opacity = "0.9";
            });

            appLink.addEventListener("mouseout", function () {
                this.style.transform = "scale(1)";
                this.style.opacity = "1";
            });

            submenuItems.forEach(item => {
                item.addEventListener("mouseover", function () {
                    this.style.transform = "scale(1.03)";
                    this.style.opacity = "0.9";
                });

                item.addEventListener("mouseout", function () {
                    this.style.transform = "scale(1)";
                    this.style.opacity = "1";
                });
            });
        }
    });

    // Close submenu when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.sidebar')) {
            document.querySelectorAll('.sidebar .model-list').forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });
});