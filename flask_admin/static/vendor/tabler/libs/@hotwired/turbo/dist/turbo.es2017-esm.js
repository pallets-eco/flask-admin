/*!
Turbo 8.0.13
Copyright © 2025 37signals LLC
 */
/**
 * The MIT License (MIT)
 *
 * Copyright (c) 2019 Javan Makhmali
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

(function (prototype) {
  if (typeof prototype.requestSubmit == "function") return

  prototype.requestSubmit = function (submitter) {
    if (submitter) {
      validateSubmitter(submitter, this);
      submitter.click();
    } else {
      submitter = document.createElement("input");
      submitter.type = "submit";
      submitter.hidden = true;
      this.appendChild(submitter);
      submitter.click();
      this.removeChild(submitter);
    }
  };

  function validateSubmitter(submitter, form) {
    submitter instanceof HTMLElement || raise(TypeError, "parameter 1 is not of type 'HTMLElement'");
    submitter.type == "submit" || raise(TypeError, "The specified element is not a submit button");
    submitter.form == form ||
      raise(DOMException, "The specified element is not owned by this form element", "NotFoundError");
  }

  function raise(errorConstructor, message, name) {
    throw new errorConstructor("Failed to execute 'requestSubmit' on 'HTMLFormElement': " + message + ".", name)
  }
})(HTMLFormElement.prototype);

const submittersByForm = new WeakMap();

function findSubmitterFromClickTarget(target) {
  const element = target instanceof Element ? target : target instanceof Node ? target.parentElement : null;
  const candidate = element ? element.closest("input, button") : null;
  return candidate?.type == "submit" ? candidate : null
}

function clickCaptured(event) {
  const submitter = findSubmitterFromClickTarget(event.target);

  if (submitter && submitter.form) {
    submittersByForm.set(submitter.form, submitter);
  }
}

(function () {
  if ("submitter" in Event.prototype) return

  let prototype = window.Event.prototype;
  // Certain versions of Safari 15 have a bug where they won't
  // populate the submitter. This hurts TurboDrive's enable/disable detection.
  // See https://bugs.webkit.org/show_bug.cgi?id=229660
  if ("SubmitEvent" in window) {
    const prototypeOfSubmitEvent = window.SubmitEvent.prototype;

    if (/Apple Computer/.test(navigator.vendor) && !("submitter" in prototypeOfSubmitEvent)) {
      prototype = prototypeOfSubmitEvent;
    } else {
      return // polyfill not needed
    }
  }

  addEventListener("click", clickCaptured, true);

  Object.defineProperty(prototype, "submitter", {
    get() {
      if (this.type == "submit" && this.target instanceof HTMLFormElement) {
        return submittersByForm.get(this.target)
      }
    }
  });
})();

const FrameLoadingStyle = {
  eager: "eager",
  lazy: "lazy"
};

/**
 * Contains a fragment of HTML which is updated based on navigation within
 * it (e.g. via links or form submissions).
 *
 * @customElement turbo-frame
 * @example
 *   <turbo-frame id="messages">
 *     <a href="/messages/expanded">
 *       Show all expanded messages in this frame.
 *     </a>
 *
 *     <form action="/messages">
 *       Show response from this form within this frame.
 *     </form>
 *   </turbo-frame>
 */
class FrameElement extends HTMLElement {
  static delegateConstructor = undefined

  loaded = Promise.resolve()

  static get observedAttributes() {
    return ["disabled", "loading", "src"]
  }

  constructor() {
    super();
    this.delegate = new FrameElement.delegateConstructor(this);
  }

  connectedCallback() {
    this.delegate.connect();
  }

  disconnectedCallback() {
    this.delegate.disconnect();
  }

  reload() {
    return this.delegate.sourceURLReloaded()
  }

  attributeChangedCallback(name) {
    if (name == "loading") {
      this.delegate.loadingStyleChanged();
    } else if (name == "src") {
      this.delegate.sourceURLChanged();
    } else if (name == "disabled") {
      this.delegate.disabledChanged();
    }
  }

  /**
   * Gets the URL to lazily load source HTML from
   */
  get src() {
    return this.getAttribute("src")
  }

  /**
   * Sets the URL to lazily load source HTML from
   */
  set src(value) {
    if (value) {
      this.setAttribute("src", value);
    } else {
      this.removeAttribute("src");
    }
  }

  /**
   * Gets the refresh mode for the frame.
   */
  get refresh() {
    return this.getAttribute("refresh")
  }

  /**
   * Sets the refresh mode for the frame.
   */
  set refresh(value) {
    if (value) {
      this.setAttribute("refresh", value);
    } else {
      this.removeAttribute("refresh");
    }
  }

  get shouldReloadWithMorph() {
    return this.src && this.refresh === "morph"
  }

  /**
   * Determines if the element is loading
   */
  get loading() {
    return frameLoadingStyleFromString(this.getAttribute("loading") || "")
  }

  /**
   * Sets the value of if the element is loading
   */
  set loading(value) {
    if (value) {
      this.setAttribute("loading", value);
    } else {
      this.removeAttribute("loading");
    }
  }

  /**
   * Gets the disabled state of the frame.
   *
   * If disabled, no requests will be intercepted by the frame.
   */
  get disabled() {
    return this.hasAttribute("disabled")
  }

  /**
   * Sets the disabled state of the frame.
   *
   * If disabled, no requests will be intercepted by the frame.
   */
  set disabled(value) {
    if (value) {
      this.setAttribute("disabled", "");
    } else {
      this.removeAttribute("disabled");
    }
  }

  /**
   * Gets the autoscroll state of the frame.
   *
   * If true, the frame will be scrolled into view automatically on update.
   */
  get autoscroll() {
    return this.hasAttribute("autoscroll")
  }

  /**
   * Sets the autoscroll state of the frame.
   *
   * If true, the frame will be scrolled into view automatically on update.
   */
  set autoscroll(value) {
    if (value) {
      this.setAttribute("autoscroll", "");
    } else {
      this.removeAttribute("autoscroll");
    }
  }

  /**
   * Determines if the element has finished loading
   */
  get complete() {
    return !this.delegate.isLoading
  }

  /**
   * Gets the active state of the frame.
   *
   * If inactive, source changes will not be observed.
   */
  get isActive() {
    return this.ownerDocument === document && !this.isPreview
  }

  /**
   * Sets the active state of the frame.
   *
   * If inactive, source changes will not be observed.
   */
  get isPreview() {
    return this.ownerDocument?.documentElement?.hasAttribute("data-turbo-preview")
  }
}

function frameLoadingStyleFromString(style) {
  switch (style.toLowerCase()) {
    case "lazy":
      return FrameLoadingStyle.lazy
    default:
      return FrameLoadingStyle.eager
  }
}

const drive = {
  enabled: true,
  progressBarDelay: 500,
  unvisitableExtensions: new Set(
    [
      ".7z", ".aac", ".apk", ".avi", ".bmp", ".bz2", ".css", ".csv", ".deb", ".dmg", ".doc",
      ".docx", ".exe", ".gif", ".gz", ".heic", ".heif", ".ico", ".iso", ".jpeg", ".jpg",
      ".js", ".json", ".m4a", ".mkv", ".mov", ".mp3", ".mp4", ".mpeg", ".mpg", ".msi",
      ".ogg", ".ogv", ".pdf", ".pkg", ".png", ".ppt", ".pptx", ".rar", ".rtf",
      ".svg", ".tar", ".tif", ".tiff", ".txt", ".wav", ".webm", ".webp", ".wma", ".wmv",
      ".xls", ".xlsx", ".xml", ".zip"
    ]
  )
};

function activateScriptElement(element) {
  if (element.getAttribute("data-turbo-eval") == "false") {
    return element
  } else {
    const createdScriptElement = document.createElement("script");
    const cspNonce = getCspNonce();
    if (cspNonce) {
      createdScriptElement.nonce = cspNonce;
    }
    createdScriptElement.textContent = element.textContent;
    createdScriptElement.async = false;
    copyElementAttributes(createdScriptElement, element);
    return createdScriptElement
  }
}

function copyElementAttributes(destinationElement, sourceElement) {
  for (const { name, value } of sourceElement.attributes) {
    destinationElement.setAttribute(name, value);
  }
}

function createDocumentFragment(html) {
  const template = document.createElement("template");
  template.innerHTML = html;
  return template.content
}

function dispatch(eventName, { target, cancelable, detail } = {}) {
  const event = new CustomEvent(eventName, {
    cancelable,
    bubbles: true,
    composed: true,
    detail
  });

  if (target && target.isConnected) {
    target.dispatchEvent(event);
  } else {
    document.documentElement.dispatchEvent(event);
  }

  return event
}

function cancelEvent(event) {
  event.preventDefault();
  event.stopImmediatePropagation();
}

function nextRepaint() {
  if (document.visibilityState === "hidden") {
    return nextEventLoopTick()
  } else {
    return nextAnimationFrame()
  }
}

function nextAnimationFrame() {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()))
}

function nextEventLoopTick() {
  return new Promise((resolve) => setTimeout(() => resolve(), 0))
}

function nextMicrotask() {
  return Promise.resolve()
}

function parseHTMLDocument(html = "") {
  return new DOMParser().parseFromString(html, "text/html")
}

function unindent(strings, ...values) {
  const lines = interpolate(strings, values).replace(/^\n/, "").split("\n");
  const match = lines[0].match(/^\s+/);
  const indent = match ? match[0].length : 0;
  return lines.map((line) => line.slice(indent)).join("\n")
}

function interpolate(strings, values) {
  return strings.reduce((result, string, i) => {
    const value = values[i] == undefined ? "" : values[i];
    return result + string + value
  }, "")
}

function uuid() {
  return Array.from({ length: 36 })
    .map((_, i) => {
      if (i == 8 || i == 13 || i == 18 || i == 23) {
        return "-"
      } else if (i == 14) {
        return "4"
      } else if (i == 19) {
        return (Math.floor(Math.random() * 4) + 8).toString(16)
      } else {
        return Math.floor(Math.random() * 15).toString(16)
      }
    })
    .join("")
}

function getAttribute(attributeName, ...elements) {
  for (const value of elements.map((element) => element?.getAttribute(attributeName))) {
    if (typeof value == "string") return value
  }

  return null
}

function hasAttribute(attributeName, ...elements) {
  return elements.some((element) => element && element.hasAttribute(attributeName))
}

function markAsBusy(...elements) {
  for (const element of elements) {
    if (element.localName == "turbo-frame") {
      element.setAttribute("busy", "");
    }
    element.setAttribute("aria-busy", "true");
  }
}

function clearBusyState(...elements) {
  for (const element of elements) {
    if (element.localName == "turbo-frame") {
      element.removeAttribute("busy");
    }

    element.removeAttribute("aria-busy");
  }
}

function waitForLoad(element, timeoutInMilliseconds = 2000) {
  return new Promise((resolve) => {
    const onComplete = () => {
      element.removeEventListener("error", onComplete);
      element.removeEventListener("load", onComplete);
      resolve();
    };

    element.addEventListener("load", onComplete, { once: true });
    element.addEventListener("error", onComplete, { once: true });
    setTimeout(resolve, timeoutInMilliseconds);
  })
}

function getHistoryMethodForAction(action) {
  switch (action) {
    case "replace":
      return history.replaceState
    case "advance":
    case "restore":
      return history.pushState
  }
}

function isAction(action) {
  return action == "advance" || action == "replace" || action == "restore"
}

function getVisitAction(...elements) {
  const action = getAttribute("data-turbo-action", ...elements);

  return isAction(action) ? action : null
}

function getMetaElement(name) {
  return document.querySelector(`meta[name="${name}"]`)
}

function getMetaContent(name) {
  const element = getMetaElement(name);
  return element && element.content
}

function getCspNonce() {
  const element = getMetaElement("csp-nonce");

  if (element) {
    const { nonce, content } = element;
    return nonce == "" ? content : nonce
  }
}

function setMetaContent(name, content) {
  let element = getMetaElement(name);

  if (!element) {
    element = document.createElement("meta");
    element.setAttribute("name", name);

    document.head.appendChild(element);
  }

  element.setAttribute("content", content);

  return element
}

function findClosestRecursively(element, selector) {
  if (element instanceof Element) {
    return (
      element.closest(selector) || findClosestRecursively(element.assignedSlot || element.getRootNode()?.host, selector)
    )
  }
}

function elementIsFocusable(element) {
  const inertDisabledOrHidden = "[inert], :disabled, [hidden], details:not([open]), dialog:not([open])";

  return !!element && element.closest(inertDisabledOrHidden) == null && typeof element.focus == "function"
}

function queryAutofocusableElement(elementOrDocumentFragment) {
  return Array.from(elementOrDocumentFragment.querySelectorAll("[autofocus]")).find(elementIsFocusable)
}

async function around(callback, reader) {
  const before = reader();

  callback();

  await nextAnimationFrame();

  const after = reader();

  return [before, after]
}

function doesNotTargetIFrame(name) {
  if (name === "_blank") {
    return false
  } else if (name) {
    for (const element of document.getElementsByName(name)) {
      if (element instanceof HTMLIFrameElement) return false
    }

    return true
  } else {
    return true
  }
}

function findLinkFromClickTarget(target) {
  return findClosestRecursively(target, "a[href]:not([target^=_]):not([download])")
}

function getLocationForLink(link) {
  return expandURL(link.getAttribute("href") || "")
}

function debounce(fn, delay) {
  let timeoutId = null;

  return (...args) => {
    const callback = () => fn.apply(this, args);
    clearTimeout(timeoutId);
    timeoutId = setTimeout(callback, delay);
  }
}

const submitter = {
  "aria-disabled": {
    beforeSubmit: submitter => {
      submitter.setAttribute("aria-disabled", "true");
      submitter.addEventListener("click", cancelEvent);
    },

    afterSubmit: submitter => {
      submitter.removeAttribute("aria-disabled");
      submitter.removeEventListener("click", cancelEvent);
    }
  },

  "disabled": {
    beforeSubmit: submitter => submitter.disabled = true,
    afterSubmit: submitter => submitter.disabled = false
  }
};

class Config {
  #submitter = null

  constructor(config) {
    Object.assign(this, config);
  }

  get submitter() {
    return this.#submitter
  }

  set submitter(value) {
    this.#submitter = submitter[value] || value;
  }
}

const forms = new Config({
  mode: "on",
  submitter: "disabled"
});

const config = {
  drive,
  forms
};

function expandURL(locatable) {
  return new URL(locatable.toString(), document.baseURI)
}

