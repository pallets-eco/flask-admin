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

    $('.confirm-first').on('click', function (e)
    {
        console.log('confirm-first');
        var message = $(this).data('msg');
        return confirm(message);
    });

    $('.btn-delete-row').on('click', function (e)
    {
        const msg = $(this).data('msg');
        return faHelpers.safeConfirm(msg);
    });


})();
