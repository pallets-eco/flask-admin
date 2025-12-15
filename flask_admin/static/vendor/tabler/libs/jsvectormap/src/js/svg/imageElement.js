import SVGShapeElement from './shapeElement'

class SVGImageElement extends SVGShapeElement {
  constructor(config, style) {
    super('image', config, style)
  }

  applyAttr(attr, value) {
    let imageUrl

    if (attr === 'image') {
      // This get executed when we have url in series.markers[0].scale.someScale.url
      if (typeof value === 'object') {
        imageUrl = value.url
        this.offset = value.offset || [0, 0]
      } else {
        imageUrl = value
        this.offset = [0, 0]
      }

      this.node.setAttributeNS('http://www.w3.org/1999/xlink', 'href', imageUrl)

      // Set width and height then call this `applyAttr` again
      this.width = 23
      this.height = 23
      this.applyAttr('width', this.width)
      this.applyAttr('height', this.height)
      this.applyAttr('x', this.cx - this.width / 2 + this.offset[0])
      this.applyAttr('y', this.cy - this.height / 2 + this.offset[1])
    } else if (attr == 'cx') {
      this.cx = value

      if (this.width) {
        this.applyAttr('x', value - this.width / 2 + this.offset[0])
      }
    } else if (attr == 'cy') {
      this.cy = value

      if (this.height) {
        this.applyAttr('y', value - this.height / 2 + this.offset[1])
      }
    } else {
      // This time Call SVGElement
      super.applyAttr.apply(this, arguments)
    }
  }
}

export default SVGImageElement