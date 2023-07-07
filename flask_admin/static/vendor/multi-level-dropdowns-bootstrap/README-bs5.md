# Bootstrap 5 Multiple Level Dropdown.

For Bootstrap 4, please visit [Bootstrap 4 Multiple Level Dropdown](https://github.com/dallaslu/bootstrap-4-multi-level-dropdown)

Using official HTML without adding extra CSS styles and classes, it's just like native support. 

All things listed in https://v5.getbootstrap.com/docs/5.0/components/dropdowns/ are not effected. You can use css classes and js methods/events/options freely.

Dropdown of bootstrap can be easily changed to infinite level. It's a pity that they didn't do it.

## Usage

### Base
Just add js after bootstrap js files:

```html
<script src="https://raw.githubusercontent.com/dallaslu/bootstrap-5-multi-level-dropdown/master/bootstrap5-dropdown-ml-hack.js"></script>
```
#### Base Example
```html
...
<div class="dropdown mt-3">
    <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        Dropdown button
    </button>
    <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
        <a class="dropdown-item" href="#">Action</a>
        <!-- level #2 -->
        <div class="dropdown dropend">
            <a class="dropdown-item dropdown-toggle" href="#" id="dropdown-layouts" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Layouts</a>
            <div class="dropdown-menu" aria-labelledby="dropdown-layouts">
                <a class="dropdown-item" href="#">Basic</a>
                <a class="dropdown-item" href="#">Compact Aside</a>
                <div class="dropdown-divider"></div>
                <!-- level #3 -->
                <div class="dropdown dropend">
                    <a class="dropdown-item dropdown-toggle" href="#" id="dropdown-layouts" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Custom</a>
                    <div class="dropdown-menu" aria-labelledby="dropdown-layouts">
                        <a class="dropdown-item" href="#">Fullscreen</a>
                        <a class="dropdown-item" href="#">Empty</a>
                        <div class="dropdown-divider"></div>
                        <a class="dropdown-item" href="#">Magic</a>
                    </div>
                </div>
                <!-- /level #3 -->
            </div>
        </div>
        <!-- /level #2 -->
        <a class="dropdown-item" href="#">Something else here</a>
    </div>
</div>
...
<script src="https://raw.githubusercontent.com/dallaslu/bootstrap-5-multi-level-dropdown/master/bootstrap5-dropdown-ml-hack.js"></script>
```
### Hover
If your want a hover tigger, just add class and some custom styles to reduce spacing to avoid triggering mouseleave.
```css
.dropdown-hover-all .dropdown-menu, .dropdown-hover > .dropdown-menu.dropend { margin-left:-1px !important }
```
or:
```html
<link rel="stylesheet" href="https://raw.githubusercontent.com/dallaslu/bootstrap-5-multi-level-dropdown/master/bootstrap5-dropdown-ml-hack-hover.css" />
```
Then, add classes for dropdown elements;
```html
<div class="dropdown-hover-all">
  <!-- .dropdown elements -->
</div>
<div class="dropdown dropdown-hover">
  <!-- toggle and menu elements -->
</div>
```
#### Hover Example
```html
<link rel="stylesheet" href="https://raw.githubusercontent.com/dallaslu/bootstrap-5-multi-level-dropdown/master/bootstrap5-dropdown-ml-hack-hover.css" />
...
<div class="dropdown-hover-all">
  <!-- .dropdown elements -->
</div>
<div class="dropdown dropdown-hover">
  <!-- toggle and menu elements -->
</div>
...
<script src="https://raw.githubusercontent.com/dallaslu/bootstrap-5-multi-level-dropdown/master/bootstrap5-dropdown-ml-hack.js"></script>
```

## Demo

### demo.html
```bash
git clone git@github.com:dallaslu/bootstrap-5-multi-level-dropdown.git
cd bootstrap-5-multi-level-dropdown
npm install
gulp
```

### jsfiddle

Here is a perfect demo: https://jsfiddle.net/dallaslu/mvk4uhzL/ (works well with Bootstrap v5.0.2)
