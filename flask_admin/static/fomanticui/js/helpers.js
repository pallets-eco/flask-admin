(function () {
  window.faHelpers = {
    // A simple confirm() wrapper
    safeConfirm: function (msg) {
      try {
        return confirm(msg) ? true : false;
      } catch (e) {
        return false;
      }
    }
  };
  $('.message .close')
    .on('click', function () {
      $(this)
        .closest('.message')
        .transition('fade');
    });
  $('.ui.dropdown').dropdown();
  $('.ui.accordion').accordion();
})();
