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

      var isFirstVisit = !sessionStorage.getItem('meltPlayed');

      // Inject text SVG inline — letter-by-letter entrance on first visit only
      injectSVG(navLogotype, function (svg) {
        svg.classList.add('nav__logotype', 'svg-injected');
        svg.style.height = '28px';
        svg.style.width = 'auto';

        if (isFirstVisit) {
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
        }
      });

      // Inject icon SVG inline for melt-drop entrance + hover replay
      injectSVG(navIcon, function (svg) {
        svg.classList.add('nav__logo-icon', 'svg-injected');
        svg.style.height = '54px';
        svg.style.width = 'auto';
        svg.style.marginLeft = '-12px';
        svg.style.overflow = 'visible';

        // --- Melt-drop animation engine ---
        var easeOutCubic = function (t) { return 1 - Math.pow(1 - t, 3); };
        var easeOutQuart = function (t) { return 1 - Math.pow(1 - t, 4); };
        function lerpArr(a, b, t) { return a.map(function (v, i) { return v + (b[i] - v) * t; }); }

        // Animation config (user's chosen settings from prototype)
        var DURATION = 3400;
        var DROP = 200;
        var ROTATION = -18;
        var LOBE_SCALE = 1.15;

        // Crown keyframe matrices: F1 (tilted on head) -> F2 (straightened) -> F3 (tilted again)
        var crownF1 = [1.832551, 0.416626, -0.416626, 1.832551, 95.351392, 1692.706607];
        var crownF2 = [1.87882, 0.043051, -0.043051, 1.87882, -128.955479, 1852.173149];
        var crownF3 = [1.832551, 0.416626, -0.416626, 1.832551, 95.351392, 1692.706607];

        // Circle body: F1 (rounder) -> F3 (squished/melted)
        var circleF1 = [0.528874, -0.005225, 0.0055, 0.556673, 32.810, -48.031];
        var circleF3 = [0.528874, -0.005225, 0.005279, 0.534319, 32.943, -34.574];

        // Lobe max offsets (F1 spread values; F3 = 0,0)
        var lobeMaxLL1 = [164.284, -29.657];
        var lobeMaxLL2 = [125.124, -42.339];
        var lobeMaxRL1 = [-111.297, -27.438];

        // Element refs inside the injected SVG
        var mWrapper = svg.getElementById('melt-wrapper');
        var mCrown = svg.getElementById('melt-crown');
        var mCircle = svg.getElementById('melt-circle');
        var mLL1 = svg.getElementById('melt-ll1');
        var mLL2 = svg.getElementById('melt-ll2');
        var mRL1 = svg.getElementById('melt-rl1');

        var meltAnimId = null;

        function setMeltFrame(t, ct) {
          // Wrapper: rotation + vertical drop centered on viewBox (700,700)
          var rot = ROTATION * (1 - t);
          var dropY = -DROP * (1 - t);
          mWrapper.setAttribute('transform',
            'translate(700,700) rotate(' + rot + ') translate(0,' + dropY + ') translate(-700,-700)');

          // Crown: smooth pass through F2
          var crownVals;
          if (ct < 0.5) {
            crownVals = lerpArr(crownF1, crownF2, ct * 2);
          } else {
            crownVals = lerpArr(crownF2, crownF3, (ct - 0.5) * 2);
          }
          mCrown.setAttribute('transform', 'matrix(' + crownVals.join(',') + ')');

          // Circle: round -> squished
          var circleVals = lerpArr(circleF1, circleF3, t);
          mCircle.setAttribute('transform', 'matrix(' + circleVals.join(',') + ')');

          // Lobes: spread -> tucked
          var lobeT = 1 - t;
          var ls = LOBE_SCALE;
          mLL1.setAttribute('transform', 'translate(' + (lobeMaxLL1[0]*lobeT*ls) + ',' + (lobeMaxLL1[1]*lobeT*ls) + ')');
          mLL2.setAttribute('transform', 'translate(' + (lobeMaxLL2[0]*lobeT*ls) + ',' + (lobeMaxLL2[1]*lobeT*ls) + ')');
          mRL1.setAttribute('transform', 'translate(' + (lobeMaxRL1[0]*lobeT*ls) + ',' + (lobeMaxRL1[1]*lobeT*ls) + ')');
        }

        // Play forward: F1 -> F3 (drop + melt)
        function playMelt(onDone) {
          if (meltAnimId) { cancelAnimationFrame(meltAnimId); meltAnimId = null; }
          function tick(startTime, timestamp) {
            var elapsed = timestamp - startTime;
            var rawT = Math.min(elapsed / DURATION, 1);
            setMeltFrame(easeOutCubic(rawT), easeOutQuart(rawT));
            if (rawT < 1) {
              meltAnimId = requestAnimationFrame(function (ts) { tick(startTime, ts); });
            } else {
              meltAnimId = null;
              if (onDone) onDone();
            }
          }
          meltAnimId = requestAnimationFrame(function (ts) { tick(ts, ts); });
        }

        // Subtle bounce: unsquish 25% then re-melt
        var BOUNCE_PEAK = 0.25; // how far to reverse (0 = none, 1 = full)
        var BOUNCE_OUT = 500;   // ms to unsquish
        var BOUNCE_IN = 1400;   // ms to re-melt (slower, settling feel)
        function playBounceMelt(onDone) {
          if (meltAnimId) { cancelAnimationFrame(meltAnimId); meltAnimId = null; }
          // Phase 1: ease out from t=1 to t=(1-BOUNCE_PEAK)
          function tickOut(startTime, timestamp) {
            var elapsed = timestamp - startTime;
            var rawT = Math.min(elapsed / BOUNCE_OUT, 1);
            var progress = easeOutCubic(rawT) * BOUNCE_PEAK;
            setMeltFrame(1 - progress, 1 - progress);
            if (rawT < 1) {
              meltAnimId = requestAnimationFrame(function (ts) { tickOut(startTime, ts); });
            } else {
              // Phase 2: ease back from t=(1-BOUNCE_PEAK) to t=1
              meltAnimId = requestAnimationFrame(function (ts) { tickIn(ts, ts); });
            }
          }
          function tickIn(startTime, timestamp) {
            var elapsed = timestamp - startTime;
            var rawT = Math.min(elapsed / BOUNCE_IN, 1);
            var progress = BOUNCE_PEAK * (1 - easeOutCubic(rawT));
            setMeltFrame(1 - progress, 1 - progress);
            if (rawT < 1) {
              meltAnimId = requestAnimationFrame(function (ts) { tickIn(startTime, ts); });
            } else {
              meltAnimId = null;
              if (onDone) onDone();
            }
          }
          meltAnimId = requestAnimationFrame(function (ts) { tickOut(ts, ts); });
        }

        // Entrance behavior
        if (isFirstVisit) {
          // First visit: fade in + full drop animation after letters finish
          svg.style.opacity = '0';
          var entranceDelay = (0.4 + 13 * 0.045 + 0.15) * 1000;
          setTimeout(function () {
            svg.style.transition = 'opacity 0.3s ease-out';
            svg.style.opacity = '1';
            playMelt(function () {
              sessionStorage.setItem('meltPlayed', '1');
            });
          }, entranceDelay);
        } else {
          // Return visit: reverse-then-forward bounce
          playBounceMelt();
        }

        // Hover: reverse-then-forward bounce
        var isAnimating = false;
        navLogo.addEventListener('mouseenter', function () {
          if (isAnimating) return;
          isAnimating = true;
          playBounceMelt(function () { isAnimating = false; });
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

  // --- Chapters expand/collapse ---
  var chaptersToggle = document.getElementById('chaptersToggle');
  var chaptersSection = document.getElementById('chaptersSection');
  if (chaptersToggle && chaptersSection) {
    chaptersToggle.addEventListener('click', function () {
      var expanded = chaptersSection.classList.toggle('chapters--expanded');
      chaptersToggle.setAttribute('aria-expanded', expanded);
      var textEl = chaptersToggle.querySelector('.chapters__toggle-text');
      if (textEl) {
        textEl.textContent = expanded ? 'Show less' : textEl.dataset.collapsed;
      }
    });
    // Store the collapsed label
    var textEl = chaptersToggle.querySelector('.chapters__toggle-text');
    if (textEl) textEl.dataset.collapsed = textEl.textContent;
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
