import Component from './base';

export class Route extends Component {
  constructor(options, style) {
    super();
    this._options = options;
    this._style = style;
    this._draw();
  }

  _draw() {
    const { node: path } = this._options.map.canvas.createPath(
      {
        d: this._getDAttribute(),
        fill: 'none',
        stroke: '#666',
        strokeWidth: 1,
        dataIndex: this._options.index,
        'stroke-dasharray': '2 4 2',
      },
      this.style,
      this._options.group
    );

    // Get the total length of the path
    const totalLength = path.getTotalLength();

    // Initialize the stroke dash array and offset to create the drawing effect
    path.style.strokeDasharray = totalLength;
    path.style.strokeDashoffset = totalLength;

    // Animate the stroke dash offset to draw the line
    path.animate([{ strokeDashoffset: totalLength }, { strokeDashoffset: 0 }], {
      duration: 4000, // Duration of the animation
      easing: 'linear', // Easing function
      fill: 'forwards', // Keep the line visible after animation ends
    });
  }

  _getDAttribute() {
    const curvature = -0.2;
    const points = this._getPoints();
    let d = `M${points[0].x},${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const nextPoint = points[i + 1];
      const cpX =
        (points[i].x + nextPoint.x) / 2 +
        curvature * (nextPoint.y - points[i].y);
      const cpY =
        (points[i].y + nextPoint.y) / 2 -
        curvature * (nextPoint.x - points[i].x);
      d += ` Q${cpX},${cpY} ${nextPoint.x},${nextPoint.y}`;
    }
    // let d = `M${points[0].x},${points[0].y}`
    // for (let i = 1; i < points.length; i++) {
    //   d += ` L${points[i].x},${points[i].y}`
    // }
    return d
  }

  _getPoints() {
    const map = this._options.map;
    const points = [];

    for (let i = 0; i < this._options.waypoints.length; i++) {
      const p = this._options.map.getMarkerPosition({
        coords: [
          this._options.waypoints[i].lat,
          this._options.waypoints[i].lng,
        ],
      });
      points.push(p);
    }
    return points;
  }
}
