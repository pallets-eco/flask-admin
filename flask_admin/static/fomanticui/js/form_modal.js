$(document).ready(function () {
    $('#fa-modal').modal({
        autofocus: false,
        observeChanges: true,
        onApprove: function (elm) {
            $('#fa-modal-content form').submit();
        },
        onHidden: function () {
            // Revert loading dimmer for better performance and UX
            $('#fa-modal-content').html('<br><br><div class="ui active inverted dimmer"><div class="ui loader"></div></div><br><br>');
        }
    });
    $('a.modal-opener').click(function (event) {
        event.preventDefault();
        $('#fa-modal').modal('show');
        var $this = $(this);
        var action = $this.data('action');
        if (action === 'view') {
            $('#fa-modal > .actions').hide();
        } else if (action === 'edit') {
            $('#fa-modal > .actions').show();
        }
        var url = $this.attr('href');
        $('#fa-modal-content').load(url, function () {
            // Remove loading dimmer after content is loaded
            window.faForm.applyGlobalStyles(document.getElementById('fa-modal-content'));
        });

    });
});
