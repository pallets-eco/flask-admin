/**
 * Plugin: "checkbox_options" (Tom Select)
 * Copyright (c) contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this
 * file except in compliance with the License. You may obtain a copy of the License at:
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
 * ANY KIND, either express or implied. See the License for the specific language
 * governing permissions and limitations under the License.
 *
 */

import type TomSelect from '../../tom-select.ts';
import { TomTemplate } from '../../types/index.ts';
import { preventDefault, hash_key } from '../../utils.ts';
import { getDom } from '../../vanilla.ts';
import { CBOptions } from './types.ts';


export default function(this:TomSelect, userOptions:CBOptions) {
	var self = this;
	var orig_onOptionSelect = self.onOptionSelect;

	self.settings.hideSelected = false;

	const cbOptions : CBOptions = Object.assign({
		// so that the user may add different ones as well
		className             : "tomselect-checkbox",

		// the following default to the historic plugin's values
		checkedClassNames     : undefined,
		uncheckedClassNames   : undefined,
	}, userOptions);


	var UpdateChecked = function(checkbox:HTMLInputElement, toCheck : boolean) {
		if( toCheck ){
			checkbox.checked = true;
			if (cbOptions.uncheckedClassNames) {
				checkbox.classList.remove(...cbOptions.uncheckedClassNames);
			}
			if (cbOptions.checkedClassNames) {
				checkbox.classList.add(...cbOptions.checkedClassNames);
			}
		}else{
			checkbox.checked = false;
			if (cbOptions.checkedClassNames) {
				checkbox.classList.remove(...cbOptions.checkedClassNames);
			}
			if (cbOptions.uncheckedClassNames) {
				checkbox.classList.add(...cbOptions.uncheckedClassNames);
			}
		}
	}

	// update the checkbox for an option
	var UpdateCheckbox = function(option:HTMLElement){
		setTimeout(()=>{
			var checkbox = option.querySelector('input.' + cbOptions.className);
			if( checkbox instanceof HTMLInputElement ){
				UpdateChecked(checkbox, option.classList.contains('selected'));
			}
		},1);
	};

	// add checkbox to option template
	self.hook('after','setupTemplates',() => {

		var orig_render_option = self.settings.render.option;

		self.settings.render.option = ((data, escape_html) => {
			var rendered = getDom(orig_render_option.call(self, data, escape_html));
			var checkbox = document.createElement('input');
			if (cbOptions.className) {
				checkbox.classList.add(cbOptions.className);
			}
			checkbox.addEventListener('click',function(evt){
				preventDefault(evt);
			});

			checkbox.type = 'checkbox';
			const hashed = hash_key(data[self.settings.valueField]);

			UpdateChecked(checkbox, !!(hashed && self.items.indexOf(hashed) > -1) );

			rendered.prepend(checkbox);
			return rendered;
		}) satisfies TomTemplate;
	});

	// uncheck when item removed
	self.on('item_remove',(value:string) => {
		var option = self.getOption(value);

		if( option ){ // if dropdown hasn't been opened yet, the option won't exist
			option.classList.remove('selected'); // selected class won't be removed yet
			UpdateCheckbox(option);
		}
	});

	// check when item added
	self.on('item_add',(value:string) => {
		var option = self.getOption(value);

		if( option ){ // if dropdown hasn't been opened yet, the option won't exist
			UpdateCheckbox(option);
		}
	});


	// remove items when selected option is clicked
	self.hook('instead','onOptionSelect',( evt:KeyboardEvent, option:HTMLElement )=>{

		if( option.classList.contains('selected') ){
			option.classList.remove('selected')
			self.removeItem(option.dataset.value);
			self.refreshOptions();
			preventDefault(evt,true);
			return;
        }

		orig_onOptionSelect.call(self, evt, option);

		UpdateCheckbox(option);
	});

};
