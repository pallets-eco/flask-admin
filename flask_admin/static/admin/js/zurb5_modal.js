// fixes "remote modal shows same content every time"
$('.modal').on('hidden', function() {
  $(this).removeData('modal');
});