function getAnchor(url) {
  let anchorMatch;
  if (url.hash) {
    return url.hash.slice(1)
    // eslint-disable-next-line no-cond-assign
  } else if ((anchorMatch = url.href.match(/#(.*)$/))) {
    return anchorMatch[1]
  }
}

function getAction$1(form, submitter) {
  const action = submitter?.getAttribute("formaction") || form.getAttribute("action") || form.action;

  return expandURL(action)
}

function getExtension(url) {
  return (getLastPathComponent(url).match(/\.[^.]*$/) || [])[0] || ""
}

function isPrefixedBy(baseURL, url) {
  const prefix = getPrefix(url);
  return baseURL.href === expandURL(prefix).href || baseURL.href.startsWith(prefix)
}

function locationIsVisitable(location, rootLocation) {
  return isPrefixedBy(location, rootLocation) && !config.drive.unvisitableExtensions.has(getExtension(location))
}

function getRequestURL(url) {
  const anchor = getAnchor(url);
  return anchor != null ? url.href.slice(0, -(anchor.length + 1)) : url.href
}

function toCacheKey(url) {
  return getRequestURL(url)
}

function urlsAreEqual(left, right) {
  return expandURL(left).href == expandURL(right).href
}

function getPathComponents(url) {
  return url.pathname.split("/").slice(1)
}

function getLastPathComponent(url) {
  return getPathComponents(url).slice(-1)[0]
}

function getPrefix(url) {
  return addTrailingSlash(url.origin + url.pathname)
}

function addTrailingSlash(value) {
  return value.endsWith("/") ? value : value + "/"
}

class FetchResponse {
  constructor(response) {
    this.response = response;
  }

  get succeeded() {
    return this.response.ok
  }

  get failed() {
    return !this.succeeded
  }

  get clientError() {
    return this.statusCode >= 400 && this.statusCode <= 499
  }

  get serverError() {
    return this.statusCode >= 500 && this.statusCode <= 599
  }

  get redirected() {
    return this.response.redirected
  }

  get location() {
    return expandURL(this.response.url)
  }

  get isHTML() {
    return this.contentType && this.contentType.match(/^(?:text\/([^\s;,]+\b)?html|application\/xhtml\+xml)\b/)
  }

  get statusCode() {
    return this.response.status
  }

  get contentType() {
    return this.header("Content-Type")
  }

  get responseText() {
    return this.response.clone().text()
  }

  get responseHTML() {
    if (this.isHTML) {
      return this.response.clone().text()
    } else {
      return Promise.resolve(undefined)
    }
  }

  header(name) {
    return this.response.headers.get(name)
  }
}

class LimitedSet extends Set {
  constructor(maxSize) {
    super();
    this.maxSize = maxSize;
  }

  add(value) {
    if (this.size >= this.maxSize) {
      const iterator = this.values();
      const oldestValue = iterator.next().value;
      this.delete(oldestValue);
    }
    super.add(value);
  }
}

const recentRequests = new LimitedSet(20);

const nativeFetch = window.fetch;

function fetchWithTurboHeaders(url, options = {}) {
  const modifiedHeaders = new Headers(options.headers || {});
  const requestUID = uuid();
  recentRequests.add(requestUID);
  modifiedHeaders.append("X-Turbo-Request-Id", requestUID);

  return nativeFetch(url, {
    ...options,
    headers: modifiedHeaders
  })
}

function fetchMethodFromString(method) {
  switch (method.toLowerCase()) {
    case "get":
      return FetchMethod.get
    case "post":
      return FetchMethod.post
    case "put":
      return FetchMethod.put
    case "patch":
      return FetchMethod.patch
    case "delete":
      return FetchMethod.delete
  }
}

const FetchMethod = {
  get: "get",
  post: "post",
  put: "put",
  patch: "patch",
  delete: "delete"
};

function fetchEnctypeFromString(encoding) {
  switch (encoding.toLowerCase()) {
    case FetchEnctype.multipart:
      return FetchEnctype.multipart
    case FetchEnctype.plain:
      return FetchEnctype.plain
    default:
      return FetchEnctype.urlEncoded
  }
}

const FetchEnctype = {
  urlEncoded: "application/x-www-form-urlencoded",
  multipart: "multipart/form-data",
  plain: "text/plain"
};

class FetchRequest {
  abortController = new AbortController()
  #resolveRequestPromise = (_value) => {}

  constructor(delegate, method, location, requestBody = new URLSearchParams(), target = null, enctype = FetchEnctype.urlEncoded) {
    const [url, body] = buildResourceAndBody(expandURL(location), method, requestBody, enctype);

    this.delegate = delegate;
    this.url = url;
    this.target = target;
    this.fetchOptions = {
      credentials: "same-origin",
      redirect: "follow",
      method: method.toUpperCase(),
      headers: { ...this.defaultHeaders },
      body: body,
      signal: this.abortSignal,
      referrer: this.delegate.referrer?.href
    };
    this.enctype = enctype;
  }

  get method() {
    return this.fetchOptions.method
  }

  set method(value) {
    const fetchBody = this.isSafe ? this.url.searchParams : this.fetchOptions.body || new FormData();
    const fetchMethod = fetchMethodFromString(value) || FetchMethod.get;

    this.url.search = "";

    const [url, body] = buildResourceAndBody(this.url, fetchMethod, fetchBody, this.enctype);

    this.url = url;
    this.fetchOptions.body = body;
    this.fetchOptions.method = fetchMethod.toUpperCase();
  }

  get headers() {
    return this.fetchOptions.headers
  }

  set headers(value) {
    this.fetchOptions.headers = value;
  }

  get body() {
    if (this.isSafe) {
      return this.url.searchParams
    } else {
      return this.fetchOptions.body
    }
  }

  set body(value) {
    this.fetchOptions.body = value;
  }

  get location() {
    return this.url
  }

  get params() {
    return this.url.searchParams
  }

  get entries() {
    return this.body ? Array.from(this.body.entries()) : []
  }

  cancel() {
    this.abortController.abort();
  }

  async perform() {
    const { fetchOptions } = this;
    this.delegate.prepareRequest(this);
    const event = await this.#allowRequestToBeIntercepted(fetchOptions);
    try {
      this.delegate.requestStarted(this);

      if (event.detail.fetchRequest) {
        this.response = event.detail.fetchRequest.response;
      } else {
        this.response = fetchWithTurboHeaders(this.url.href, fetchOptions);
      }

      const response = await this.response;
      return await this.receive(response)
    } catch (error) {
      if (error.name !== "AbortError") {
        if (this.#willDelegateErrorHandling(error)) {
          this.delegate.requestErrored(this, error);
        }
        throw error
      }
    } finally {
      this.delegate.requestFinished(this);
    }
  }

  async receive(response) {
    const fetchResponse = new FetchResponse(response);
    const event = dispatch("turbo:before-fetch-response", {
      cancelable: true,
      detail: { fetchResponse },
      target: this.target
    });
    if (event.defaultPrevented) {
      this.delegate.requestPreventedHandlingResponse(this, fetchResponse);
    } else if (fetchResponse.succeeded) {
      this.delegate.requestSucceededWithResponse(this, fetchResponse);
    } else {
      this.delegate.requestFailedWithResponse(this, fetchResponse);
    }
    return fetchResponse
  }

  get defaultHeaders() {
    return {
      Accept: "text/html, application/xhtml+xml"
    }
  }

  get isSafe() {
    return isSafe(this.method)
  }

  get abortSignal() {
    return this.abortController.signal
  }

  acceptResponseType(mimeType) {
    this.headers["Accept"] = [mimeType, this.headers["Accept"]].join(", ");
  }

  async #allowRequestToBeIntercepted(fetchOptions) {
    const requestInterception = new Promise((resolve) => (this.#resolveRequestPromise = resolve));
    const event = dispatch("turbo:before-fetch-request", {
      cancelable: true,
      detail: {
        fetchOptions,
        url: this.url,
        resume: this.#resolveRequestPromise
      },
      target: this.target
    });
    this.url = event.detail.url;
    if (event.defaultPrevented) await requestInterception;

    return event
  }

  #willDelegateErrorHandling(error) {
    const event = dispatch("turbo:fetch-request-error", {
      target: this.target,
      cancelable: true,
      detail: { request: this, error: error }
    });

    return !event.defaultPrevented
  }
}

function isSafe(fetchMethod) {
  return fetchMethodFromString(fetchMethod) == FetchMethod.get
}

function buildResourceAndBody(resource, method, requestBody, enctype) {
  const searchParams =
    Array.from(requestBody).length > 0 ? new URLSearchParams(entriesExcludingFiles(requestBody)) : resource.searchParams;

  if (isSafe(method)) {
    return [mergeIntoURLSearchParams(resource, searchParams), null]
  } else if (enctype == FetchEnctype.urlEncoded) {
    return [resource, searchParams]
  } else {
    return [resource, requestBody]
  }
}

function entriesExcludingFiles(requestBody) {
  const entries = [];

  for (const [name, value] of requestBody) {
    if (value instanceof File) continue
    else entries.push([name, value]);
  }

  return entries
}

function mergeIntoURLSearchParams(url, requestBody) {
  const searchParams = new URLSearchParams(entriesExcludingFiles(requestBody));

  url.search = searchParams.toString();

  return url
}

class AppearanceObserver {
  started = false

  constructor(delegate, element) {
    this.delegate = delegate;
    this.element = element;
    this.intersectionObserver = new IntersectionObserver(this.intersect);
  }

  start() {
    if (!this.started) {
      this.started = true;
      this.intersectionObserver.observe(this.element);
    }
  }

  stop() {
    if (this.started) {
      this.started = false;
      this.intersectionObserver.unobserve(this.element);
    }
  }

  intersect = (entries) => {
    const lastEntry = entries.slice(-1)[0];
    if (lastEntry?.isIntersecting) {
      this.delegate.elementAppearedInViewport(this.element);
    }
  }
}

class StreamMessage {
  static contentType = "text/vnd.turbo-stream.html"

  static wrap(message) {
    if (typeof message == "string") {
      return new this(createDocumentFragment(message))
    } else {
      return message
    }
  }

  constructor(fragment) {
    this.fragment = importStreamElements(fragment);
  }
}

function importStreamElements(fragment) {
  for (const element of fragment.querySelectorAll("turbo-stream")) {
    const streamElement = document.importNode(element, true);

    for (const inertScriptElement of streamElement.templateElement.content.querySelectorAll("script")) {
      inertScriptElement.replaceWith(activateScriptElement(inertScriptElement));
    }

    element.replaceWith(streamElement);
  }

  return fragment
}

const PREFETCH_DELAY = 100;

class PrefetchCache {
  #prefetchTimeout = null
  #prefetched = null

  get(url) {
    if (this.#prefetched && this.#prefetched.url === url && this.#prefetched.expire > Date.now()) {
      return this.#prefetched.request
    }
  }

  setLater(url, request, ttl) {
    this.clear();

    this.#prefetchTimeout = setTimeout(() => {
      request.perform();
      this.set(url, request, ttl);
      this.#prefetchTimeout = null;
    }, PREFETCH_DELAY);
  }

  set(url, request, ttl) {
    this.#prefetched = { url, request, expire: new Date(new Date().getTime() + ttl) };
  }

  clear() {
    if (this.#prefetchTimeout) clearTimeout(this.#prefetchTimeout);
    this.#prefetched = null;
  }
}

const cacheTtl = 10 * 1000;
const prefetchCache = new PrefetchCache();

const FormSubmissionState = {
  initialized: "initialized",
  requesting: "requesting",
  waiting: "waiting",
  receiving: "receiving",
  stopping: "stopping",
  stopped: "stopped"
};

class FormSubmission {
  state = FormSubmissionState.initialized

  static confirmMethod(message) {
    return Promise.resolve(confirm(message))
  }

  constructor(delegate, formElement, submitter, mustRedirect = false) {
    const method = getMethod(formElement, submitter);
    const action = getAction(getFormAction(formElement, submitter), method);
    const body = buildFormData(formElement, submitter);
    const enctype = getEnctype(formElement, submitter);

    this.delegate = delegate;
    this.formElement = formElement;
    this.submitter = submitter;
    this.fetchRequest = new FetchRequest(this, method, action, body, formElement, enctype);
    this.mustRedirect = mustRedirect;
  }

  get method() {
    return this.fetchRequest.method
  }

  set method(value) {
    this.fetchRequest.method = value;
  }

  get action() {
    return this.fetchRequest.url.toString()
  }

  set action(value) {
    this.fetchRequest.url = expandURL(value);
  }

  get body() {
    return this.fetchRequest.body
  }

  get enctype() {
    return this.fetchRequest.enctype
  }

  get isSafe() {
    return this.fetchRequest.isSafe
  }

  get location() {
    return this.fetchRequest.url
  }

  // The submission process

  async start() {
    const { initialized, requesting } = FormSubmissionState;
    const confirmationMessage = getAttribute("data-turbo-confirm", this.submitter, this.formElement);

    if (typeof confirmationMessage === "string") {
      const confirmMethod = typeof config.forms.confirm === "function" ?
        config.forms.confirm :
        FormSubmission.confirmMethod;

      const answer = await confirmMethod(confirmationMessage, this.formElement, this.submitter);
      if (!answer) {
        return
      }
    }

    if (this.state == initialized) {
      this.state = requesting;
      return this.fetchRequest.perform()
    }
  }

  stop() {
    const { stopping, stopped } = FormSubmissionState;
    if (this.state != stopping && this.state != stopped) {
      this.state = stopping;
      this.fetchRequest.cancel();
      return true
    }
  }

  // Fetch request delegate

  prepareRequest(request) {
    if (!request.isSafe) {
      const token = getCookieValue(getMetaContent("csrf-param")) || getMetaContent("csrf-token");
      if (token) {
        request.headers["X-CSRF-Token"] = token;
      }
    }

    if (this.requestAcceptsTurboStreamResponse(request)) {
      request.acceptResponseType(StreamMessage.contentType);
    }
  }

  requestStarted(_request) {
    this.state = FormSubmissionState.waiting;
    if (this.submitter) config.forms.submitter.beforeSubmit(this.submitter);
    this.setSubmitsWith();
    markAsBusy(this.formElement);
    dispatch("turbo:submit-start", {
      target: this.formElement,
      detail: { formSubmission: this }
    });
    this.delegate.formSubmissionStarted(this);
  }

  requestPreventedHandlingResponse(request, response) {
    prefetchCache.clear();

    this.result = { success: response.succeeded, fetchResponse: response };
  }

  requestSucceededWithResponse(request, response) {
    if (response.clientError || response.serverError) {
      this.delegate.formSubmissionFailedWithResponse(this, response);
      return
    }

    prefetchCache.clear();

    if (this.requestMustRedirect(request) && responseSucceededWithoutRedirect(response)) {
      const error = new Error("Form responses must redirect to another location");
      this.delegate.formSubmissionErrored(this, error);
    } else {
      this.state = FormSubmissionState.receiving;
      this.result = { success: true, fetchResponse: response };
      this.delegate.formSubmissionSucceededWithResponse(this, response);
    }
  }

  requestFailedWithResponse(request, response) {
    this.result = { success: false, fetchResponse: response };
    this.delegate.formSubmissionFailedWithResponse(this, response);
  }

  requestErrored(request, error) {
    this.result = { success: false, error };
    this.delegate.formSubmissionErrored(this, error);
  }

  requestFinished(_request) {
    this.state = FormSubmissionState.stopped;
    if (this.submitter) config.forms.submitter.afterSubmit(this.submitter);
    this.resetSubmitterText();
    clearBusyState(this.formElement);
    dispatch("turbo:submit-end", {
      target: this.formElement,
      detail: { formSubmission: this, ...this.result }
    });
    this.delegate.formSubmissionFinished(this);
  }

  // Private

  setSubmitsWith() {
    if (!this.submitter || !this.submitsWith) return

    if (this.submitter.matches("button")) {
      this.originalSubmitText = this.submitter.innerHTML;
      this.submitter.innerHTML = this.submitsWith;
    } else if (this.submitter.matches("input")) {
      const input = this.submitter;
      this.originalSubmitText = input.value;
      input.value = this.submitsWith;
    }
  }

  resetSubmitterText() {
    if (!this.submitter || !this.originalSubmitText) return

    if (this.submitter.matches("button")) {
      this.submitter.innerHTML = this.originalSubmitText;
    } else if (this.submitter.matches("input")) {
      const input = this.submitter;
      input.value = this.originalSubmitText;
    }
  }

  requestMustRedirect(request) {
    return !request.isSafe && this.mustRedirect
  }

  requestAcceptsTurboStreamResponse(request) {
    return !request.isSafe || hasAttribute("data-turbo-stream", this.submitter, this.formElement)
  }

  get submitsWith() {
    return this.submitter?.getAttribute("data-turbo-submits-with")
  }
}

function buildFormData(formElement, submitter) {
  const formData = new FormData(formElement);
  const name = submitter?.getAttribute("name");
  const value = submitter?.getAttribute("value");

  if (name) {
    formData.append(name, value || "");
  }

  return formData
}

function getCookieValue(cookieName) {
  if (cookieName != null) {
    const cookies = document.cookie ? document.cookie.split("; ") : [];
    const cookie = cookies.find((cookie) => cookie.startsWith(cookieName));
    if (cookie) {
      const value = cookie.split("=").slice(1).join("=");
      return value ? decodeURIComponent(value) : undefined
    }
  }
}

function responseSucceededWithoutRedirect(response) {
  return response.statusCode == 200 && !response.redirected
}

function getFormAction(formElement, submitter) {
  const formElementAction = typeof formElement.action === "string" ? formElement.action : null;

  if (submitter?.hasAttribute("formaction")) {
    return submitter.getAttribute("formaction") || ""
  } else {
    return formElement.getAttribute("action") || formElementAction || ""
  }
}

function getAction(formAction, fetchMethod) {
  const action = expandURL(formAction);

  if (isSafe(fetchMethod)) {
    action.search = "";
  }

  return action
}

function getMethod(formElement, submitter) {
  const method = submitter?.getAttribute("formmethod") || formElement.getAttribute("method") || "";
  return fetchMethodFromString(method.toLowerCase()) || FetchMethod.get
}

function getEnctype(formElement, submitter) {
  return fetchEnctypeFromString(submitter?.getAttribute("formenctype") || formElement.enctype)
}

class Snapshot {
  constructor(element) {
    this.element = element;
  }

  get activeElement() {
    return this.element.ownerDocument.activeElement
  }

  get children() {
    return [...this.element.children]
  }

  hasAnchor(anchor) {
    return this.getElementForAnchor(anchor) != null
  }

  getElementForAnchor(anchor) {
    return anchor ? this.element.querySelector(`[id='${anchor}'], a[name='${anchor}']`) : null
  }

  get isConnected() {
    return this.element.isConnected
  }

  get firstAutofocusableElement() {
    return queryAutofocusableElement(this.element)
  }

  get permanentElements() {
    return queryPermanentElementsAll(this.element)
  }

  getPermanentElementById(id) {
    return getPermanentElementById(this.element, id)
  }

  getPermanentElementMapForSnapshot(snapshot) {
    const permanentElementMap = {};

    for (const currentPermanentElement of this.permanentElements) {
      const { id } = currentPermanentElement;
      const newPermanentElement = snapshot.getPermanentElementById(id);
      if (newPermanentElement) {
        permanentElementMap[id] = [currentPermanentElement, newPermanentElement];
      }
    }

    return permanentElementMap
  }
}

function getPermanentElementById(node, id) {
  return node.querySelector(`#${id}[data-turbo-permanent]`)
}

function queryPermanentElementsAll(node) {
  return node.querySelectorAll("[id][data-turbo-permanent]")
}

class FormSubmitObserver {
  started = false

  constructor(delegate, eventTarget) {
    this.delegate = delegate;
    this.eventTarget = eventTarget;
  }

  start() {
    if (!this.started) {
      this.eventTarget.addEventListener("submit", this.submitCaptured, true);
      this.started = true;
    }
  }

  stop() {
    if (this.started) {
      this.eventTarget.removeEventListener("submit", this.submitCaptured, true);
      this.started = false;
    }
  }

  submitCaptured = () => {
    this.eventTarget.removeEventListener("submit", this.submitBubbled, false);
    this.eventTarget.addEventListener("submit", this.submitBubbled, false);
  }

  submitBubbled = (event) => {
    if (!event.defaultPrevented) {
      const form = event.target instanceof HTMLFormElement ? event.target : undefined;
      const submitter = event.submitter || undefined;

      if (
        form &&
        submissionDoesNotDismissDialog(form, submitter) &&
        submissionDoesNotTargetIFrame(form, submitter) &&
        this.delegate.willSubmitForm(form, submitter)
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();
        this.delegate.formSubmitted(form, submitter);
      }
    }
  }
}

function submissionDoesNotDismissDialog(form, submitter) {
  const method = submitter?.getAttribute("formmethod") || form.getAttribute("method");

  return method != "dialog"
}

function submissionDoesNotTargetIFrame(form, submitter) {
  const target = submitter?.getAttribute("formtarget") || form.getAttribute("target");

  return doesNotTargetIFrame(target)
}

class View {
  #resolveRenderPromise = (_value) => {}
  #resolveInterceptionPromise = (_value) => {}

  constructor(delegate, element) {
    this.delegate = delegate;
    this.element = element;
  }

  // Scrolling

  scrollToAnchor(anchor) {
    const element = this.snapshot.getElementForAnchor(anchor);
    if (element) {
      this.scrollToElement(element);
      this.focusElement(element);
    } else {
      this.scrollToPosition({ x: 0, y: 0 });
    }
  }

  scrollToAnchorFromLocation(location) {
    this.scrollToAnchor(getAnchor(location));
  }

  scrollToElement(element) {
    element.scrollIntoView();
  }

  focusElement(element) {
    if (element instanceof HTMLElement) {
      if (element.hasAttribute("tabindex")) {
        element.focus();
      } else {
        element.setAttribute("tabindex", "-1");
        element.focus();
        element.removeAttribute("tabindex");
      }
    }
  }

  scrollToPosition({ x, y }) {
    this.scrollRoot.scrollTo(x, y);
  }

  scrollToTop() {
    this.scrollToPosition({ x: 0, y: 0 });
  }

  get scrollRoot() {
    return window
  }

  // Rendering

  async render(renderer) {
    const { isPreview, shouldRender, willRender, newSnapshot: snapshot } = renderer;

    // A workaround to ignore tracked element mismatch reloads when performing
    // a promoted Visit from a frame navigation
    const shouldInvalidate = willRender;

    if (shouldRender) {
      try {
        this.renderPromise = new Promise((resolve) => (this.#resolveRenderPromise = resolve));
        this.renderer = renderer;
        await this.prepareToRenderSnapshot(renderer);

        const renderInterception = new Promise((resolve) => (this.#resolveInterceptionPromise = resolve));
        const options = { resume: this.#resolveInterceptionPromise, render: this.renderer.renderElement, renderMethod: this.renderer.renderMethod };
        const immediateRender = this.delegate.allowsImmediateRender(snapshot, options);
        if (!immediateRender) await renderInterception;

        await this.renderSnapshot(renderer);
        this.delegate.viewRenderedSnapshot(snapshot, isPreview, this.renderer.renderMethod);
        this.delegate.preloadOnLoadLinksForView(this.element);
        this.finishRenderingSnapshot(renderer);
      } finally {
        delete this.renderer;
        this.#resolveRenderPromise(undefined);
        delete this.renderPromise;
      }
    } else if (shouldInvalidate) {
      this.invalidate(renderer.reloadReason);
    }
  }

  invalidate(reason) {
    this.delegate.viewInvalidated(reason);
  }

  async prepareToRenderSnapshot(renderer) {
    this.markAsPreview(renderer.isPreview);
    await renderer.prepareToRender();
  }

  markAsPreview(isPreview) {
    if (isPreview) {
      this.element.setAttribute("data-turbo-preview", "");
    } else {
      this.element.removeAttribute("data-turbo-preview");
    }
  }

  markVisitDirection(direction) {
    this.element.setAttribute("data-turbo-visit-direction", direction);
  }

  unmarkVisitDirection() {
    this.element.removeAttribute("data-turbo-visit-direction");
  }

  async renderSnapshot(renderer) {
    await renderer.render();
  }

  finishRenderingSnapshot(renderer) {
    renderer.finishRendering();
  }
}

class FrameView extends View {
  missing() {
    this.element.innerHTML = `<strong class="turbo-frame-error">Content missing</strong>`;
  }

  get snapshot() {
    return new Snapshot(this.element)
  }
}

class LinkInterceptor {
  constructor(delegate, element) {
    this.delegate = delegate;
    this.element = element;
  }

  start() {
    this.element.addEventListener("click", this.clickBubbled);
    document.addEventListener("turbo:click", this.linkClicked);
    document.addEventListener("turbo:before-visit", this.willVisit);
  }

  stop() {
    this.element.removeEventListener("click", this.clickBubbled);
    document.removeEventListener("turbo:click", this.linkClicked);
    document.removeEventListener("turbo:before-visit", this.willVisit);
  }

  clickBubbled = (event) => {
    if (this.clickEventIsSignificant(event)) {
      this.clickEvent = event;
    } else {
      delete this.clickEvent;
    }
  }

  linkClicked = (event) => {
    if (this.clickEvent && this.clickEventIsSignificant(event)) {
      if (this.delegate.shouldInterceptLinkClick(event.target, event.detail.url, event.detail.originalEvent)) {
        this.clickEvent.preventDefault();
        event.preventDefault();
        this.delegate.linkClickIntercepted(event.target, event.detail.url, event.detail.originalEvent);
      }
    }
    delete this.clickEvent;
  }

  willVisit = (_event) => {
    delete this.clickEvent;
  }

  clickEventIsSignificant(event) {
    const target = event.composed ? event.target?.parentElement : event.target;
    const element = findLinkFromClickTarget(target) || target;

    return element instanceof Element && element.closest("turbo-frame, html") == this.element
  }
}

class LinkClickObserver {
  started = false

  constructor(delegate, eventTarget) {
    this.delegate = delegate;
    this.eventTarget = eventTarget;
  }

  start() {
    if (!this.started) {
      this.eventTarget.addEventListener("click", this.clickCaptured, true);
      this.started = true;
    }
  }

  stop() {
    if (this.started) {
      this.eventTarget.removeEventListener("click", this.clickCaptured, true);
      this.started = false;
    }
  }

  clickCaptured = () => {
    this.eventTarget.removeEventListener("click", this.clickBubbled, false);
    this.eventTarget.addEventListener("click", this.clickBubbled, false);
  }

  clickBubbled = (event) => {
    if (event instanceof MouseEvent && this.clickEventIsSignificant(event)) {
      const target = (event.composedPath && event.composedPath()[0]) || event.target;
      const link = findLinkFromClickTarget(target);
      if (link && doesNotTargetIFrame(link.target)) {
        const location = getLocationForLink(link);
        if (this.delegate.willFollowLinkToLocation(link, location, event)) {
          event.preventDefault();
          this.delegate.followedLinkToLocation(link, location);
        }
      }
    }
  }

  clickEventIsSignificant(event) {
    return !(
      (event.target && event.target.isContentEditable) ||
      event.defaultPrevented ||
      event.which > 1 ||
      event.altKey ||
      event.ctrlKey ||
      event.metaKey ||
      event.shiftKey
    )
  }
}

class FormLinkClickObserver {
  constructor(delegate, element) {
    this.delegate = delegate;
    this.linkInterceptor = new LinkClickObserver(this, element);
  }

  start() {
    this.linkInterceptor.start();
  }

  stop() {
    this.linkInterceptor.stop();
  }

  // Link hover observer delegate

  canPrefetchRequestToLocation(link, location) {
    return false
  }

  prefetchAndCacheRequestToLocation(link, location) {
    return
  }

  // Link click observer delegate

  willFollowLinkToLocation(link, location, originalEvent) {
    return (
      this.delegate.willSubmitFormLinkToLocation(link, location, originalEvent) &&
      (link.hasAttribute("data-turbo-method") || link.hasAttribute("data-turbo-stream"))
    )
  }

  followedLinkToLocation(link, location) {
    const form = document.createElement("form");

    const type = "hidden";
    for (const [name, value] of location.searchParams) {
      form.append(Object.assign(document.createElement("input"), { type, name, value }));
    }

    const action = Object.assign(location, { search: "" });
    form.setAttribute("data-turbo", "true");
    form.setAttribute("action", action.href);
    form.setAttribute("hidden", "");

    const method = link.getAttribute("data-turbo-method");
    if (method) form.setAttribute("method", method);

    const turboFrame = link.getAttribute("data-turbo-frame");
    if (turboFrame) form.setAttribute("data-turbo-frame", turboFrame);

    const turboAction = getVisitAction(link);
    if (turboAction) form.setAttribute("data-turbo-action", turboAction);

    const turboConfirm = link.getAttribute("data-turbo-confirm");
    if (turboConfirm) form.setAttribute("data-turbo-confirm", turboConfirm);

    const turboStream = link.hasAttribute("data-turbo-stream");
    if (turboStream) form.setAttribute("data-turbo-stream", "");

    this.delegate.submittedFormLinkToLocation(link, location, form);

    document.body.appendChild(form);
    form.addEventListener("turbo:submit-end", () => form.remove(), { once: true });
    requestAnimationFrame(() => form.requestSubmit());
  }
}

class Bardo {
  static async preservingPermanentElements(delegate, permanentElementMap, callback) {
    const bardo = new this(delegate, permanentElementMap);
    bardo.enter();
    await callback();
    bardo.leave();
  }

  constructor(delegate, permanentElementMap) {
    this.delegate = delegate;
    this.permanentElementMap = permanentElementMap;
  }

  enter() {
    for (const id in this.permanentElementMap) {
      const [currentPermanentElement, newPermanentElement] = this.permanentElementMap[id];
      this.delegate.enteringBardo(currentPermanentElement, newPermanentElement);
      this.replaceNewPermanentElementWithPlaceholder(newPermanentElement);
    }
  }

  leave() {
    for (const id in this.permanentElementMap) {
      const [currentPermanentElement] = this.permanentElementMap[id];
      this.replaceCurrentPermanentElementWithClone(currentPermanentElement);
      this.replacePlaceholderWithPermanentElement(currentPermanentElement);
      this.delegate.leavingBardo(currentPermanentElement);
    }
  }

  replaceNewPermanentElementWithPlaceholder(permanentElement) {
    const placeholder = createPlaceholderForPermanentElement(permanentElement);
    permanentElement.replaceWith(placeholder);
  }

  replaceCurrentPermanentElementWithClone(permanentElement) {
    const clone = permanentElement.cloneNode(true);
    permanentElement.replaceWith(clone);
  }

  replacePlaceholderWithPermanentElement(permanentElement) {
    const placeholder = this.getPlaceholderById(permanentElement.id);
    placeholder?.replaceWith(permanentElement);
  }

  getPlaceholderById(id) {
    return this.placeholders.find((element) => element.content == id)
  }

  get placeholders() {
    return [...document.querySelectorAll("meta[name=turbo-permanent-placeholder][content]")]
  }
}

function createPlaceholderForPermanentElement(permanentElement) {
  const element = document.createElement("meta");
  element.setAttribute("name", "turbo-permanent-placeholder");
  element.setAttribute("content", permanentElement.id);
  return element
}

class Renderer {
  #activeElement = null

  static renderElement(currentElement, newElement) {
    // Abstract method
  }

  constructor(currentSnapshot, newSnapshot, isPreview, willRender = true) {
    this.currentSnapshot = currentSnapshot;
    this.newSnapshot = newSnapshot;
    this.isPreview = isPreview;
    this.willRender = willRender;
    this.renderElement = this.constructor.renderElement;
    this.promise = new Promise((resolve, reject) => (this.resolvingFunctions = { resolve, reject }));
  }

  get shouldRender() {
    return true
  }

  get shouldAutofocus() {
    return true
  }

  get reloadReason() {
    return
  }

  prepareToRender() {
    return
  }

  render() {
    // Abstract method
  }

  finishRendering() {
    if (this.resolvingFunctions) {
      this.resolvingFunctions.resolve();
      delete this.resolvingFunctions;
    }
  }

  async preservingPermanentElements(callback) {
    await Bardo.preservingPermanentElements(this, this.permanentElementMap, callback);
  }

  focusFirstAutofocusableElement() {
    if (this.shouldAutofocus) {
      const element = this.connectedSnapshot.firstAutofocusableElement;
      if (element) {
        element.focus();
      }
    }
  }

  // Bardo delegate

  enteringBardo(currentPermanentElement) {
    if (this.#activeElement) return

    if (currentPermanentElement.contains(this.currentSnapshot.activeElement)) {
      this.#activeElement = this.currentSnapshot.activeElement;
    }
  }

  leavingBardo(currentPermanentElement) {
    if (currentPermanentElement.contains(this.#activeElement) && this.#activeElement instanceof HTMLElement) {
      this.#activeElement.focus();

      this.#activeElement = null;
    }
  }

  get connectedSnapshot() {
    return this.newSnapshot.isConnected ? this.newSnapshot : this.currentSnapshot
  }

  get currentElement() {
    return this.currentSnapshot.element
  }

  get newElement() {
    return this.newSnapshot.element
  }

  get permanentElementMap() {
    return this.currentSnapshot.getPermanentElementMapForSnapshot(this.newSnapshot)
  }

  get renderMethod() {
    return "replace"
  }
}

class FrameRenderer extends Renderer {
  static renderElement(currentElement, newElement) {
    const destinationRange = document.createRange();
    destinationRange.selectNodeContents(currentElement);
    destinationRange.deleteContents();

    const frameElement = newElement;
    const sourceRange = frameElement.ownerDocument?.createRange();
    if (sourceRange) {
      sourceRange.selectNodeContents(frameElement);
      currentElement.appendChild(sourceRange.extractContents());
    }
  }

  constructor(delegate, currentSnapshot, newSnapshot, renderElement, isPreview, willRender = true) {
    super(currentSnapshot, newSnapshot, renderElement, isPreview, willRender);
    this.delegate = delegate;
  }

  get shouldRender() {
    return true
  }

  async render() {
    await nextRepaint();
    this.preservingPermanentElements(() => {
      this.loadFrameElement();
    });
    this.scrollFrameIntoView();
    await nextRepaint();
    this.focusFirstAutofocusableElement();
    await nextRepaint();
    this.activateScriptElements();
  }

  loadFrameElement() {
    this.delegate.willRenderFrame(this.currentElement, this.newElement);
    this.renderElement(this.currentElement, this.newElement);
  }

  scrollFrameIntoView() {
    if (this.currentElement.autoscroll || this.newElement.autoscroll) {
      const element = this.currentElement.firstElementChild;
      const block = readScrollLogicalPosition(this.currentElement.getAttribute("data-autoscroll-block"), "end");
      const behavior = readScrollBehavior(this.currentElement.getAttribute("data-autoscroll-behavior"), "auto");

      if (element) {
        element.scrollIntoView({ block, behavior });
        return true
      }
    }
    return false
  }

  activateScriptElements() {
    for (const inertScriptElement of this.newScriptElements) {
      const activatedScriptElement = activateScriptElement(inertScriptElement);
      inertScriptElement.replaceWith(activatedScriptElement);
    }
  }

  get newScriptElements() {
    return this.currentElement.querySelectorAll("script")
  }
}

function readScrollLogicalPosition(value, defaultValue) {
  if (value == "end" || value == "start" || value == "center" || value == "nearest") {
    return value
  } else {
    return defaultValue
  }
}

function readScrollBehavior(value, defaultValue) {
  if (value == "auto" || value == "smooth") {
    return value
  } else {
    return defaultValue
  }
}

/**
 * @typedef {object} ConfigHead
 *
 * @property {'merge' | 'append' | 'morph' | 'none'} [style]
 * @property {boolean} [block]
 * @property {boolean} [ignore]
 * @property {function(Element): boolean} [shouldPreserve]
 * @property {function(Element): boolean} [shouldReAppend]
 * @property {function(Element): boolean} [shouldRemove]
 * @property {function(Element, {added: Node[], kept: Element[], removed: Element[]}): void} [afterHeadMorphed]
 */

/**
 * @typedef {object} ConfigCallbacks
 *
 * @property {function(Node): boolean} [beforeNodeAdded]
 * @property {function(Node): void} [afterNodeAdded]
 * @property {function(Element, Node): boolean} [beforeNodeMorphed]
 * @property {function(Element, Node): void} [afterNodeMorphed]
 * @property {function(Element): boolean} [beforeNodeRemoved]
 * @property {function(Element): void} [afterNodeRemoved]
 * @property {function(string, Element, "update" | "remove"): boolean} [beforeAttributeUpdated]
 */

/**
 * @typedef {object} Config
 *
 * @property {'outerHTML' | 'innerHTML'} [morphStyle]
 * @property {boolean} [ignoreActive]
 * @property {boolean} [ignoreActiveValue]
 * @property {boolean} [restoreFocus]
 * @property {ConfigCallbacks} [callbacks]
 * @property {ConfigHead} [head]
 */

/**
 * @typedef {function} NoOp
 *
 * @returns {void}
 */

/**
 * @typedef {object} ConfigHeadInternal
 *
 * @property {'merge' | 'append' | 'morph' | 'none'} style
 * @property {boolean} [block]
 * @property {boolean} [ignore]
 * @property {(function(Element): boolean) | NoOp} shouldPreserve
 * @property {(function(Element): boolean) | NoOp} shouldReAppend
 * @property {(function(Element): boolean) | NoOp} shouldRemove
 * @property {(function(Element, {added: Node[], kept: Element[], removed: Element[]}): void) | NoOp} afterHeadMorphed
 */

/**
 * @typedef {object} ConfigCallbacksInternal
 *
 * @property {(function(Node): boolean) | NoOp} beforeNodeAdded
 * @property {(function(Node): void) | NoOp} afterNodeAdded
 * @property {(function(Node, Node): boolean) | NoOp} beforeNodeMorphed
 * @property {(function(Node, Node): void) | NoOp} afterNodeMorphed
 * @property {(function(Node): boolean) | NoOp} beforeNodeRemoved
 * @property {(function(Node): void) | NoOp} afterNodeRemoved
 * @property {(function(string, Element, "update" | "remove"): boolean) | NoOp} beforeAttributeUpdated
 */

/**
 * @typedef {object} ConfigInternal
 *
 * @property {'outerHTML' | 'innerHTML'} morphStyle
 * @property {boolean} [ignoreActive]
 * @property {boolean} [ignoreActiveValue]
 * @property {boolean} [restoreFocus]
 * @property {ConfigCallbacksInternal} callbacks
 * @property {ConfigHeadInternal} head
 */

/**
 * @typedef {Object} IdSets
 * @property {Set<string>} persistentIds
 * @property {Map<Node, Set<string>>} idMap
 */

/**
 * @typedef {Function} Morph
 *
 * @param {Element | Document} oldNode
 * @param {Element | Node | HTMLCollection | Node[] | string | null} newContent
 * @param {Config} [config]
 * @returns {undefined | Node[]}
 */

// base IIFE to define idiomorph
/**
 *
 * @type {{defaults: ConfigInternal, morph: Morph}}
 */
var Idiomorph = (function () {

  /**
   * @typedef {object} MorphContext
   *
   * @property {Element} target
   * @property {Element} newContent
   * @property {ConfigInternal} config
   * @property {ConfigInternal['morphStyle']} morphStyle
   * @property {ConfigInternal['ignoreActive']} ignoreActive
   * @property {ConfigInternal['ignoreActiveValue']} ignoreActiveValue
   * @property {ConfigInternal['restoreFocus']} restoreFocus
   * @property {Map<Node, Set<string>>} idMap
   * @property {Set<string>} persistentIds
   * @property {ConfigInternal['callbacks']} callbacks
   * @property {ConfigInternal['head']} head
   * @property {HTMLDivElement} pantry
   */

  //=============================================================================
  // AND NOW IT BEGINS...
  //=============================================================================

  const noOp = () => {};
  /**
   * Default configuration values, updatable by users now
   * @type {ConfigInternal}
   */
  const defaults = {
    morphStyle: "outerHTML",
    callbacks: {
      beforeNodeAdded: noOp,
      afterNodeAdded: noOp,
      beforeNodeMorphed: noOp,
      afterNodeMorphed: noOp,
      beforeNodeRemoved: noOp,
      afterNodeRemoved: noOp,
      beforeAttributeUpdated: noOp,
    },
    head: {
      style: "merge",
      shouldPreserve: (elt) => elt.getAttribute("im-preserve") === "true",
      shouldReAppend: (elt) => elt.getAttribute("im-re-append") === "true",
      shouldRemove: noOp,
      afterHeadMorphed: noOp,
    },
    restoreFocus: true,
  };

  /**
   * Core idiomorph function for morphing one DOM tree to another
   *
   * @param {Element | Document} oldNode
   * @param {Element | Node | HTMLCollection | Node[] | string | null} newContent
   * @param {Config} [config]
   * @returns {Promise<Node[]> | Node[]}
   */
  function morph(oldNode, newContent, config = {}) {
    oldNode = normalizeElement(oldNode);
    const newNode = normalizeParent(newContent);
    const ctx = createMorphContext(oldNode, newNode, config);

    const morphedNodes = saveAndRestoreFocus(ctx, () => {
      return withHeadBlocking(
        ctx,
        oldNode,
        newNode,
        /** @param {MorphContext} ctx */ (ctx) => {
          if (ctx.morphStyle === "innerHTML") {
            morphChildren(ctx, oldNode, newNode);
            return Array.from(oldNode.childNodes);
          } else {
            return morphOuterHTML(ctx, oldNode, newNode);
          }
        },
      );
    });

    ctx.pantry.remove();
    return morphedNodes;
  }

  /**
   * Morph just the outerHTML of the oldNode to the newContent
   * We have to be careful because the oldNode could have siblings which need to be untouched
   * @param {MorphContext} ctx
   * @param {Element} oldNode
   * @param {Element} newNode
   * @returns {Node[]}
   */
  function morphOuterHTML(ctx, oldNode, newNode) {
    const oldParent = normalizeParent(oldNode);

    // basis for calulating which nodes were morphed
    // since there may be unmorphed sibling nodes
    let childNodes = Array.from(oldParent.childNodes);
    const index = childNodes.indexOf(oldNode);
    // how many elements are to the right of the oldNode
    const rightMargin = childNodes.length - (index + 1);

    morphChildren(
      ctx,
      oldParent,
      newNode,
      // these two optional params are the secret sauce
      oldNode, // start point for iteration
      oldNode.nextSibling, // end point for iteration
    );

    // return just the morphed nodes
    childNodes = Array.from(oldParent.childNodes);
    return childNodes.slice(index, childNodes.length - rightMargin);
  }

  /**
   * @param {MorphContext} ctx
   * @param {Function} fn
   * @returns {Promise<Node[]> | Node[]}
   */
  function saveAndRestoreFocus(ctx, fn) {
    if (!ctx.config.restoreFocus) return fn();
    let activeElement =
      /** @type {HTMLInputElement|HTMLTextAreaElement|null} */ (
        document.activeElement
      );

    // don't bother if the active element is not an input or textarea
    if (
      !(
        activeElement instanceof HTMLInputElement ||
        activeElement instanceof HTMLTextAreaElement
      )
    ) {
      return fn();
    }

    const { id: activeElementId, selectionStart, selectionEnd } = activeElement;

    const results = fn();

    if (activeElementId && activeElementId !== document.activeElement?.id) {
      activeElement = ctx.target.querySelector(`#${activeElementId}`);
      activeElement?.focus();
    }
    if (activeElement && !activeElement.selectionEnd && selectionEnd) {
      activeElement.setSelectionRange(selectionStart, selectionEnd);
    }

    return results;
  }

  const morphChildren = (function () {
    /**
     * This is the core algorithm for matching up children.  The idea is to use id sets to try to match up
     * nodes as faithfully as possible.  We greedily match, which allows us to keep the algorithm fast, but
     * by using id sets, we are able to better match up with content deeper in the DOM.
     *
     * Basic algorithm:
     * - for each node in the new content:
     *   - search self and siblings for an id set match, falling back to a soft match
     *   - if match found
     *     - remove any nodes up to the match:
     *       - pantry persistent nodes
     *       - delete the rest
     *     - morph the match
     *   - elsif no match found, and node is persistent
     *     - find its match by querying the old root (future) and pantry (past)
     *     - move it and its children here
     *     - morph it
     *   - else
     *     - create a new node from scratch as a last result
     *
     * @param {MorphContext} ctx the merge context
     * @param {Element} oldParent the old content that we are merging the new content into
     * @param {Element} newParent the parent element of the new content
     * @param {Node|null} [insertionPoint] the point in the DOM we start morphing at (defaults to first child)
     * @param {Node|null} [endPoint] the point in the DOM we stop morphing at (defaults to after last child)
     */
    function morphChildren(
      ctx,
      oldParent,
      newParent,
      insertionPoint = null,
      endPoint = null,
    ) {
      // normalize
      if (
        oldParent instanceof HTMLTemplateElement &&
        newParent instanceof HTMLTemplateElement
      ) {
        // @ts-ignore we can pretend the DocumentFragment is an Element
        oldParent = oldParent.content;
        // @ts-ignore ditto
        newParent = newParent.content;
      }
      insertionPoint ||= oldParent.firstChild;

      // run through all the new content
      for (const newChild of newParent.childNodes) {
        // once we reach the end of the old parent content skip to the end and insert the rest
        if (insertionPoint && insertionPoint != endPoint) {
          const bestMatch = findBestMatch(
            ctx,
            newChild,
            insertionPoint,
            endPoint,
          );
          if (bestMatch) {
            // if the node to morph is not at the insertion point then remove/move up to it
            if (bestMatch !== insertionPoint) {
              removeNodesBetween(ctx, insertionPoint, bestMatch);
            }
            morphNode(bestMatch, newChild, ctx);
            insertionPoint = bestMatch.nextSibling;
            continue;
          }
        }

        // if the matching node is elsewhere in the original content
        if (newChild instanceof Element && ctx.persistentIds.has(newChild.id)) {
          // move it and all its children here and morph
          const movedChild = moveBeforeById(
            oldParent,
            newChild.id,
            insertionPoint,
            ctx,
          );
          morphNode(movedChild, newChild, ctx);
          insertionPoint = movedChild.nextSibling;
          continue;
        }

        // last resort: insert the new node from scratch
        const insertedNode = createNode(
          oldParent,
          newChild,
          insertionPoint,
          ctx,
        );
        // could be null if beforeNodeAdded prevented insertion
        if (insertedNode) {
          insertionPoint = insertedNode.nextSibling;
        }
      }

      // remove any remaining old nodes that didn't match up with new content
      while (insertionPoint && insertionPoint != endPoint) {
        const tempNode = insertionPoint;
        insertionPoint = insertionPoint.nextSibling;
        removeNode(ctx, tempNode);
      }
    }

    /**
     * This performs the action of inserting a new node while handling situations where the node contains
     * elements with persistent ids and possible state info we can still preserve by moving in and then morphing
     *
     * @param {Element} oldParent
     * @param {Node} newChild
     * @param {Node|null} insertionPoint
     * @param {MorphContext} ctx
     * @returns {Node|null}
     */
    function createNode(oldParent, newChild, insertionPoint, ctx) {
      if (ctx.callbacks.beforeNodeAdded(newChild) === false) return null;
      if (ctx.idMap.has(newChild)) {
        // node has children with ids with possible state so create a dummy elt of same type and apply full morph algorithm
        const newEmptyChild = document.createElement(
          /** @type {Element} */ (newChild).tagName,
        );
        oldParent.insertBefore(newEmptyChild, insertionPoint);
        morphNode(newEmptyChild, newChild, ctx);
        ctx.callbacks.afterNodeAdded(newEmptyChild);
        return newEmptyChild;
      } else {
        // optimisation: no id state to preserve so we can just insert a clone of the newChild and its descendants
        const newClonedChild = document.importNode(newChild, true); // importNode to not mutate newParent
        oldParent.insertBefore(newClonedChild, insertionPoint);
        ctx.callbacks.afterNodeAdded(newClonedChild);
        return newClonedChild;
      }
    }

    //=============================================================================
    // Matching Functions
    //=============================================================================
    const findBestMatch = (function () {
      /**
       * Scans forward from the startPoint to the endPoint looking for a match
       * for the node. It looks for an id set match first, then a soft match.
       * We abort softmatching if we find two future soft matches, to reduce churn.
       * @param {Node} node
       * @param {MorphContext} ctx
       * @param {Node | null} startPoint
       * @param {Node | null} endPoint
       * @returns {Node | null}
       */
      function findBestMatch(ctx, node, startPoint, endPoint) {
        let softMatch = null;
        let nextSibling = node.nextSibling;
        let siblingSoftMatchCount = 0;

        let cursor = startPoint;
        while (cursor && cursor != endPoint) {
          // soft matching is a prerequisite for id set matching
          if (isSoftMatch(cursor, node)) {
            if (isIdSetMatch(ctx, cursor, node)) {
              return cursor; // found an id set match, we're done!
            }

            // we haven't yet saved a soft match fallback
            if (softMatch === null) {
              // the current soft match will hard match something else in the future, leave it
              if (!ctx.idMap.has(cursor)) {
                // save this as the fallback if we get through the loop without finding a hard match
                softMatch = cursor;
              }
            }
          }
          if (
            softMatch === null &&
            nextSibling &&
            isSoftMatch(cursor, nextSibling)
          ) {
            // The next new node has a soft match with this node, so
            // increment the count of future soft matches
            siblingSoftMatchCount++;
            nextSibling = nextSibling.nextSibling;

            // If there are two future soft matches, block soft matching for this node to allow
            // future siblings to soft match. This is to reduce churn in the DOM when an element
            // is prepended.
            if (siblingSoftMatchCount >= 2) {
              softMatch = undefined;
            }
          }

          // if the current node contains active element, stop looking for better future matches,
          // because if one is found, this node will be moved to the pantry, reparenting it and thus losing focus
          if (cursor.contains(document.activeElement)) break;

          cursor = cursor.nextSibling;
        }

        return softMatch || null;
      }

      /**
       *
       * @param {MorphContext} ctx
       * @param {Node} oldNode
       * @param {Node} newNode
       * @returns {boolean}
       */
      function isIdSetMatch(ctx, oldNode, newNode) {
        let oldSet = ctx.idMap.get(oldNode);
        let newSet = ctx.idMap.get(newNode);

        if (!newSet || !oldSet) return false;

        for (const id of oldSet) {
          // a potential match is an id in the new and old nodes that
          // has not already been merged into the DOM
          // But the newNode content we call this on has not been
          // merged yet and we don't allow duplicate IDs so it is simple
          if (newSet.has(id)) {
            return true;
          }
        }
        return false;
      }

      /**
       *
       * @param {Node} oldNode
       * @param {Node} newNode
       * @returns {boolean}
       */
      function isSoftMatch(oldNode, newNode) {
        // ok to cast: if one is not element, `id` and `tagName` will be undefined and we'll just compare that.
        const oldElt = /** @type {Element} */ (oldNode);
        const newElt = /** @type {Element} */ (newNode);

        return (
          oldElt.nodeType === newElt.nodeType &&
          oldElt.tagName === newElt.tagName &&
          // If oldElt has an `id` with possible state and it doesn't match newElt.id then avoid morphing.
          // We'll still match an anonymous node with an IDed newElt, though, because if it got this far,
          // its not persistent, and new nodes can't have any hidden state.
          (!oldElt.id || oldElt.id === newElt.id)
        );
      }

      return findBestMatch;
    })();

    //=============================================================================
    // DOM Manipulation Functions
    //=============================================================================

    /**
     * Gets rid of an unwanted DOM node; strategy depends on nature of its reuse:
     * - Persistent nodes will be moved to the pantry for later reuse
     * - Other nodes will have their hooks called, and then are removed
     * @param {MorphContext} ctx
     * @param {Node} node
     */
    function removeNode(ctx, node) {
      // are we going to id set match this later?
      if (ctx.idMap.has(node)) {
        // skip callbacks and move to pantry
        moveBefore(ctx.pantry, node, null);
      } else {
        // remove for realsies
        if (ctx.callbacks.beforeNodeRemoved(node) === false) return;
        node.parentNode?.removeChild(node);
        ctx.callbacks.afterNodeRemoved(node);
      }
    }

    /**
     * Remove nodes between the start and end nodes
     * @param {MorphContext} ctx
     * @param {Node} startInclusive
     * @param {Node} endExclusive
     * @returns {Node|null}
     */
    function removeNodesBetween(ctx, startInclusive, endExclusive) {
      /** @type {Node | null} */
      let cursor = startInclusive;
      // remove nodes until the endExclusive node
      while (cursor && cursor !== endExclusive) {
        let tempNode = /** @type {Node} */ (cursor);
        cursor = cursor.nextSibling;
        removeNode(ctx, tempNode);
      }
      return cursor;
    }

    /**
     * Search for an element by id within the document and pantry, and move it using moveBefore.
     *
     * @param {Element} parentNode - The parent node to which the element will be moved.
     * @param {string} id - The ID of the element to be moved.
     * @param {Node | null} after - The reference node to insert the element before.
     *                              If `null`, the element is appended as the last child.
     * @param {MorphContext} ctx
     * @returns {Element} The found element
     */
    function moveBeforeById(parentNode, id, after, ctx) {
      const target =
        /** @type {Element} - will always be found */
        (
          ctx.target.querySelector(`#${id}`) ||
            ctx.pantry.querySelector(`#${id}`)
        );
      removeElementFromAncestorsIdMaps(target, ctx);
      moveBefore(parentNode, target, after);
      return target;
    }

    /**
     * Removes an element from its ancestors' id maps. This is needed when an element is moved from the
     * "future" via `moveBeforeId`. Otherwise, its erstwhile ancestors could be mistakenly moved to the
     * pantry rather than being deleted, preventing their removal hooks from being called.
     *
     * @param {Element} element - element to remove from its ancestors' id maps
     * @param {MorphContext} ctx
     */
    function removeElementFromAncestorsIdMaps(element, ctx) {
      const id = element.id;
      /** @ts-ignore - safe to loop in this way **/
      while ((element = element.parentNode)) {
        let idSet = ctx.idMap.get(element);
        if (idSet) {
          idSet.delete(id);
          if (!idSet.size) {
            ctx.idMap.delete(element);
          }
        }
      }
    }

    /**
     * Moves an element before another element within the same parent.
     * Uses the proposed `moveBefore` API if available (and working), otherwise falls back to `insertBefore`.
     * This is essentialy a forward-compat wrapper.
     *
     * @param {Element} parentNode - The parent node containing the after element.
     * @param {Node} element - The element to be moved.
     * @param {Node | null} after - The reference node to insert `element` before.
     *                              If `null`, `element` is appended as the last child.
     */
    function moveBefore(parentNode, element, after) {
      // @ts-ignore - use proposed moveBefore feature
      if (parentNode.moveBefore) {
        try {
          // @ts-ignore - use proposed moveBefore feature
          parentNode.moveBefore(element, after);
        } catch (e) {
          // fall back to insertBefore as some browsers may fail on moveBefore when trying to move Dom disconnected nodes to pantry
          parentNode.insertBefore(element, after);
        }
      } else {
        parentNode.insertBefore(element, after);
      }
    }

    return morphChildren;
  })();

  //=============================================================================
  // Single Node Morphing Code
  //=============================================================================
  const morphNode = (function () {
    /**
     * @param {Node} oldNode root node to merge content into
     * @param {Node} newContent new content to merge
     * @param {MorphContext} ctx the merge context
     * @returns {Node | null} the element that ended up in the DOM
     */
    function morphNode(oldNode, newContent, ctx) {
      if (ctx.ignoreActive && oldNode === document.activeElement) {
        // don't morph focused element
        return null;
      }

      if (ctx.callbacks.beforeNodeMorphed(oldNode, newContent) === false) {
        return oldNode;
      }

      if (oldNode instanceof HTMLHeadElement && ctx.head.ignore) ; else if (
        oldNode instanceof HTMLHeadElement &&
        ctx.head.style !== "morph"
      ) {
        // ok to cast: if newContent wasn't also a <head>, it would've got caught in the `!isSoftMatch` branch above
        handleHeadElement(
          oldNode,
          /** @type {HTMLHeadElement} */ (newContent),
          ctx,
        );
      } else {
        morphAttributes(oldNode, newContent, ctx);
        if (!ignoreValueOfActiveElement(oldNode, ctx)) {
          // @ts-ignore newContent can be a node here because .firstChild will be null
          morphChildren(ctx, oldNode, newContent);
        }
      }
      ctx.callbacks.afterNodeMorphed(oldNode, newContent);
      return oldNode;
    }

    /**
     * syncs the oldNode to the newNode, copying over all attributes and
     * inner element state from the newNode to the oldNode
     *
     * @param {Node} oldNode the node to copy attributes & state to
     * @param {Node} newNode the node to copy attributes & state from
     * @param {MorphContext} ctx the merge context
     */
    function morphAttributes(oldNode, newNode, ctx) {
      let type = newNode.nodeType;

      // if is an element type, sync the attributes from the
      // new node into the new node
      if (type === 1 /* element type */) {
        const oldElt = /** @type {Element} */ (oldNode);
        const newElt = /** @type {Element} */ (newNode);

        const oldAttributes = oldElt.attributes;
        const newAttributes = newElt.attributes;
        for (const newAttribute of newAttributes) {
          if (ignoreAttribute(newAttribute.name, oldElt, "update", ctx)) {
            continue;
          }
          if (oldElt.getAttribute(newAttribute.name) !== newAttribute.value) {
            oldElt.setAttribute(newAttribute.name, newAttribute.value);
          }
        }
        // iterate backwards to avoid skipping over items when a delete occurs
        for (let i = oldAttributes.length - 1; 0 <= i; i--) {
          const oldAttribute = oldAttributes[i];

          // toAttributes is a live NamedNodeMap, so iteration+mutation is unsafe
          // e.g. custom element attribute callbacks can remove other attributes
          if (!oldAttribute) continue;

          if (!newElt.hasAttribute(oldAttribute.name)) {
            if (ignoreAttribute(oldAttribute.name, oldElt, "remove", ctx)) {
              continue;
            }
            oldElt.removeAttribute(oldAttribute.name);
          }
        }

        if (!ignoreValueOfActiveElement(oldElt, ctx)) {
          syncInputValue(oldElt, newElt, ctx);
        }
      }

      // sync text nodes
      if (type === 8 /* comment */ || type === 3 /* text */) {
        if (oldNode.nodeValue !== newNode.nodeValue) {
          oldNode.nodeValue = newNode.nodeValue;
        }
      }
    }

    /**
     * NB: many bothans died to bring us information:
     *
     *  https://github.com/patrick-steele-idem/morphdom/blob/master/src/specialElHandlers.js
     *  https://github.com/choojs/nanomorph/blob/master/lib/morph.jsL113
     *
     * @param {Element} oldElement the element to sync the input value to
     * @param {Element} newElement the element to sync the input value from
     * @param {MorphContext} ctx the merge context
     */
    function syncInputValue(oldElement, newElement, ctx) {
      if (
        oldElement instanceof HTMLInputElement &&
        newElement instanceof HTMLInputElement &&
        newElement.type !== "file"
      ) {
        let newValue = newElement.value;
        let oldValue = oldElement.value;

        // sync boolean attributes
        syncBooleanAttribute(oldElement, newElement, "checked", ctx);
        syncBooleanAttribute(oldElement, newElement, "disabled", ctx);

        if (!newElement.hasAttribute("value")) {
          if (!ignoreAttribute("value", oldElement, "remove", ctx)) {
            oldElement.value = "";
            oldElement.removeAttribute("value");
          }
        } else if (oldValue !== newValue) {
          if (!ignoreAttribute("value", oldElement, "update", ctx)) {
            oldElement.setAttribute("value", newValue);
            oldElement.value = newValue;
          }
        }
        // TODO: QUESTION(1cg): this used to only check `newElement` unlike the other branches -- why?
        // did I break something?
      } else if (
        oldElement instanceof HTMLOptionElement &&
        newElement instanceof HTMLOptionElement
      ) {
        syncBooleanAttribute(oldElement, newElement, "selected", ctx);
      } else if (
        oldElement instanceof HTMLTextAreaElement &&
        newElement instanceof HTMLTextAreaElement
      ) {
        let newValue = newElement.value;
        let oldValue = oldElement.value;
        if (ignoreAttribute("value", oldElement, "update", ctx)) {
          return;
        }
        if (newValue !== oldValue) {
          oldElement.value = newValue;
        }
        if (
          oldElement.firstChild &&
          oldElement.firstChild.nodeValue !== newValue
        ) {
          oldElement.firstChild.nodeValue = newValue;
        }
      }
    }

    /**
     * @param {Element} oldElement element to write the value to
     * @param {Element} newElement element to read the value from
     * @param {string} attributeName the attribute name
     * @param {MorphContext} ctx the merge context
     */
    function syncBooleanAttribute(oldElement, newElement, attributeName, ctx) {
      // @ts-ignore this function is only used on boolean attrs that are reflected as dom properties
      const newLiveValue = newElement[attributeName],
        // @ts-ignore ditto
        oldLiveValue = oldElement[attributeName];
      if (newLiveValue !== oldLiveValue) {
        const ignoreUpdate = ignoreAttribute(
          attributeName,
          oldElement,
          "update",
          ctx,
        );
        if (!ignoreUpdate) {
          // update attribute's associated DOM property
          // @ts-ignore this function is only used on boolean attrs that are reflected as dom properties
          oldElement[attributeName] = newElement[attributeName];
        }
        if (newLiveValue) {
          if (!ignoreUpdate) {
            // https://developer.mozilla.org/en-US/docs/Glossary/Boolean/HTML
            // this is the correct way to set a boolean attribute to "true"
            oldElement.setAttribute(attributeName, "");
          }
        } else {
          if (!ignoreAttribute(attributeName, oldElement, "remove", ctx)) {
            oldElement.removeAttribute(attributeName);
          }
        }
      }
    }

    /**
     * @param {string} attr the attribute to be mutated
     * @param {Element} element the element that is going to be updated
     * @param {"update" | "remove"} updateType
     * @param {MorphContext} ctx the merge context
     * @returns {boolean} true if the attribute should be ignored, false otherwise
     */
    function ignoreAttribute(attr, element, updateType, ctx) {
      if (
        attr === "value" &&
        ctx.ignoreActiveValue &&
        element === document.activeElement
      ) {
        return true;
      }
      return (
        ctx.callbacks.beforeAttributeUpdated(attr, element, updateType) ===
        false
      );
    }

    /**
     * @param {Node} possibleActiveElement
     * @param {MorphContext} ctx
     * @returns {boolean}
     */
    function ignoreValueOfActiveElement(possibleActiveElement, ctx) {
      return (
        !!ctx.ignoreActiveValue &&
        possibleActiveElement === document.activeElement &&
        possibleActiveElement !== document.body
      );
    }

    return morphNode;
  })();

  //=============================================================================
  // Head Management Functions
  //=============================================================================
  /**
   * @param {MorphContext} ctx
   * @param {Element} oldNode
   * @param {Element} newNode
   * @param {function} callback
   * @returns {Node[] | Promise<Node[]>}
   */
  function withHeadBlocking(ctx, oldNode, newNode, callback) {
    if (ctx.head.block) {
      const oldHead = oldNode.querySelector("head");
      const newHead = newNode.querySelector("head");
      if (oldHead && newHead) {
        const promises = handleHeadElement(oldHead, newHead, ctx);
        // when head promises resolve, proceed ignoring the head tag
        return Promise.all(promises).then(() => {
          const newCtx = Object.assign(ctx, {
            head: {
              block: false,
              ignore: true,
            },
          });
          return callback(newCtx);
        });
      }
    }
    // just proceed if we not head blocking
    return callback(ctx);
  }

  /**
   *  The HEAD tag can be handled specially, either w/ a 'merge' or 'append' style
   *
   * @param {Element} oldHead
   * @param {Element} newHead
   * @param {MorphContext} ctx
   * @returns {Promise<void>[]}
   */
  function handleHeadElement(oldHead, newHead, ctx) {
    let added = [];
    let removed = [];
    let preserved = [];
    let nodesToAppend = [];

    // put all new head elements into a Map, by their outerHTML
    let srcToNewHeadNodes = new Map();
    for (const newHeadChild of newHead.children) {
      srcToNewHeadNodes.set(newHeadChild.outerHTML, newHeadChild);
    }

    // for each elt in the current head
    for (const currentHeadElt of oldHead.children) {
      // If the current head element is in the map
      let inNewContent = srcToNewHeadNodes.has(currentHeadElt.outerHTML);
      let isReAppended = ctx.head.shouldReAppend(currentHeadElt);
      let isPreserved = ctx.head.shouldPreserve(currentHeadElt);
      if (inNewContent || isPreserved) {
        if (isReAppended) {
          // remove the current version and let the new version replace it and re-execute
          removed.push(currentHeadElt);
        } else {
          // this element already exists and should not be re-appended, so remove it from
          // the new content map, preserving it in the DOM
          srcToNewHeadNodes.delete(currentHeadElt.outerHTML);
          preserved.push(currentHeadElt);
        }
      } else {
        if (ctx.head.style === "append") {
          // we are appending and this existing element is not new content
          // so if and only if it is marked for re-append do we do anything
          if (isReAppended) {
            removed.push(currentHeadElt);
            nodesToAppend.push(currentHeadElt);
          }
        } else {
          // if this is a merge, we remove this content since it is not in the new head
          if (ctx.head.shouldRemove(currentHeadElt) !== false) {
            removed.push(currentHeadElt);
          }
        }
      }
    }

    // Push the remaining new head elements in the Map into the
    // nodes to append to the head tag
    nodesToAppend.push(...srcToNewHeadNodes.values());

    let promises = [];
    for (const newNode of nodesToAppend) {
      // TODO: This could theoretically be null, based on type
      let newElt = /** @type {ChildNode} */ (
        document.createRange().createContextualFragment(newNode.outerHTML)
          .firstChild
      );
      if (ctx.callbacks.beforeNodeAdded(newElt) !== false) {
        if (
          ("href" in newElt && newElt.href) ||
          ("src" in newElt && newElt.src)
        ) {
          /** @type {(result?: any) => void} */ let resolve;
          let promise = new Promise(function (_resolve) {
            resolve = _resolve;
          });
          newElt.addEventListener("load", function () {
            resolve();
          });
          promises.push(promise);
        }
        oldHead.appendChild(newElt);
        ctx.callbacks.afterNodeAdded(newElt);
        added.push(newElt);
      }
    }

    // remove all removed elements, after we have appended the new elements to avoid
    // additional network requests for things like style sheets
    for (const removedElement of removed) {
      if (ctx.callbacks.beforeNodeRemoved(removedElement) !== false) {
        oldHead.removeChild(removedElement);
        ctx.callbacks.afterNodeRemoved(removedElement);
      }
    }

    ctx.head.afterHeadMorphed(oldHead, {
      added: added,
      kept: preserved,
      removed: removed,
    });
    return promises;
  }

  //=============================================================================
  // Create Morph Context Functions
  //=============================================================================
  const createMorphContext = (function () {
    /**
     *
     * @param {Element} oldNode
     * @param {Element} newContent
     * @param {Config} config
     * @returns {MorphContext}
     */
    function createMorphContext(oldNode, newContent, config) {
      const { persistentIds, idMap } = createIdMaps(oldNode, newContent);

      const mergedConfig = mergeDefaults(config);
      const morphStyle = mergedConfig.morphStyle || "outerHTML";
      if (!["innerHTML", "outerHTML"].includes(morphStyle)) {
        throw `Do not understand how to morph style ${morphStyle}`;
      }

      return {
        target: oldNode,
        newContent: newContent,
        config: mergedConfig,
        morphStyle: morphStyle,
        ignoreActive: mergedConfig.ignoreActive,
        ignoreActiveValue: mergedConfig.ignoreActiveValue,
        restoreFocus: mergedConfig.restoreFocus,
        idMap: idMap,
        persistentIds: persistentIds,
        pantry: createPantry(),
        callbacks: mergedConfig.callbacks,
        head: mergedConfig.head,
      };
    }

    /**
     * Deep merges the config object and the Idiomorph.defaults object to
     * produce a final configuration object
     * @param {Config} config
     * @returns {ConfigInternal}
     */
    function mergeDefaults(config) {
      let finalConfig = Object.assign({}, defaults);

      // copy top level stuff into final config
      Object.assign(finalConfig, config);

      // copy callbacks into final config (do this to deep merge the callbacks)
      finalConfig.callbacks = Object.assign(
        {},
        defaults.callbacks,
        config.callbacks,
      );

      // copy head config into final config  (do this to deep merge the head)
      finalConfig.head = Object.assign({}, defaults.head, config.head);

      return finalConfig;
    }

    /**
     * @returns {HTMLDivElement}
     */
    function createPantry() {
      const pantry = document.createElement("div");
      pantry.hidden = true;
      document.body.insertAdjacentElement("afterend", pantry);
      return pantry;
    }

    /**
     * Returns all elements with an ID contained within the root element and its descendants
     *
     * @param {Element} root
     * @returns {Element[]}
     */
    function findIdElements(root) {
      let elements = Array.from(root.querySelectorAll("[id]"));
      if (root.id) {
        elements.push(root);
      }
      return elements;
    }

    /**
     * A bottom-up algorithm that populates a map of Element -> IdSet.
     * The idSet for a given element is the set of all IDs contained within its subtree.
     * As an optimzation, we filter these IDs through the given list of persistent IDs,
     * because we don't need to bother considering IDed elements that won't be in the new content.
     *
     * @param {Map<Node, Set<string>>} idMap
     * @param {Set<string>} persistentIds
     * @param {Element} root
     * @param {Element[]} elements
     */
    function populateIdMapWithTree(idMap, persistentIds, root, elements) {
      for (const elt of elements) {
        if (persistentIds.has(elt.id)) {
          /** @type {Element|null} */
          let current = elt;
          // walk up the parent hierarchy of that element, adding the id
          // of element to the parent's id set
          while (current) {
            let idSet = idMap.get(current);
            // if the id set doesn't exist, create it and insert it in the map
            if (idSet == null) {
              idSet = new Set();
              idMap.set(current, idSet);
            }
            idSet.add(elt.id);

            if (current === root) break;
            current = current.parentElement;
          }
        }
      }
    }

    /**
     * This function computes a map of nodes to all ids contained within that node (inclusive of the
     * node).  This map can be used to ask if two nodes have intersecting sets of ids, which allows
     * for a looser definition of "matching" than tradition id matching, and allows child nodes
     * to contribute to a parent nodes matching.
     *
     * @param {Element} oldContent  the old content that will be morphed
     * @param {Element} newContent  the new content to morph to
     * @returns {IdSets}
     */
    function createIdMaps(oldContent, newContent) {
      const oldIdElements = findIdElements(oldContent);
      const newIdElements = findIdElements(newContent);

      const persistentIds = createPersistentIds(oldIdElements, newIdElements);

      /** @type {Map<Node, Set<string>>} */
      let idMap = new Map();
      populateIdMapWithTree(idMap, persistentIds, oldContent, oldIdElements);

      /** @ts-ignore - if newContent is a duck-typed parent, pass its single child node as the root to halt upwards iteration */
      const newRoot = newContent.__idiomorphRoot || newContent;
      populateIdMapWithTree(idMap, persistentIds, newRoot, newIdElements);

      return { persistentIds, idMap };
    }

    /**
     * This function computes the set of ids that persist between the two contents excluding duplicates
     *
     * @param {Element[]} oldIdElements
     * @param {Element[]} newIdElements
     * @returns {Set<string>}
     */
    function createPersistentIds(oldIdElements, newIdElements) {
      let duplicateIds = new Set();

      /** @type {Map<string, string>} */
      let oldIdTagNameMap = new Map();
      for (const { id, tagName } of oldIdElements) {
        if (oldIdTagNameMap.has(id)) {
          duplicateIds.add(id);
        } else {
          oldIdTagNameMap.set(id, tagName);
        }
      }

      let persistentIds = new Set();
      for (const { id, tagName } of newIdElements) {
        if (persistentIds.has(id)) {
          duplicateIds.add(id);
        } else if (oldIdTagNameMap.get(id) === tagName) {
          persistentIds.add(id);
        }
        // skip if tag types mismatch because its not possible to morph one tag into another
      }

      for (const id of duplicateIds) {
        persistentIds.delete(id);
      }
      return persistentIds;
    }

    return createMorphContext;
  })();

  //=============================================================================
  // HTML Normalization Functions
  //=============================================================================
  const { normalizeElement, normalizeParent } = (function () {
    /** @type {WeakSet<Node>} */
    const generatedByIdiomorph = new WeakSet();

    /**
     *
     * @param {Element | Document} content
     * @returns {Element}
     */
    function normalizeElement(content) {
      if (content instanceof Document) {
        return content.documentElement;
      } else {
        return content;
      }
    }

    /**
     *
     * @param {null | string | Node | HTMLCollection | Node[] | Document & {generatedByIdiomorph:boolean}} newContent
     * @returns {Element}
     */
    function normalizeParent(newContent) {
      if (newContent == null) {
        return document.createElement("div"); // dummy parent element
      } else if (typeof newContent === "string") {
        return normalizeParent(parseContent(newContent));
      } else if (
        generatedByIdiomorph.has(/** @type {Element} */ (newContent))
      ) {
        // the template tag created by idiomorph parsing can serve as a dummy parent
        return /** @type {Element} */ (newContent);
      } else if (newContent instanceof Node) {
        if (newContent.parentNode) {
          // we can't use the parent directly because newContent may have siblings
          // that we don't want in the morph, and reparenting might be expensive (TODO is it?),
          // so we create a duck-typed parent node instead.
          return createDuckTypedParent(newContent);
        } else {
          // a single node is added as a child to a dummy parent
          const dummyParent = document.createElement("div");
          dummyParent.append(newContent);
          return dummyParent;
        }
      } else {
        // all nodes in the array or HTMLElement collection are consolidated under
        // a single dummy parent element
        const dummyParent = document.createElement("div");
        for (const elt of [...newContent]) {
          dummyParent.append(elt);
        }
        return dummyParent;
      }
    }

    /**
     * Creates a fake duck-typed parent element to wrap a single node, without actually reparenting it.
     * "If it walks like a duck, and quacks like a duck, then it must be a duck!" -- James Whitcomb Riley (1849–1916)
     *
     * @param {Node} newContent
     * @returns {Element}
     */
    function createDuckTypedParent(newContent) {
      return /** @type {Element} */ (
        /** @type {unknown} */ ({
          childNodes: [newContent],
          /** @ts-ignore - cover your eyes for a minute, tsc */
          querySelectorAll: (s) => {
            /** @ts-ignore */
            const elements = newContent.querySelectorAll(s);
            /** @ts-ignore */
            return newContent.matches(s) ? [newContent, ...elements] : elements;
          },
          /** @ts-ignore */
          insertBefore: (n, r) => newContent.parentNode.insertBefore(n, r),
          /** @ts-ignore */
          moveBefore: (n, r) => newContent.parentNode.moveBefore(n, r),
          // for later use with populateIdMapWithTree to halt upwards iteration
          get __idiomorphRoot() {
            return newContent;
          },
        })
      );
    }

    /**
     *
     * @param {string} newContent
     * @returns {Node | null | DocumentFragment}
     */
    function parseContent(newContent) {
      let parser = new DOMParser();

      // remove svgs to avoid false-positive matches on head, etc.
      let contentWithSvgsRemoved = newContent.replace(
        /<svg(\s[^>]*>|>)([\s\S]*?)<\/svg>/gim,
        "",
      );

      // if the newContent contains a html, head or body tag, we can simply parse it w/o wrapping
      if (
        contentWithSvgsRemoved.match(/<\/html>/) ||
        contentWithSvgsRemoved.match(/<\/head>/) ||
        contentWithSvgsRemoved.match(/<\/body>/)
      ) {
        let content = parser.parseFromString(newContent, "text/html");
        // if it is a full HTML document, return the document itself as the parent container
        if (contentWithSvgsRemoved.match(/<\/html>/)) {
          generatedByIdiomorph.add(content);
          return content;
        } else {
          // otherwise return the html element as the parent container
          let htmlElement = content.firstChild;
          if (htmlElement) {
            generatedByIdiomorph.add(htmlElement);
          }
          return htmlElement;
        }
      } else {
        // if it is partial HTML, wrap it in a template tag to provide a parent element and also to help
        // deal with touchy tags like tr, tbody, etc.
        let responseDoc = parser.parseFromString(
          "<body><template>" + newContent + "</template></body>",
          "text/html",
        );
        let content = /** @type {HTMLTemplateElement} */ (
          responseDoc.body.querySelector("template")
        ).content;
        generatedByIdiomorph.add(content);
        return content;
      }
    }

    return { normalizeElement, normalizeParent };
  })();

  //=============================================================================
  // This is what ends up becoming the Idiomorph global object
  //=============================================================================
  return {
    morph,
    defaults,
  };
})();

function morphElements(currentElement, newElement, { callbacks, ...options } = {}) {
  Idiomorph.morph(currentElement, newElement, {
    ...options,
    callbacks: new DefaultIdiomorphCallbacks(callbacks)
  });
}

function morphChildren(currentElement, newElement) {
  morphElements(currentElement, newElement.childNodes, {
    morphStyle: "innerHTML"
  });
}

class DefaultIdiomorphCallbacks {
  #beforeNodeMorphed

  constructor({ beforeNodeMorphed } = {}) {
    this.#beforeNodeMorphed = beforeNodeMorphed || (() => true);
  }

  beforeNodeAdded = (node) => {
    return !(node.id && node.hasAttribute("data-turbo-permanent") && document.getElementById(node.id))
  }

  beforeNodeMorphed = (currentElement, newElement) => {
    if (currentElement instanceof Element) {
      if (!currentElement.hasAttribute("data-turbo-permanent") && this.#beforeNodeMorphed(currentElement, newElement)) {
        const event = dispatch("turbo:before-morph-element", {
          cancelable: true,
          target: currentElement,
          detail: { currentElement, newElement }
        });

        return !event.defaultPrevented
      } else {
        return false
      }
    }
  }

  beforeAttributeUpdated = (attributeName, target, mutationType) => {
    const event = dispatch("turbo:before-morph-attribute", {
      cancelable: true,
      target,
      detail: { attributeName, mutationType }
    });

    return !event.defaultPrevented
  }

  beforeNodeRemoved = (node) => {
    return this.beforeNodeMorphed(node)
  }

  afterNodeMorphed = (currentElement, newElement) => {
    if (currentElement instanceof Element) {
      dispatch("turbo:morph-element", {
        target: currentElement,
        detail: { currentElement, newElement }
      });
    }
  }
}

class MorphingFrameRenderer extends FrameRenderer {
  static renderElement(currentElement, newElement) {
    dispatch("turbo:before-frame-morph", {
      target: currentElement,
      detail: { currentElement, newElement }
    });

    morphChildren(currentElement, newElement);
  }

  async preservingPermanentElements(callback) {
    return await callback()
  }
}

class ProgressBar {
  static animationDuration = 300 /*ms*/

  static get defaultCSS() {
    return unindent`
      .turbo-progress-bar {
        position: fixed;
        display: block;
        top: 0;
        left: 0;
        height: 3px;
        background: #0076ff;
        z-index: 2147483647;
        transition:
          width ${ProgressBar.animationDuration}ms ease-out,
          opacity ${ProgressBar.animationDuration / 2}ms ${ProgressBar.animationDuration / 2}ms ease-in;
        transform: translate3d(0, 0, 0);
      }
    `
  }

  hiding = false
  value = 0
  visible = false

  constructor() {
    this.stylesheetElement = this.createStylesheetElement();
    this.progressElement = this.createProgressElement();
    this.installStylesheetElement();
    this.setValue(0);
  }

  show() {
    if (!this.visible) {
      this.visible = true;
      this.installProgressElement();
      this.startTrickling();
    }
  }

  hide() {
    if (this.visible && !this.hiding) {
      this.hiding = true;
      this.fadeProgressElement(() => {
        this.uninstallProgressElement();
        this.stopTrickling();
        this.visible = false;
        this.hiding = false;
      });
    }
  }

  setValue(value) {
    this.value = value;
    this.refresh();
  }

  // Private

  installStylesheetElement() {
    document.head.insertBefore(this.stylesheetElement, document.head.firstChild);
  }

  installProgressElement() {
    this.progressElement.style.width = "0";
    this.progressElement.style.opacity = "1";
    document.documentElement.insertBefore(this.progressElement, document.body);
    this.refresh();
  }

  fadeProgressElement(callback) {
    this.progressElement.style.opacity = "0";
    setTimeout(callback, ProgressBar.animationDuration * 1.5);
  }

  uninstallProgressElement() {
    if (this.progressElement.parentNode) {
      document.documentElement.removeChild(this.progressElement);
    }
  }

  startTrickling() {
    if (!this.trickleInterval) {
      this.trickleInterval = window.setInterval(this.trickle, ProgressBar.animationDuration);
    }
  }

  stopTrickling() {
    window.clearInterval(this.trickleInterval);
    delete this.trickleInterval;
  }

  trickle = () => {
    this.setValue(this.value + Math.random() / 100);
  }

  refresh() {
    requestAnimationFrame(() => {
      this.progressElement.style.width = `${10 + this.value * 90}%`;
    });
  }

  createStylesheetElement() {
    const element = document.createElement("style");
    element.type = "text/css";
    element.textContent = ProgressBar.defaultCSS;
    const cspNonce = getCspNonce();
    if (cspNonce) {
      element.nonce = cspNonce;
    }
    return element
  }

  createProgressElement() {
    const element = document.createElement("div");
    element.className = "turbo-progress-bar";
    return element
  }
}

class HeadSnapshot extends Snapshot {
  detailsByOuterHTML = this.children
    .filter((element) => !elementIsNoscript(element))
    .map((element) => elementWithoutNonce(element))
    .reduce((result, element) => {
      const { outerHTML } = element;
      const details =
        outerHTML in result
          ? result[outerHTML]
          : {
              type: elementType(element),
              tracked: elementIsTracked(element),
              elements: []
            };
      return {
        ...result,
        [outerHTML]: {
          ...details,
          elements: [...details.elements, element]
        }
      }
    }, {})

  get trackedElementSignature() {
    return Object.keys(this.detailsByOuterHTML)
      .filter((outerHTML) => this.detailsByOuterHTML[outerHTML].tracked)
      .join("")
  }

  getScriptElementsNotInSnapshot(snapshot) {
    return this.getElementsMatchingTypeNotInSnapshot("script", snapshot)
  }

  getStylesheetElementsNotInSnapshot(snapshot) {
    return this.getElementsMatchingTypeNotInSnapshot("stylesheet", snapshot)
  }

  getElementsMatchingTypeNotInSnapshot(matchedType, snapshot) {
    return Object.keys(this.detailsByOuterHTML)
      .filter((outerHTML) => !(outerHTML in snapshot.detailsByOuterHTML))
      .map((outerHTML) => this.detailsByOuterHTML[outerHTML])
      .filter(({ type }) => type == matchedType)
      .map(({ elements: [element] }) => element)
  }

  get provisionalElements() {
    return Object.keys(this.detailsByOuterHTML).reduce((result, outerHTML) => {
      const { type, tracked, elements } = this.detailsByOuterHTML[outerHTML];
      if (type == null && !tracked) {
        return [...result, ...elements]
      } else if (elements.length > 1) {
        return [...result, ...elements.slice(1)]
      } else {
        return result
      }
    }, [])
  }

  getMetaValue(name) {
    const element = this.findMetaElementByName(name);
    return element ? element.getAttribute("content") : null
  }

  findMetaElementByName(name) {
    return Object.keys(this.detailsByOuterHTML).reduce((result, outerHTML) => {
      const {
        elements: [element]
      } = this.detailsByOuterHTML[outerHTML];
      return elementIsMetaElementWithName(element, name) ? element : result
    }, undefined | undefined)
  }
}

function elementType(element) {
  if (elementIsScript(element)) {
    return "script"
  } else if (elementIsStylesheet(element)) {
    return "stylesheet"
  }
}

function elementIsTracked(element) {
  return element.getAttribute("data-turbo-track") == "reload"
}

function elementIsScript(element) {
  const tagName = element.localName;
  return tagName == "script"
}

function elementIsNoscript(element) {
  const tagName = element.localName;
  return tagName == "noscript"
}

function elementIsStylesheet(element) {
  const tagName = element.localName;
  return tagName == "style" || (tagName == "link" && element.getAttribute("rel") == "stylesheet")
}

function elementIsMetaElementWithName(element, name) {
  const tagName = element.localName;
  return tagName == "meta" && element.getAttribute("name") == name
}

function elementWithoutNonce(element) {
  if (element.hasAttribute("nonce")) {
    element.setAttribute("nonce", "");
  }

  return element
}

class PageSnapshot extends Snapshot {
  static fromHTMLString(html = "") {
    return this.fromDocument(parseHTMLDocument(html))
  }

  static fromElement(element) {
    return this.fromDocument(element.ownerDocument)
  }

  static fromDocument({ documentElement, body, head }) {
    return new this(documentElement, body, new HeadSnapshot(head))
  }

  constructor(documentElement, body, headSnapshot) {
    super(body);
    this.documentElement = documentElement;
    this.headSnapshot = headSnapshot;
  }

  clone() {
    const clonedElement = this.element.cloneNode(true);

    const selectElements = this.element.querySelectorAll("select");
    const clonedSelectElements = clonedElement.querySelectorAll("select");

    for (const [index, source] of selectElements.entries()) {
      const clone = clonedSelectElements[index];
      for (const option of clone.selectedOptions) option.selected = false;
      for (const option of source.selectedOptions) clone.options[option.index].selected = true;
    }

    for (const clonedPasswordInput of clonedElement.querySelectorAll('input[type="password"]')) {
      clonedPasswordInput.value = "";
    }

    return new PageSnapshot(this.documentElement, clonedElement, this.headSnapshot)
  }

  get lang() {
    return this.documentElement.getAttribute("lang")
  }

  get headElement() {
    return this.headSnapshot.element
  }

  get rootLocation() {
    const root = this.getSetting("root") ?? "/";
    return expandURL(root)
  }

  get cacheControlValue() {
    return this.getSetting("cache-control")
  }

  get isPreviewable() {
    return this.cacheControlValue != "no-preview"
  }

  get isCacheable() {
    return this.cacheControlValue != "no-cache"
  }

  get isVisitable() {
    return this.getSetting("visit-control") != "reload"
  }

  get prefersViewTransitions() {
    return this.headSnapshot.getMetaValue("view-transition") === "same-origin"
  }

  get shouldMorphPage() {
    return this.getSetting("refresh-method") === "morph"
  }

  get shouldPreserveScrollPosition() {
    return this.getSetting("refresh-scroll") === "preserve"
  }

  // Private

  getSetting(name) {
    return this.headSnapshot.getMetaValue(`turbo-${name}`)
  }
}

class ViewTransitioner {
  #viewTransitionStarted = false
  #lastOperation = Promise.resolve()

  renderChange(useViewTransition, render) {
    if (useViewTransition && this.viewTransitionsAvailable && !this.#viewTransitionStarted) {
      this.#viewTransitionStarted = true;
      this.#lastOperation = this.#lastOperation.then(async () => {
        await document.startViewTransition(render).finished;
      });
    } else {
      this.#lastOperation = this.#lastOperation.then(render);
    }

    return this.#lastOperation
  }

  get viewTransitionsAvailable() {
    return document.startViewTransition
  }
}

const defaultOptions = {
  action: "advance",
  historyChanged: false,
  visitCachedSnapshot: () => {},
  willRender: true,
  updateHistory: true,
  shouldCacheSnapshot: true,
  acceptsStreamResponse: false
};

const TimingMetric = {
  visitStart: "visitStart",
  requestStart: "requestStart",
  requestEnd: "requestEnd",
  visitEnd: "visitEnd"
};

const VisitState = {
  initialized: "initialized",
  started: "started",
  canceled: "canceled",
  failed: "failed",
  completed: "completed"
};

const SystemStatusCode = {
  networkFailure: 0,
  timeoutFailure: -1,
  contentTypeMismatch: -2
};

const Direction = {
  advance: "forward",
  restore: "back",
  replace: "none"
};

class Visit {
  identifier = uuid() // Required by turbo-ios
  timingMetrics = {}

  followedRedirect = false
  historyChanged = false
  scrolled = false
  shouldCacheSnapshot = true
  acceptsStreamResponse = false
  snapshotCached = false
  state = VisitState.initialized
  viewTransitioner = new ViewTransitioner()

  constructor(delegate, location, restorationIdentifier, options = {}) {
    this.delegate = delegate;
    this.location = location;
    this.restorationIdentifier = restorationIdentifier || uuid();

    const {
      action,
      historyChanged,
      referrer,
      snapshot,
      snapshotHTML,
      response,
      visitCachedSnapshot,
      willRender,
      updateHistory,
      shouldCacheSnapshot,
      acceptsStreamResponse,
      direction
    } = {
      ...defaultOptions,
      ...options
    };
    this.action = action;
    this.historyChanged = historyChanged;
    this.referrer = referrer;
    this.snapshot = snapshot;
    this.snapshotHTML = snapshotHTML;
    this.response = response;
    this.isSamePage = this.delegate.locationWithActionIsSamePage(this.location, this.action);
    this.isPageRefresh = this.view.isPageRefresh(this);
    this.visitCachedSnapshot = visitCachedSnapshot;
    this.willRender = willRender;
    this.updateHistory = updateHistory;
    this.scrolled = !willRender;
    this.shouldCacheSnapshot = shouldCacheSnapshot;
    this.acceptsStreamResponse = acceptsStreamResponse;
    this.direction = direction || Direction[action];
  }

  get adapter() {
    return this.delegate.adapter
  }

  get view() {
    return this.delegate.view
  }

  get history() {
    return this.delegate.history
  }

  get restorationData() {
    return this.history.getRestorationDataForIdentifier(this.restorationIdentifier)
  }

  get silent() {
    return this.isSamePage
  }

  start() {
    if (this.state == VisitState.initialized) {
      this.recordTimingMetric(TimingMetric.visitStart);
      this.state = VisitState.started;
      this.adapter.visitStarted(this);
      this.delegate.visitStarted(this);
    }
  }

  cancel() {
    if (this.state == VisitState.started) {
      if (this.request) {
        this.request.cancel();
      }
      this.cancelRender();
      this.state = VisitState.canceled;
    }
  }

  complete() {
    if (this.state == VisitState.started) {
      this.recordTimingMetric(TimingMetric.visitEnd);
      this.adapter.visitCompleted(this);
      this.state = VisitState.completed;
      this.followRedirect();

      if (!this.followedRedirect) {
        this.delegate.visitCompleted(this);
      }
    }
  }

  fail() {
    if (this.state == VisitState.started) {
      this.state = VisitState.failed;
      this.adapter.visitFailed(this);
      this.delegate.visitCompleted(this);
    }
  }

  changeHistory() {
    if (!this.historyChanged && this.updateHistory) {
      const actionForHistory = this.location.href === this.referrer?.href ? "replace" : this.action;
      const method = getHistoryMethodForAction(actionForHistory);
      this.history.update(method, this.location, this.restorationIdentifier);
      this.historyChanged = true;
    }
  }

  issueRequest() {
    if (this.hasPreloadedResponse()) {
      this.simulateRequest();
    } else if (this.shouldIssueRequest() && !this.request) {
      this.request = new FetchRequest(this, FetchMethod.get, this.location);
      this.request.perform();
    }
  }

  simulateRequest() {
    if (this.response) {
      this.startRequest();
      this.recordResponse();
      this.finishRequest();
    }
  }

  startRequest() {
    this.recordTimingMetric(TimingMetric.requestStart);
    this.adapter.visitRequestStarted(this);
  }

  recordResponse(response = this.response) {
    this.response = response;
    if (response) {
      const { statusCode } = response;
      if (isSuccessful(statusCode)) {
        this.adapter.visitRequestCompleted(this);
      } else {
        this.adapter.visitRequestFailedWithStatusCode(this, statusCode);
      }
    }
  }

  finishRequest() {
    this.recordTimingMetric(TimingMetric.requestEnd);
    this.adapter.visitRequestFinished(this);
  }

  loadResponse() {
    if (this.response) {
      const { statusCode, responseHTML } = this.response;
      this.render(async () => {
        if (this.shouldCacheSnapshot) this.cacheSnapshot();
        if (this.view.renderPromise) await this.view.renderPromise;

        if (isSuccessful(statusCode) && responseHTML != null) {
          const snapshot = PageSnapshot.fromHTMLString(responseHTML);
          await this.renderPageSnapshot(snapshot, false);

          this.adapter.visitRendered(this);
          this.complete();
        } else {
          await this.view.renderError(PageSnapshot.fromHTMLString(responseHTML), this);
          this.adapter.visitRendered(this);
          this.fail();
        }
      });
    }
  }

  getCachedSnapshot() {
    const snapshot = this.view.getCachedSnapshotForLocation(this.location) || this.getPreloadedSnapshot();

    if (snapshot && (!getAnchor(this.location) || snapshot.hasAnchor(getAnchor(this.location)))) {
      if (this.action == "restore" || snapshot.isPreviewable) {
        return snapshot
      }
    }
  }

  getPreloadedSnapshot() {
    if (this.snapshotHTML) {
      return PageSnapshot.fromHTMLString(this.snapshotHTML)
    }
  }

  hasCachedSnapshot() {
    return this.getCachedSnapshot() != null
  }

  loadCachedSnapshot() {
    const snapshot = this.getCachedSnapshot();
    if (snapshot) {
      const isPreview = this.shouldIssueRequest();
      this.render(async () => {
        this.cacheSnapshot();
        if (this.isSamePage || this.isPageRefresh) {
          this.adapter.visitRendered(this);
        } else {
          if (this.view.renderPromise) await this.view.renderPromise;

          await this.renderPageSnapshot(snapshot, isPreview);

          this.adapter.visitRendered(this);
          if (!isPreview) {
            this.complete();
          }
        }
      });
    }
  }

  followRedirect() {
    if (this.redirectedToLocation && !this.followedRedirect && this.response?.redirected) {
      this.adapter.visitProposedToLocation(this.redirectedToLocation, {
        action: "replace",
        response: this.response,
        shouldCacheSnapshot: false,
        willRender: false
      });
      this.followedRedirect = true;
    }
  }

  goToSamePageAnchor() {
    if (this.isSamePage) {
      this.render(async () => {
        this.cacheSnapshot();
        this.performScroll();
        this.changeHistory();
        this.adapter.visitRendered(this);
      });
    }
  }

  // Fetch request delegate

  prepareRequest(request) {
    if (this.acceptsStreamResponse) {
      request.acceptResponseType(StreamMessage.contentType);
    }
  }

  requestStarted() {
    this.startRequest();
  }

  requestPreventedHandlingResponse(_request, _response) {}

  async requestSucceededWithResponse(request, response) {
    const responseHTML = await response.responseHTML;
    const { redirected, statusCode } = response;
    if (responseHTML == undefined) {
      this.recordResponse({
        statusCode: SystemStatusCode.contentTypeMismatch,
        redirected
      });
    } else {
      this.redirectedToLocation = response.redirected ? response.location : undefined;
      this.recordResponse({ statusCode: statusCode, responseHTML, redirected });
    }
  }

  async requestFailedWithResponse(request, response) {
    const responseHTML = await response.responseHTML;
    const { redirected, statusCode } = response;
    if (responseHTML == undefined) {
      this.recordResponse({
        statusCode: SystemStatusCode.contentTypeMismatch,
        redirected
      });
    } else {
      this.recordResponse({ statusCode: statusCode, responseHTML, redirected });
    }
  }

  requestErrored(_request, _error) {
    this.recordResponse({
      statusCode: SystemStatusCode.networkFailure,
      redirected: false
    });
  }

  requestFinished() {
    this.finishRequest();
  }

  // Scrolling

  performScroll() {
    if (!this.scrolled && !this.view.forceReloaded && !this.view.shouldPreserveScrollPosition(this)) {
      if (this.action == "restore") {
        this.scrollToRestoredPosition() || this.scrollToAnchor() || this.view.scrollToTop();
      } else {
        this.scrollToAnchor() || this.view.scrollToTop();
      }
      if (this.isSamePage) {
        this.delegate.visitScrolledToSamePageLocation(this.view.lastRenderedLocation, this.location);
      }

      this.scrolled = true;
    }
  }

  scrollToRestoredPosition() {
    const { scrollPosition } = this.restorationData;
    if (scrollPosition) {
      this.view.scrollToPosition(scrollPosition);
      return true
    }
  }

  scrollToAnchor() {
    const anchor = getAnchor(this.location);
    if (anchor != null) {
      this.view.scrollToAnchor(anchor);
      return true
    }
  }

  // Instrumentation

  recordTimingMetric(metric) {
    this.timingMetrics[metric] = new Date().getTime();
  }

  getTimingMetrics() {
    return { ...this.timingMetrics }
  }

  // Private

  hasPreloadedResponse() {
    return typeof this.response == "object"
  }

  shouldIssueRequest() {
    if (this.isSamePage) {
      return false
    } else if (this.action == "restore") {
      return !this.hasCachedSnapshot()
    } else {
      return this.willRender
    }
  }

  cacheSnapshot() {
    if (!this.snapshotCached) {
      this.view.cacheSnapshot(this.snapshot).then((snapshot) => snapshot && this.visitCachedSnapshot(snapshot));
      this.snapshotCached = true;
    }
  }

  async render(callback) {
    this.cancelRender();
    await new Promise((resolve) => {
      this.frame =
        document.visibilityState === "hidden" ? setTimeout(() => resolve(), 0) : requestAnimationFrame(() => resolve());
    });
    await callback();
    delete this.frame;
  }

  async renderPageSnapshot(snapshot, isPreview) {
    await this.viewTransitioner.renderChange(this.view.shouldTransitionTo(snapshot), async () => {
      await this.view.renderPage(snapshot, isPreview, this.willRender, this);
      this.performScroll();
    });
  }

  cancelRender() {
    if (this.frame) {
      cancelAnimationFrame(this.frame);
      delete this.frame;
    }
  }
}

function isSuccessful(statusCode) {
  return statusCode >= 200 && statusCode < 300
}

class BrowserAdapter {
  progressBar = new ProgressBar()

  constructor(session) {
    this.session = session;
  }

  visitProposedToLocation(location, options) {
    if (locationIsVisitable(location, this.navigator.rootLocation)) {
      this.navigator.startVisit(location, options?.restorationIdentifier || uuid(), options);
    } else {
      window.location.href = location.toString();
    }
  }

  visitStarted(visit) {
    this.location = visit.location;
    visit.loadCachedSnapshot();
    visit.issueRequest();
    visit.goToSamePageAnchor();
  }

  visitRequestStarted(visit) {
    this.progressBar.setValue(0);
    if (visit.hasCachedSnapshot() || visit.action != "restore") {
      this.showVisitProgressBarAfterDelay();
    } else {
      this.showProgressBar();
    }
  }

  visitRequestCompleted(visit) {
    visit.loadResponse();
  }

  visitRequestFailedWithStatusCode(visit, statusCode) {
    switch (statusCode) {
      case SystemStatusCode.networkFailure:
      case SystemStatusCode.timeoutFailure:
      case SystemStatusCode.contentTypeMismatch:
        return this.reload({
          reason: "request_failed",
          context: {
            statusCode
          }
        })
      default:
        return visit.loadResponse()
    }
  }

  visitRequestFinished(_visit) {}

  visitCompleted(_visit) {
    this.progressBar.setValue(1);
    this.hideVisitProgressBar();
  }

  pageInvalidated(reason) {
    this.reload(reason);
  }

  visitFailed(_visit) {
    this.progressBar.setValue(1);
    this.hideVisitProgressBar();
  }

  visitRendered(_visit) {}

  // Link prefetching

  linkPrefetchingIsEnabledForLocation(location) {
    return true
  }

  // Form Submission Delegate

  formSubmissionStarted(_formSubmission) {
    this.progressBar.setValue(0);
    this.showFormProgressBarAfterDelay();
  }

  formSubmissionFinished(_formSubmission) {
    this.progressBar.setValue(1);
    this.hideFormProgressBar();
  }

  // Private

  showVisitProgressBarAfterDelay() {
    this.visitProgressBarTimeout = window.setTimeout(this.showProgressBar, this.session.progressBarDelay);
  }

  hideVisitProgressBar() {
    this.progressBar.hide();
    if (this.visitProgressBarTimeout != null) {
      window.clearTimeout(this.visitProgressBarTimeout);
      delete this.visitProgressBarTimeout;
    }
  }

  showFormProgressBarAfterDelay() {
    if (this.formProgressBarTimeout == null) {
      this.formProgressBarTimeout = window.setTimeout(this.showProgressBar, this.session.progressBarDelay);
    }
  }

  hideFormProgressBar() {
    this.progressBar.hide();
    if (this.formProgressBarTimeout != null) {
      window.clearTimeout(this.formProgressBarTimeout);
      delete this.formProgressBarTimeout;
    }
  }

  showProgressBar = () => {
    this.progressBar.show();
  }

  reload(reason) {
    dispatch("turbo:reload", { detail: reason });

    window.location.href = this.location?.toString() || window.location.href;
  }

  get navigator() {
    return this.session.navigator
  }
}

class CacheObserver {
  selector = "[data-turbo-temporary]"
  deprecatedSelector = "[data-turbo-cache=false]"

  started = false

  start() {
    if (!this.started) {
      this.started = true;
      addEventListener("turbo:before-cache", this.removeTemporaryElements, false);
    }
  }

  stop() {
    if (this.started) {
      this.started = false;
      removeEventListener("turbo:before-cache", this.removeTemporaryElements, false);
    }
  }

  removeTemporaryElements = (_event) => {
    for (const element of this.temporaryElements) {
      element.remove();
    }
  }

  get temporaryElements() {
    return [...document.querySelectorAll(this.selector), ...this.temporaryElementsWithDeprecation]
  }

  get temporaryElementsWithDeprecation() {
    const elements = document.querySelectorAll(this.deprecatedSelector);

    if (elements.length) {
      console.warn(
        `The ${this.deprecatedSelector} selector is deprecated and will be removed in a future version. Use ${this.selector} instead.`
      );
    }

    return [...elements]
  }
}

class FrameRedirector {
  constructor(session, element) {
    this.session = session;
    this.element = element;
    this.linkInterceptor = new LinkInterceptor(this, element);
    this.formSubmitObserver = new FormSubmitObserver(this, element);
  }

  start() {
    this.linkInterceptor.start();
    this.formSubmitObserver.start();
  }

  stop() {
    this.linkInterceptor.stop();
    this.formSubmitObserver.stop();
  }

  // Link interceptor delegate

  shouldInterceptLinkClick(element, _location, _event) {
    return this.#shouldRedirect(element)
  }

  linkClickIntercepted(element, url, event) {
    const frame = this.#findFrameElement(element);
    if (frame) {
      frame.delegate.linkClickIntercepted(element, url, event);
    }
  }

  // Form submit observer delegate

  willSubmitForm(element, submitter) {
    return (
      element.closest("turbo-frame") == null &&
      this.#shouldSubmit(element, submitter) &&
      this.#shouldRedirect(element, submitter)
    )
  }

  formSubmitted(element, submitter) {
    const frame = this.#findFrameElement(element, submitter);
    if (frame) {
      frame.delegate.formSubmitted(element, submitter);
    }
  }

  #shouldSubmit(form, submitter) {
    const action = getAction$1(form, submitter);
    const meta = this.element.ownerDocument.querySelector(`meta[name="turbo-root"]`);
    const rootLocation = expandURL(meta?.content ?? "/");

    return this.#shouldRedirect(form, submitter) && locationIsVisitable(action, rootLocation)
  }

  #shouldRedirect(element, submitter) {
    const isNavigatable =
      element instanceof HTMLFormElement
        ? this.session.submissionIsNavigatable(element, submitter)
        : this.session.elementIsNavigatable(element);

    if (isNavigatable) {
      const frame = this.#findFrameElement(element, submitter);
      return frame ? frame != element.closest("turbo-frame") : false
    } else {
      return false
    }
  }

  #findFrameElement(element, submitter) {
    const id = submitter?.getAttribute("data-turbo-frame") || element.getAttribute("data-turbo-frame");
    if (id && id != "_top") {
      const frame = this.element.querySelector(`#${id}:not([disabled])`);
      if (frame instanceof FrameElement) {
        return frame
      }
    }
  }
}

class History {
  location
  restorationIdentifier = uuid()
  restorationData = {}
  started = false
  pageLoaded = false
  currentIndex = 0

  constructor(delegate) {
    this.delegate = delegate;
  }

  start() {
    if (!this.started) {
      addEventListener("popstate", this.onPopState, false);
      addEventListener("load", this.onPageLoad, false);
      this.currentIndex = history.state?.turbo?.restorationIndex || 0;
      this.started = true;
      this.replace(new URL(window.location.href));
    }
  }

  stop() {
    if (this.started) {
      removeEventListener("popstate", this.onPopState, false);
      removeEventListener("load", this.onPageLoad, false);
      this.started = false;
    }
  }

  push(location, restorationIdentifier) {
    this.update(history.pushState, location, restorationIdentifier);
  }

  replace(location, restorationIdentifier) {
    this.update(history.replaceState, location, restorationIdentifier);
  }

  update(method, location, restorationIdentifier = uuid()) {
    if (method === history.pushState) ++this.currentIndex;

    const state = { turbo: { restorationIdentifier, restorationIndex: this.currentIndex } };
    method.call(history, state, "", location.href);
    this.location = location;
    this.restorationIdentifier = restorationIdentifier;
  }

  // Restoration data

  getRestorationDataForIdentifier(restorationIdentifier) {
    return this.restorationData[restorationIdentifier] || {}
  }

  updateRestorationData(additionalData) {
    const { restorationIdentifier } = this;
    const restorationData = this.restorationData[restorationIdentifier];
    this.restorationData[restorationIdentifier] = {
      ...restorationData,
      ...additionalData
    };
  }

  // Scroll restoration

  assumeControlOfScrollRestoration() {
    if (!this.previousScrollRestoration) {
      this.previousScrollRestoration = history.scrollRestoration ?? "auto";
      history.scrollRestoration = "manual";
    }
  }

  relinquishControlOfScrollRestoration() {
    if (this.previousScrollRestoration) {
      history.scrollRestoration = this.previousScrollRestoration;
      delete this.previousScrollRestoration;
    }
  }

  // Event handlers

  onPopState = (event) => {
    if (this.shouldHandlePopState()) {
      const { turbo } = event.state || {};
      if (turbo) {
        this.location = new URL(window.location.href);
        const { restorationIdentifier, restorationIndex } = turbo;
        this.restorationIdentifier = restorationIdentifier;
        const direction = restorationIndex > this.currentIndex ? "forward" : "back";
        this.delegate.historyPoppedToLocationWithRestorationIdentifierAndDirection(this.location, restorationIdentifier, direction);
        this.currentIndex = restorationIndex;
      }
    }
  }

  onPageLoad = async (_event) => {
    await nextMicrotask();
    this.pageLoaded = true;
  }

  // Private

  shouldHandlePopState() {
    // Safari dispatches a popstate event after window's load event, ignore it
    return this.pageIsLoaded()
  }

  pageIsLoaded() {
    return this.pageLoaded || document.readyState == "complete"
  }
}

class LinkPrefetchObserver {
  started = false
  #prefetchedLink = null

  constructor(delegate, eventTarget) {
    this.delegate = delegate;
    this.eventTarget = eventTarget;
  }

  start() {
    if (this.started) return

    if (this.eventTarget.readyState === "loading") {
      this.eventTarget.addEventListener("DOMContentLoaded", this.#enable, { once: true });
    } else {
      this.#enable();
    }
  }

  stop() {
    if (!this.started) return

    this.eventTarget.removeEventListener("mouseenter", this.#tryToPrefetchRequest, {
      capture: true,
      passive: true
    });
    this.eventTarget.removeEventListener("mouseleave", this.#cancelRequestIfObsolete, {
      capture: true,
      passive: true
    });

    this.eventTarget.removeEventListener("turbo:before-fetch-request", this.#tryToUsePrefetchedRequest, true);
    this.started = false;
  }

  #enable = () => {
    this.eventTarget.addEventListener("mouseenter", this.#tryToPrefetchRequest, {
      capture: true,
      passive: true
    });
    this.eventTarget.addEventListener("mouseleave", this.#cancelRequestIfObsolete, {
      capture: true,
      passive: true
    });

    this.eventTarget.addEventListener("turbo:before-fetch-request", this.#tryToUsePrefetchedRequest, true);
    this.started = true;
  }

  #tryToPrefetchRequest = (event) => {
    if (getMetaContent("turbo-prefetch") === "false") return

    const target = event.target;
    const isLink = target.matches && target.matches("a[href]:not([target^=_]):not([download])");

    if (isLink && this.#isPrefetchable(target)) {
      const link = target;
      const location = getLocationForLink(link);

      if (this.delegate.canPrefetchRequestToLocation(link, location)) {
        this.#prefetchedLink = link;

        const fetchRequest = new FetchRequest(
          this,
          FetchMethod.get,
          location,
          new URLSearchParams(),
          target
        );

        prefetchCache.setLater(location.toString(), fetchRequest, this.#cacheTtl);
      }
    }
  }

  #cancelRequestIfObsolete = (event) => {
    if (event.target === this.#prefetchedLink) this.#cancelPrefetchRequest();
  }

  #cancelPrefetchRequest = () => {
    prefetchCache.clear();
    this.#prefetchedLink = null;
  }

  #tryToUsePrefetchedRequest = (event) => {
    if (event.target.tagName !== "FORM" && event.detail.fetchOptions.method === "GET") {
      const cached = prefetchCache.get(event.detail.url.toString());

      if (cached) {
        // User clicked link, use cache response
        event.detail.fetchRequest = cached;
      }

      prefetchCache.clear();
    }
  }

  prepareRequest(request) {
    const link = request.target;

    request.headers["X-Sec-Purpose"] = "prefetch";

    const turboFrame = link.closest("turbo-frame");
    const turboFrameTarget = link.getAttribute("data-turbo-frame") || turboFrame?.getAttribute("target") || turboFrame?.id;

    if (turboFrameTarget && turboFrameTarget !== "_top") {
      request.headers["Turbo-Frame"] = turboFrameTarget;
    }
  }

  // Fetch request interface

  requestSucceededWithResponse() {}

  requestStarted(fetchRequest) {}

  requestErrored(fetchRequest) {}

  requestFinished(fetchRequest) {}

  requestPreventedHandlingResponse(fetchRequest, fetchResponse) {}

  requestFailedWithResponse(fetchRequest, fetchResponse) {}

  get #cacheTtl() {
    return Number(getMetaContent("turbo-prefetch-cache-time")) || cacheTtl
  }

  #isPrefetchable(link) {
    const href = link.getAttribute("href");

    if (!href) return false

    if (unfetchableLink(link)) return false
    if (linkToTheSamePage(link)) return false
    if (linkOptsOut(link)) return false
    if (nonSafeLink(link)) return false
    if (eventPrevented(link)) return false

    return true
  }
}

