$(document).ready(function() {
    var socket;
    var roomId;

    function initSocketConnection() {
        if (socket) {
            socket.close();
        }

        socket = io.connect('http://' + window.location.hostname + ':' + location.port, {
            query: 'room_id=' + roomId
        });

        socket.on('connect', function() {
            console.log("Connected to roomid" + roomId);
            socket.emit('join', { room_id: roomId });
        });

        socket.on('join_response', function(data) {
            if (data.error) {
                // If there was an error joining the room, display an alert with the error message.
                alert(data.error);
            } else {
                // If the user joined the room successfully, print a confirmation message to the console.
                console.log(data.message);
                console.log('Joined room: ' + data.room_id);
            }
        });

        socket.on('message', handleReceivedMessage);
    }

    function handleReceivedMessage(data) {
        var card = $('<div>').addClass('card chat-message mb-3');
        var cardBody = $('<div>').addClass('card-body').text(data.msg);

        card.css('background-color', data.color);
        card.append(cardBody);

        if (data.sender == 'ai') {
            card.addClass('ai-message');
        }

        $('#messages').append(card);
        $('#chat-window').scrollTop($('#chat-window')[0].scrollHeight);
    }

    function sendMessage() {
        var message = $('#m').val();
        socket.emit('message', { message: message, room_id: roomId });
        $('#m').val('');
        $('#chat-window').scrollTop($('#chat-window')[0].scrollHeight);
        return false;
    }

    $(document).on('click', '.room', function() {
        roomId = $(this).attr('id').replace('room_', '');
        initSocketConnection();
        loadRoom(roomId);
    });
    
    $('#send').click(sendMessage);
    $('#m').keypress(function (e) {
        if (e.which == 13) {  // Enter key
            sendMessage();
        }
    });

    $('#logoutButton').click(function() {
        $.get('/logout', function() {
            window.location.href = '/login';
        });
    });

    $("#search").keyup(function() {
        var query = $(this).val();
        if (query != "") {
            $.ajax({
                url: '/chat/search',
                method: 'GET',
                data: {query: query},
                success: function(data) {
                    $('#searchResults').empty(); // Clear previous results
                    data.forEach(function(user){
                        var $a = $('<a href="#" class="list-group-item list-group-item-action">' + user.username + '</a>');
                        $a.on('click', function() { createRoom(user.id); });
                        $('#searchResults').append($a);
                    });
                }
            });
        } else {
            $('#searchResults').empty();
        }
    });

    function createRoom(userId) {
        $.ajax({
            type: 'POST',
            url: '/rooms/create_room/' + userId,
            success: function(data) {
                // Assuming you're using Socket.IO to handle real-time updates,
                // you can emit an event to the server to notify the user about the new room.
                socket.emit('new_room', {room_id: data.room_id});
    
                // Add the new room to the sidebar. This now creates a list group item.
                $('#sidebar').append('<a href="#" id="room_' + data.room_id + '" class="list-group-item list-group-item-action room">Room ' + data.room_id + '</a>');
                $('#room_' + data.room_id).click(function() { loadRoom(data.room_id); });

                // Clear the search results.
                $('#searchResults').empty();
    
                // Load the new room's chat history.
                loadRoom(data.room_id);
            },
            error: function(data) {
                alert(data.responseJSON.error);
            }
        });
    }

    function loadRoom(roomId) {
        if (!roomId) {
            console.error('Invalid room ID');
            return;
        }
        $.ajax({
            url: '/rooms/room/' + roomId,
            success: function(data) {
                // Load the chat history.
                $('#messages').empty();
                data.messages.forEach(function(message) {
                    var card = $('<div>').addClass('card chat-message mb-3');
                    var cardBody = $('<div>').addClass('card-body').text(
                        (message.sender ? message.sender + ": " : "") + message.text
                    );

                    // Apply color to card body
                    card.css('background-color', message.color); 
    
                    card.append(cardBody);
    
                    if (message.sender == 'ai') {
                        card.addClass('ai-message');
                    }
                    // else {
                    //     card.addClass('client-message');
                    // }
    
                    $('#messages').append(card);
                });
                $('#chat-window').scrollTop($('#chat-window')[0].scrollHeight);
            },
            error: function(data) {
                alert(data.responseJSON.error);
            }
        });
    }

    $.ajax({
        url: '/rooms/get_rooms',
        success: function(data) {
            if (data.rooms.length > 0) {
                data.rooms.forEach(function(room) {
                    var roomLink = $('<a>')
                        .attr('id', 'room_' + room.id)
                        .addClass('list-group-item list-group-item-action room')
                        .text('Room ' + room.id);
                    $('#sidebar').append(roomLink);
                });
                roomId = data.rooms[0].id;
                initSocketConnection();
                loadRoom(roomId);
            } else {
                $('#sidebar').append('<p class="text-center">No rooms found. Click <a href="/create_room_page">here</a> to create a new one.</p>');
            }
        },
        error: function(data) {
            alert(data.responseJSON.error);
        }
    });
});