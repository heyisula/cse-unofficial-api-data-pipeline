document.addEventListener('DOMContentLoaded', () => {

    // --- Sidebar Navigation & Active State ---
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section');
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.toggle-menu');

    // Smooth scrolling
    navLinks.forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                // Determine offset based on whether header is fixed or not roughly
                const offset = 40;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.scrollY - offset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });

                // Close mobile menu
                if (window.innerWidth <= 1024) {
                    sidebar.classList.remove('active');
                }
            }
        });
    });

    // ScrollSpy: Highlights active link in sidebar while scrolling
    window.addEventListener('scroll', () => {
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            // Provide a generous offset so it highlights before scrolling fully past
            if (scrollY >= (sectionTop - 150)) {
                current = '#' + section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === current) {
                link.classList.add('active');
            }
        });
    });

    // --- Mobile Menu Toggle ---
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });

        // Close when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 1024 &&
                sidebar.classList.contains('active') &&
                !sidebar.contains(e.target) &&
                !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        });
    }

    // --- Copy to Clipboard Functionality ---
    window.copyToClipboard = function (text, buttonElement) {
        navigator.clipboard.writeText(text).then(() => {
            // Find the button if passed (we can bind 'this' in HTML)
            // Or create a generic toast
            showToast('Copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy: ', err);
            showToast('Failed to copy', true);
        });
    };

    // Simple toast notification
    function showToast(message, isError = false) {
        // Remove existing toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;

        Object.assign(toast.style, {
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            backgroundColor: isError ? '#ef4444' : '#10b981',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            zIndex: '1000',
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
            fontWeight: '600',
            opacity: '0',
            transform: 'translateY(20px)',
            transition: 'all 0.3s ease'
        });

        document.body.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });

        // Animate out
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

});
