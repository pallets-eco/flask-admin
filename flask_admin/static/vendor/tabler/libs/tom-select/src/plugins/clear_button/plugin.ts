/**
 * Plugin: "dropdown_header" (Tom Select)
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
import { getDom } from '../../vanilla.ts';
import { CBOptions } from './types.ts';

export default function(this:TomSelect, userOptions:CBOptions) {
	const self = this;

	const options = Object.assign({
		className: 'clear-button',
		title: 'Clear All',
		html: (data:CBOptions) => {
			return `<div class="${data.className}" title="${data.title}">&#10799;</div>`;
		}
	}, userOptions);

	self.on('initialize',()=>{
		var button = getDom(options.html(options));
		button.addEventListener('click',(evt)=>{

			if( self.isLocked ) return;

			self.clear();

			if( self.settings.mode === 'single' && self.settings.allowEmptyOption ){
				self.addItem('');
			}

			evt.preventDefault();
			evt.stopPropagation();
		});
		self.control.appendChild(button);
	});

};
