class DataVisualization {
  constructor({ scale, values }, map) {
    this._scale = scale
    this._values = values
    this._fromColor = this.hexToRgb(scale[0])
    this._toColor = this.hexToRgb(scale[1])
    this._map = map

    this.setMinMaxValues(values)
    this.visualize()
  }

  setMinMaxValues(values) {
    this.min = Number.MAX_VALUE
    this.max = 0

    for (let value in values) {
      value = parseFloat(values[value])

      if (value > this.max) {
        this.max = value
      }

      if (value < this.min) {
        this.min = value
      }
    }
  }

  visualize() {
    let attrs = {}, value

    for (let regionCode in this._values) {
      value = parseFloat(this._values[regionCode])

      if (!isNaN(value)) {
        attrs[regionCode] = this.getValue(value)
      }
    }

    this.setAttributes(attrs)
  }

  setAttributes(attrs) {
    for (let code in attrs) {
      if (this._map.regions[code]) {
        this._map.regions[code].element.setStyle('fill', attrs[code])
      }
    }
  }

  getValue(value) {
    if (this.min === this.max) {
      return `#${this._toColor.join('')}`
    }

    let hex, color = '#'
  
    for (var i = 0; i < 3; i++) {
      hex = Math.round(
        this._fromColor[i] + (this._toColor[i] - this._fromColor[i]) * ((value - this.min) / (this.max - this.min))
      ).toString(16)

      color += (hex.length === 1 ? '0' : '') + hex
    }

    return color
  }

  hexToRgb(h) {
    let r = 0, g = 0, b = 0
  
    if (h.length == 4) {
      r = '0x' + h[1] + h[1]
      g = '0x' + h[2] + h[2]
      b = '0x' + h[3] + h[3]
    } else if (h.length == 7) {
      r = '0x' + h[1] + h[2]
      g = '0x' + h[3] + h[4]
      b = '0x' + h[5] + h[6]
    }

    return [parseInt(r), parseInt(g), parseInt(b)]
  }
}

export default DataVisualization