const unfetchableLink = (link) => {
  return link.origin !== document.location.origin || !["http:", "https:"].includes(link.protocol) || link.hasAttribute("target")
};

const linkToTheSamePage = (link) => {
  return (link.pathname + link.search === document.location.pathname + document.location.search) || link.href.startsWith("#")
};

const linkOptsOut = (link) => {
  if (link.getAttribute("data-turbo-prefetch") === "false") return true
  if (link.getAttribute("data-turbo") === "false") return true

  const turboPrefetchParent = findClosestRecursively(link, "[data-turbo-prefetch]");
  if (turboPrefetchParent && turboPrefetchParent.getAttribute("data-turbo-prefetch") === "false") return true

  return false
};

const nonSafeLink = (link) => {
  const turboMethod = link.getAttribute("data-turbo-method");
  if (turboMethod && turboMethod.toLowerCase() !== "get") return true

  if (isUJS(link)) return true
  if (link.hasAttribute("data-turbo-confirm")) return true
  if (link.hasAttribute("data-turbo-stream")) return true

  return false
};

const isUJS = (link) => {
  return link.hasAttribute("data-remote") || link.hasAttribute("data-behavior") || link.hasAttribute("data-confirm") || link.hasAttribute("data-method")
};

const eventPrevented = (link) => {
  const event = dispatch("turbo:before-prefetch", { target: link, cancelable: true });
  return event.defaultPrevented
};

