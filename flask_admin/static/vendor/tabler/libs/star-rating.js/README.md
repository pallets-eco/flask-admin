# star-rating.js

[![npm version](https://badge.fury.io/js/star-rating.js.svg)](https://badge.fury.io/js/star-rating.js)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/pryley/star-rating.js/blob/master/LICENSE)

A zero-dependency library that transforms a select with numerical-range values (i.e. 1-5) into a dynamic star rating element.

For production, use the files from the `dist/` folder.

## Installation

```js
npm i star-rating.js
```

## Usage

Your SELECT option fields must have numerical values.

```html
<link href="css/star-rating.css" rel="stylesheet">

<select class="star-rating">
    <option value="">Select a rating</option>
    <option value="5">Excellent</option>
    <option value="4">Very Good</option>
    <option value="3">Average</option>
    <option value="2">Poor</option>
    <option value="1">Terrible</option>
</select>

<script src="js/star-rating.min.js"></script>
<script>
    var stars = new StarRating('.star-rating');
</script>
```

To rebuild all star rating controls (e.g. after form fields have changed with ajax):

```js
stars.rebuild();
```

To fully remove all star rating controls, including all attached Event Listeners:

```js
stars.destroy();
```

## Options

Here are the default options

```js
{
    classNames: {
        active: 'gl-active',
        base: 'gl-star-rating',
        selected: 'gl-selected',
    },
    clearable: true,
    maxStars: 10,
    prebuilt: false,
    stars: null,
    tooltip: 'Select a Rating',
}
```

### classNames.active

Type: `String`

The classname to use for the active (hovered or value <= of the selected value) state of a star.

### classNames.base

Type: `String`

The classname to use for the base element that wraps the star rating.

### classNames.selected

Type: `String`

The classname to use for the selected state of a star.

### clearable

Type: `Boolean`

Whether or not the star rating can be cleared by clicking on an already selected star.

### maxStars:

Type: `Integer`

The maximum number of stars allowed in a star rating.

### prebuilt:

Type: `Boolean`

If this option is `true`, only the event listeners will be added and no DOM manipulation will take place. You will need to ensure that the DOM looks something like this:

```html
<span class="gl-star-rating">
    <select>
        <option value="">Select a rating</option>
        <option value="5">5 Stars</option>
        <option value="4">4 Stars</option>
        <option value="3">3 Stars</option>
        <option value="2">2 Stars</option>
        <option value="1">1 Star</option>
    </select>
    <span class="gl-star-rating--stars">
        <span data-value="1"></span>
        <span data-value="2"></span>
        <span data-value="3"></span>
        <span data-value="4"></span>
        <span data-value="5"></span>
    </span>
</span>
```

### stars:

Type: `Function`

This can be used to add a SVG image to each star value instead of using the background images in the CSS.

### tooltip:

Type: `String|False`

The placeholder text for the rating tooltip, or `false` to disable the tooltip.

## Build

```sh
npm install
npm run build
```

The compiled files will be saved in the `dist/` folder.

**Note:** If importing this into your project, you will need to add [@babel/plugin-proposal-optional-chaining](https://www.npmjs.com/package/@babel/plugin-proposal-optional-chaining) to your babel config.

### Style Customization

Following are the default CSS variable values for Star Rating:

```css
:root {
    --gl-star-color: #fdd835;                     /* if using SVG images */
    --gl-star-color-inactive: #dcdce6;            /* if using SVG images */
    --gl-star-empty: url(../img/star-empty.svg);  /* if using background images */
    --gl-star-full: url(../img/star-full.svg);    /* if using background images */
    --gl-star-size: 24px;
    --gl-tooltip-background: rgba(17,17,17, .9);
    --gl-tooltip-border-radius: 4px;
    --gl-tooltip-color: #fff;
    --gl-tooltip-font-size: 0.875rem;
    --gl-tooltip-font-weight: 400;
    --gl-tooltip-line-height: 1;
    --gl-tooltip-margin: 12px;
    --gl-tooltip-padding: .5em 1em;
}
```

To override any values with your own, simply import the CSS file into your project, then enter new CSS variable values after the import.

```css
@import 'star-rating';

:root {
    --gl-star-size: 32px;
}
```

### How to change CSS style priority

Sometimes an existing stylesheet rules will override the default CSS styles for Star Ratings. To solve this problem, you can use the [postcss-selector-namespace](https://github.com/topaxi/postcss-selector-namespace) plugin in your PostCSS build on the CSS file before combining with your main stylesheet. This namespace value should be a high priority/specificity property such as an id attribute or similar.

## Compatibility

- All modern browsers

If you need to use the Star Rating library in a unsupported browser (i.e. Internet Explorer), use the [Polyfill service](https://polyfill.io).

## Tips

1. If your star rating has a label field, add the `pointer-events: none;` style to it to prevent the focus event from triggering on touch devices.

## Contributing

All changes should be committed to the files in `src/`.

## Changelog

`v4.3.1 - [2024-04-30]`

- Fixed edge-case bug with prebuilt config option
- Fixed tooltip CSS

`v4.3.0 - [2022-08-05]`

- Added module and exports fields to package.json
- Fixed left/right keydown events
- Optimised CSS

`v4.2.5 - [2022-07-30]`

- Fixed active index when stars have gaps between them

`v4.2.3 - [2022-06-03]`

- Disabled pointer-events on tooltip

`v4.2.2 - [2022-03-30]`

- Fixed rebuild function

`v4.2.0 - [2022-03-24]`

- Perform a complete teardown on destroy allowing a rebuild from the selector in a new DOM

`v4.1.5 - [2021-09-25]`

- Added a data-rating attribute on the widget which holds the transient/selected rating

`v4.1.4 - [2021-05-29]`

- Fixed selected index on reset

`v4.1.3 - [2021-04-09]`

- Fixed focus state with pointer events

`v4.1.2 - [2021-02-24]`

- Fixed error when initialising more than once

`v4.1.1 - [2021-02-14]`

- Removed v3 compatibility mode when using the `prebuilt` option

`v4.1.0 - [2021-02-13]`

- Added the `prebuilt` option

`v4.0.6 - [2021-02-05]`

- Remove the focus from being triggered entirely as it caused to many problems on ios and I don't have time to fix it

`v4.0.5 - [2021-02-03]`

- Fixed an invalid change event from being triggered by the reset event

`v4.0.4 - [2021-02-02]`

- Export a babel-transpiled commonjs module

`v4.0.3 - [2021-01-29]`

- Fixed rollup config to support optional-chaining in babel

`v4.0.2 - [2021-01-23]`

- Fixed compatibility mode (when `'function' !== typeof options.stars`)
- Removed trigger of change event after init as this could trigger unwanted validation

`v4.0.1 - [2021-01-22]`

- Fixed the change event for disabled SELECT elements

`v4.0.0 - [2021-01-22]`

- Code has been rewritten as an ES6 module and optimised
- Added requestAnimationFrame to the pointer move events
- Added the `stars` option which allows you to use custom SVG images for each star
- Replaced the `classname` option with the `classNames` option
- Replaced the `initialText` with the `tooltip` option
- Replaced gulp with rollup for the build
- Replaced SASS with PostCSS

`v3.4.0 - [2020-10-18]`

- Specify passive:false on event listeners to suppress Chrome warnings

`v3.2.0 - [2020-07-13]`
- Cleanup stale DOM if needed before initializing

`v3.1.8 - [2020-06-29]`
- Fixed clearable option
- Fixed events on disabled SELECT

`v3.1.5 - [2019-11-01]`
- Added ability to use a NodeList as a selector

`v3.1.4 - [2019-01-28]`
- Updated package URL

`v3.1.3 - [2019-01-27]`
- Fixed issue when used outside of a FORM

`v3.1.2 - [2019-01-07]`
- Fixed issue that allowed multiple star-rating transformations on the same SELECT element

`v3.1.1 - [2018-07-27]`
- Provided an un-minified CSS file in /dist
- Removed the change event trigger from the reset event

`v3.1.0 - [2018-07-24]`
- Changed the `star-filled` SCSS map option to `star-full`
- Changed the `star-empty`, `star-full`, and `star-half` SCSS map options to `url(...)`. This allows one to use `none` as the value of `background-image`.

`v3.0.0 - [2018-07-24]`
- Dropped support for Internet Explorer (use polyfill.io, specifically: Element.prototype.closest, Element.prototype.dataset, Event)
- Removed the `onClick` option (listen for the `change` event instead)

`v2.3.1 - [2018-07-22]`
- CSS improvements

`v2.3.0 - [2018-07-20]`
- Added a `$star-rating[parent]` SCSS option

`v2.2.2 - [2018-07-16]`
- Fixed IE 11+ compatibility

`v2.2.1 - [2018-07-13]`
- Fixed touch events on Android devices

`v2.2.0 - [2018-07-09]`

- Added a `classname` option
- Added a `$star-rating[base-classname]` SCSS option
- Added touch events
- Fixed detection of an unset option value
- Optimised the minified output
- Removed unused code

`v2.1.1 - [2018-05-25]`

- Fixed jshint warnings

`v2.1.0 - [2018-05-11]`

- Added support for the keyboard
- Fixed accessibility support
- Fixed RTL support

`v2.0.0 - [2018-05-02]`

- Major rewrite of library
- Added support for loading as a module
- Added support for RTL
- Removed jQuery plugin
- Removed IE9 support

`v1.3.3 - [2017-04-11]`

- Fixed race conditions preventing correct element.outerWidth calculation

`v1.3.1 - [2016-12-22]`

- Fixed checking existence of parent form element before attaching an event to it
- Fixed mousemove event not correctly unattaching

`v1.3.0 - [2016-10-10]`

- Changed `clickFn` to `onClick` which now passes the select HTMLElement as the argument

`v1.2.2 - [2016-10-10]`

- Fixed "reset" event when the `clearable` option is false

`v1.2.1 - [2016-10-09]`

- Fixed resetting the star-rating when a form "reset" event is triggered

`v1.2.0 - [2016-10-09]`

- Removed dependencies
- Fixed HTML5 “required” attribute validation

`v1.1.0 - [2016-10-06]`

- Added `showText` option

`v1.0.1 - [2016-10-06]`

- Fixed using the wrong left offset

`v1.0.0 - [2016-10-06]`

- Initial release

## License

[MIT](/LICENSE)
