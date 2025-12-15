import { inherit } from '../util'
import BaseComponent from './base'
import Interactable from './concerns/interactable'

const NAME = 'marker'
const JVM_PREFIX = 'jvm-'
const MARKER_CLASS = `${JVM_PREFIX}element ${JVM_PREFIX}marker`
const MARKER_LABEL_CLASS = `${JVM_PREFIX}element ${JVM_PREFIX}label`

class Marker extends BaseComponent {
  static get Name() {
    return NAME
  }

  constructor(options, style) {
    super()

    this._options = options
    this._style = style
    this._labelX = null
    this._labelY = null
    this._offsets = null
    this._isImage = !!style.initial.image

    this._draw()

    if (this._options.label) {
      this._drawLabel()
    }

    if (this._isImage) {
      this.updateLabelPosition()
    }
  }

  getConfig() {
    return this._options.config
  }

  updateLabelPosition() {
    const map = this._options.map
    if (this.label) {
      this.label.set({
        x:
          this._labelX * map.scale +
          this._offsets[0] +
          map.transX * map.scale +
          5 +
          (this._isImage
            ? (this.shape.width || 0) / 2
            : this.shape.node.r.baseVal.value),
        y:
          this._labelY * map.scale +
          map.transY * this._options.map.scale +
          this._offsets[1],
      })
    }
  }

  _draw() {
    const { index, map, group, cx, cy } = this._options
    const shapeType = this._isImage ? 'createImage' : 'createCircle'

    this.shape = map.canvas[shapeType](
      { dataIndex: index, cx, cy },
      this._style,
      group
    )
    this.shape.addClass(MARKER_CLASS)
  }

  _drawLabel() {
    const {
      index,
      map,
      label,
      labelsGroup,
      cx,
      cy,
      config,
      isRecentlyCreated,
    } = this._options
    const labelText = this.getLabelText(index, label)

    this._labelX = cx / map.scale - map.transX
    this._labelY = cy / map.scale - map.transY
    this._offsets = isRecentlyCreated && config.offsets ? config.offsets : this.getLabelOffsets(index, label)
    this.label = map.canvas.createText(
      {
        text: labelText,
        dataIndex: index,
        x: this._labelX,
        y: this._labelY,
        dy: '0.6ex',
      },
      map.params.markerLabelStyle,
      labelsGroup
    )
    this.label.addClass(MARKER_LABEL_CLASS)

    if (isRecentlyCreated) {
      this.updateLabelPosition()
    }
  }
}

inherit(Marker, Interactable)

export default Marker