class Navigator {
  constructor(delegate) {
    this.delegate = delegate;
  }

  proposeVisit(location, options = {}) {
    if (this.delegate.allowsVisitingLocationWithAction(location, options.action)) {
      this.delegate.visitProposedToLocation(location, options);
    }
  }

  startVisit(locatable, restorationIdentifier, options = {}) {
    this.stop();
    this.currentVisit = new Visit(this, expandURL(locatable), restorationIdentifier, {
      referrer: this.location,
      ...options
    });
    this.currentVisit.start();
  }

  submitForm(form, submitter) {
    this.stop();
    this.formSubmission = new FormSubmission(this, form, submitter, true);

    this.formSubmission.start();
  }

  stop() {
    if (this.formSubmission) {
      this.formSubmission.stop();
      delete this.formSubmission;
    }

    if (this.currentVisit) {
      this.currentVisit.cancel();
      delete this.currentVisit;
    }
  }

  get adapter() {
    return this.delegate.adapter
  }

  get view() {
    return this.delegate.view
  }

  get rootLocation() {
    return this.view.snapshot.rootLocation
  }

  get history() {
    return this.delegate.history
  }

  // Form submission delegate

  formSubmissionStarted(formSubmission) {
    // Not all adapters implement formSubmissionStarted
    if (typeof this.adapter.formSubmissionStarted === "function") {
      this.adapter.formSubmissionStarted(formSubmission);
    }
  }

