/**
 * Copyright (c) 2026 Anthony Mugendi
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

(function () {
  // Configuration
  var MAX_RECONNECT_DELAY = 30000; // Max 30 seconds between attempts
  var INITIAL_RECONNECT_DELAY = 1000; // Start with 1 second
  
  var reconnectDelay = INITIAL_RECONNECT_DELAY;
  var reconnectTimeout;
  var ws;

  // Dynamic protocol (ws or wss) and host resolution
  var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  var ws_url = `${protocol}//${window.location.host}/ws/hot-reload`;

  function connect() {
    console.log('Connecting to:', ws_url);
    ws = new WebSocket(ws_url);

    ws.onopen = function (event) {
      console.log('Connected! Ready for hot-reloading');
      // Reset reconnect delay on successful connection
      reconnectDelay = INITIAL_RECONNECT_DELAY;
    };

    ws.onmessage = function (event) {
      console.log('Received:', event.data);

      // OPTION A: If you want to Reload the page (Hot Reload behavior)
      if (event.data === 'reload') {
        window.location.reload();
        return;
      }

      // OPTION B: Your original logic (Append to DOM)
      var messages = document.getElementById('messages');
      if (messages) {
        var message = document.createElement('li');
        var content = document.createTextNode(event.data);
        message.appendChild(content);
        messages.appendChild(message);
      }
    };

    ws.onclose = function (event) {
      console.log('WebSocket Disconnected. Attempting to reconnect in ' + (reconnectDelay / 1000) + 's...');
      scheduleReconnect();
    };

    ws.onerror = function (error) {
      console.error('WebSocket error:', error);
      ws.close();
    };
  }

  function scheduleReconnect() {
    // Clear any existing reconnect timeout
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
    }

    // Schedule reconnection with current delay
    reconnectTimeout = setTimeout(function () {
      connect();
      // Increase delay for next attempt (exponential backoff)
      reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
    }, reconnectDelay);
  }

  // Initial connection
  connect();
})();