(() => {
  const notice = document.querySelector('#form-errors, #form-success');
  if (notice) notice.focus({ preventScroll: true });
  const form = document.querySelector('.inquiry-form');
  if (form) form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Sending…';
  });
  window.addEventListener('pageshow', () => {
    const button = document.querySelector('.inquiry-form button[type="submit"]');
    if (button) { button.disabled = false; button.innerHTML = 'Send inquiry <span aria-hidden="true">↗</span>'; }
  });
})();
