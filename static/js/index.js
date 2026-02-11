window.HELP_IMPROVE_VIDEOJS = false;

// More Works Dropdown Functionality
function toggleMoreWorks() {
    const dropdown = document.getElementById('moreWorksDropdown');
    const button = document.querySelector('.more-works-btn');
    
    if (dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
        button.classList.remove('active');
    } else {
        dropdown.classList.add('show');
        button.classList.add('active');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const container = document.querySelector('.more-works-container');
    const dropdown = document.getElementById('moreWorksDropdown');
    const button = document.querySelector('.more-works-btn');
    
    if (container && !container.contains(event.target)) {
        dropdown.classList.remove('show');
        button.classList.remove('active');
    }
});

// Close dropdown on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const dropdown = document.getElementById('moreWorksDropdown');
        const button = document.querySelector('.more-works-btn');
        dropdown.classList.remove('show');
        button.classList.remove('active');
    }
});

// Copy BibTeX to clipboard
function copyBibTeX() {
    const bibtexElement = document.getElementById('bibtex-code');
    const button = document.querySelector('.copy-bibtex-btn');
    const copyText = button.querySelector('.copy-text');
    
    if (bibtexElement) {
        navigator.clipboard.writeText(bibtexElement.textContent).then(function() {
            // Success feedback
            button.classList.add('copied');
            copyText.textContent = 'Cop';
            
            setTimeout(function() {
                button.classList.remove('copied');
                copyText.textContent = 'Copy';
            }, 2000);
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = bibtexElement.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            button.classList.add('copied');
            copyText.textContent = 'Cop';
            setTimeout(function() {
                button.classList.remove('copied');
                copyText.textContent = 'Copy';
            }, 2000);
        });
    }
}

// Scroll to top functionality
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Show/hide scroll to top button
window.addEventListener('scroll', function() {
    const scrollButton = document.querySelector('.scroll-to-top');
    if (window.pageYOffset > 300) {
        scrollButton.classList.add('visible');
    } else {
        scrollButton.classList.remove('visible');
    }
});

// Video carousel autoplay when in view
function setupVideoCarouselAutoplay() {
    const carouselVideos = document.querySelectorAll('.results-carousel video');
    
    if (carouselVideos.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const video = entry.target;
            if (entry.isIntersecting) {
                // Video is in view, play it
                video.play().catch(e => {
                    // Autoplay failed, probably due to browser policy
                    console.log('Autoplay prevented:', e);
                });
            } else {
                // Video is out of view, pause it
                video.pause();
            }
        });
    }, {
        threshold: 0.5 // Trigger when 50% of the video is visible
    });
    
    carouselVideos.forEach(video => {
        observer.observe(video);
    });
}

function setupUserCasesTabs() {
    const tabs = document.querySelectorAll('.case-tab');
    const panels = document.querySelectorAll('.case-panel');

    if (tabs.length === 0 || panels.length === 0) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-case');

            tabs.forEach(btn => {
                btn.classList.remove('is-active');
                btn.setAttribute('aria-selected', 'false');
            });

            panels.forEach(panel => {
                panel.classList.remove('is-active');
                panel.setAttribute('aria-hidden', 'true');
            });

            tab.classList.add('is-active');
            tab.setAttribute('aria-selected', 'true');

            const activePanel = document.querySelector(`.case-panel[data-case="${target}"]`);
            if (activePanel) {
                activePanel.classList.add('is-active');
                activePanel.setAttribute('aria-hidden', 'false');
            }
        });
    });
}

function setupCaseFigureCarousels() {
    const wrappers = document.querySelectorAll('.case-carousel-wrapper');

    wrappers.forEach(wrapper => {
        const track = wrapper.querySelector('.case-carousel-track');
        const slides = wrapper.querySelectorAll('.case-slide');
        const dots = wrapper.querySelectorAll('.case-dot');

        if (!track || slides.length === 0 || dots.length === 0) return;

        const setActive = (index) => {
            const clampedIndex = Math.max(0, Math.min(index, slides.length - 1));
            track.style.transform = `translateX(-${clampedIndex * 100}%)`;

            dots.forEach((dot, dotIndex) => {
                const isActive = dotIndex === clampedIndex;
                dot.classList.toggle('is-active', isActive);
                dot.setAttribute('aria-selected', isActive ? 'true' : 'false');
            });
        };

        dots.forEach(dot => {
            dot.addEventListener('click', () => {
                const index = Number(dot.getAttribute('data-index'));
                if (!Number.isNaN(index)) {
                    setActive(index);
                }
            });
        });

        setActive(0);
    });
}

function setupExternalCodeBlocks() {
    const codeBlocks = document.querySelectorAll('code[data-code-src]');
    if (codeBlocks.length === 0) return;

    codeBlocks.forEach(async (codeBlock) => {
        const source = codeBlock.getAttribute('data-code-src');
        if (!source) return;

        try {
            const response = await fetch(source);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const text = await response.text();
            codeBlock.textContent = text;
        } catch (error) {
            console.error(`Failed to load code from ${source}:`, error);
            codeBlock.textContent = `# Failed to load code from ${source}`;
        }
    });
}

$(document).ready(function() {
    // Check for click events on the navbar burger icon

    var options = {
		slidesToScroll: 1,
		slidesToShow: 1,
		loop: true,
		infinite: true,
		autoplay: true,
		autoplaySpeed: 5000,
    }

	// Initialize all div with carousel class
    var carousels = bulmaCarousel.attach('.carousel', options);
	
    bulmaSlider.attach();
    
    // Setup video autoplay for carousel
    setupVideoCarouselAutoplay();
    setupUserCasesTabs();
    setupCaseFigureCarousels();
    setupExternalCodeBlocks();

})
