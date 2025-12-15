import { merge } from './util/index'
import Legend from './legend'
import OrdinalScale from './scales/ordinalScale'

class Series {
  constructor(config = {}, elements, map) {
    // Private
    this._map = map
    this._elements = elements // Could be markers or regions
    this._values = config.values || {}

    // Protected
    this.config = config
    this.config.attribute = config.attribute || 'fill'

    // Set initial attributes
    if (config.attributes) {
      this.setAttributes(config.attributes)
    }

    if (typeof config.scale === 'object') {
      this.scale = new OrdinalScale(config.scale)
    }

    if (this.config.legend) {
      this.legend = new Legend(
        merge({ map: this._map, series: this }, this.config.legend)
      )
    }

    this.setValues(this._values)
  }

  setValues(values) {
    let attrs = {}

    for (let key in values) {
      if (values[key]) {
        attrs[key] = this.scale.getValue(values[key])
      }
    }

    this.setAttributes(attrs)
  }

  setAttributes(attrs) {
    for (let code in attrs) {
      if (this._elements[code]) {
        this._elements[code].element.setStyle(this.config.attribute, attrs[code])
      }
    }
  }

  clear() {
    let key, attrs = {}

    for (key in this._values) {
      if (this._elements[key]) {
        attrs[key] = this._elements[key].element.shape.style.initial[this.config.attribute]
      }
    }

    this.setAttributes(attrs)
    this._values = {}
  }
}

export default Series