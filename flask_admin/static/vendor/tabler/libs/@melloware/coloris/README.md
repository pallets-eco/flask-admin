[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![npm version](https://badge.fury.io/js/@melloware%2Fcoloris.svg)](https://badge.fury.io/js/@melloware%2Fcoloris)
![Maven](https://img.shields.io/maven-central/v/org.webjars.npm/melloware__coloris)
![NPM Downloads](https://img.shields.io/npm/dm/@melloware%2Fcoloris?color=purple)
[![@melloware/coloris](https://snyk.io/advisor/npm-package/@melloware/coloris/badge.svg)](https://snyk.io/advisor/npm-package/@melloware/coloris)

# Coloris NPM

A lightweight and elegant JavaScript color picker written in vanilla ES6.  
Convert any text input field into a color field.

Forked from https://github.com/mdbassit/Coloris so we could provide TypeScript and NPM support. Head over to Momo Bassit's original repo for user documentation.

## Bundlers

See [the tests directory](./test-npm) for examples with different bundlers.

## NPM

You can download the color picker from NPM:

```bash
# using NPM
npm install @melloware/coloris
# using Yarn
yarn add @melloware/coloris
```

And then use it within a module environment, e.g. with browserify, rollup,
webpack etc. In this case, you must initialize the color picker before its
first use (which has several side-effects such as adding DOM elements):

```javascript
import "@melloware/coloris/dist/coloris.css";
import Coloris from "@melloware/coloris";
Coloris.init();
Coloris({el: "#coloris"});
```

Since default exports can be tricky, if this does not work with your bundler, use named imports instead:

```javascript
import "@melloware/coloris/dist/coloris.css";
import { coloris, init } from "@melloware/coloris";
init();
coloris({el: "#coloris"});
```

## AMD

The color picker also works with AMD / require.js:

```javascript
requirejs(['path/to/coloris'], function (Coloris) {
  Coloris.init();
  Coloris({
    el: "#coloris",
  });
});
```

## Java / Maven

The colorpicker can also be downloaded from [Maven Central](https://central.sonatype.dev/search?q=coloris)
as a Java JAR for use in Java web applicatons:

```xml
<dependency>
   <groupId>org.webjars.npm</groupId>
   <artifactId>melloware__coloris</artifactId>
   <version>...</version>
</dependency>
```

## TypeScript

This package includes TypeScript declarations. When you use it in a module
environment, just import it:

```typescript
import "@melloware/coloris/dist/coloris.css";
import * as Color from "@melloware/coloris";

Coloris.init();
Coloris.coloris({el: "#coloris"});
Coloris.close();
```

If you have `allowSyntheticDefaultImports` enabled, you could also use:

```typescript
import "@melloware/coloris/dist/coloris.css";
import Coloris from "@melloware/coloris";

Coloris.init();
Coloris({el: "#coloris"});
Coloris.close();
```

If you wish to write a global script file, use a triple slash reference:

```typescript
/// <reference types="@melloware/coloris" />
Coloris({
    el: "#coloris",
});
```

## Building from source

First of all, again, please note that this is a fork of the original repo!

Clone the git repo:
```bash
git clone git@github.com:melloware/coloris-npm
```

Enter the Coloris directory and install the development dependencies:
```bash
cd coloris-npm && npm install
```

Run the build script:
```bash
npm run build
```
The built version will be in the `dist` directory in both minified and full copies.

Alternatively, you can start a gulp watch task to automatically build when the source files are modified:
```bash
npm run start
```

## Publishing

Adjust the version in the `package.json` if necessary, then

```bash
npm login
# This will run npm run build automatically
npm publish --access public
```

Then upload code to github, create tag & release.

## License

Copyright (c) 2021 Momo Bassit.
**Coloris** is licensed under the [MIT license](https://github.com/melloware/coloris-npm/blob/main/LICENSE).
