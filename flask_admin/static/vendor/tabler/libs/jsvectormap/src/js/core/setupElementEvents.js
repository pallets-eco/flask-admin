import { getElement } from '../util'
import EventHandler from '../eventHandler'
import Events from '../defaults/events'

const parseEvent = (map, selector, isTooltip) => {
  const element = getElement(selector)
  const type = element.getAttribute('class').indexOf('jvm-region') === -1 ? 'marker' : 'region'
  const isRegion = type === 'region'
  const code = isRegion ? element.getAttribute('data-code') : element.getAttribute('data-index')
  let event = isRegion ? Events.onRegionSelected : Events.onMarkerSelected

  // Init tooltip event
  if (isTooltip) {
    event = isRegion ? Events.onRegionTooltipShow : Events.onMarkerTooltipShow
  }

  return {
    type,
    code,
    event,
    element: isRegion ? map.regions[code].element : map._markers[code].element,
    tooltipText: isRegion ? map._mapData.paths[code].name || '' : (map._markers[code].config.name || '')
  }
}

export default function setupElementEvents() {
  const map = this
  const container = this.container
  let pageX, pageY, mouseMoved

  EventHandler.on(container, 'mousemove', (event) => {
    if (Math.abs(pageX - event.pageX) + Math.abs(pageY - event.pageY) > 2) {
      mouseMoved = true
    }
  })

  // When the mouse is pressed
  EventHandler.delegate(container, 'mousedown', '.jvm-element', (event) => {
    pageX = event.pageX
    pageY = event.pageY
    mouseMoved = false
  })

  // When the mouse is over the region/marker | When the mouse is out the region/marker
  EventHandler.delegate(container, 'mouseover mouseout', '.jvm-element', function (event) {
    const data = parseEvent(map, this, true)
    const { showTooltip } = map.params

    if (event.type === 'mouseover') {
      data.element.hover(true)

      if (showTooltip) {
        map._tooltip.text(data.tooltipText)
        map._emit(data.event, [event, map._tooltip, data.code])
        if (!event.defaultPrevented) {
          map._tooltip.show()
        }
      }
    } else {
      data.element.hover(false)

      if (showTooltip) {
        map._tooltip.hide()
      }
    }
  })

  // When the click is released
  EventHandler.delegate(container, 'mouseup', '.jvm-element', function (event) {
    const data = parseEvent(map, this)

    if (mouseMoved) {
      return
    }

    if (
      (data.type === 'region' && map.params.regionsSelectable) ||
      (data.type === 'marker' && map.params.markersSelectable)
    ) {
      const element = data.element

      // We're checking if regions/markers|SelectableOne option is presented
      if (map.params[`${data.type}sSelectableOne`]) {
        data.type === 'region' ? map.clearSelectedRegions() : map.clearSelectedMarkers()
      }

      if (data.element.isSelected) {
        element.select(false)
      } else {
        element.select(true)
      }

      map._emit(data.event, [
        data.code,
        element.isSelected,
        data.type === 'region'
          ? map.getSelectedRegions()
          : map.getSelectedMarkers()
      ])
    }
  })

  // When region/marker is clicked
  EventHandler.delegate(container, 'click', '.jvm-element', function (event) {
    const { type, code } = parseEvent(map, this)

    map._emit(
      type === 'region' ? Events.onRegionClick : Events.onMarkerClick,
      [event, code]
    )
  })
}