// fixes "content does not load remote modal on clicked modal button"
$('body').on('click.modal.data-api', '[data-toggle="modal"]', function () {
    $($(this).data("target") + ' .modal-content').load($(this).attr('href'));
});

$(function() {
  // Apply flask-admin form styles after the modal is loaded
  window.faForm.applyGlobalStyles(document);
});
