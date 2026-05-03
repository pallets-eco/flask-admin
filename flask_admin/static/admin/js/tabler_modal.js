// Handles remote content loading for Bootstrap 5 / Tabler modals.
// Replaces bs4_modal.js (which relied on jQuery and Bootstrap 4 data attributes).
//
// Bootstrap 5 opens the modal itself via data-bs-toggle/data-bs-target.
// This script only handles loading remote content into .modal-content
// by hooking the show.bs.modal event and reading the triggering element's href.
document.addEventListener('show.bs.modal', function (event) {
    const trigger = event.relatedTarget;
    if (!trigger) return;

    const href = trigger.getAttribute('href');
    if (!href || href === '#' || href.startsWith('javascript')) return;

    const modalContent = event.target.querySelector('.modal-content');
    if (!modalContent) return;

    fetch(href)
        .then(function (response) { return response.text(); })
        .then(function (html) { modalContent.innerHTML = html; });
});
