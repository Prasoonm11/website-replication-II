document.addEventListener('DOMContentLoaded', () => {

    // ==== TAB SYSTEM LOGIC (With Mobile Accordion Fix) ====
    const navLinks = document.querySelectorAll('.content-nav a, .mobile-content-menu a');
    const contentPanels = document.querySelectorAll('.tab-content');
    const mobileNav = document.getElementById('mobile-nav');
    const desktopPanelContainer = document.querySelector('.content-panel'); // The desktop column

    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            // 1. Prevent the default instant "jump"
            event.preventDefault(); 

            // 2. Get the target for switching content
            const targetId = link.getAttribute('data-target');
            const targetPanel = document.getElementById(targetId);

            // 3. Get the target for scrolling
            const href = link.getAttribute('href');
            const scrollTargetId = href.substring(1); // Removes the '#'
            const scrollTargetElement = document.getElementById(scrollTargetId);

            // 4. Update the 'active' class on all links (desktop & mobile)
            navLinks.forEach(navLink => {
                navLink.classList.remove('active');
                if (navLink.getAttribute('data-target') === targetId) {
                    navLink.classList.add('active');
                }
            });

            // 5. Hide all panels AND move them back to the desktop container
            // This resets the layout on every click.
            contentPanels.forEach(panel => {
                panel.classList.remove('active');
                if (desktopPanelContainer) { // Check if container exists
                    desktopPanelContainer.appendChild(panel); // Return to hidden container
                }
            });
            
            // 6. Check if we are in mobile view
            if (targetPanel) {
                const isMobileView = window.innerWidth <= 992;

                // --- THIS IS THE FIX ---
                // We must find the ON-PAGE accordion button, no matter which link was clicked
                const onPageLink = document.querySelector(`.content-nav a[data-target="${targetId}"]`);
                const onPageListItem = onPageLink ? onPageLink.closest('li') : null;

                if (isMobileView && onPageListItem) {
                    // On mobile, move the active panel to be *after* the on-page accordion button
                    onPageListItem.after(targetPanel);
                }
                // --- END OF FIX ---
                
                // 7. Show the target panel (it's now in the right place)
                targetPanel.classList.add('active');
            }

            // 8. Close the mobile menu (if it's open)
            if (link.closest('#mobile-nav')) {
                mobileNav.classList.remove('active');
            }

            // 9. Scroll to the element smoothly
            if (scrollTargetElement) {
                setTimeout(() => {
                    scrollTargetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }, 300); // Delay to let menu close
            }
        });
    });
    // ==== END OF TAB LOGIC ====


    // ==== SEARCH OVERLAY LOGIC ====
    const openSearchButton = document.getElementById('open-search-btn');
    const searchOverlay = document.getElementById('search-overlay');
    
    if (openSearchButton && searchOverlay) {
        const closeSearchButton = searchOverlay.querySelector('.close-btn');

        openSearchButton.addEventListener('click', function(event) {
            event.preventDefault(); 
            searchOverlay.classList.add('active');
        });

        if (closeSearchButton) {
            closeSearchButton.addEventListener('click', function(event) {
                event.preventDefault(); 
                searchOverlay.classList.remove('active');
            });
        }
    }
    // ==== END OF SEARCH LOGIC ====


    // ==== MOBILE CONTENT MENU TOGGLE LOGIC ====
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const menuClose = document.getElementById('mobile-menu-close');
    // const mobileNav is already defined above

    if (menuToggle && mobileNav && menuClose) {
        
        // Open menu when hamburger icon (3 lines) is clicked
        menuToggle.addEventListener('click', () => {
            mobileNav.classList.add('active');
        });

        // Close menu when 'X' button is clicked
        menuClose.addEventListener('click', () => {
            mobileNav.classList.remove('active');
        });
    }
    // ==== END OF MOBILE MENU LOGIC ====


    // ==== ENQUIRY MODAL LOGIC ====
    const openEnquiryBtns = document.querySelectorAll('.side-btn.enquiry');
    const enquiryModal = document.getElementById('enquiry-modal');
    
    if (enquiryModal) {
        const closeEnquiryBtn = enquiryModal.querySelector('.modal-close');
        const modalOverlay = enquiryModal.querySelector('.modal-overlay');

        openEnquiryBtns.forEach(btn => {
            btn.addEventListener('click', function(event) {
                event.preventDefault();
                enquiryModal.classList.add('active');
            });
        });

        if (closeEnquiryBtn) {
            closeEnquiryBtn.addEventListener('click', function(event) {
                event.preventDefault();
                enquiryModal.classList.remove('active');
            });
        }

        if (modalOverlay) {
            modalOverlay.addEventListener('click', function() {
                enquiryModal.classList.remove('active');
            });
        }
    }
    // ==== END OF ENQUIRY MODAL LOGIC ====

});