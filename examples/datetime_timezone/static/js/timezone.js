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
    let localizedTime;

    const isInput = element.tagName.toLowerCase() === 'input'
    // Check if the element is an input or a span
    if (isInput) {
      // For input elements, use the value attribute
      localizedTime = new Date(element.getAttribute("value") + "Z");
    } else {
      // For span elements, use the text content
      localizedTime = new Date(element.textContent.trim() + "Z");
    }

    const formattedTime = moment(localizedTime).format('YYYY-MM-DD HH:mm:ss');

    if (isInput) {
      element.setAttribute("value", formattedTime);
    } else {
      element.textContent = formattedTime;
    }
  });
}

localizeDateTimes();
