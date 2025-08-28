class RedisCli {
    // Constants
    static KEY_UP = 38;
    static KEY_DOWN = 40;
    static MAX_ITEMS = 128;

    constructor(postUrl) {
        this.postUrl = postUrl;

        // DOM Elements
        this.con = document.querySelector('.console');
        this.container = this.con.querySelector('.console-container');
        this.form = this.con.querySelector('form');
        this.input = this.con.querySelector('input');

        // State
        this.history = [];
        this.historyPos = 0;

        this.init();
    }

    scrollBottom() {
        this.container.scrollTop = this.container.scrollHeight;
    }

    createEntry(cmd) {
        const entry = document.createElement('div');
        entry.className = 'entry';

        const cmdDiv = document.createElement('div');
        cmdDiv.className = 'cmd';
        cmdDiv.innerHTML = cmd; // Use innerHTML to render '>' safely
        entry.appendChild(cmdDiv);

        this.container.appendChild(entry);

        // Limit the number of entries in the console
        if (this.container.children.length > RedisCli.MAX_ITEMS) {
            this.container.firstElementChild.remove();
        }

        this.scrollBottom();
        return entry;
    }

    addResponse(entry, response) {
        const responseDiv = document.createElement('div');
        responseDiv.className = 'response';
        responseDiv.innerHTML = response;
        entry.appendChild(responseDiv);
        this.scrollBottom();
    }

    addError(entry, response) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'response error';
        errorDiv.textContent = response; // Use textContent for plain error messages
        entry.appendChild(errorDiv);
        this.scrollBottom();
    }

    addHistory(cmd) {
        this.history.push(cmd);

        if (this.history.length > RedisCli.MAX_ITEMS) {
            this.history.shift(); // Remove the oldest item
        }

        this.historyPos = this.history.length;
    }

    async sendCommand(cmd) {
        const entry = this.createEntry('> ' + cmd);
        this.addHistory(cmd);

        try {
            const response = await fetch(this.postUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ cmd: cmd }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const responseData = await response.text();
            this.addResponse(entry, responseData);
        } catch (error) {
            console.error('Fetch error:', error);
            this.addError(entry, 'Failed to communicate with the server.');
        }
    }

    submitCommand(event) {
        event.preventDefault();
        const val = this.input.value.trim();
        if (!val.length) return;

        this.sendCommand(val);
        this.input.value = '';
    }

    onKeyDown(event) {
        if (event.keyCode === RedisCli.KEY_UP) {
            event.preventDefault();
            this.historyPos = Math.max(0, this.historyPos - 1);
            if (this.historyPos < this.history.length) {
                this.input.value = this.history[this.historyPos];
            }
        } else if (event.keyCode === RedisCli.KEY_DOWN) {
            event.preventDefault();
            this.historyPos = Math.min(this.history.length, this.historyPos + 1);
            if (this.historyPos >= this.history.length) {
                this.input.value = '';
            } else {
                this.input.value = this.history[this.historyPos];
            }
        }
    }

    init() {
        // Bind 'this' context for event handlers
        this.form.addEventListener('submit', this.submitCommand.bind(this));
        this.input.addEventListener('keydown', this.onKeyDown.bind(this));

        // Focus the input on load
        this.input.focus();

        // Send an initial 'ping' command
        this.sendCommand('ping');
    }
}

// Initialize the console when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const dataElement = document.getElementById('execute-view-data');
    if (dataElement) {
        try {
            const postUrl = JSON.parse(dataElement.textContent);
            new RedisCli(postUrl);
        } catch (e) {
            console.error('Failed to parse Redis CLI data:', e);
        }
    }
});
