document.addEventListener("DOMContentLoaded", function() {
    // Select all images with the class 'lazy-load'
    const lazyImages = document.querySelectorAll('img.lazy-load');

    // Function to load the image
    const loadImage = (img) => {
        const src = img.getAttribute('data-src');
        if (src) {
            img.src = src;
            img.classList.remove('lazy-load'); // Remove the lazy-load class after loading
        }
    };

    // Intersection Observer for lazy loading
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    loadImage(entry.target);
                    observer.unobserve(entry.target); // Stop observing once the image is loaded
                }
            });
        });

        lazyImages.forEach(img => {
            observer.observe(img); // Observe each lazy-loaded image
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        lazyImages.forEach(img => {
            loadImage(img);
        });
    }
});