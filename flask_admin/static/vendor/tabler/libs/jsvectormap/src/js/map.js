import {
  merge,
  getLineUid,
  getElement,
  createElement,
  removeElement,
} from './util'
import core from './core'
import Defaults from './defaults/options'
import SVGCanvasElement from './svg/canvasElement'
import Events from './defaults/events'
import EventHandler from './eventHandler'
import Tooltip from './components/tooltip'
import DataVisualization from './dataVisualization'

const JVM_PREFIX = 'jvm-'
const CONTAINER_CLASS = `${JVM_PREFIX}container`
const MARKERS_GROUP_ID = `${JVM_PREFIX}markers-group`
const MARKERS_LABELS_GROUP_ID = `${JVM_PREFIX}markers-labels-group`
const LINES_GROUP_ID = `${JVM_PREFIX}lines-group`
const SERIES_CONTAINER_CLASS = `${JVM_PREFIX}series-container`
const SERIES_CONTAINER_H_CLASS = `${SERIES_CONTAINER_CLASS} ${JVM_PREFIX}series-h`
const SERIES_CONTAINER_V_CLASS = `${SERIES_CONTAINER_CLASS} ${JVM_PREFIX}series-v`

class Map {
  static maps = {}
  static defaults = Defaults

  constructor(options = {}) {
    // Merge the given options with the default options
    this.params = merge(Map.defaults, options, true)

    // Throw an error if the given map name doesn't match
    // the map that was set in map file
    if (!Map.maps[this.params.map]) {
      throw new Error(`Attempt to use map which was not loaded: ${options.map}`)
    }

    this.regions = {}
    this.scale = 1
    this.transX = 0
    this.transY = 0

    this._mapData = Map.maps[this.params.map]
    this._markers = {}
    this._lines = {}
    this._defaultWidth = this._mapData.width
    this._defaultHeight = this._mapData.height
    this._height = 0
    this._width = 0
    this._baseScale = 1
    this._baseTransX = 0
    this._baseTransY = 0

    // `document` is already ready, just initialise now
    if (document.readyState !== 'loading') {
      this._init()
    } else {
      // Wait until `document` is ready
      window.addEventListener('DOMContentLoaded', () => this._init())
    }
  }

  _init() {
    const options = this.params

    this.container = getElement(options.selector)
    this.container.classList.add(CONTAINER_CLASS)

    // The map canvas element
    this.canvas = new SVGCanvasElement(this.container)

    // Set the map's background color
    this.setBackgroundColor(options.backgroundColor)

    // Create regions
    this._createRegions()

    // Update size
    this.updateSize()

    // Lines group must be created before markers
    // Otherwise the lines will be drawn on top of the markers.
    if (options.lines) {
      this._linesGroup = this.canvas.createGroup(LINES_GROUP_ID)
    }

    if (options.markers) {
      this._markersGroup = this.canvas.createGroup(MARKERS_GROUP_ID)
      this._markerLabelsGroup = this.canvas.createGroup(MARKERS_LABELS_GROUP_ID)
    }

    // Create markers
    this._createMarkers(options.markers)

    // Create lines
    this._createLines(options.lines || {})

    // Position labels
    this._repositionLabels()

    // Setup the container events
    this._setupContainerEvents()

    // Setup regions/markers events
    this._setupElementEvents()

    // Create zoom buttons if `zoomButtons` is presented
    if (options.zoomButtons) {
      this._setupZoomButtons()
    }

    // Create toolip
    if (options.showTooltip) {
      this._tooltip = new Tooltip(this)
    }

    // Set selected regions if any
    if (options.selectedRegions) {
      this._setSelected('regions', options.selectedRegions)
    }

    // Set selected regions if any
    if (options.selectedMarkers) {
      this._setSelected('_markers', options.selectedMarkers)
    }

    // Set focus on a spcific region
    if (options.focusOn) {
      this.setFocus(options.focusOn)
    }

    // Data visualization
    if (options.visualizeData) {
      this.dataVisualization = new DataVisualization(options.visualizeData, this)
    }

    // Bind touch events if true
    if (options.bindTouchEvents) {
      if (
        ('ontouchstart' in window) || (window.DocumentTouch && document instanceof DocumentTouch)
      ) {
        this._setupContainerTouchEvents()
      }
    }

    // Create series if any
    if (options.series) {
      this.container.appendChild(this.legendHorizontal = createElement(
        'div', SERIES_CONTAINER_H_CLASS
      ))

      this.container.appendChild(this.legendVertical = createElement(
        'div', SERIES_CONTAINER_V_CLASS
      ))

      this._createSeries()
    }

    // Fire loaded event
    this._emit(Events.onLoaded, [this])
  }

