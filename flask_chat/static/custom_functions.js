$(document).ready(function() {
    var socket = io();

    socket.on('connect', () => {
        console.log('Socket connected');
    });
    
    socket.on('disconnect', () => {
        console.log('Socket disconnected');
    });

    $('#send').click(sendMessage);
    $('#m').keypress(function (e) {
        if (e.which == 13) {  // Enter key
            sendMessage();
        }
    });

    socket.on('message', function(data){
        var card = $('<div>').addClass('card chat-message mb-3');
        var cardBody = $('<div>').addClass('card-body').text(data.msg);

        // Apply color to card body
        card.css('background-color', data.color); 

        card.append(cardBody);

        if (data.sender == 'ai') {
            card.addClass('ai-message');
        }
        // } else {
        //     card.addClass('client-message');
        // }
                        
        $('#messages').append(card);
        $('#chat-window').scrollTop($('#chat-window')[0].scrollHeight);
    });


    function sendMessage() {
        console.log('Room ID:', roomId);  // Debugging line
        var message = $('#m').val();
        console.log(roomId);
        socket.emit('message', { message: message, room_id: roomId });
        $('#m').val('');
        $('#chat-window').scrollTop($('#chat-window')[0].scrollHeight);
        return false;
    }
    
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
                    $('#messages').append('<div class="message">' + message.text + '</div>');
                });
            },
            error: function(data) {
                alert(data.responseJSON.error);
            }
        });
    }

    $.ajax({
        url: '/rooms/get_rooms',
        success: function(data) {
            // Check if there are rooms
            if (data.rooms.length > 0) {
                // Load the rooms into the sidebar
                data.rooms.forEach(function(room) {
                    $('#sidebar').append('<a href="#" id="room_' + room.id + '" class="list-group-item list-group-item-action room">Room ' + room.id + '</a>');
                    $('#room_' + room.id).click(function() { loadRoom(room.id); });
                });
                // Load the chat history of the first room
                loadRoom(data.rooms[0].id);
            } else {
                // No rooms exist, show a message to the user
                $('#sidebar').append('<p class="text-center">No rooms found. Click <a href="/create_room_page">here</a> to create a new one.</p>');
            }
        },
        error: function(data) {
            alert(data.responseJSON.error);
        }
    });
});