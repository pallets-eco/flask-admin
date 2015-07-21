// filters the details table based on input
$(document).ready(function () {
  $('#fa_filter').keyup(function () {
      var rex = new RegExp($(this).val(), 'i');
      $('.searchable tr').hide();
      $('.searchable tr').filter(function () {
          return rex.test($(this).text());
      }).show();
  });
});
