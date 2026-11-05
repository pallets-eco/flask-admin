(function() {
    window.faHelpers = {
        // A simple confirm() wrapper
        safeConfirm: function(msg) {
            try {
                return confirm(msg) ? true : false;
            } catch (e) {
                return false;
            }
        }
    };

    $('.a-unlink').on('click', function(e) {
      e.preventDefault();
    });

})();
