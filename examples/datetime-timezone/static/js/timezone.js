// post client's timezone so that backend can correctly convert datetime inputs to UTC
fetch('/set_timezone', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(Intl.DateTimeFormat().resolvedOptions().timeZone)
})

// Helper function to pad single digits with leading zero
function pad(num) {
  return num.toString().padStart(2, '0');
}

// format datetime to "%Y-%m-%d %H:%M:%S"
function formatDate(date) {
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1); // Months are zero-based
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  const seconds = pad(date.getSeconds());

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

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

    const formattedTime = formatDate(localizedTime);

    if (isInput) {
      element.setAttribute("value", formattedTime);
    } else {
      element.textContent = formattedTime;
    }
  });
}

localizeDateTimes();
