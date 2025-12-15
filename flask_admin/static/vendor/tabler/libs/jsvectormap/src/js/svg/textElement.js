import SVGShapeElement from './shapeElement'

class SVGTextElement extends SVGShapeElement {
  constructor(config, style) {
    super('text', config, style)
  }

  applyAttr(attr, value) {
    attr === 'text' ? this.node.textContent = value : super.applyAttr(attr, value)
  }
}

export default SVGTextElement