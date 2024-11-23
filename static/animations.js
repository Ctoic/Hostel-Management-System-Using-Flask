document.addEventListener('DOMContentLoaded', () => {
    const elements = document.querySelectorAll('.footer, .navbar-brand, .nav-link, h6, p');
    elements.forEach(el => {
        el.style.transition = 'all 0.5s ease';
        el.style.opacity = 0;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = 1;
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        });
        observer.observe(el);
    });
});
