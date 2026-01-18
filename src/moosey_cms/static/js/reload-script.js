/**
 * Copyright (c) 2026 Anthony Mugendi
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

(function () {
  // 1. dynamic protocol (ws or wss) and host resolution
  var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  var ws_url = `${protocol}//${window.location.host}/ws/hot-reload`;

  console.log('Connecting to:', ws_url);
  var ws = new WebSocket(ws_url);

  // 2. Wait for connection to open before sending data
  ws.onopen = function (event) {
    console.log('Connected! Ready for hot-reloading');
    // ws.send('hi');
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
    console.log('WebSocket Disconnected');
  };
})();
