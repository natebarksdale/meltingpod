// ============================================
// THE MELTING POD v7 — Interactions
// ============================================

(function () {
  'use strict';

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // --- Nav scroll effect ---
  const nav = document.getElementById('nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('nav--scrolled', window.scrollY > 40);
    }, { passive: true });
  }

  // --- Mobile menu ---
  const burger = document.getElementById('navBurger');
  const mobileMenu = document.getElementById('mobileMenu');

  if (burger && mobileMenu) {
    burger.addEventListener('click', () => {
      const isOpen = burger.classList.toggle('nav__burger--open');
      mobileMenu.classList.toggle('mobile-menu--open');
      burger.setAttribute('aria-expanded', isOpen);
      mobileMenu.setAttribute('aria-hidden', !isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && mobileMenu.classList.contains('mobile-menu--open')) {
        burger.click();
      }
    });
  }

  // --- Generate waveform bars ---
  document.querySelectorAll('.player__bars').forEach(container => {
    const barCount = 60;
    for (let i = 0; i < barCount; i++) {
      const bar = document.createElement('div');
      bar.className = 'player__bar';
      // Random heights for waveform look
      const h = 15 + Math.random() * 85;
      bar.style.height = h + '%';
      container.appendChild(bar);
    }
  });

  // --- Mock audio player ---
  document.querySelectorAll('.player__play').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const svg = btn.querySelector('svg');
      const isPlaying = btn.classList.toggle('player__play--playing');
      svg.innerHTML = isPlaying
        ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>'
        : '<path d="M8 5v14l11-7z"/>';
      btn.setAttribute('aria-label', isPlaying ? 'Pause episode' : 'Play episode');
    });
  });

  // --- Scroll-triggered reveals ---
  if (!prefersReducedMotion) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.08,
      rootMargin: '0px 0px -30px 0px'
    });

    document.querySelectorAll('.scroll-reveal').forEach(el => {
      revealObserver.observe(el);
    });
  } else {
    document.querySelectorAll('.scroll-reveal').forEach(el => {
      el.classList.add('is-visible');
    });
  }

  // --- Stagger episode cards ---
  if (!prefersReducedMotion) {
    document.querySelectorAll('.episode-card').forEach((card, i) => {
      card.style.transitionDelay = `${i * 0.08}s`;
    });
  }

  // --- Logo animations (nav) ---
  if (!prefersReducedMotion) {
    const navLogo = document.querySelector('.nav__logo');
    if (navLogo) {
      const navLogotype = navLogo.querySelector('.nav__logotype');
      const navIcon = navLogo.querySelector('.nav__logo-icon');

      // Inject text SVG inline for letter-by-letter entrance
      injectSVG(navLogotype, function (svg) {
        svg.classList.add('nav__logotype', 'svg-injected');
        svg.style.height = '28px';
        svg.style.width = 'auto';

        var letters = svg.querySelectorAll('[id^="_"]');
        letters.forEach(function (letter, i) {
          letter.style.transformBox = 'fill-box';
          letter.style.transformOrigin = 'center center';
          letter.style.opacity = '0';
          letter.style.transform = 'translateY(6px)';
          letter.style.transition = 'opacity 0.45s ease-out, transform 0.45s ease-out';
          letter.style.transitionDelay = (0.4 + i * 0.045) + 's';
        });
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            letters.forEach(function (letter) {
              letter.style.opacity = '1';
              letter.style.transform = 'translateY(0)';
            });
          });
        });
      });

      // Inject icon SVG inline for entrance bounce + hover wobble
      injectSVG(navIcon, function (svg) {
        svg.classList.add('nav__logo-icon', 'svg-injected');
        svg.style.height = '40px';
        svg.style.width = 'auto';
        svg.style.marginLeft = '-8px';
        svg.style.overflow = 'visible';

        // Entrance: pop in with spring bounce after letters finish
        svg.style.opacity = '0';
        svg.style.transform = 'scale(0.8)';
        svg.style.transition = 'opacity 0.5s cubic-bezier(0.23,1,0.32,1), transform 0.6s cubic-bezier(0.34,1.56,0.64,1)';
        svg.style.transitionDelay = (0.4 + 13 * 0.045 + 0.15) + 's';
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            svg.style.opacity = '1';
            svg.style.transform = 'scale(1)';
          });
        });

        // Hover: bouncy zoom on the whole icon
        svg.style.transformOrigin = 'center center';
        navLogo.addEventListener('mouseenter', function () {
          if (svg.style.animationName === 'logoWobble') return;
          svg.style.animation = 'logoWobble 0.5s cubic-bezier(0.34,1.56,0.64,1)';
          svg.addEventListener('animationend', function () {
            svg.style.animation = '';
          }, { once: true });
        });
      });
    }
  }

  // --- Chapter timestamp seeking (Megaphone player) ---
  const megaphonePlayer = document.getElementById('megaphonePlayer');
  if (megaphonePlayer) {
    function seekTo(seconds) {
      const baseSrc = megaphonePlayer.src.split('?')[0];
      megaphonePlayer.src = baseSrc + '?start=' + seconds;
      megaphonePlayer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Click on timestamp button
    document.querySelectorAll('.chapters__time[data-seconds]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        seekTo(parseInt(btn.dataset.seconds, 10));
      });
    });

    // Click anywhere on the chapter row
    document.querySelectorAll('.chapters__item').forEach(item => {
      item.addEventListener('click', () => {
        const btn = item.querySelector('.chapters__time[data-seconds]');
        if (btn) seekTo(parseInt(btn.dataset.seconds, 10));
      });
    });
  }

  // --- SVG injection utility ---
  function injectSVG(imgEl, callback) {
    if (!imgEl || !imgEl.src) return;
    fetch(imgEl.src)
      .then(function (res) { return res.text(); })
      .then(function (svgText) {
        var parser = new DOMParser();
        var doc = parser.parseFromString(svgText, 'image/svg+xml');
        var svg = doc.documentElement;
        var alt = imgEl.getAttribute('alt');
        if (alt) {
          svg.setAttribute('role', 'img');
          svg.setAttribute('aria-label', alt);
        } else {
          svg.setAttribute('aria-hidden', 'true');
        }
        imgEl.parentNode.replaceChild(svg, imgEl);
        if (callback) callback(svg);
      })
      .catch(function () {
        // Graceful degradation: img stays as-is
      });
  }

})();
