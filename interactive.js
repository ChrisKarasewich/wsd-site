/* WSD — interactive behaviour for the pre-rendered static site.
   Pure vanilla JS. No framework. */
(function(){
  'use strict';

  // --- Header scrolled state -----------------------------------------------
  const header = document.querySelector('header');
  if (header) {
    const update = () => {
      header.style.borderBottomColor =
        window.scrollY > 16 ? 'var(--border)' : 'transparent';
    };
    update();
    window.addEventListener('scroll', update, { passive: true });
  }

  // --- FAQ accordion -------------------------------------------------------
  document.querySelectorAll('.faq-item__q').forEach(q => {
    q.addEventListener('click', () => {
      const item = q.closest('.faq-item');
      if (!item) return;
      const group = item.closest('.faq');
      const willOpen = !item.classList.contains('open');
      if (willOpen && group) {
        group.querySelectorAll('.faq-item.open').forEach(i => i.classList.remove('open'));
      }
      item.classList.toggle('open', willOpen);
    });
  });

  // --- Booking form: send to Google Apps Script (sheet + email), then redirect
  // The Apps Script web app appends the submission to the Google Sheet AND emails
  // info@winnipegsd.com. See SETUP-form.md for how to deploy it and get this URL.
  //
  // Paste your deployed web-app URL below (it ends in /exec). Until a real URL is
  // in place the form fails safely and tells the visitor to call instead.
  const FORM_ENDPOINT = 'https://script.google.com/macros/s/AKfycbzE1kQ9sX_HXo8T48Qx7qytzLrkXfGVyIMGPnnbizgb6xbvgYRL-Q7wEtqmMJnmkwoB/exec';

  // --- reCAPTCHA v3 (invisible) -------------------------------------------
  // Public site key — safe to expose. The matching SECRET key lives only in the
  // Apps Script (Code.gs) and verifies each token server-side before a lead is
  // saved/emailed. If you ever rotate keys, update both places.
  const RECAPTCHA_SITE_KEY = '6LdGziQtAAAAAJGGeOC6t1VWbomcQas-j1Z2Ll0D';

  // Load the reCAPTCHA v3 library once, on any page that has a booking form.
  if (RECAPTCHA_SITE_KEY && document.querySelector('form.card') &&
      !document.querySelector('script[data-recaptcha]')) {
    const rc = document.createElement('script');
    rc.src = 'https://www.google.com/recaptcha/api.js?render=' + RECAPTCHA_SITE_KEY;
    rc.async = true; rc.defer = true;
    rc.setAttribute('data-recaptcha', '');
    document.head.appendChild(rc);
  }

  // Resolve a fresh v3 token. Waits briefly for the library if it's still loading,
  // and resolves to '' if reCAPTCHA never becomes available (the server then decides).
  function getRecaptchaToken() {
    return new Promise(resolve => {
      if (!RECAPTCHA_SITE_KEY) { resolve(''); return; }
      let waited = 0;
      const tryExec = () => {
        if (typeof grecaptcha !== 'undefined' && grecaptcha.execute) {
          grecaptcha.ready(() => {
            grecaptcha.execute(RECAPTCHA_SITE_KEY, { action: 'submit' })
              .then(token => resolve(token || ''))
              .catch(() => resolve(''));
          });
        } else if (waited < 5000) {
          waited += 200;
          setTimeout(tryExec, 200);
        } else {
          resolve('');
        }
      };
      tryExec();
    });
  }

  document.querySelectorAll('form.card').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = form.querySelector('button[type="submit"], button:not([type])');
      const restore = () => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.style.opacity = '';
          submitBtn.style.pointerEvents = '';
        }
      };
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.65';
        submitBtn.style.pointerEvents = 'none';
      }

      try {
        // Get a reCAPTCHA v3 token and attach it to the submission so the
        // Apps Script can verify the visitor server-side.
        const token = await getRecaptchaToken();
        const payload = new FormData(form);
        if (token) payload.append('g-recaptcha-response', token);

        // Apps Script web apps don't return CORS headers, so we POST with
        // mode:'no-cors'. The request still reaches the server (row is written and
        // the email is sent); we just can't read the response, so a completed
        // request is treated as success.
        await fetch(FORM_ENDPOINT, {
          method: 'POST',
          mode: 'no-cors',
          body: payload
        });
        window.location.href = 'thank-you.html';
      } catch (err) {
        restore();
        alert("Sorry — we couldn't send your request just now. " +
              "Please call us at (204) 786-4060 and we'll get you booked right away.");
      }
    });
  });

  // --- Recent-updates category filter --------------------------------------
  // Filter buttons live in a .container that has a 'Filter by' label.
  // Each post card sits inside a flex grid; we tag them with their category at runtime.
  const filterStrip = Array.from(document.querySelectorAll('section'))
    .find(s => s.textContent.includes('Filter by'));
  if (filterStrip) {
    const buttons = filterStrip.querySelectorAll('button');
    if (buttons.length) {
      const setActive = (label) => {
        buttons.forEach(b => {
          const active = b.textContent.trim().toLowerCase() === label.toLowerCase();
          b.style.background = active ? 'var(--wsd-navy)' : 'white';
          b.style.color = active ? 'white' : 'var(--wsd-navy)';
          b.style.borderColor = active ? 'var(--wsd-navy)' : 'var(--border)';
        });
      };
      buttons.forEach(b => {
        b.addEventListener('click', () => setActive(b.textContent.trim()));
      });
    }
  }

  // --- Mobile navigation drawer (injected on small screens) --------------
  (function setupMobileNav() {
    const headerEl = document.querySelector('header');
    if (!headerEl) return;
    const containerEl = headerEl.querySelector(':scope > .container');
    if (!containerEl) return;

    // Build the hamburger button and append to the header.
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'wsd-hamburger';
    btn.setAttribute('aria-label', 'Open menu');
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" ' +
      'stroke-linecap="round" stroke-linejoin="round">' +
      '<line x1="3" y1="6" x2="21" y2="6"/>' +
      '<line x1="3" y1="12" x2="21" y2="12"/>' +
      '<line x1="3" y1="18" x2="21" y2="18"/></svg>';
    containerEl.appendChild(btn);

    // Build the drawer from the existing nav links.
    const drawer = document.createElement('div');
    drawer.className = 'wsd-mobile-nav';
    drawer.innerHTML =
      '<div class="wsd-mobile-nav__panel" role="dialog" aria-label="Site navigation">' +
        '<div class="wsd-mobile-nav__head">' +
          '<a href="index.html"><img src="assets/wsd-logo-primary.png" alt="Winnipeg Sewer and Drain"/></a>' +
          '<button type="button" class="wsd-mobile-nav__close" aria-label="Close menu">' +
            '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" ' +
            'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">' +
            '<line x1="18" y1="6" x2="6" y2="18"/>' +
            '<line x1="6" y1="6" x2="18" y2="18"/></svg>' +
          '</button>' +
        '</div>' +
        '<div class="wsd-mobile-nav__body"></div>' +
        '<div class="wsd-mobile-nav__foot">' +
          '<a class="btn btn--amber btn--md" href="tel:+12047864060">' +
            '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" ' +
            'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 ' +
            '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.12.9.34 1.78.66 2.62a2 ' +
            '2 0 0 1-.45 2.11L8 9.91a16 16 0 0 0 6 6l1.46-1.32a2 2 0 0 1 2.11-.45c.84.32 1.72.54 2.62.66A2 ' +
            '2 0 0 1 22 16.92z"/></svg>' +
            ' Call (204) 786-4060</a>' +
          '<small>24/7 emergency line · Same-day across Winnipeg</small>' +
        '</div>' +
      '</div>';

    // Populate the body with the same links the desktop nav uses.
    const body = drawer.querySelector('.wsd-mobile-nav__body');
    const navEl = containerEl.querySelector(':scope > nav');
    if (navEl) {
      // Each child of the nav is either an <a> (no children) or a <div> wrapper
      // containing a top-level <a> + a dropdown panel of <a>s.
      navEl.querySelectorAll(':scope > a, :scope > div').forEach(item => {
        if (item.tagName === 'A') {
          const a = document.createElement('a');
          a.className = 'wsd-mobile-nav__link';
          a.href = item.getAttribute('href');
          a.textContent = item.textContent.trim();
          body.appendChild(a);
        } else {
          // div wrapper — first <a> is the parent label, the rest are children.
          // Render as a collapsible dropdown group.
          const links = item.querySelectorAll('a');
          if (!links.length) return;
          const parent = links[0];

          const group = document.createElement('div');
          group.className = 'wsd-mobile-nav__group';

          const toggle = document.createElement('button');
          toggle.type = 'button';
          toggle.className = 'wsd-mobile-nav__toggle';
          toggle.setAttribute('aria-expanded', 'false');
          toggle.innerHTML =
            '<span>' + parent.textContent.trim() + '</span>' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<polyline points="6 9 12 15 18 9"></polyline></svg>';

          const sub = document.createElement('div');
          sub.className = 'wsd-mobile-nav__sub';
          const inner = document.createElement('div');
          inner.className = 'wsd-mobile-nav__sub-inner';
          for (let i = 1; i < links.length; i++) {
            const sa = document.createElement('a');
            sa.href = links[i].getAttribute('href');
            sa.textContent = links[i].textContent.trim();
            inner.appendChild(sa);
          }
          sub.appendChild(inner);
          group.appendChild(toggle);
          group.appendChild(sub);
          body.appendChild(group);

          toggle.addEventListener('click', () => {
            const isOpen = group.classList.toggle('open');
            toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
          });
        }
      });
    }

    document.body.appendChild(drawer);

    const open  = () => { drawer.classList.add('open');    document.body.classList.add('wsd-mobile-nav-open'); };
    const close = () => { drawer.classList.remove('open'); document.body.classList.remove('wsd-mobile-nav-open'); };

    btn.addEventListener('click', open);
    drawer.addEventListener('click', (e) => {
      if (e.target === drawer) close();
    });
    drawer.querySelector('.wsd-mobile-nav__close').addEventListener('click', close);
    drawer.querySelectorAll('.wsd-mobile-nav__body a').forEach(a => {
      a.addEventListener('click', close);
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close();
    });
  })();

})();
