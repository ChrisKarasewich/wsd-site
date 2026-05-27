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

  // --- Booking form: simulate submit & show thank-you state ---------------
  document.querySelectorAll('form.card').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const phone = (form.querySelector('input[type="tel"]') || {}).value || '';
      form.outerHTML =
        '<div class="card" style="padding:40px 36px;background:var(--wsd-blue-50);' +
        'border-color:var(--wsd-blue-100);border-left:4px solid var(--wsd-blue);text-align:left;">' +
        '<div style="width:48px;height:48px;border-radius:50%;background:var(--wsd-blue);color:white;' +
          'display:flex;align-items:center;justify-content:center;margin-bottom:18px;">' +
          '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
          'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>' +
        '</div>' +
        '<h3 style="font-size:32px;color:var(--wsd-navy);margin-bottom:12px;">Request received.</h3>' +
        '<p style="font-size:16px;color:var(--fg-1);line-height:1.5;margin-bottom:20px;max-width:46ch;">' +
          "We'll call you within 15 minutes to confirm the appointment. " +
          'If it&rsquo;s an active backup, call ' +
          '<a href="tel:+12045550123" style="font-weight:700;">(204) 555-0123</a> instead &mdash; ' +
          'we hold same-day slots for emergencies.' +
        '</p></div>';
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

})();
