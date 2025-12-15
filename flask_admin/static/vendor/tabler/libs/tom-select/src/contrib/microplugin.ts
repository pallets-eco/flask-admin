/**
 * microplugin.js
 * Copyright (c) 2013 Brian Reavis & contributors
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
 * @author Brian Reavis <brian@thirdroute.com>
 */

type TSettings = {
	[key:string]:any
}

type TPlugins = {
	names: string[],
	settings: TSettings,
	requested: {[key:string]:boolean},
	loaded: {[key:string]:any}
};

export type TPluginItem = {name:string,options:{}};
export type TPluginHash = {[key:string]:{}};




export default function MicroPlugin(Interface: any ){

	Interface.plugins = {};

	return class extends Interface{

		public plugins:TPlugins = {
			names     : [],
			settings  : {},
			requested : {},
			loaded    : {}
		};

		/**
		 * Registers a plugin.
		 *
		 * @param {function} fn
		 */
		static define(name:string, fn:(this:any,settings:TSettings)=>any){
			Interface.plugins[name] = {
				'name' : name,
				'fn'   : fn
			};
		}


		/**
		 * Initializes the listed plugins (with options).
		 * Acceptable formats:
		 *
		 * List (without options):
		 *   ['a', 'b', 'c']
		 *
		 * List (with options):
		 *   [{'name': 'a', options: {}}, {'name': 'b', options: {}}]
		 *
		 * Hash (with options):
		 *   {'a': { ... }, 'b': { ... }, 'c': { ... }}
		 *
		 * @param {array|object} plugins
		 */
		initializePlugins(plugins:string[]|TPluginItem[]|TPluginHash) {
			var key, name;
			const self  = this;
			const queue:string[] = [];

			if (Array.isArray(plugins)) {
				plugins.forEach((plugin:string|TPluginItem)=>{
					if (typeof plugin === 'string') {
						queue.push(plugin);
					} else {
						self.plugins.settings[plugin.name] = plugin.options;
						queue.push(plugin.name);
					}
				});
			} else if (plugins) {
				for (key in plugins) {
					if (plugins.hasOwnProperty(key)) {
						self.plugins.settings[key] = plugins[key];
						queue.push(key);
					}
				}
			}

			while( name = queue.shift() ){
				self.require(name);
			}
		}

		loadPlugin(name:string) {
			var self    = this;
			var plugins = self.plugins;
			var plugin  = Interface.plugins[name];

			if (!Interface.plugins.hasOwnProperty(name)) {
				throw new Error('Unable to find "' +  name + '" plugin');
			}

			plugins.requested[name] = true;
			plugins.loaded[name] = plugin.fn.apply(self, [self.plugins.settings[name] || {}]);
			plugins.names.push(name);
		}

		/**
		 * Initializes a plugin.
		 *
		 */
		require(name:string) {
			var self = this;
			var plugins = self.plugins;

			if (!self.plugins.loaded.hasOwnProperty(name)) {
				if (plugins.requested[name]) {
					throw new Error('Plugin has circular dependency ("' + name + '")');
				}
				self.loadPlugin(name);
			}

			return plugins.loaded[name];
		}

	};

}
