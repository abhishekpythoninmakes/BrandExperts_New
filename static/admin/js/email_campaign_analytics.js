// This file should be placed at static/admin/js/email_campaign_analytics.js

document.addEventListener('DOMContentLoaded', function() {
    // Add tooltips to analytics cards
    const statCards = document.querySelectorAll('.stat-card');

    statCards.forEach(card => {
        const tooltip = card.getAttribute('data-tooltip');
        if (tooltip) {
            card.setAttribute('title', tooltip);
        }
    });

    // Add color coding to percentage values
    const percentages = document.querySelectorAll('.percentage');
    percentages.forEach(elem => {
        const value = parseFloat(elem.textContent);
        if (value > 50) {
            elem.classList.add('good-rate');
        } else if (value > 25) {
            elem.classList.add('average-rate');
        } else {
            elem.classList.add('low-rate');
        }
    });

    // Enable table sorting if datatables is available
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.analytics-table').DataTable({
            "pageLength": 10,
            "order": [[0, "desc"]]
        });
    }
});