/**
 * jsVectorMap
 * Copyrights (c) Mustafa Omar https://github.com/themustafaomar
 * Released under the MIT License.
 */
import Map from './map'

import '../scss/jsvectormap.scss'

class jsVectorMap {
  constructor(options = {}) {
    if (!options.selector) {
      throw new Error('Selector is not given.')
    }

    return new Map(options)
  }

  // Public
  static addMap(name, map) {
    Map.maps[name] = map
  }
}

export default window.jsVectorMap = jsVectorMap