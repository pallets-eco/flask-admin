import {
  hyphenate,
  removeElement
} from '../util/index'

class SVGElement {
  constructor(name, config) {
    this.node = this._createElement(name)

    if (config) {
      this.set(config)
    }
  }

  // Create new SVG element `svg`, `g`, `path`, `line`, `circle`, `image`, etc.
  // https://developer.mozilla.org/en-US/docs/Web/API/Document/createElementNS#important_namespace_uris
  _createElement(tagName) {
    return document.createElementNS('http://www.w3.org/2000/svg', tagName)
  }

  addClass(className) {
    this.node.setAttribute('class', className)
  }

  getBBox() {
    return this.node.getBBox()
  }

  // Apply attributes on the current node element
  set(property, value) {
    if (typeof property === 'object') {
      for (let attr in property) {
        this.applyAttr(attr, property[attr])
      }
    } else {
      this.applyAttr(property, value)
    }
  }

  get(property) {
    return this.style.initial[property]
  }

  applyAttr(property, value) {
    this.node.setAttribute(hyphenate(property), value)
  }

  remove() {
    removeElement(this.node)
  }
}

export default SVGElement