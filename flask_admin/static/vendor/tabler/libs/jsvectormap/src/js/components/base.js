import { removeElement } from '../util'

class BaseComponent {
  dispose() {
    if (this._tooltip) {
      removeElement(this._tooltip)
    } else {
      // @todo: move shape in base component in v2
      this.shape.remove()
    }

    for (const propertyName of Object.getOwnPropertyNames(this)) {
      this[propertyName] = null
    }
  }
}

export default BaseComponent