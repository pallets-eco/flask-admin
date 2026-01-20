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

    $(document).ready(function() {
        // Prevent default action for all links with 'unlink-btn' class
        $('a.unlink-btn').click( (e) => {
            e.preventDefault();
        });
    });
})();
