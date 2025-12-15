import { createElement } from '../util'
import EventHandler from '../eventHandler'

export default function setupZoomButtons() {
  const zoomInOption = this.params.zoomInButton
  const zoomOutOption = this.params.zoomOutButton

  const getZoomButton = (zoomOption) => typeof zoomOption === 'string'
    ? document.querySelector(zoomOption)
    : zoomOption

  const zoomIn = zoomInOption
    ? getZoomButton(zoomInOption)
    : createElement('div', 'jvm-zoom-btn jvm-zoomin', '&#43;', true)

  const zoomOut = zoomOutOption
    ? getZoomButton(zoomOutOption)
    : createElement('div', 'jvm-zoom-btn jvm-zoomout', '&#x2212', true)

  if (!zoomInOption) {
    this.container.appendChild(zoomIn)
  }

  if (!zoomOutOption) {
    this.container.appendChild(zoomOut)
  }

  const handler = (zoomin = true) => {
    return () => this._setScale(
      zoomin ? this.scale * this.params.zoomStep : this.scale / this.params.zoomStep,
      this._width / 2,
      this._height / 2,
      false,
      this.params.zoomAnimate
    )
  }

  EventHandler.on(zoomIn, 'click', handler())
  EventHandler.on(zoomOut, 'click', handler(false))
}