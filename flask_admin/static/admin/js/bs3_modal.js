// fixes "remote modal shows same content every time", avoiding the flicker
$('body').on('hidden.bs.modal', '.modal', function () {
  $(this).removeData('bs.modal').find(".modal-content").empty();
});

$(function() {
  // Apply flask-admin form styles after the modal is loaded
  window.faForm.applyGlobalStyles(document);
});