  // Public

  setBackgroundColor(color) {
    this.container.style.backgroundColor = color
  }

  // Regions

  getSelectedRegions() {
    return this._getSelected('regions')
  }

  clearSelectedRegions(regions = undefined) {
    regions = this._normalizeRegions(regions) || this._getSelected('regions')
    regions.forEach((key) => {
      this.regions[key].element.select(false)
    })
  }

  setSelectedRegions(regions) {
    this.clearSelectedRegions()
    this._setSelected('regions', this._normalizeRegions(regions))
  }

  // Markers

  getSelectedMarkers() {
    return this._getSelected('_markers')
  }

  clearSelectedMarkers() {
    this._clearSelected('_markers')
  }

  setSelectedMarkers(markers) {
    this._setSelected('_markers', markers)
  }

  addMarkers(config) {
    config = Array.isArray(config) ? config : [config]
    this._createMarkers(config, true)
  }

  removeMarkers(markers) {
    if (!markers) {
      markers = Object.keys(this._markers)
    }

    markers.forEach(index => {
      // Remove the element from the DOM
      this._markers[index].element.remove()
      // Remove the element from markers object
      delete this._markers[index]
    })
  }

  // Lines

  addLine(from, to, style = {}) {
    console.warn('`addLine` method is deprecated, please use `addLines` instead.')
    this._createLines([{ from, to, style }], this._markers, true)
  }

  addLines(config) {
    const uids = this._getLinesAsUids()

    if (!Array.isArray(config)) {
      config = [config]
    }

    this._createLines(config.filter(line => {
      return !(uids.indexOf(getLineUid(line.from, line.to)) > -1)
    }), true)
  }

  removeLines(lines) {
    if (Array.isArray(lines)) {
      lines = lines.map(line => getLineUid(line.from, line.to))
    } else {
      lines = this._getLinesAsUids()
    }

    lines.forEach(uid => {
      this._lines[uid].dispose()
      delete this._lines[uid]
    })
  }

  removeLine(from, to) {
    console.warn('`removeLine` method is deprecated, please use `removeLines` instead.')
    const uid = getLineUid(from, to)

    if (this._lines.hasOwnProperty(uid)) {
      this._lines[uid].element.remove()
      delete this._lines[uid]
    }
  }

  // Reset map
  reset() {
    for (let key in this.series) {
      for (let i = 0; i < this.series[key].length; i++) {
        this.series[key][i].clear()
      }
    }

    if (this.legendHorizontal) {
      removeElement(this.legendHorizontal)
      this.legendHorizontal = null
    }

    if (this.legendVertical) {
      removeElement(this.legendVertical)
      this.legendVertical = null
    }

    this.scale = this._baseScale
    this.transX = this._baseTransX
    this.transY = this._baseTransY

    this._applyTransform()
    this.clearSelectedMarkers()
    this.clearSelectedRegions()
    this.removeMarkers()
  }

  // Destroy the map
  destroy(destroyInstance = true) {
    // Remove event registry
    EventHandler.flush()

    // Remove tooltip from DOM and memory
    this._tooltip.dispose()

    // Fire destroyed event
    this._emit(Events.onDestroyed)

    // Remove references
    if (destroyInstance) {
      Object.keys(this).forEach(key => {
        try {
          delete this[key]
        } catch (e) {}
      })
    }
  }

  extend(name, callback) {
    if (typeof this[name] === 'function') {
      throw new Error(`The method [${name}] does already exist, please use another name.`)
    }

    Map.prototype[name] = callback
  }

  // Private

  _emit(eventName, args) {
    for (const event in Events) {
      if (Events[event] === eventName && typeof this.params[event] === 'function') {
        this.params[event].apply(this, args)
      }
    }
  }

  // Get selected markers/regions
  _getSelected(type) {
    const selected = []

    for (const key in this[type]) {
      if (this[type][key].element.isSelected) {
        selected.push(key)
      }
    }

    return selected
  }

  _setSelected(type, keys) {
    keys.forEach(key => {
      if (this[type][key]) {
        this[type][key].element.select(true)
      }
    })
  }

  _clearSelected(type) {
    this._getSelected(type).forEach(key => {
      this[type][key].element.select(false)
    })
  }

  _getLinesAsUids() {
    return Object.keys(this._lines)
  }

  _normalizeRegions(regions) {
    return typeof regions === 'string' ? [regions] : regions
  }
}

Object.assign(Map.prototype, core)

export default Map