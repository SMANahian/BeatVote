var socket = io('/room');
if (window.roomId) {
  socket.emit('room:join', { room_id: window.roomId });
}
