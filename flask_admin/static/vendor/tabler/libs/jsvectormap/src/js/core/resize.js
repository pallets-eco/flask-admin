export default function resize() {
  const curBaseScale = this._baseScale

  if (this._width / this._height > this._defaultWidth / this._defaultHeight) {
    this._baseScale = this._height / this._defaultHeight
    this._baseTransX = Math.abs(this._width - this._defaultWidth * this._baseScale) / (2 * this._baseScale)
  } else {
    this._baseScale = this._width / this._defaultWidth
    this._baseTransY = Math.abs(this._height - this._defaultHeight * this._baseScale) / (2 * this._baseScale)
  }

  this.scale *= this._baseScale / curBaseScale
  this.transX *= this._baseScale / curBaseScale
  this.transY *= this._baseScale / curBaseScale
}