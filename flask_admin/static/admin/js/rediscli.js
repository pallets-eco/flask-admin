var RedisCli = function(postUrl) {
	var $con = $('.console');
	var $container = $con.find('.console-container');
	var $input = $con.find('input');

	function resizeConsole() {
		var height = $(window).height();

		var offset = $con.offset();
		$con.height(height - offset.top);
	}

	function scrollBottom() {
		$container.animate({scrollTop: $container.height()}, 100);
	}

	function createEntry(cmd) {
		var $entry = $('<div>').addClass('entry').appendTo($container);
		$entry.append($('<div>').addClass('cmd').html(cmd));
		scrollBottom();
		return $entry;
	}

	function addResponse($entry, response) {
		$entry.append($('<div>').addClass('response').html(response));
		scrollBottom();
	}

	function submitCommand() {
		var val = $input.val().trim();
		if (!val.length)
			return false;

		var $entry = createEntry('> ' + val);

		$.ajax({
			type: 'POST',
			url: postUrl,
			data: {'cmd': val},
			success: function(response) {
				addResponse($entry, response);
			},
			error: function() {
				addResponse($entry, 'Failed to communicate with server.');
			}
		});

		$input.val('');

		return false;
	}

	// Setup
	$con.find('form').submit(submitCommand);

	$(window).resize(resizeConsole);
	resizeConsole();

	$input.focus();
};
