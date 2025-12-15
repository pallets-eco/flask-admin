export default function repositionMarkers() {
  for (const index in this._markers) {
    const point = this.getMarkerPosition(this._markers[index].config)

    if (point !== false) {
      this._markers[index].element.setStyle({
        cx: point.x, cy: point.y
      })
    }
  }
}