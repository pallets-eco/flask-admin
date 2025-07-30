$(document).ready(function () {
    $('#fa-modal').modal({
        autofocus: false,
        observeChanges: true,
        onApprove: function (elm) {
            $('#fa-modal-content form').submit();
        }
    });
    $('a.modal-opener').click(function (event) {
        event.preventDefault();
        var url = $(this).attr('href');
        $('#fa-modal-content').empty();
        $('#fa-modal').modal('show');
        // @TODO: Dimmer a loader while fetching
        $('#fa-modal-content').load(url);
        window.faForm.applyGlobalStyles(document.getElementById('fa-modal-content'));
    });
});
