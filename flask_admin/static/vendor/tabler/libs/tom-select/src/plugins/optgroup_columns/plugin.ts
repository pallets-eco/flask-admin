/**
 * Plugin: "optgroup_columns" (Tom Select.js)
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
import * as constants from '../../constants.ts';
import { parentMatch, nodeIndex } from '../../vanilla.ts';

export default function(this:TomSelect) {
	var self = this;

	var orig_keydown = self.onKeyDown;

	self.hook('instead','onKeyDown',(evt:KeyboardEvent)=>{
		var index, option, options, optgroup;

		if( !self.isOpen || !(evt.keyCode === constants.KEY_LEFT || evt.keyCode === constants.KEY_RIGHT)) {
			return orig_keydown.call(self,evt);
		}

		self.ignoreHover	= true;
		optgroup			= parentMatch(self.activeOption,'[data-group]');
		index				= nodeIndex(self.activeOption,'[data-selectable]');

		if( !optgroup ){
			return;
		}

		if( evt.keyCode === constants.KEY_LEFT ){
			optgroup = optgroup.previousSibling;
		} else {
			optgroup = optgroup.nextSibling;
		}

		if( !optgroup ){
			return;
		}

		options				= (<HTMLOptGroupElement>optgroup).querySelectorAll('[data-selectable]');
		option				= options[ Math.min(options.length - 1, index) ] as HTMLElement;

		if( option ){
			self.setActiveOption(option);
		}

	});

};