  async formSubmissionSucceededWithResponse(formSubmission, fetchResponse) {
    if (formSubmission == this.formSubmission) {
      const responseHTML = await fetchResponse.responseHTML;
      if (responseHTML) {
        const shouldCacheSnapshot = formSubmission.isSafe;
        if (!shouldCacheSnapshot) {
          this.view.clearSnapshotCache();
        }

        const { statusCode, redirected } = fetchResponse;
        const action = this.#getActionForFormSubmission(formSubmission, fetchResponse);
        const visitOptions = {
          action,
          shouldCacheSnapshot,
          response: { statusCode, responseHTML, redirected }
        };
        this.proposeVisit(fetchResponse.location, visitOptions);
      }
    }
  }

  async formSubmissionFailedWithResponse(formSubmission, fetchResponse) {
    const responseHTML = await fetchResponse.responseHTML;

    if (responseHTML) {
      const snapshot = PageSnapshot.fromHTMLString(responseHTML);
      if (fetchResponse.serverError) {
        await this.view.renderError(snapshot, this.currentVisit);
      } else {
        await this.view.renderPage(snapshot, false, true, this.currentVisit);
      }
      if(!snapshot.shouldPreserveScrollPosition) {
        this.view.scrollToTop();
      }
      this.view.clearSnapshotCache();
    }
  }

