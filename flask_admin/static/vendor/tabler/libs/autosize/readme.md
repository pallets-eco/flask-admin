## Summary

Autosize is a small, stand-alone script to automatically adjust textarea height to fit text.

#### Demo

Full documentation and a demo can be found at [jacklmoore.com/autosize](http://jacklmoore.com/autosize)

#### Install via NPM
```bash
npm install autosize
```

#### Usage

The autosize function accepts a single textarea element, or an array or array-like object (such as a NodeList or jQuery collection) of textarea elements.

```javascript
// from a NodeList
autosize(document.querySelectorAll('textarea'));

// from a single Node
autosize(document.querySelector('textarea'));

// from a jQuery collection
autosize($('textarea'));
```

Released under the [MIT License](http://www.opensource.org/licenses/mit-license.php)
