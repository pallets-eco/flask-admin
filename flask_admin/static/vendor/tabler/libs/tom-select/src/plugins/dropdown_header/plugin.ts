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
import { preventDefault } from '../../utils.ts';
import { DHOptions } from './types.ts';

export default function(this:TomSelect, userOptions:DHOptions) {
	const self = this;

	const options = Object.assign({
		title         : 'Untitled',
		headerClass   : 'dropdown-header',
		titleRowClass : 'dropdown-header-title',
		labelClass    : 'dropdown-header-label',
		closeClass    : 'dropdown-header-close',

		html: (data:DHOptions) => {
			return (
				'<div class="' + data.headerClass + '">' +
					'<div class="' + data.titleRowClass + '">' +
						'<span class="' + data.labelClass + '">' + data.title + '</span>' +
						'<a class="' + data.closeClass + '">&times;</a>' +
					'</div>' +
				'</div>'
			);
		}
	}, userOptions);

	self.on('initialize',()=>{
		var header = getDom(options.html(options));

		var close_link = header.querySelector('.'+options.closeClass);
		if( close_link ){
			close_link.addEventListener('click',(evt)=>{
				preventDefault(evt,true);
				self.close();
			});
		}

		self.dropdown.insertBefore(header, self.dropdown.firstChild);
	});

};
