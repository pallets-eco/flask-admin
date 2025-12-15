import { merge } from '../util/index'
import SVGElement from './baseElement'

class SVGShapeElement extends SVGElement {
  constructor(name, config, style = {}) {
    super(name, config)

    this.isHovered = false
    this.isSelected = false
    this.style = style
    this.style.current = {}

    this.updateStyle()
  }

  setStyle(property, value) {
    if (typeof property === 'object') {
      merge(this.style.current, property)
    } else {
      merge(this.style.current, { [property]: value })
    }

    this.updateStyle()
  }

  updateStyle() {
    const attrs = {}

    merge(attrs, this.style.initial)
    merge(attrs, this.style.current)

    if (this.isHovered) {
      merge(attrs, this.style.hover)
    }

    if (this.isSelected) {
      merge(attrs, this.style.selected)

      if (this.isHovered) {
        merge(attrs, this.style.selectedHover)
      }
    }

    this.set(attrs)
  }
}

export default SVGShapeElement