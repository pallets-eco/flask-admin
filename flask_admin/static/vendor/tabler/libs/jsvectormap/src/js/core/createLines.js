import { merge, getLineUid } from '../util'
import Line from '../components/line'

export default function createLines(lines) {
  let point1 = false, point2 = false
  const { curvature, ...lineStyle } = this.params.lineStyle

  for (let index in lines) {
    const lineConfig = lines[index]

    for (let { config: markerConfig } of Object.values(this._markers)) {
      if (markerConfig.name === lineConfig.from) {
        point1 = this.getMarkerPosition(markerConfig)
      }

      if (markerConfig.name === lineConfig.to) {
        point2 = this.getMarkerPosition(markerConfig)
      }
    }

    if (point1 !== false && point2 !== false) {
      const {
        curvature: curvatureOption,
        ...style
      } = lineConfig.style || {}

      // Register lines with unique keys
      this._lines[getLineUid(lineConfig.from, lineConfig.to)] = new Line(
        {
          index,
          map: this,
          group: this._linesGroup,
          config: lineConfig,
          x1: point1.x,
          y1: point1.y,
          x2: point2.x,
          y2: point2.y,
          curvature: curvatureOption == 0 ? 0 : (curvatureOption || curvature),
        },
        merge(lineStyle, style, true)
      )
    }
  }
}