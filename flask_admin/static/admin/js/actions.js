var AdminModelActions = function(actionErrorMessage, actionConfirmations) {
    // Actions helpers. TODO: Move to separate file
    this.execute = function(name) {
        var selected = $('input.action-checkbox:checked').size();

        if (selected === 0) {
            alert(actionErrorMessage);
            return false;
        }

        var msg = actionConfirmations[name];

        if (!!msg)
            if (!confirm(msg))
                return false;

        // Update hidden form and submit it
        var form = $('#action_form');
        $('#action', form).val(name);

        $('input.action-checkbox', form).remove();
        $('input.action-checkbox:checked').each(function() {
            form.append($(this).clone());
        });

        form.submit();

        return false;
    };

    $(function() {
        $('.action-rowtoggle').change(function() {
            $('input.action-checkbox').prop('checked', this.checked);
        });
    });
};
