import Map from '../map'
import Proj from '../projection'

export default function coordsToPoint(lat, lng) {
  const projection = Map.maps[this.params.map].projection
  let { x, y } = Proj[projection.type](lat, lng, projection.centralMeridian)
  let inset = this.getInsetForPoint(x, y)

  if (!inset) {
    return false
  }

  let bbox = inset.bbox

  x = (x - bbox[0].x) / (bbox[1].x - bbox[0].x) * inset.width * this.scale
  y = (y - bbox[0].y) / (bbox[1].y - bbox[0].y) * inset.height * this.scale

  return {
    x: x + this.transX * this.scale + inset.left * this.scale,
    y: y + this.transY * this.scale + inset.top * this.scale
  }
}