  formSubmissionErrored(formSubmission, error) {
    console.error(error);
  }

  formSubmissionFinished(formSubmission) {
    // Not all adapters implement formSubmissionFinished
    if (typeof this.adapter.formSubmissionFinished === "function") {
      this.adapter.formSubmissionFinished(formSubmission);
    }
  }

  // Link prefetching

  linkPrefetchingIsEnabledForLocation(location) {
    // Not all adapters implement linkPrefetchingIsEnabledForLocation
    if (typeof this.adapter.linkPrefetchingIsEnabledForLocation === "function") {
      return this.adapter.linkPrefetchingIsEnabledForLocation(location)
    }

    return true
  }

  // Visit delegate

  visitStarted(visit) {
    this.delegate.visitStarted(visit);
  }

  visitCompleted(visit) {
    this.delegate.visitCompleted(visit);
    delete this.currentVisit;
  }

  locationWithActionIsSamePage(location, action) {
    const anchor = getAnchor(location);
    const currentAnchor = getAnchor(this.view.lastRenderedLocation);
    const isRestorationToTop = action === "restore" && typeof anchor === "undefined";

    return (
      action !== "replace" &&
      getRequestURL(location) === getRequestURL(this.view.lastRenderedLocation) &&
      (isRestorationToTop || (anchor != null && anchor !== currentAnchor))
    )
  }

  visitScrolledToSamePageLocation(oldURL, newURL) {
    this.delegate.visitScrolledToSamePageLocation(oldURL, newURL);
  }

  // Visits

  get location() {
    return this.history.location
  }

  get restorationIdentifier() {
    return this.history.restorationIdentifier
  }

  #getActionForFormSubmission(formSubmission, fetchResponse) {
    const { submitter, formElement } = formSubmission;
    return getVisitAction(submitter, formElement) || this.#getDefaultAction(fetchResponse)
  }

  #getDefaultAction(fetchResponse) {
    const sameLocationRedirect = fetchResponse.redirected && fetchResponse.location.href === this.location?.href;
    return sameLocationRedirect ? "replace" : "advance"
  }
}

const PageStage = {
  initial: 0,
  loading: 1,
  interactive: 2,
  complete: 3
};

class PageObserver {
  stage = PageStage.initial
  started = false

  constructor(delegate) {
    this.delegate = delegate;
  }

  start() {
    if (!this.started) {
      if (this.stage == PageStage.initial) {
        this.stage = PageStage.loading;
      }
      document.addEventListener("readystatechange", this.interpretReadyState, false);
      addEventListener("pagehide", this.pageWillUnload, false);
      this.started = true;
    }
  }

  stop() {
    if (this.started) {
      document.removeEventListener("readystatechange", this.interpretReadyState, false);
      removeEventListener("pagehide", this.pageWillUnload, false);
      this.started = false;
    }
  }

  interpretReadyState = () => {
    const { readyState } = this;
    if (readyState == "interactive") {
      this.pageIsInteractive();
    } else if (readyState == "complete") {
      this.pageIsComplete();
    }
  }

  pageIsInteractive() {
    if (this.stage == PageStage.loading) {
      this.stage = PageStage.interactive;
      this.delegate.pageBecameInteractive();
    }
  }

  pageIsComplete() {
    this.pageIsInteractive();
    if (this.stage == PageStage.interactive) {
      this.stage = PageStage.complete;
      this.delegate.pageLoaded();
    }
  }

  pageWillUnload = () => {
    this.delegate.pageWillUnload();
  }

  get readyState() {
    return document.readyState
  }
}

class ScrollObserver {
  started = false

  constructor(delegate) {
    this.delegate = delegate;
  }

  start() {
    if (!this.started) {
      addEventListener("scroll", this.onScroll, false);
      this.onScroll();
      this.started = true;
    }
  }

  stop() {
    if (this.started) {
      removeEventListener("scroll", this.onScroll, false);
      this.started = false;
    }
  }

  onScroll = () => {
    this.updatePosition({ x: window.pageXOffset, y: window.pageYOffset });
  }

  // Private

  updatePosition(position) {
    this.delegate.scrollPositionChanged(position);
  }
}

class StreamMessageRenderer {
  render({ fragment }) {
    Bardo.preservingPermanentElements(this, getPermanentElementMapForFragment(fragment), () => {
      withAutofocusFromFragment(fragment, () => {
        withPreservedFocus(() => {
          document.documentElement.appendChild(fragment);
        });
      });
    });
  }

  // Bardo delegate

  enteringBardo(currentPermanentElement, newPermanentElement) {
    newPermanentElement.replaceWith(currentPermanentElement.cloneNode(true));
  }

  leavingBardo() {}
}

function getPermanentElementMapForFragment(fragment) {
  const permanentElementsInDocument = queryPermanentElementsAll(document.documentElement);
  const permanentElementMap = {};
  for (const permanentElementInDocument of permanentElementsInDocument) {
    const { id } = permanentElementInDocument;

    for (const streamElement of fragment.querySelectorAll("turbo-stream")) {
      const elementInStream = getPermanentElementById(streamElement.templateElement.content, id);

      if (elementInStream) {
        permanentElementMap[id] = [permanentElementInDocument, elementInStream];
      }
    }
  }

  return permanentElementMap
}

async function withAutofocusFromFragment(fragment, callback) {
  const generatedID = `turbo-stream-autofocus-${uuid()}`;
  const turboStreams = fragment.querySelectorAll("turbo-stream");
  const elementWithAutofocus = firstAutofocusableElementInStreams(turboStreams);
  let willAutofocusId = null;

  if (elementWithAutofocus) {
    if (elementWithAutofocus.id) {
      willAutofocusId = elementWithAutofocus.id;
    } else {
      willAutofocusId = generatedID;
    }

    elementWithAutofocus.id = willAutofocusId;
  }

  callback();
  await nextRepaint();

  const hasNoActiveElement = document.activeElement == null || document.activeElement == document.body;

  if (hasNoActiveElement && willAutofocusId) {
    const elementToAutofocus = document.getElementById(willAutofocusId);

    if (elementIsFocusable(elementToAutofocus)) {
      elementToAutofocus.focus();
    }
    if (elementToAutofocus && elementToAutofocus.id == generatedID) {
      elementToAutofocus.removeAttribute("id");
    }
  }
}

async function withPreservedFocus(callback) {
  const [activeElementBeforeRender, activeElementAfterRender] = await around(callback, () => document.activeElement);

  const restoreFocusTo = activeElementBeforeRender && activeElementBeforeRender.id;

  if (restoreFocusTo) {
    const elementToFocus = document.getElementById(restoreFocusTo);

    if (elementIsFocusable(elementToFocus) && elementToFocus != activeElementAfterRender) {
      elementToFocus.focus();
    }
  }
}

function firstAutofocusableElementInStreams(nodeListOfStreamElements) {
  for (const streamElement of nodeListOfStreamElements) {
    const elementWithAutofocus = queryAutofocusableElement(streamElement.templateElement.content);

    if (elementWithAutofocus) return elementWithAutofocus
  }

  return null
}

class StreamObserver {
  sources = new Set()
  #started = false

  constructor(delegate) {
    this.delegate = delegate;
  }

  start() {
    if (!this.#started) {
      this.#started = true;
      addEventListener("turbo:before-fetch-response", this.inspectFetchResponse, false);
    }
  }

  stop() {
    if (this.#started) {
      this.#started = false;
      removeEventListener("turbo:before-fetch-response", this.inspectFetchResponse, false);
    }
  }

  connectStreamSource(source) {
    if (!this.streamSourceIsConnected(source)) {
      this.sources.add(source);
      source.addEventListener("message", this.receiveMessageEvent, false);
    }
  }

  disconnectStreamSource(source) {
    if (this.streamSourceIsConnected(source)) {
      this.sources.delete(source);
      source.removeEventListener("message", this.receiveMessageEvent, false);
    }
  }

  streamSourceIsConnected(source) {
    return this.sources.has(source)
  }

  inspectFetchResponse = (event) => {
    const response = fetchResponseFromEvent(event);
    if (response && fetchResponseIsStream(response)) {
      event.preventDefault();
      this.receiveMessageResponse(response);
    }
  }

  receiveMessageEvent = (event) => {
    if (this.#started && typeof event.data == "string") {
      this.receiveMessageHTML(event.data);
    }
  }

  async receiveMessageResponse(response) {
    const html = await response.responseHTML;
    if (html) {
      this.receiveMessageHTML(html);
    }
  }

  receiveMessageHTML(html) {
    this.delegate.receivedMessageFromStream(StreamMessage.wrap(html));
  }
}

function fetchResponseFromEvent(event) {
  const fetchResponse = event.detail?.fetchResponse;
  if (fetchResponse instanceof FetchResponse) {
    return fetchResponse
  }
}

function fetchResponseIsStream(response) {
  const contentType = response.contentType ?? "";
  return contentType.startsWith(StreamMessage.contentType)
}

class ErrorRenderer extends Renderer {
  static renderElement(currentElement, newElement) {
    const { documentElement, body } = document;

    documentElement.replaceChild(newElement, body);
  }

  async render() {
    this.replaceHeadAndBody();
    this.activateScriptElements();
  }

  replaceHeadAndBody() {
    const { documentElement, head } = document;
    documentElement.replaceChild(this.newHead, head);
    this.renderElement(this.currentElement, this.newElement);
  }

  activateScriptElements() {
    for (const replaceableElement of this.scriptElements) {
      const parentNode = replaceableElement.parentNode;
      if (parentNode) {
        const element = activateScriptElement(replaceableElement);
        parentNode.replaceChild(element, replaceableElement);
      }
    }
  }

  get newHead() {
    return this.newSnapshot.headSnapshot.element
  }

  get scriptElements() {
    return document.documentElement.querySelectorAll("script")
  }
}

class PageRenderer extends Renderer {
  static renderElement(currentElement, newElement) {
    if (document.body && newElement instanceof HTMLBodyElement) {
      document.body.replaceWith(newElement);
    } else {
      document.documentElement.appendChild(newElement);
    }
  }

  get shouldRender() {
    return this.newSnapshot.isVisitable && this.trackedElementsAreIdentical
  }

  get reloadReason() {
    if (!this.newSnapshot.isVisitable) {
      return {
        reason: "turbo_visit_control_is_reload"
      }
    }

    if (!this.trackedElementsAreIdentical) {
      return {
        reason: "tracked_element_mismatch"
      }
    }
  }

  async prepareToRender() {
    this.#setLanguage();
    await this.mergeHead();
  }

  async render() {
    if (this.willRender) {
      await this.replaceBody();
    }
  }

  finishRendering() {
    super.finishRendering();
    if (!this.isPreview) {
      this.focusFirstAutofocusableElement();
    }
  }

  get currentHeadSnapshot() {
    return this.currentSnapshot.headSnapshot
  }

  get newHeadSnapshot() {
    return this.newSnapshot.headSnapshot
  }

  get newElement() {
    return this.newSnapshot.element
  }

  #setLanguage() {
    const { documentElement } = this.currentSnapshot;
    const { lang } = this.newSnapshot;

