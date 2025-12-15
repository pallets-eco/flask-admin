/**
 * Plugin: "dropdown_input" (Tom Select)
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
import { getDom, addClasses } from '../../vanilla.ts';
import { addEvent, preventDefault } from '../../utils.ts';


export default function(this:TomSelect) {
	const self = this;

	self.settings.shouldOpen = true; // make sure the input is shown even if there are no options to display in the dropdown

	self.hook('before','setup',()=>{
		self.focus_node		= self.control;

		addClasses( self.control_input, 'dropdown-input');

	 	const div = getDom('<div class="dropdown-input-wrap">');
		div.append(self.control_input);
		self.dropdown.insertBefore(div, self.dropdown.firstChild);

		// set a placeholder in the select control
		const placeholder = getDom('<input class="items-placeholder" tabindex="-1" />') as HTMLInputElement;
		placeholder.placeholder = self.settings.placeholder ||'';
		self.control.append(placeholder);

	});


	self.on('initialize',()=>{

		// set tabIndex on control to -1, otherwise [shift+tab] will put focus right back on control_input
		self.control_input.addEventListener('keydown',(evt:KeyboardEvent) =>{
		//addEvent(self.control_input,'keydown' as const,(evt:KeyboardEvent) =>{
			switch( evt.keyCode ){
				case constants.KEY_ESC:
					if (self.isOpen) {
						preventDefault(evt,true);
						self.close();
					}
					self.clearActiveItems();
				return;
				case constants.KEY_TAB:
					self.focus_node.tabIndex = -1;
				break;
			}
			return self.onKeyDown.call(self,evt);
		});

		self.on('blur',()=>{
			self.focus_node.tabIndex = self.isDisabled ? -1 : self.tabIndex;
		});


		// give the control_input focus when the dropdown is open
		self.on('dropdown_open',() =>{
			self.control_input.focus();
		});

		// prevent onBlur from closing when focus is on the control_input
		const orig_onBlur = self.onBlur;
		self.hook('instead','onBlur',(evt?:FocusEvent)=>{
			if( evt && evt.relatedTarget == self.control_input ) return;
			return orig_onBlur.call(self);
		});

		addEvent(self.control_input,'blur', () => self.onBlur() );

		// return focus to control to allow further keyboard input
		self.hook('before','close',() =>{

			if( !self.isOpen ) return;
			self.focus_node.focus({preventScroll: true});
		});

	});

};
