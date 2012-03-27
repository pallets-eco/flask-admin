var adminForm = new function() {
  this.applyStyle = function(el, name) {
    switch (name) {
        case 'chosen':
            $(el).chosen();
            break;
        case 'chosenblank':
            $(el).chosen({allow_single_deselect: true});
            break;
        case 'datepicker':
            $(el).datepicker();
            break;
        case 'datetimepicker':
            $(el).datepicker({displayTime: true});
            break;
    };
  }

  // Apply automatic styles
  $('[data-role=chosen]').chosen();
  $('[data-role=chosenblank]').chosen({allow_single_deselect: true});
  $('[data-role=datepicker]').datepicker();
  $('[data-role=datetimepicker]').datepicker({displayTime: true});
}