    if (lang) {
      documentElement.setAttribute("lang", lang);
    } else {
      documentElement.removeAttribute("lang");
    }
  }

  async mergeHead() {
    const mergedHeadElements = this.mergeProvisionalElements();
    const newStylesheetElements = this.copyNewHeadStylesheetElements();
    this.copyNewHeadScriptElements();

    await mergedHeadElements;
    await newStylesheetElements;

    if (this.willRender) {
      this.removeUnusedDynamicStylesheetElements();
    }
  }

  async replaceBody() {
    await this.preservingPermanentElements(async () => {
      this.activateNewBody();
      await this.assignNewBody();
    });
  }

  get trackedElementsAreIdentical() {
    return this.currentHeadSnapshot.trackedElementSignature == this.newHeadSnapshot.trackedElementSignature
  }

  async copyNewHeadStylesheetElements() {
    const loadingElements = [];

    for (const element of this.newHeadStylesheetElements) {
      loadingElements.push(waitForLoad(element));

      document.head.appendChild(element);
    }

    await Promise.all(loadingElements);
  }

  copyNewHeadScriptElements() {
    for (const element of this.newHeadScriptElements) {
      document.head.appendChild(activateScriptElement(element));
    }
  }

  removeUnusedDynamicStylesheetElements() {
    for (const element of this.unusedDynamicStylesheetElements) {
      document.head.removeChild(element);
    }
  }

  async mergeProvisionalElements() {
    const newHeadElements = [...this.newHeadProvisionalElements];

    for (const element of this.currentHeadProvisionalElements) {
      if (!this.isCurrentElementInElementList(element, newHeadElements)) {
        document.head.removeChild(element);
      }
    }

    for (const element of newHeadElements) {
      document.head.appendChild(element);
    }
  }

  isCurrentElementInElementList(element, elementList) {
    for (const [index, newElement] of elementList.entries()) {
      // if title element...
      if (element.tagName == "TITLE") {
        if (newElement.tagName != "TITLE") {
          continue
        }
        if (element.innerHTML == newElement.innerHTML) {
          elementList.splice(index, 1);
          return true
        }
      }

      // if any other element...
      if (newElement.isEqualNode(element)) {
        elementList.splice(index, 1);
        return true
      }
    }

    return false
  }

  removeCurrentHeadProvisionalElements() {
    for (const element of this.currentHeadProvisionalElements) {
      document.head.removeChild(element);
    }
  }

  copyNewHeadProvisionalElements() {
    for (const element of this.newHeadProvisionalElements) {
      document.head.appendChild(element);
    }
  }

  activateNewBody() {
    document.adoptNode(this.newElement);
    this.activateNewBodyScriptElements();
  }

  activateNewBodyScriptElements() {
    for (const inertScriptElement of this.newBodyScriptElements) {
      const activatedScriptElement = activateScriptElement(inertScriptElement);
      inertScriptElement.replaceWith(activatedScriptElement);
    }
  }

  async assignNewBody() {
    await this.renderElement(this.currentElement, this.newElement);
  }

  get unusedDynamicStylesheetElements() {
    return this.oldHeadStylesheetElements.filter((element) => {
      return element.getAttribute("data-turbo-track") === "dynamic"
    })
  }

  get oldHeadStylesheetElements() {
    return this.currentHeadSnapshot.getStylesheetElementsNotInSnapshot(this.newHeadSnapshot)
  }

  get newHeadStylesheetElements() {
    return this.newHeadSnapshot.getStylesheetElementsNotInSnapshot(this.currentHeadSnapshot)
  }

  get newHeadScriptElements() {
    return this.newHeadSnapshot.getScriptElementsNotInSnapshot(this.currentHeadSnapshot)
  }

  get currentHeadProvisionalElements() {
    return this.currentHeadSnapshot.provisionalElements
  }

  get newHeadProvisionalElements() {
    return this.newHeadSnapshot.provisionalElements
  }

  get newBodyScriptElements() {
    return this.newElement.querySelectorAll("script")
  }
}

class MorphingPageRenderer extends PageRenderer {
  static renderElement(currentElement, newElement) {
    morphElements(currentElement, newElement, {
      callbacks: {
        beforeNodeMorphed: element => !canRefreshFrame(element)
      }
    });

    for (const frame of currentElement.querySelectorAll("turbo-frame")) {
      if (canRefreshFrame(frame)) frame.reload();
    }

    dispatch("turbo:morph", { detail: { currentElement, newElement } });
  }

  async preservingPermanentElements(callback) {
    return await callback()
  }

  get renderMethod() {
    return "morph"
  }

  get shouldAutofocus() {
    return false
  }
}

function canRefreshFrame(frame) {
  return frame instanceof FrameElement &&
    frame.src &&
    frame.refresh === "morph" &&
    !frame.closest("[data-turbo-permanent]")
}

class SnapshotCache {
  keys = []
  snapshots = {}

  constructor(size) {
    this.size = size;
  }

  has(location) {
    return toCacheKey(location) in this.snapshots
  }

  get(location) {
    if (this.has(location)) {
      const snapshot = this.read(location);
      this.touch(location);
      return snapshot
    }
  }

  put(location, snapshot) {
    this.write(location, snapshot);
    this.touch(location);
    return snapshot
  }

  clear() {
    this.snapshots = {};
  }

  // Private

  read(location) {
    return this.snapshots[toCacheKey(location)]
  }

  write(location, snapshot) {
    this.snapshots[toCacheKey(location)] = snapshot;
  }

  touch(location) {
    const key = toCacheKey(location);
    const index = this.keys.indexOf(key);
    if (index > -1) this.keys.splice(index, 1);
    this.keys.unshift(key);
    this.trim();
  }

  trim() {
    for (const key of this.keys.splice(this.size)) {
      delete this.snapshots[key];
    }
  }
}

class PageView extends View {
  snapshotCache = new SnapshotCache(10)
  lastRenderedLocation = new URL(location.href)
  forceReloaded = false

  shouldTransitionTo(newSnapshot) {
    return this.snapshot.prefersViewTransitions && newSnapshot.prefersViewTransitions
  }

  renderPage(snapshot, isPreview = false, willRender = true, visit) {
    const shouldMorphPage = this.isPageRefresh(visit) && this.snapshot.shouldMorphPage;
    const rendererClass = shouldMorphPage ? MorphingPageRenderer : PageRenderer;

    const renderer = new rendererClass(this.snapshot, snapshot, isPreview, willRender);

    if (!renderer.shouldRender) {
      this.forceReloaded = true;
    } else {
      visit?.changeHistory();
    }

    return this.render(renderer)
  }

  renderError(snapshot, visit) {
    visit?.changeHistory();
    const renderer = new ErrorRenderer(this.snapshot, snapshot, false);
    return this.render(renderer)
  }

  clearSnapshotCache() {
    this.snapshotCache.clear();
  }

  async cacheSnapshot(snapshot = this.snapshot) {
    if (snapshot.isCacheable) {
      this.delegate.viewWillCacheSnapshot();
      const { lastRenderedLocation: location } = this;
      await nextEventLoopTick();
      const cachedSnapshot = snapshot.clone();
      this.snapshotCache.put(location, cachedSnapshot);
      return cachedSnapshot
    }
  }

  getCachedSnapshotForLocation(location) {
    return this.snapshotCache.get(location)
  }

  isPageRefresh(visit) {
    return !visit || (this.lastRenderedLocation.pathname === visit.location.pathname && visit.action === "replace")
  }

  shouldPreserveScrollPosition(visit) {
    return this.isPageRefresh(visit) && this.snapshot.shouldPreserveScrollPosition
  }

  get snapshot() {
    return PageSnapshot.fromElement(this.element)
  }
}

class Preloader {
  selector = "a[data-turbo-preload]"

  constructor(delegate, snapshotCache) {
    this.delegate = delegate;
    this.snapshotCache = snapshotCache;
  }

  start() {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", this.#preloadAll);
    } else {
      this.preloadOnLoadLinksForView(document.body);
    }
  }

  stop() {
    document.removeEventListener("DOMContentLoaded", this.#preloadAll);
  }

  preloadOnLoadLinksForView(element) {
    for (const link of element.querySelectorAll(this.selector)) {
      if (this.delegate.shouldPreloadLink(link)) {
        this.preloadURL(link);
      }
    }
  }

  async preloadURL(link) {
    const location = new URL(link.href);

    if (this.snapshotCache.has(location)) {
      return
    }

    const fetchRequest = new FetchRequest(this, FetchMethod.get, location, new URLSearchParams(), link);
    await fetchRequest.perform();
  }

  // Fetch request delegate

  prepareRequest(fetchRequest) {
    fetchRequest.headers["X-Sec-Purpose"] = "prefetch";
  }

  async requestSucceededWithResponse(fetchRequest, fetchResponse) {
    try {
      const responseHTML = await fetchResponse.responseHTML;
      const snapshot = PageSnapshot.fromHTMLString(responseHTML);

      this.snapshotCache.put(fetchRequest.url, snapshot);
    } catch (_) {
      // If we cannot preload that is ok!
    }
  }

  requestStarted(fetchRequest) {}

  requestErrored(fetchRequest) {}

  requestFinished(fetchRequest) {}

  requestPreventedHandlingResponse(fetchRequest, fetchResponse) {}

  requestFailedWithResponse(fetchRequest, fetchResponse) {}

  #preloadAll = () => {
    this.preloadOnLoadLinksForView(document.body);
  }
}

class Cache {
  constructor(session) {
    this.session = session;
  }

  clear() {
    this.session.clearCache();
  }

  resetCacheControl() {
    this.#setCacheControl("");
  }

  exemptPageFromCache() {
    this.#setCacheControl("no-cache");
  }

  exemptPageFromPreview() {
    this.#setCacheControl("no-preview");
  }

  #setCacheControl(value) {
    setMetaContent("turbo-cache-control", value);
  }
}

class Session {
  navigator = new Navigator(this)
  history = new History(this)
  view = new PageView(this, document.documentElement)
  adapter = new BrowserAdapter(this)

  pageObserver = new PageObserver(this)
  cacheObserver = new CacheObserver()
  linkPrefetchObserver = new LinkPrefetchObserver(this, document)
  linkClickObserver = new LinkClickObserver(this, window)
  formSubmitObserver = new FormSubmitObserver(this, document)
  scrollObserver = new ScrollObserver(this)
  streamObserver = new StreamObserver(this)
  formLinkClickObserver = new FormLinkClickObserver(this, document.documentElement)
  frameRedirector = new FrameRedirector(this, document.documentElement)
  streamMessageRenderer = new StreamMessageRenderer()
  cache = new Cache(this)

  enabled = true
  started = false
  #pageRefreshDebouncePeriod = 150

  constructor(recentRequests) {
    this.recentRequests = recentRequests;
    this.preloader = new Preloader(this, this.view.snapshotCache);
    this.debouncedRefresh = this.refresh;
    this.pageRefreshDebouncePeriod = this.pageRefreshDebouncePeriod;
  }

  start() {
    if (!this.started) {
      this.pageObserver.start();
      this.cacheObserver.start();
      this.linkPrefetchObserver.start();
      this.formLinkClickObserver.start();
      this.linkClickObserver.start();
      this.formSubmitObserver.start();
      this.scrollObserver.start();
      this.streamObserver.start();
      this.frameRedirector.start();
      this.history.start();
      this.preloader.start();
      this.started = true;
      this.enabled = true;
    }
  }

  disable() {
    this.enabled = false;
  }

  stop() {
    if (this.started) {
      this.pageObserver.stop();
      this.cacheObserver.stop();
      this.linkPrefetchObserver.stop();
      this.formLinkClickObserver.stop();
      this.linkClickObserver.stop();
      this.formSubmitObserver.stop();
      this.scrollObserver.stop();
      this.streamObserver.stop();
      this.frameRedirector.stop();
      this.history.stop();
      this.preloader.stop();
      this.started = false;
    }
  }

  registerAdapter(adapter) {
    this.adapter = adapter;
  }

  visit(location, options = {}) {
    const frameElement = options.frame ? document.getElementById(options.frame) : null;

    if (frameElement instanceof FrameElement) {
      const action = options.action || getVisitAction(frameElement);

      frameElement.delegate.proposeVisitIfNavigatedWithAction(frameElement, action);
      frameElement.src = location.toString();
    } else {
      this.navigator.proposeVisit(expandURL(location), options);
    }
  }

  refresh(url, requestId) {
    const isRecentRequest = requestId && this.recentRequests.has(requestId);
    const isCurrentUrl = url === document.baseURI;
    if (!isRecentRequest && !this.navigator.currentVisit && isCurrentUrl) {
      this.visit(url, { action: "replace", shouldCacheSnapshot: false });
    }
  }

  connectStreamSource(source) {
    this.streamObserver.connectStreamSource(source);
  }

  disconnectStreamSource(source) {
    this.streamObserver.disconnectStreamSource(source);
  }

  renderStreamMessage(message) {
    this.streamMessageRenderer.render(StreamMessage.wrap(message));
  }

  clearCache() {
    this.view.clearSnapshotCache();
  }

  setProgressBarDelay(delay) {
    console.warn(
      "Please replace `session.setProgressBarDelay(delay)` with `session.progressBarDelay = delay`. The function is deprecated and will be removed in a future version of Turbo.`"
    );

    this.progressBarDelay = delay;
  }

  set progressBarDelay(delay) {
    config.drive.progressBarDelay = delay;
  }

  get progressBarDelay() {
    return config.drive.progressBarDelay
  }

  set drive(value) {
    config.drive.enabled = value;
  }

  get drive() {
    return config.drive.enabled
  }

  set formMode(value) {
    config.forms.mode = value;
  }

  get formMode() {
    return config.forms.mode
  }

  get location() {
    return this.history.location
  }

  get restorationIdentifier() {
    return this.history.restorationIdentifier
  }

  get pageRefreshDebouncePeriod() {
    return this.#pageRefreshDebouncePeriod
  }

  set pageRefreshDebouncePeriod(value) {
    this.refresh = debounce(this.debouncedRefresh.bind(this), value);
    this.#pageRefreshDebouncePeriod = value;
  }

  // Preloader delegate

  shouldPreloadLink(element) {
    const isUnsafe = element.hasAttribute("data-turbo-method");
    const isStream = element.hasAttribute("data-turbo-stream");
    const frameTarget = element.getAttribute("data-turbo-frame");
    const frame = frameTarget == "_top" ?
      null :
      document.getElementById(frameTarget) || findClosestRecursively(element, "turbo-frame:not([disabled])");

    if (isUnsafe || isStream || frame instanceof FrameElement) {
      return false
    } else {
      const location = new URL(element.href);

      return this.elementIsNavigatable(element) && locationIsVisitable(location, this.snapshot.rootLocation)
    }
  }

  // History delegate

  historyPoppedToLocationWithRestorationIdentifierAndDirection(location, restorationIdentifier, direction) {
    if (this.enabled) {
      this.navigator.startVisit(location, restorationIdentifier, {
        action: "restore",
        historyChanged: true,
        direction
      });
    } else {
      this.adapter.pageInvalidated({
        reason: "turbo_disabled"
      });
    }
  }

  // Scroll observer delegate

  scrollPositionChanged(position) {
    this.history.updateRestorationData({ scrollPosition: position });
  }

  // Form click observer delegate

  willSubmitFormLinkToLocation(link, location) {
    return this.elementIsNavigatable(link) && locationIsVisitable(location, this.snapshot.rootLocation)
  }

  submittedFormLinkToLocation() {}

  // Link hover observer delegate

  canPrefetchRequestToLocation(link, location) {
    return (
      this.elementIsNavigatable(link) &&
      locationIsVisitable(location, this.snapshot.rootLocation) &&
      this.navigator.linkPrefetchingIsEnabledForLocation(location)
    )
  }

  // Link click observer delegate

  willFollowLinkToLocation(link, location, event) {
    return (
      this.elementIsNavigatable(link) &&
      locationIsVisitable(location, this.snapshot.rootLocation) &&
      this.applicationAllowsFollowingLinkToLocation(link, location, event)
    )
  }

  followedLinkToLocation(link, location) {
    const action = this.getActionForLink(link);
    const acceptsStreamResponse = link.hasAttribute("data-turbo-stream");

    this.visit(location.href, { action, acceptsStreamResponse });
  }

  // Navigator delegate

  allowsVisitingLocationWithAction(location, action) {
    return this.locationWithActionIsSamePage(location, action) || this.applicationAllowsVisitingLocation(location)
  }

  visitProposedToLocation(location, options) {
    extendURLWithDeprecatedProperties(location);
    this.adapter.visitProposedToLocation(location, options);
  }

  // Visit delegate

  visitStarted(visit) {
    if (!visit.acceptsStreamResponse) {
      markAsBusy(document.documentElement);
      this.view.markVisitDirection(visit.direction);
    }
    extendURLWithDeprecatedProperties(visit.location);
    if (!visit.silent) {
      this.notifyApplicationAfterVisitingLocation(visit.location, visit.action);
    }
  }

  visitCompleted(visit) {
    this.view.unmarkVisitDirection();
    clearBusyState(document.documentElement);
    this.notifyApplicationAfterPageLoad(visit.getTimingMetrics());
  }

  locationWithActionIsSamePage(location, action) {
    return this.navigator.locationWithActionIsSamePage(location, action)
  }

  visitScrolledToSamePageLocation(oldURL, newURL) {
    this.notifyApplicationAfterVisitingSamePageLocation(oldURL, newURL);
  }

  // Form submit observer delegate

  willSubmitForm(form, submitter) {
    const action = getAction$1(form, submitter);

    return (
      this.submissionIsNavigatable(form, submitter) &&
      locationIsVisitable(expandURL(action), this.snapshot.rootLocation)
    )
  }

  formSubmitted(form, submitter) {
    this.navigator.submitForm(form, submitter);
  }

  // Page observer delegate

  pageBecameInteractive() {
    this.view.lastRenderedLocation = this.location;
    this.notifyApplicationAfterPageLoad();
  }

  pageLoaded() {
    this.history.assumeControlOfScrollRestoration();
  }

  pageWillUnload() {
    this.history.relinquishControlOfScrollRestoration();
  }

  // Stream observer delegate

  receivedMessageFromStream(message) {
    this.renderStreamMessage(message);
  }

  // Page view delegate

  viewWillCacheSnapshot() {
    if (!this.navigator.currentVisit?.silent) {
      this.notifyApplicationBeforeCachingSnapshot();
    }
  }

  allowsImmediateRender({ element }, options) {
    const event = this.notifyApplicationBeforeRender(element, options);
    const {
      defaultPrevented,
      detail: { render }
    } = event;

    if (this.view.renderer && render) {
      this.view.renderer.renderElement = render;
    }

    return !defaultPrevented
  }

  viewRenderedSnapshot(_snapshot, _isPreview, renderMethod) {
    this.view.lastRenderedLocation = this.history.location;
    this.notifyApplicationAfterRender(renderMethod);
  }

  preloadOnLoadLinksForView(element) {
    this.preloader.preloadOnLoadLinksForView(element);
  }

  viewInvalidated(reason) {
    this.adapter.pageInvalidated(reason);
  }

  // Frame element

  frameLoaded(frame) {
    this.notifyApplicationAfterFrameLoad(frame);
  }

  frameRendered(fetchResponse, frame) {
    this.notifyApplicationAfterFrameRender(fetchResponse, frame);
  }

  // Application events

  applicationAllowsFollowingLinkToLocation(link, location, ev) {
    const event = this.notifyApplicationAfterClickingLinkToLocation(link, location, ev);
    return !event.defaultPrevented
  }

  applicationAllowsVisitingLocation(location) {
    const event = this.notifyApplicationBeforeVisitingLocation(location);
    return !event.defaultPrevented
  }

  notifyApplicationAfterClickingLinkToLocation(link, location, event) {
    return dispatch("turbo:click", {
      target: link,
      detail: { url: location.href, originalEvent: event },
      cancelable: true
    })
  }

  notifyApplicationBeforeVisitingLocation(location) {
    return dispatch("turbo:before-visit", {
      detail: { url: location.href },
      cancelable: true
    })
  }

  notifyApplicationAfterVisitingLocation(location, action) {
    return dispatch("turbo:visit", { detail: { url: location.href, action } })
  }

  notifyApplicationBeforeCachingSnapshot() {
    return dispatch("turbo:before-cache")
  }

  notifyApplicationBeforeRender(newBody, options) {
    return dispatch("turbo:before-render", {
      detail: { newBody, ...options },
      cancelable: true
    })
  }

  notifyApplicationAfterRender(renderMethod) {
    return dispatch("turbo:render", { detail: { renderMethod } })
  }

  notifyApplicationAfterPageLoad(timing = {}) {
    return dispatch("turbo:load", {
      detail: { url: this.location.href, timing }
    })
  }

  notifyApplicationAfterVisitingSamePageLocation(oldURL, newURL) {
    dispatchEvent(
      new HashChangeEvent("hashchange", {
        oldURL: oldURL.toString(),
        newURL: newURL.toString()
      })
    );
  }

  notifyApplicationAfterFrameLoad(frame) {
    return dispatch("turbo:frame-load", { target: frame })
  }

  notifyApplicationAfterFrameRender(fetchResponse, frame) {
    return dispatch("turbo:frame-render", {
      detail: { fetchResponse },
      target: frame,
      cancelable: true
    })
  }

  // Helpers

  submissionIsNavigatable(form, submitter) {
    if (config.forms.mode == "off") {
      return false
    } else {
      const submitterIsNavigatable = submitter ? this.elementIsNavigatable(submitter) : true;

      if (config.forms.mode == "optin") {
        return submitterIsNavigatable && form.closest('[data-turbo="true"]') != null
      } else {
        return submitterIsNavigatable && this.elementIsNavigatable(form)
      }
    }
  }

  elementIsNavigatable(element) {
    const container = findClosestRecursively(element, "[data-turbo]");
    const withinFrame = findClosestRecursively(element, "turbo-frame");

    // Check if Drive is enabled on the session or we're within a Frame.
    if (config.drive.enabled || withinFrame) {
      // Element is navigatable by default, unless `data-turbo="false"`.
      if (container) {
        return container.getAttribute("data-turbo") != "false"
      } else {
        return true
      }
    } else {
      // Element isn't navigatable by default, unless `data-turbo="true"`.
      if (container) {
        return container.getAttribute("data-turbo") == "true"
      } else {
        return false
      }
    }
  }

  // Private

  getActionForLink(link) {
    return getVisitAction(link) || "advance"
  }

  get snapshot() {
    return this.view.snapshot
  }
}

// Older versions of the Turbo Native adapters referenced the
// `Location#absoluteURL` property in their implementations of
// the `Adapter#visitProposedToLocation()` and `#visitStarted()`
// methods. The Location class has since been removed in favor
// of the DOM URL API, and accordingly all Adapter methods now
// receive URL objects.
//
// We alias #absoluteURL to #toString() here to avoid crashing
// older adapters which do not expect URL objects. We should
// consider removing this support at some point in the future.

function extendURLWithDeprecatedProperties(url) {
  Object.defineProperties(url, deprecatedLocationPropertyDescriptors);
}

const deprecatedLocationPropertyDescriptors = {
  absoluteURL: {
    get() {
      return this.toString()
    }
  }
};

const session = new Session(recentRequests);
const { cache, navigator: navigator$1 } = session;

/**
 * Starts the main session.
 * This initialises any necessary observers such as those to monitor
 * link interactions.
 */
function start() {
  session.start();
}

/**
 * Registers an adapter for the main session.
 *
 * @param adapter Adapter to register
 */
function registerAdapter(adapter) {
  session.registerAdapter(adapter);
}

/**
 * Performs an application visit to the given location.
 *
 * @param location Location to visit (a URL or path)
 * @param options Options to apply
 * @param options.action Type of history navigation to apply ("restore",
 * "replace" or "advance")
 * @param options.historyChanged Specifies whether the browser history has
 * already been changed for this visit or not
 * @param options.referrer Specifies the referrer of this visit such that
 * navigations to the same page will not result in a new history entry.
 * @param options.snapshotHTML Cached snapshot to render
 * @param options.response Response of the specified location
 */
function visit(location, options) {
  session.visit(location, options);
}

/**
 * Connects a stream source to the main session.
 *
 * @param source Stream source to connect
 */
function connectStreamSource(source) {
  session.connectStreamSource(source);
}

/**
 * Disconnects a stream source from the main session.
 *
 * @param source Stream source to disconnect
 */
function disconnectStreamSource(source) {
  session.disconnectStreamSource(source);
}

/**
 * Renders a stream message to the main session by appending it to the
 * current document.
 *
 * @param message Message to render
 */
function renderStreamMessage(message) {
  session.renderStreamMessage(message);
}

/**
 * Removes all entries from the Turbo Drive page cache.
 * Call this when state has changed on the server that may affect cached pages.
 *
 * @deprecated since version 7.2.0 in favor of `Turbo.cache.clear()`
 */
function clearCache() {
  console.warn(
    "Please replace `Turbo.clearCache()` with `Turbo.cache.clear()`. The top-level function is deprecated and will be removed in a future version of Turbo.`"
  );
  session.clearCache();
}

/**
 * Sets the delay after which the progress bar will appear during navigation.
 *
 * The progress bar appears after 500ms by default.
 *
 * Note that this method has no effect when used with the iOS or Android
 * adapters.
 *
 * @param delay Time to delay in milliseconds
 */
function setProgressBarDelay(delay) {
  console.warn(
    "Please replace `Turbo.setProgressBarDelay(delay)` with `Turbo.config.drive.progressBarDelay = delay`. The top-level function is deprecated and will be removed in a future version of Turbo.`"
  );
  config.drive.progressBarDelay = delay;
}

