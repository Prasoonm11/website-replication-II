// Wait until the entire page is loaded before running the script
document.addEventListener('DOMContentLoaded', () => {

    // ==== TAB SYSTEM LOGIC ====
    const navLinks = document.querySelectorAll('.content-nav a');
    const contentPanels = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();

            // --- Step 1: Update the buttons ---
            navLinks.forEach(navLink => {
                navLink.classList.remove('active');
            });
            link.classList.add('active');

            // --- Step 2: Update the content panels ---
            const targetId = link.getAttribute('data-target');
            const targetPanel = document.getElementById(targetId);

            // Hide all content panels (KEEP THIS PART)
            contentPanels.forEach(panel => {
                panel.classList.remove('active');
                // Optional: Move inactive panels back to original container if they stray
                // document.querySelector('.content-panel').appendChild(panel); 
            });
            
            // --- NEW LOGIC TO MOVE & SHOW PANEL ---
            const listItem = link.closest('li'); // Find the parent <li> of the clicked link

            // Check if the window width is less than or equal to 992px (tablet/mobile breakpoint)
            if (window.innerWidth <= 992 && listItem && targetPanel) {
                // *** MOBILE/TABLET VIEW: Move panel for accordion effect ***
                listItem.after(targetPanel); 
            } else if (targetPanel) {
                // *** DESKTOP VIEW: Put panel back in original container (if needed) ***
                // This ensures panels don't get stuck under list items if resizing window
                document.querySelector('.content-panel').appendChild(targetPanel); 
            }

            // Show the target panel (whether moved or not)
            if (targetPanel) {
                targetPanel.classList.add('active'); 
            }
            // --- END OF NEW LOGIC ---
        });
    });
    // ==== END OF TAB LOGIC ====4


    // ==== SEARCH OVERLAY LOGIC (FIXED: Moved inside DOMContentLoaded) ====
    const openSearchButton = document.getElementById('open-search-btn');
    const searchOverlay = document.getElementById('search-overlay');
    const closeSearchButton = searchOverlay.querySelector('.close-btn');

    openSearchButton.addEventListener('click', function(event) {
        event.preventDefault(); 
        searchOverlay.classList.add('active');
    });

    closeSearchButton.addEventListener('click', function(event) {
        event.preventDefault(); 
        searchOverlay.classList.remove('active');
    });
    // ==== END OF SEARCH LOGIC ====


    // ==== NEW: MOBILE MENU TOGGLE LOGIC ====
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const headerNav = document.querySelector('header nav');

    if (mobileMenuToggle && headerNav) {
        mobileMenuToggle.addEventListener('click', function(event) {
            event.preventDefault();
            // This will toggle the 'active' class on the <nav> element
            headerNav.classList.toggle('active');
        });
    }
    // ==== END OF MOBILE MENU LOGIC ====

    // ==== NEW: ENQUIRY MODAL LOGIC ====
    const openEnquiryBtns = document.querySelectorAll('.side-btn.enquiry');
    const enquiryModal = document.getElementById('enquiry-modal');
    
    // Check if the modal exists before adding listeners
    if (enquiryModal) {
        const closeEnquiryBtn = enquiryModal.querySelector('.modal-close');
        const modalOverlay = enquiryModal.querySelector('.modal-overlay');

        // Open modal when any "Make an Enquiry" button is clicked
        openEnquiryBtns.forEach(btn => {
            btn.addEventListener('click', function(event) {
                event.preventDefault();
                enquiryModal.classList.add('active');
            });
        });

        // Close modal when the 'X' is clicked
        closeEnquiryBtn.addEventListener('click', function(event) {
            event.preventDefault();
            enquiryModal.classList.remove('active');
        });

        // Close modal when clicking on the dark background
        modalOverlay.addEventListener('click', function() {
            enquiryModal.classList.remove('active');
        });
    }
    // ==== END OF ENQUIRY MODAL LOGIC ====

});