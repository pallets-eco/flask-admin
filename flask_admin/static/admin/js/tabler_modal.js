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
