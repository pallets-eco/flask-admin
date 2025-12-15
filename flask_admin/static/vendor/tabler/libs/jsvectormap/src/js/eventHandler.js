let eventRegistry = {}
let eventUid = 1

const EventHandler = {
  on(element, event, handler, options = {}) {
    const uid = `jvm:${event}::${eventUid++}`

    eventRegistry[uid] = {
      selector: element,
      handler,
    }

    handler._uid = uid

    element.addEventListener(event, handler, options)
  },
  delegate(element, event, selector, handler) {
    event = event.split(' ')

    event.forEach(eventName => {
      EventHandler.on(element, eventName, (e) => {
        const target = e.target

        if (target.matches(selector)) {
          handler.call(target, e)
        }
      })
    })
  },
  off(element, event, handler) {
    const eventType = event.split(':')[1]

    element.removeEventListener(eventType, handler)

    delete eventRegistry[handler._uid]
  },
  flush() {
    Object.keys(eventRegistry).forEach(event => {
      EventHandler.off(eventRegistry[event].selector, event, eventRegistry[event].handler)
    })
  },
  getEventRegistry() {
    return eventRegistry
  },
}

export default EventHandler