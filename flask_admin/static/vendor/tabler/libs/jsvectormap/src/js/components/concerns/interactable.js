const Interactable = {
  getLabelText(key, label) {
    if (!label) {
      return
    }

    if (typeof label.render === 'function') {
      let params = []

      // Pass additional paramater (Marker config object) in case it's a Marker.
      if (this.constructor.Name === 'marker') {
        params.push(this.getConfig())
      }

      // Becuase we need to add the key always at the end
      params.push(key)

      return label.render.apply(this, params)
    }

    return key
  },

  getLabelOffsets(key, label) {
    if (typeof label.offsets === 'function') {
      return label.offsets(key)
    }

    // If offsets are an array of offsets e.g offsets: [ [0, 25], [10, 15] ]
    if (Array.isArray(label.offsets)) {
      return label.offsets[key]
    }

    return [0, 0]
  },

  setStyle(property, value) {
    this.shape.setStyle(property, value)
  },

  remove() {
    this.shape.remove()
    if (this.label) this.label.remove()
  },

  hover(state) {
    this._setStatus('isHovered', state)
  },

  select(state) {
    this._setStatus('isSelected', state)
  },

  // Private

  _setStatus(property, state) {
    this.shape[property] = state
    this.shape.updateStyle()
    this[property] = state

    if (this.label) {
      this.label[property] = state
      this.label.updateStyle()
    }
  }
}

export default Interactable