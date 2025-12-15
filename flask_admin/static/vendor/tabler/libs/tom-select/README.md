<p align="center">
<h1 align="center">Tom Select</h1>
</p>

<p align="center">
<a href="https://github.com/orchidjs/tom-select" class="m-1 d-inline-block"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/orchidjs/tom-select?label=GitHub%20stars&color=007ec6"></a>
<a href="https://www.jsdelivr.com/package/npm/tom-select" class="m-1 d-inline-block"><img alt="jsDelivr hits (npm)" src="https://img.shields.io/jsdelivr/npm/hm/tom-select?label=jsDelivr%20hits&color=007ec6"></a>
<a href="https://www.npmjs.com/package/tom-select" class="m-1 d-inline-block"><img alt="npmjs.org" src="https://img.shields.io/npm/v/tom-select.svg?color=007ec6"></a>
<a href="https://github.com/orchidjs/tom-select/actions/workflows/tests.yml" class="m-1 d-inline-block"><img alt="tests" src="https://github.com/orchidjs/tom-select/actions/workflows/tests.yml/badge.svg"></a>
<a href="https://coveralls.io/github/orchidjs/tom-select" class="m-1 d-inline-block"><img alt="Coveralls Coverage" src="https://img.shields.io/coveralls/github/orchidjs/tom-select?color=4c1"></a>
<a href="https://github.com/orchidjs/tom-select/issues" class="m-1 d-inline-block"><img alt="GitHub Issues" src="https://img.shields.io/github/issues/orchidjs/tom-select"></a>
</p>

Tom Select is a dynamic, framework agnostic, and lightweight (~16kb gzipped) &lt;select&gt; UI control.
With autocomplete and native-feeling keyboard navigation, it's useful for tagging, contact lists, country selectors, and so on.
Tom Select was forked from [selectize.js](https://tom-select.js.org/docs/selectize.js/) with the goal of modernizing the code base, decoupling from jQuery, and expanding functionality.


### Features

- **Smart Option Searching / Ranking**<br>Options are efficiently scored and sorted on-the-fly (using [sifter](https://github.com/orchidjs/sifter.js)). Want to search an item's title *and* description? No problem.
- **Caret between items**<br>Order matters sometimes. With the <a href="https://tom-select.js.org/plugins/caret-position">Caret Position Plugin</a>, you can use the <kbd>&larr;</kbd> and <kbd>&rarr;</kbd> arrow keys to move between selected items</li>
- **Select &amp; delete multiple items at once**<br>Hold down <kbd>command</kbd> on Mac or <kbd>ctrl</kbd> on Windows to select more than one item to delete.
- **Díåcritîçs supported**<br>Great for international environments.
- **Item creation**<br>Allow users to create items on the fly (async saving is supported; the control locks until the callback is fired).
- **Remote data loading**<br>For when you have thousands of options and want them provided by the server as the user types.
- **Extensible**<br> [Plugin API](https://tom-select.js.org/docs/plugins/) for developing custom features (uses [microplugin](https://github.com/brianreavis/microplugin.js)).
- **Accessible**, **Touch Support**, **Clean API**, ...

## Usage

```html
<input id="tom-select-it" />
<link rel="stylesheet" href="/css/tom-select.default.css">
<script src="/js/tom-select.complete.js"></script>
<script>
var config = {};
new TomSelect('#tom-select-it',config);
</script>
```

Available configuration settings are [documented here](https://tom-select.js.org/docs)


## Installation

All pre-built files needed to use Tom Select can be found in the "dist" folder via any of these sources:

<table class="table mt-5">
	<tr>
		<th class="border-top-0">Source</th>
		<th class="border-top-0"></th>
	</tr>
	<tr>
		<td><a href="https://www.jsdelivr.com/package/npm/tom-select?path=dist">jsDelivr</a></td>
		<td>
		The fastest way to add Tom Select into your project is to just include the js and css from jsDelivr.
<pre>
&lt;link href="https://cdn.jsdelivr.net/npm/tom-select/dist/css/tom-select.css" rel="stylesheet"&gt;
&lt;script src="https://cdn.jsdelivr.net/npm/tom-select/dist/js/tom-select.complete.min.js"&gt;&lt;/script&gt;
</pre>
		</td>
	</tr>
	<tr>
		<td><a href="https://www.npmjs.com/package/tom-select">npm</a></td>
		<td><pre><code>npm i tom-select</code></pre>
		<div><a href="https://tom-select.js.org/docs/contribute/">Additional CLI usage</a></div>
		</td>
	</tr>
	<tr>
		<td><a href="https://github.com/orchidjs/tom-select/">GitHub</a></td>
		<td>Clone or <a href="https://github.com/orchidjs/tom-select/archive/master.zip">download</a> the full repo.
		Use <code>npm run build</code> <a href="/docs/contribute">and other commands</a> to build from source, test and start the doc server.
		</td>
	</tr>
</table>


## Files
- [tom-select.complete.js](https://cdn.jsdelivr.net/npm/tom-select/dist/js/tom-select.complete.js) — Includes dependencies and plugins
- [tom-select.base.js](https://cdn.jsdelivr.net/npm/tom-select/dist/js/tom-select.base.js) — Does not include any plugins
- [CSS](https://www.jsdelivr.com/package/npm/tom-select?path=dist%2Fcss) — Compiled themes
- [SCSS](https://www.jsdelivr.com/package/npm/tom-select?path=dist%2Fscss) — Uncompiled theme sources


## Sponsors
<p>
Many thanks to all our sponsors who help make development possible. <a href="https://opencollective.com/tom-select">Become a sponsor</a>.
</p>
<p>
<a href="https://opencollective.com/tom-select/sponsor/0/website"><img src="https://opencollective.com/tom-select/sponsor/0/avatar.svg" alt="Trust My Paper Logo"></a>
<a href="https://opencollective.com/tom-select/sponsor/2/website"><img src="https://opencollective.com/tom-select/sponsor/2/avatar.svg" alt="WiseEssays.com"></a>
</p>
<br>



## License

Copyright &copy; 2013–2023 [Contributors](https://github.com/orchidjs/tom-select/graphs/contributors)

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
