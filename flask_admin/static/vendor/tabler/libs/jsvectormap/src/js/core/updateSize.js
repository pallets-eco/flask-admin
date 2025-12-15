export default function updateSize() {
  this._width = this.container.offsetWidth
  this._height = this.container.offsetHeight
  this._resize()
  this.canvas.setSize(this._width, this._height)
  this._applyTransform()
}