function setConfirmMethod(confirmMethod) {
  console.warn(
    "Please replace `Turbo.setConfirmMethod(confirmMethod)` with `Turbo.config.forms.confirm = confirmMethod`. The top-level function is deprecated and will be removed in a future version of Turbo.`"
  );
  config.forms.confirm = confirmMethod;
}

function setFormMode(mode) {
  console.warn(
    "Please replace `Turbo.setFormMode(mode)` with `Turbo.config.forms.mode = mode`. The top-level function is deprecated and will be removed in a future version of Turbo.`"
  );
  config.forms.mode = mode;
}

var Turbo = /*#__PURE__*/Object.freeze({
  __proto__: null,
  navigator: navigator$1,
  session: session,
  cache: cache,
  PageRenderer: PageRenderer,
  PageSnapshot: PageSnapshot,
  FrameRenderer: FrameRenderer,
  fetch: fetchWithTurboHeaders,
  config: config,
  start: start,
  registerAdapter: registerAdapter,
  visit: visit,
  connectStreamSource: connectStreamSource,
  disconnectStreamSource: disconnectStreamSource,
  renderStreamMessage: renderStreamMessage,
  clearCache: clearCache,
  setProgressBarDelay: setProgressBarDelay,
  setConfirmMethod: setConfirmMethod,
  setFormMode: setFormMode
});

class TurboFrameMissingError extends Error {}

class FrameController {
  fetchResponseLoaded = (_fetchResponse) => Promise.resolve()
  #currentFetchRequest = null
  #resolveVisitPromise = () => {}
  #connected = false
  #hasBeenLoaded = false
  #ignoredAttributes = new Set()
  #shouldMorphFrame = false
  action = null

  constructor(element) {
    this.element = element;
    this.view = new FrameView(this, this.element);
    this.appearanceObserver = new AppearanceObserver(this, this.element);
    this.formLinkClickObserver = new FormLinkClickObserver(this, this.element);
    this.linkInterceptor = new LinkInterceptor(this, this.element);
    this.restorationIdentifier = uuid();
    this.formSubmitObserver = new FormSubmitObserver(this, this.element);
  }

  // Frame delegate

  connect() {
    if (!this.#connected) {
      this.#connected = true;
      if (this.loadingStyle == FrameLoadingStyle.lazy) {
        this.appearanceObserver.start();
      } else {
        this.#loadSourceURL();
      }
      this.formLinkClickObserver.start();
      this.linkInterceptor.start();
      this.formSubmitObserver.start();
    }
  }

  disconnect() {
    if (this.#connected) {
      this.#connected = false;
      this.appearanceObserver.stop();
      this.formLinkClickObserver.stop();
      this.linkInterceptor.stop();
      this.formSubmitObserver.stop();
    }
  }

  disabledChanged() {
    if (this.loadingStyle == FrameLoadingStyle.eager) {
      this.#loadSourceURL();
    }
  }

  sourceURLChanged() {
    if (this.#isIgnoringChangesTo("src")) return

    if (this.element.isConnected) {
      this.complete = false;
    }

    if (this.loadingStyle == FrameLoadingStyle.eager || this.#hasBeenLoaded) {
      this.#loadSourceURL();
    }
  }

  sourceURLReloaded() {
    const { refresh, src } = this.element;

    this.#shouldMorphFrame = src && refresh === "morph";

    this.element.removeAttribute("complete");
    this.element.src = null;
    this.element.src = src;
    return this.element.loaded
  }

  loadingStyleChanged() {
    if (this.loadingStyle == FrameLoadingStyle.lazy) {
      this.appearanceObserver.start();
    } else {
      this.appearanceObserver.stop();
      this.#loadSourceURL();
    }
  }

  async #loadSourceURL() {
    if (this.enabled && this.isActive && !this.complete && this.sourceURL) {
      this.element.loaded = this.#visit(expandURL(this.sourceURL));
      this.appearanceObserver.stop();
      await this.element.loaded;
      this.#hasBeenLoaded = true;
    }
  }

  async loadResponse(fetchResponse) {
    if (fetchResponse.redirected || (fetchResponse.succeeded && fetchResponse.isHTML)) {
      this.sourceURL = fetchResponse.response.url;
    }

    try {
      const html = await fetchResponse.responseHTML;
      if (html) {
        const document = parseHTMLDocument(html);
        const pageSnapshot = PageSnapshot.fromDocument(document);

        if (pageSnapshot.isVisitable) {
          await this.#loadFrameResponse(fetchResponse, document);
        } else {
          await this.#handleUnvisitableFrameResponse(fetchResponse);
        }
      }
    } finally {
      this.#shouldMorphFrame = false;
      this.fetchResponseLoaded = () => Promise.resolve();
    }
  }

  // Appearance observer delegate

  elementAppearedInViewport(element) {
    this.proposeVisitIfNavigatedWithAction(element, getVisitAction(element));
    this.#loadSourceURL();
  }

  // Form link click observer delegate

  willSubmitFormLinkToLocation(link) {
    return this.#shouldInterceptNavigation(link)
  }

  submittedFormLinkToLocation(link, _location, form) {
    const frame = this.#findFrameElement(link);
    if (frame) form.setAttribute("data-turbo-frame", frame.id);
  }

  // Link interceptor delegate

  shouldInterceptLinkClick(element, _location, _event) {
    return this.#shouldInterceptNavigation(element)
  }

  linkClickIntercepted(element, location) {
    this.#navigateFrame(element, location);
  }

  // Form submit observer delegate

  willSubmitForm(element, submitter) {
    return element.closest("turbo-frame") == this.element && this.#shouldInterceptNavigation(element, submitter)
  }

  formSubmitted(element, submitter) {
    if (this.formSubmission) {
      this.formSubmission.stop();
    }

    this.formSubmission = new FormSubmission(this, element, submitter);
    const { fetchRequest } = this.formSubmission;
    this.prepareRequest(fetchRequest);
    this.formSubmission.start();
  }

  // Fetch request delegate

  prepareRequest(request) {
    request.headers["Turbo-Frame"] = this.id;

    if (this.currentNavigationElement?.hasAttribute("data-turbo-stream")) {
      request.acceptResponseType(StreamMessage.contentType);
    }
  }

  requestStarted(_request) {
    markAsBusy(this.element);
  }

  requestPreventedHandlingResponse(_request, _response) {
    this.#resolveVisitPromise();
  }

  async requestSucceededWithResponse(request, response) {
    await this.loadResponse(response);
    this.#resolveVisitPromise();
  }

  async requestFailedWithResponse(request, response) {
    await this.loadResponse(response);
    this.#resolveVisitPromise();
  }

  requestErrored(request, error) {
    console.error(error);
    this.#resolveVisitPromise();
  }

  requestFinished(_request) {
    clearBusyState(this.element);
  }

  // Form submission delegate

  formSubmissionStarted({ formElement }) {
    markAsBusy(formElement, this.#findFrameElement(formElement));
  }

  formSubmissionSucceededWithResponse(formSubmission, response) {
    const frame = this.#findFrameElement(formSubmission.formElement, formSubmission.submitter);

    frame.delegate.proposeVisitIfNavigatedWithAction(frame, getVisitAction(formSubmission.submitter, formSubmission.formElement, frame));
    frame.delegate.loadResponse(response);

    if (!formSubmission.isSafe) {
      session.clearCache();
    }
  }

  formSubmissionFailedWithResponse(formSubmission, fetchResponse) {
    this.element.delegate.loadResponse(fetchResponse);
    session.clearCache();
  }

  formSubmissionErrored(formSubmission, error) {
    console.error(error);
  }

  formSubmissionFinished({ formElement }) {
    clearBusyState(formElement, this.#findFrameElement(formElement));
  }

  // View delegate

  allowsImmediateRender({ element: newFrame }, options) {
    const event = dispatch("turbo:before-frame-render", {
      target: this.element,
      detail: { newFrame, ...options },
      cancelable: true
    });

    const {
      defaultPrevented,
      detail: { render }
    } = event;

    if (this.view.renderer && render) {
      this.view.renderer.renderElement = render;
    }

    return !defaultPrevented
  }

  viewRenderedSnapshot(_snapshot, _isPreview, _renderMethod) {}

  preloadOnLoadLinksForView(element) {
    session.preloadOnLoadLinksForView(element);
  }

  viewInvalidated() {}

  // Frame renderer delegate

  willRenderFrame(currentElement, _newElement) {
    this.previousFrameElement = currentElement.cloneNode(true);
  }

  visitCachedSnapshot = ({ element }) => {
    const frame = element.querySelector("#" + this.element.id);

    if (frame && this.previousFrameElement) {
      frame.replaceChildren(...this.previousFrameElement.children);
    }

    delete this.previousFrameElement;
  }

  // Private

  async #loadFrameResponse(fetchResponse, document) {
    const newFrameElement = await this.extractForeignFrameElement(document.body);
    const rendererClass = this.#shouldMorphFrame ? MorphingFrameRenderer : FrameRenderer;

    if (newFrameElement) {
      const snapshot = new Snapshot(newFrameElement);
      const renderer = new rendererClass(this, this.view.snapshot, snapshot, false, false);
      if (this.view.renderPromise) await this.view.renderPromise;
      this.changeHistory();

      await this.view.render(renderer);
      this.complete = true;
      session.frameRendered(fetchResponse, this.element);
      session.frameLoaded(this.element);
      await this.fetchResponseLoaded(fetchResponse);
    } else if (this.#willHandleFrameMissingFromResponse(fetchResponse)) {
      this.#handleFrameMissingFromResponse(fetchResponse);
    }
  }

  async #visit(url) {
    const request = new FetchRequest(this, FetchMethod.get, url, new URLSearchParams(), this.element);

    this.#currentFetchRequest?.cancel();
    this.#currentFetchRequest = request;

    return new Promise((resolve) => {
      this.#resolveVisitPromise = () => {
        this.#resolveVisitPromise = () => {};
        this.#currentFetchRequest = null;
        resolve();
      };
      request.perform();
    })
  }

  #navigateFrame(element, url, submitter) {
    const frame = this.#findFrameElement(element, submitter);

    frame.delegate.proposeVisitIfNavigatedWithAction(frame, getVisitAction(submitter, element, frame));

    this.#withCurrentNavigationElement(element, () => {
      frame.src = url;
    });
  }

  proposeVisitIfNavigatedWithAction(frame, action = null) {
    this.action = action;

    if (this.action) {
      const pageSnapshot = PageSnapshot.fromElement(frame).clone();
      const { visitCachedSnapshot } = frame.delegate;

      frame.delegate.fetchResponseLoaded = async (fetchResponse) => {
        if (frame.src) {
          const { statusCode, redirected } = fetchResponse;
          const responseHTML = await fetchResponse.responseHTML;
          const response = { statusCode, redirected, responseHTML };
          const options = {
            response,
            visitCachedSnapshot,
            willRender: false,
            updateHistory: false,
            restorationIdentifier: this.restorationIdentifier,
            snapshot: pageSnapshot
          };

          if (this.action) options.action = this.action;

          session.visit(frame.src, options);
        }
      };
    }
  }

  changeHistory() {
    if (this.action) {
      const method = getHistoryMethodForAction(this.action);
      session.history.update(method, expandURL(this.element.src || ""), this.restorationIdentifier);
    }
  }

  async #handleUnvisitableFrameResponse(fetchResponse) {
    console.warn(
      `The response (${fetchResponse.statusCode}) from <turbo-frame id="${this.element.id}"> is performing a full page visit due to turbo-visit-control.`
    );

    await this.#visitResponse(fetchResponse.response);
  }

  #willHandleFrameMissingFromResponse(fetchResponse) {
    this.element.setAttribute("complete", "");

    const response = fetchResponse.response;
    const visit = async (url, options) => {
      if (url instanceof Response) {
        this.#visitResponse(url);
      } else {
        session.visit(url, options);
      }
    };

    const event = dispatch("turbo:frame-missing", {
      target: this.element,
      detail: { response, visit },
      cancelable: true
    });

    return !event.defaultPrevented
  }

  #handleFrameMissingFromResponse(fetchResponse) {
    this.view.missing();
    this.#throwFrameMissingError(fetchResponse);
  }

  #throwFrameMissingError(fetchResponse) {
    const message = `The response (${fetchResponse.statusCode}) did not contain the expected <turbo-frame id="${this.element.id}"> and will be ignored. To perform a full page visit instead, set turbo-visit-control to reload.`;
    throw new TurboFrameMissingError(message)
  }

  async #visitResponse(response) {
    const wrapped = new FetchResponse(response);
    const responseHTML = await wrapped.responseHTML;
    const { location, redirected, statusCode } = wrapped;

    return session.visit(location, { response: { redirected, statusCode, responseHTML } })
  }

  #findFrameElement(element, submitter) {
    const id = getAttribute("data-turbo-frame", submitter, element) || this.element.getAttribute("target");
    return getFrameElementById(id) ?? this.element
  }

  async extractForeignFrameElement(container) {
    let element;
    const id = CSS.escape(this.id);

    try {
      element = activateElement(container.querySelector(`turbo-frame#${id}`), this.sourceURL);
      if (element) {
        return element
      }

      element = activateElement(container.querySelector(`turbo-frame[src][recurse~=${id}]`), this.sourceURL);
      if (element) {
        await element.loaded;
        return await this.extractForeignFrameElement(element)
      }
    } catch (error) {
      console.error(error);
      return new FrameElement()
    }

    return null
  }

  #formActionIsVisitable(form, submitter) {
    const action = getAction$1(form, submitter);

    return locationIsVisitable(expandURL(action), this.rootLocation)
  }

  #shouldInterceptNavigation(element, submitter) {
    const id = getAttribute("data-turbo-frame", submitter, element) || this.element.getAttribute("target");

    if (element instanceof HTMLFormElement && !this.#formActionIsVisitable(element, submitter)) {
      return false
    }

    if (!this.enabled || id == "_top") {
      return false
    }

    if (id) {
      const frameElement = getFrameElementById(id);
      if (frameElement) {
        return !frameElement.disabled
      }
    }

    if (!session.elementIsNavigatable(element)) {
      return false
    }

    if (submitter && !session.elementIsNavigatable(submitter)) {
      return false
    }

    return true
  }

  // Computed properties

  get id() {
    return this.element.id
  }

  get enabled() {
    return !this.element.disabled
  }

  get sourceURL() {
    if (this.element.src) {
      return this.element.src
    }
  }

  set sourceURL(sourceURL) {
    this.#ignoringChangesToAttribute("src", () => {
      this.element.src = sourceURL ?? null;
    });
  }

  get loadingStyle() {
    return this.element.loading
  }

  get isLoading() {
    return this.formSubmission !== undefined || this.#resolveVisitPromise() !== undefined
  }

  get complete() {
    return this.element.hasAttribute("complete")
  }

  set complete(value) {
    if (value) {
      this.element.setAttribute("complete", "");
    } else {
      this.element.removeAttribute("complete");
    }
  }

  get isActive() {
    return this.element.isActive && this.#connected
  }

  get rootLocation() {
    const meta = this.element.ownerDocument.querySelector(`meta[name="turbo-root"]`);
    const root = meta?.content ?? "/";
    return expandURL(root)
  }

  #isIgnoringChangesTo(attributeName) {
    return this.#ignoredAttributes.has(attributeName)
  }

  #ignoringChangesToAttribute(attributeName, callback) {
    this.#ignoredAttributes.add(attributeName);
    callback();
    this.#ignoredAttributes.delete(attributeName);
  }

  #withCurrentNavigationElement(element, callback) {
    this.currentNavigationElement = element;
    callback();
    delete this.currentNavigationElement;
  }
}

function getFrameElementById(id) {
  if (id != null) {
    const element = document.getElementById(id);
    if (element instanceof FrameElement) {
      return element
    }
  }
}

function activateElement(element, currentURL) {
  if (element) {
    const src = element.getAttribute("src");
    if (src != null && currentURL != null && urlsAreEqual(src, currentURL)) {
      throw new Error(`Matching <turbo-frame id="${element.id}"> element has a source URL which references itself`)
    }
    if (element.ownerDocument !== document) {
      element = document.importNode(element, true);
    }

    if (element instanceof FrameElement) {
      element.connectedCallback();
      element.disconnectedCallback();
      return element
    }
  }
}

const StreamActions = {
  after() {
    this.targetElements.forEach((e) => e.parentElement?.insertBefore(this.templateContent, e.nextSibling));
  },

  append() {
    this.removeDuplicateTargetChildren();
    this.targetElements.forEach((e) => e.append(this.templateContent));
  },

  before() {
    this.targetElements.forEach((e) => e.parentElement?.insertBefore(this.templateContent, e));
  },

  prepend() {
    this.removeDuplicateTargetChildren();
    this.targetElements.forEach((e) => e.prepend(this.templateContent));
  },

  remove() {
    this.targetElements.forEach((e) => e.remove());
  },

  replace() {
    const method = this.getAttribute("method");

    this.targetElements.forEach((targetElement) => {
      if (method === "morph") {
        morphElements(targetElement, this.templateContent);
      } else {
        targetElement.replaceWith(this.templateContent);
      }
    });
  },

  update() {
    const method = this.getAttribute("method");

    this.targetElements.forEach((targetElement) => {
      if (method === "morph") {
        morphChildren(targetElement, this.templateContent);
      } else {
        targetElement.innerHTML = "";
        targetElement.append(this.templateContent);
      }
    });
  },

  refresh() {
    session.refresh(this.baseURI, this.requestId);
  }
};

// <turbo-stream action=replace target=id><template>...

/**
 * Renders updates to the page from a stream of messages.
 *
 * Using the `action` attribute, this can be configured one of eight ways:
 *
 * - `after` - inserts the result after the target
 * - `append` - appends the result to the target
 * - `before` - inserts the result before the target
 * - `prepend` - prepends the result to the target
 * - `refresh` - initiates a page refresh
 * - `remove` - removes the target
 * - `replace` - replaces the outer HTML of the target
 * - `update` - replaces the inner HTML of the target
 *
 * @customElement turbo-stream
 * @example
 *   <turbo-stream action="append" target="dom_id">
 *     <template>
 *       Content to append to target designated with the dom_id.
 *     </template>
 *   </turbo-stream>
 */
class StreamElement extends HTMLElement {
  static async renderElement(newElement) {
    await newElement.performAction();
  }

  async connectedCallback() {
    try {
      await this.render();
    } catch (error) {
      console.error(error);
    } finally {
      this.disconnect();
    }
  }

  async render() {
    return (this.renderPromise ??= (async () => {
      const event = this.beforeRenderEvent;

      if (this.dispatchEvent(event)) {
        await nextRepaint();
        await event.detail.render(this);
      }
    })())
  }

  disconnect() {
    try {
      this.remove();
      // eslint-disable-next-line no-empty
    } catch {}
  }

  /**
   * Removes duplicate children (by ID)
   */
  removeDuplicateTargetChildren() {
    this.duplicateChildren.forEach((c) => c.remove());
  }

  /**
   * Gets the list of duplicate children (i.e. those with the same ID)
   */
  get duplicateChildren() {
    const existingChildren = this.targetElements.flatMap((e) => [...e.children]).filter((c) => !!c.getAttribute("id"));
    const newChildrenIds = [...(this.templateContent?.children || [])].filter((c) => !!c.getAttribute("id")).map((c) => c.getAttribute("id"));

    return existingChildren.filter((c) => newChildrenIds.includes(c.getAttribute("id")))
  }

  /**
   * Gets the action function to be performed.
   */
  get performAction() {
    if (this.action) {
      const actionFunction = StreamActions[this.action];
      if (actionFunction) {
        return actionFunction
      }
      this.#raise("unknown action");
    }
    this.#raise("action attribute is missing");
  }

  /**
   * Gets the target elements which the template will be rendered to.
   */
  get targetElements() {
    if (this.target) {
      return this.targetElementsById
    } else if (this.targets) {
      return this.targetElementsByQuery
    } else {
      this.#raise("target or targets attribute is missing");
    }
  }

  /**
   * Gets the contents of the main `<template>`.
   */
  get templateContent() {
    return this.templateElement.content.cloneNode(true)
  }

  /**
   * Gets the main `<template>` used for rendering
   */
  get templateElement() {
    if (this.firstElementChild === null) {
      const template = this.ownerDocument.createElement("template");
      this.appendChild(template);
      return template
    } else if (this.firstElementChild instanceof HTMLTemplateElement) {
      return this.firstElementChild
    }
    this.#raise("first child element must be a <template> element");
  }

  /**
   * Gets the current action.
   */
  get action() {
    return this.getAttribute("action")
  }

  /**
   * Gets the current target (an element ID) to which the result will
   * be rendered.
   */
  get target() {
    return this.getAttribute("target")
  }

  /**
   * Gets the current "targets" selector (a CSS selector)
   */
  get targets() {
    return this.getAttribute("targets")
  }

  /**
   * Reads the request-id attribute
   */
  get requestId() {
    return this.getAttribute("request-id")
  }

  #raise(message) {
    throw new Error(`${this.description}: ${message}`)
  }

  get description() {
    return (this.outerHTML.match(/<[^>]+>/) ?? [])[0] ?? "<turbo-stream>"
  }

  get beforeRenderEvent() {
    return new CustomEvent("turbo:before-stream-render", {
      bubbles: true,
      cancelable: true,
      detail: { newStream: this, render: StreamElement.renderElement }
    })
  }

  get targetElementsById() {
    const element = this.ownerDocument?.getElementById(this.target);

    if (element !== null) {
      return [element]
    } else {
      return []
    }
  }

  get targetElementsByQuery() {
    const elements = this.ownerDocument?.querySelectorAll(this.targets);

    if (elements.length !== 0) {
      return Array.prototype.slice.call(elements)
    } else {
      return []
    }
  }
}

class StreamSourceElement extends HTMLElement {
  streamSource = null

  connectedCallback() {
    this.streamSource = this.src.match(/^ws{1,2}:/) ? new WebSocket(this.src) : new EventSource(this.src);

    connectStreamSource(this.streamSource);
  }

  disconnectedCallback() {
    if (this.streamSource) {
      this.streamSource.close();

      disconnectStreamSource(this.streamSource);
    }
  }

  get src() {
    return this.getAttribute("src") || ""
  }
}

FrameElement.delegateConstructor = FrameController;

if (customElements.get("turbo-frame") === undefined) {
  customElements.define("turbo-frame", FrameElement);
}

if (customElements.get("turbo-stream") === undefined) {
  customElements.define("turbo-stream", StreamElement);
}

if (customElements.get("turbo-stream-source") === undefined) {
  customElements.define("turbo-stream-source", StreamSourceElement);
}

(() => {
  let element = document.currentScript;
  if (!element) return
  if (element.hasAttribute("data-turbo-suppress-warning")) return

  element = element.parentElement;
  while (element) {
    if (element == document.body) {
      return console.warn(
        unindent`
        You are loading Turbo from a <script> element inside the <body> element. This is probably not what you meant to do!

        Load your application’s JavaScript bundle inside the <head> element instead. <script> elements in <body> are evaluated with each page change.

        For more information, see: https://turbo.hotwired.dev/handbook/building#working-with-script-elements

        ——
        Suppress this warning by adding a "data-turbo-suppress-warning" attribute to: %s
      `,
        element.outerHTML
      )
    }

    element = element.parentElement;
  }
})();

window.Turbo = { ...Turbo, StreamActions };
start();

export { FetchEnctype, FetchMethod, FetchRequest, FetchResponse, FrameElement, FrameLoadingStyle, FrameRenderer, PageRenderer, PageSnapshot, StreamActions, StreamElement, StreamSourceElement, cache, clearCache, config, connectStreamSource, disconnectStreamSource, fetchWithTurboHeaders as fetch, fetchEnctypeFromString, fetchMethodFromString, isSafe, navigator$1 as navigator, registerAdapter, renderStreamMessage, session, setConfirmMethod, setFormMode, setProgressBarDelay, start, visit };
