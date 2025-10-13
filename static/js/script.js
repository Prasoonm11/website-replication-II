// Wait until the entire page is loaded before running the script
document.addEventListener('DOMContentLoaded', () => {

    // Get all the navigation buttons and content panels
    const navLinks = document.querySelectorAll('.content-nav a');
    const contentPanels = document.querySelectorAll('.tab-content');

    // Add a click event listener to each navigation button
    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            // Prevent the link from jumping to the top of the page
            event.preventDefault();

            // --- Step 1: Update the buttons ---
            // Remove the 'active' class from all buttons
            navLinks.forEach(navLink => {
                navLink.classList.remove('active');
            });
            // Add the 'active' class to the one that was just clicked
            link.classList.add('active');


            // --- Step 2: Update the content panels ---
            // Get the target ID from the data-target attribute (e.g., "about")
            const targetId = link.getAttribute('data-target');
            const targetPanel = document.getElementById(targetId);

            // Hide all content panels
            contentPanels.forEach(panel => {
                panel.classList.remove('active');
            });
            // Show the target content panel
            targetPanel.classList.add('active');
        });
    });
});
// ==== SEARCH OVERLAY LOGIC ====

// Get the necessary elements from the DOM
const openSearchButton = document.getElementById('open-search-btn');
const searchOverlay = document.getElementById('search-overlay');
const closeSearchButton = searchOverlay.querySelector('.close-btn');

// When the search icon in the header is clicked...
openSearchButton.addEventListener('click', function(event) {
    event.preventDefault(); // Prevent the link from navigating
    searchOverlay.classList.add('active'); // Show the overlay
});

// When the 'X' close button is clicked...
closeSearchButton.addEventListener('click', function(event) {
    event.preventDefault(); // Prevent the link from navigating
    searchOverlay.classList.remove('active'); // Hide the overlay
});