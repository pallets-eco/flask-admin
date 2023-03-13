// fixes "remote modal shows same content every time"
$('.modal').on('hidden', function() {
  $(this).removeData('modal');
});

$(function() {
  // Apply flask-admin form styles after the modal is loaded
  window.faForm.applyGlobalStyles(document);
});
