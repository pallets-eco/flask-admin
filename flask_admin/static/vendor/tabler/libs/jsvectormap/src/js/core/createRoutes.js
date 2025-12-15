import waypoints from "../../../../playground/data/waypoints"
import { Route } from "../components/route"

export default function createRoutes(routes) {
  this._routes = {}

  let index = 0
  for (let route of routes) {
    this._routes[route.name] = new Route({
      map: this,
      group: this._routesGroup,
      waypoints: route.data,
      index: index++,
    }, {})
  }
}