import TomSelect from './tom-select.ts';

import caret_position from './plugins/caret_position/plugin.ts';
import dropdown_input from './plugins/dropdown_input/plugin.ts';
import no_backspace_delete from './plugins/no_backspace_delete/plugin.ts';
import remove_button from './plugins/remove_button/plugin.ts';
import restore_on_backspace from './plugins/restore_on_backspace/plugin.ts';

TomSelect.define('caret_position', caret_position);
TomSelect.define('dropdown_input', dropdown_input);
TomSelect.define('no_backspace_delete', no_backspace_delete);
TomSelect.define('remove_button', remove_button);
TomSelect.define('restore_on_backspace', restore_on_backspace);

export default TomSelect;
