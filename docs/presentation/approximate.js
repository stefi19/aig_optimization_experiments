(() => {
  const slides = [...document.querySelectorAll('.slide')];
  const deck = document.querySelector('.deck');
  const count = document.querySelector('#slide-number');
  const prev = document.querySelector('#prev');
  const next = document.querySelector('#next');
  const notes = document.querySelector('#notes-panel');
  const toggle = document.querySelector('#notes-toggle');
  const overview = document.querySelector('#overview-toggle');
  let current = 0;
  const indexFromHash = () => {
    const match = location.hash.match(/^#slide-(\d+)$/);
    return match ? Number(match[1]) - 1 : 0;
  };
  function render(index, updateHash = true) {
    current = Math.max(0, Math.min(slides.length - 1, index));
    slides.forEach((slide, i) => {
      slide.classList.toggle('active', i === current);
      slide.setAttribute('aria-hidden', deck.classList.contains('overview') || i === current ? 'false' : 'true');
    });
    count.textContent = `${current + 1} / ${slides.length}`;
    prev.disabled = current === 0;
    next.disabled = current === slides.length - 1;
    notes.textContent = slides[current].querySelector('.notes')?.textContent || '';
    document.querySelector('.progress-bar').style.width = `${100 * (current + 1) / slides.length}%`;
    document.title = `${current + 1}. ${slides[current].dataset.title} | AIG Correspondence`;
    if (updateHash) history.replaceState(null, '', `#slide-${current + 1}`);
  }
  function toggleNotes() {
    notes.classList.toggle('visible');
    toggle.setAttribute('aria-expanded', String(notes.classList.contains('visible')));
  }
  prev.addEventListener('click', () => render(current - 1));
  next.addEventListener('click', () => render(current + 1));
  toggle.addEventListener('click', toggleNotes);
  overview.addEventListener('click', () => {
    deck.classList.toggle('overview');
    overview.setAttribute('aria-pressed', String(deck.classList.contains('overview')));
    render(current);
  });
  addEventListener('hashchange', () => render(indexFromHash(), false));
  addEventListener('keydown', event => {
    if (event.target.matches('input,textarea,select')) return;
    if (event.key === ' ' && event.target.matches('button,a')) return;
    if (['ArrowRight', ' ', 'PageDown'].includes(event.key)) { event.preventDefault(); render(current + 1); }
    if (['ArrowLeft', 'PageUp'].includes(event.key)) { event.preventDefault(); render(current - 1); }
    if (event.key === 'Home') { event.preventDefault(); render(0); }
    if (event.key === 'End') { event.preventDefault(); render(slides.length - 1); }
    if (event.key.toLowerCase() === 'n') toggleNotes();
  });
  render(indexFromHash(), false);
})();
