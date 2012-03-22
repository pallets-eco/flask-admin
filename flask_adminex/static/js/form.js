$(function() {
  $('[data-role=chosen]').chosen();
  $('[data-role=chosenblank]').chosen({allow_single_deselect: true});
  $('[data-role=datepicker]').datepicker();
  $('[data-role=datetimepicker]').datepicker({displayTime: true});
});
