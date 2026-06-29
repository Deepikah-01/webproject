// StudyHub Main JS
document.addEventListener('DOMContentLoaded', () => {
    console.log('StudyHub - Smart Student Companion Initialized');

    // Handle Active Nav Links
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Add subtle hover sound effects or interactions here if needed
});

// Utility for formatting dates
function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    }).format(new Date(date));
}
