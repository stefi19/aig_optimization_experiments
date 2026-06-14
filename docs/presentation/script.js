(function () {
  const slides = Array.from(document.querySelectorAll(".slide"));
  const progressBar = document.querySelector(".progress-bar");
  const slideNumber = document.querySelector("#slide-number");
  const prevButton = document.querySelector("#prev");
  const nextButton = document.querySelector("#next");
  const notesButton = document.querySelector("#notes-toggle");
  const notesPanel = document.querySelector("#notes-panel");
  let current = 0;

  function clampIndex(index) {
    return Math.max(0, Math.min(slides.length - 1, index));
  }

  function notesFor(slide) {
    const notes = slide.querySelector(".notes");
    return notes ? notes.textContent.trim() : "";
  }

  function renderNotes() {
    const text = notesFor(slides[current]);
    notesPanel.innerHTML = text
      ? `<h3>Speaker notes</h3><p>${escapeHtml(text)}</p>`
      : "<h3>Speaker notes</h3><p>No notes for this slide.</p>";
  }

  function showSlide(index) {
    current = clampIndex(index);
    slides.forEach((slide, i) => {
      slide.classList.toggle("active", i === current);
      slide.setAttribute("aria-hidden", i === current ? "false" : "true");
    });
    const progress = ((current + 1) / slides.length) * 100;
    progressBar.style.width = `${progress}%`;
    slideNumber.textContent = `${current + 1} / ${slides.length}`;
    prevButton.disabled = current === 0;
    nextButton.disabled = current === slides.length - 1;
    renderNotes();
    window.location.hash = `slide-${current + 1}`;
  }

  function escapeHtml(text) {
    return text
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function initialSlideFromHash() {
    const match = window.location.hash.match(/^#slide-(\d+)$/);
    if (!match) {
      return 0;
    }
    return clampIndex(Number(match[1]) - 1);
  }

  prevButton.addEventListener("click", () => showSlide(current - 1));
  nextButton.addEventListener("click", () => showSlide(current + 1));
  notesButton.addEventListener("click", () => {
    notesPanel.classList.toggle("visible");
    renderNotes();
  });

  document.addEventListener("keydown", (event) => {
    const tagName = event.target && event.target.tagName;
    if (tagName === "INPUT" || tagName === "TEXTAREA" || tagName === "SELECT") {
      return;
    }

    if (event.key === "ArrowRight" || event.key === " ") {
      event.preventDefault();
      showSlide(current + 1);
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      showSlide(current - 1);
    } else if (event.key === "Home") {
      event.preventDefault();
      showSlide(0);
    } else if (event.key === "End") {
      event.preventDefault();
      showSlide(slides.length - 1);
    } else if (event.key.toLowerCase() === "n") {
      notesPanel.classList.toggle("visible");
      renderNotes();
    }
  });

  showSlide(initialSlideFromHash());
})();
