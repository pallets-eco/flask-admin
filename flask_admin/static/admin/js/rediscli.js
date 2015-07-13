var RedisCli = function(postUrl) {
	// Constants
	var KEY_UP = 38;
	var KEY_DOWN = 40;
	var MAX_ITEMS = 128;

	var $con = $('.console');
	var $container = $con.find('.console-container');
	var $input = $con.find('input');

	var history = [];
	var historyPos = 0;

	function resizeConsole() {
		var height = $(window).height();

		var offset = $con.offset();
		$con.height(height - offset.top);
	}

	function scrollBottom() {
		$container.animate({scrollTop: $container[0].scrollHeight}, 100);
	}

	function createEntry(cmd) {
		var $entry = $('<div>').addClass('entry').appendTo($container);
		$entry.append($('<div>').addClass('cmd').html(cmd));

		if ($container.find('>div').length > MAX_ITEMS)
			$container.find('>div:first-child').remove();

		scrollBottom();
		return $entry;
	}

	function addResponse($entry, response) {
		$entry.append($('<div>').addClass('response').html(response));
		scrollBottom();
	}
	function addError($entry, response) {
		$entry.append($('<div>').addClass('response').addClass('error').html(response));
		scrollBottom();
	}

	function addHistory(cmd) {
		history.push(cmd);

		if (history > MAX_ITEMS)
			history.splice(0, 1);

		historyPos = history.length;
	}

	function sendCommand(val) {
		var $entry = createEntry('> ' + val);

		addHistory(val);

		$.ajax({
			type: 'POST',
			url: postUrl,
			data: {'cmd': val},
			success: function(response) {
				addResponse($entry, response);
			},
			error: function() {
				addError($entry, 'Failed to communicate with server.');
			}
		});

		return false;
	}

	function submitCommand() {
		var val = $input.val().trim();
		if (!val.length)
			return false;

		sendCommand(val);

		$input.val('');
	}

	function onKeyPress(e) {
		if (e.keyCode == KEY_UP) {
			historyPos -= 1;
			if (historyPos < 0)
				historyPos = 0;

			if (historyPos < history.length)
				$input.val(history[historyPos]);
		} else
		if (e.keyCode == KEY_DOWN) {
			historyPos += 1;

			if (historyPos >= history.length) {
				$input.val('');
				historyPos = history.length;
			} else {
				$input.val(history[historyPos]);
			}
		}
	}

	// Setup
	$con.find('form').submit(submitCommand);

	$input.keydown(onKeyPress);

	$(window).resize(resizeConsole);
	resizeConsole();

	$input.focus();

	sendCommand('ping');
};
