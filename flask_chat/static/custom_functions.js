$(document).ready(function() {
    var socket = io();

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
        var message = $('#m').val();
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
                url: '/chat/search',  // The search endpoint
                method: 'GET',
                data: {query: query},
                success: function(data) {
                    // 'data' is a list of usernames
                    $('#searchResults').empty(); // Clear previous results
                    data.forEach(function(user){
                        $('#searchResults').append('<a href="#" class="list-group-item list-group-item-action">'+user+'</a>');
                    });
                }
            });
        } else {
            $('#searchResults').empty();
        }
    });
});