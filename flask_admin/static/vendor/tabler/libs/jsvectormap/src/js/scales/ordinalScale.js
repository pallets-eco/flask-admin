class OrdinalScale {
  constructor(scale) {
    this._scale = scale
  }

  getValue(value){
    return this._scale[value]
  }

  getTicks() {
    const ticks = []

    for (let key in this._scale) {
      ticks.push({ label: key, value: this._scale[key] })
    }

    return ticks
  }
}

export default OrdinalScale