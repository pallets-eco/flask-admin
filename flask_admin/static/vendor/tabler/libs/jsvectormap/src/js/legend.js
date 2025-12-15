import { createElement, isImageUrl } from './util'

class Legend {
  constructor(options = {}) {
    this._options = options
    this._map = this._options.map
    this._series = this._options.series
    this._body = createElement('div', 'jvm-legend')

    if (this._options.cssClass) {
      this._body.setAttribute('class', this._options.cssClass)
    }

    if (options.vertical) {
      this._map.legendVertical.appendChild(this._body)
    } else {
      this._map.legendHorizontal.appendChild(this._body)
    }

    this.render()
  }

  render() {
    let ticks = this._series.scale.getTicks()

    this._body.innderHTML = ''

    if (this._options.title) {
      let legendTitle = createElement('div', 'jvm-legend-title', this._options.title)
      this._body.appendChild(legendTitle)
    }

    for (let i = 0; i < ticks.length; i++) {
      let tick = createElement('div', 'jvm-legend-tick',)
      let sample = createElement('div', 'jvm-legend-tick-sample')

      switch (this._series.config.attribute) {
        case 'fill':
          if (isImageUrl(ticks[i].value)) {
            sample.style.background = `url(${ticks[i].value})`
          } else {
            sample.style.background = ticks[i].value
          }
          break
        case 'stroke':
          sample.style.background = ticks[i].value
          break
        case 'image':
          sample.style.background = `url(${typeof ticks[i].value === 'object' ? ticks[i].value.url : ticks[i].value}) no-repeat center center`
          sample.style.backgroundSize = 'cover'
          break
      }

      tick.appendChild(sample)
      let label = ticks[i].label

      if (this._options.labelRender) {
        label = this._options.labelRender(label)
      }

      const tickText = createElement('div', 'jvm-legend-tick-text', label)

      tick.appendChild(tickText)
      this._body.appendChild(tick)
    }
  }
}

export default Legend