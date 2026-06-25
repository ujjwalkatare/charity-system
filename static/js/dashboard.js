function showSection(section) {

    const mainContent = document.querySelector('.main-content');

    // Hide all sections
    document.querySelectorAll('.content-section').forEach(sec =>
        sec.classList.remove('active-section')
    );

    // Remove active sidebar highlight
    document.querySelectorAll('.sidebar a').forEach(link =>
        link.classList.remove('active')
    );

    // Show selected section
    document.getElementById(section + '-section')
        .classList.add('active-section');

    // Highlight sidebar item
    document.querySelector(`[onclick="showSection('${section}')"]`)
        .classList.add('active');

    // Toggle background
    if (section === 'dashboard') {
        mainContent.classList.add('dashboard-bg');
    } else {
        mainContent.classList.remove('dashboard-bg');
    }
}