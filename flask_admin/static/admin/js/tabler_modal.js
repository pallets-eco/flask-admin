document.addEventListener('show.bs.modal', function (event) {
    const trigger = event.relatedTarget;
    if (!trigger) return;

    const href = trigger.getAttribute('href');
    if (!href || href === '#' || href.startsWith('javascript')) return;

    const modalContent = event.target.querySelector('.modal-content');
    if (!modalContent) return;

    modalContent.innerHTML = '<div class="modal-body text-center py-5"><div class="spinner-border" role="status"></div></div>';

    fetch(href)
        .then(function (response) {
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            return response.text();
        })
        .then(function (html) {
            modalContent.innerHTML = html;
        })
        .catch(function (error) {
            modalContent.innerHTML = '<div class="modal-body text-danger">' + error.message + '</div>';
        });
});
