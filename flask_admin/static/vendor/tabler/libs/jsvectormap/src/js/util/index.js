import DeepMerge from './deepMerge'

/**
 * --------------------------------------------------------------------------
 * Public Util Api
 * --------------------------------------------------------------------------
 */
const getElement = selector => {
  if (typeof selector === 'object' && typeof selector.nodeType !== 'undefined') {
    return selector
  }

  if (typeof selector === 'string') {
    return document.querySelector(selector)
  }

  return null
}

const createElement = (type, classes, content, html = false) => {
  let el = document.createElement(type)

  if (content) {
    el[!html ? 'textContent' : 'innerHTML'] = content
  }

  if (classes) {
    el.className = classes
  }

  return el
}

const findElement = (parentElement, selector) => {
  return Element.prototype.querySelector.call(parentElement, selector)
}

const removeElement = target => {
  target.parentNode.removeChild(target)
}

const isImageUrl = url => {
  return /\.(jpg|gif|png)$/.test(url)
}

const hyphenate = string => {
  return string.replace(/[\w]([A-Z])/g, m => `${m[0]}-${m[1]}`).toLowerCase()
}

const merge = (target, source, deep = false) => {
  if (deep) {
    return DeepMerge(target, source)
  }

  return Object.assign(target, source)
}

const keys = object => {
  return Object.keys(object)
}

const getLineUid = (from, to) => {
  return `${from.toLowerCase()}:to:${to.toLowerCase()}`
}

const inherit = (target, source) => {
  Object.assign(target.prototype, source)
}

export {
  getElement,
  createElement,
  findElement,
  removeElement,
  isImageUrl,
  hyphenate,
  merge,
  keys,
  getLineUid,
  inherit,
}