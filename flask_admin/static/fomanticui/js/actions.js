var AdminModelActions = function (actionErrorMessage, actionConfirmations) {
    // batch actions helpers
    this.execute = function (name) {
        var selected = $('input.action-checkbox:checked').length;

        if (selected === 0) {
            $.toast({
                'class': 'warning yellow inverted',
                'message': actionErrorMessage
            });
            return false;
        }

        var msg = actionConfirmations[name];

        if (!!msg)
            // @TODO: change to modal: https://fomantic-ui.com/modules/modal.html
            if (!confirm(msg))
                return false;

        // Update hidden form and submit it
        var form = $('#action_form');
        $('#action', form).val(name);

        $('input.action-checkbox', form).remove();
        $('input.action-checkbox:checked').each(function () {
            form.append($(this).clone());
        });
        form.submit();

        return false;
    };

    $(function () {
        $('.action-rowtoggle').change(function () {
            $('input.action-checkbox').prop('checked', this.checked);
            $('input.action-checkbox').closest('tr').toggleClass('violet', this.checked);
        });
    });

    $(function () {
        $('input.action-checkbox').change(function () {
            $(this).closest('tr').toggleClass('violet', this.checked);
        });
    });
    $(function () {
        var inputs = $('input.action-checkbox');
        inputs.change(function () {
            var allInputsChecked = true;
            for (var i = 0; i < inputs.length; i++) {
                if (!inputs[i].checked) {
                    allInputsChecked = false;
                    break;
                }
            }
            $('.action-rowtoggle').attr('checked', allInputsChecked);
        });
    });
};
var modelActions = new AdminModelActions(JSON.parse($('#message-data').text()), JSON.parse($('#actions-confirmation-data').text()));





