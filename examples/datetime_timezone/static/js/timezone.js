// post client's timezone so that backend can correctly convert datetime inputs to UTC
fetch('/set_timezone', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(Intl.DateTimeFormat().resolvedOptions().timeZone)
})

// convert all datetime fields to client timezone
function localizeDateTimes() {
  const inputsOrSpans = document.querySelectorAll('input[data-date-format], span.timezone-aware');

  inputsOrSpans.forEach(element => {
    const isInput = element.tagName.toLowerCase() === 'input';
    const rawValue = isInput
      ? element.getAttribute("value")
      : element.textContent.trim();

    // Skip empty, missing, or Python "None" values
    if (!rawValue || rawValue === 'None') return;

    const localizedTime = new Date(rawValue + "Z");

    // Skip if the date parsed as invalid
    if (isNaN(localizedTime.getTime())) return;

    const formattedTime = moment(localizedTime).format('YYYY-MM-DD HH:mm:ss');

    if (isInput) {
      element.setAttribute("value", formattedTime);
    } else {
      element.textContent = formattedTime;
    }
  });
}

localizeDateTimes();
