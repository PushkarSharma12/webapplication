// $(document).ready(function() {
//     let recipient = document.querySelector('#name').innerHTML;
//     var socket = io.connect(`http://127.0.0.1:5000`);
//     var socket_msg = io(`http://127.0.0.1:5000/msg`);
//     var sender = document.querySelector('#sender_id').innerHTML
//     socket.on('connect', function() {

//         console.log('User Connected')
//     });
//     document.querySelector('#submit').onclick = () => {
//         socket_msg.emit('message', {'msg': document.querySelector('#message').value,
//         'sender': sender, 'recipient': recipient});

//       document.querySelector('#message').value = '';
//    };
//    socket_msg.on('new_msg', function() {
//         alert(msg);
//    });
    
    //document.querySelector('#submit').onclick = () => {
        //socket.emit('message', {'msg': document.querySelector('#message').value,
        //'sender': sender, 'recipient': recipient});

     //  document.querySelector('#message').value = '';
   //};
   
//socket.on('message', data => {

// Display current message
    //if (data.msg) {
        //const p = document.createElement('p');
        //const br = document.createElement('br')
        // Display user's own message
        //if (data.sender == sender) {
                //p.setAttribute("class", "my-msg");
                // HTML to append
                //p.innerHTML +=   data.msg + br.outerHTML;

                //Append
                //document.querySelector('#now-send').append(p);
        //}
        // Display other users' messages
        //else if (typeof data.sender !== 'undefined') {
           // p.setAttribute("class", "others-msg");

            // HTML to append
            //p.innerHTML += data.msg + br.outerHTML ;

            //Append
            //document.querySelector('#now-send').append(p);
       // }
        // Display system message
        //else {
          //  printSysMsg(data.msg);
        //}


//}
//scrollDownChatWindow();
//});
    
    //function scrollDownChatWindow() {
       // const chatWindow = document.querySelector("#chat-scroll");
       //chatWindow.scrollTop = chatWindow.scrollHeight;
    //}
    //function printSysMsg(msg) {
//         const p = document.createElement('p');
//         p.setAttribute("class", "system-msg");
//         p.innerHTML = msg;
//         document.querySelector('#now-send').append(p);
//         scrollDownChatWindow()

//         // Autofocus on text box
//         document.querySelector("#message").focus();
//     }
// 

    // $(document).ready(function() {
    //     $('#chat-scroll').animate({
    //     scrollTop: $('#chat-scroll').get(0).scrollHeight
    //     }, 1);
    // });   


//});
document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io.connect('http://127.0.0.1:5000');

    // Retrieve username
    const username = document.querySelector('#sender_id').innerHTML;

    // Set default room
    let room = "Pushu1980"
    joinRoom("Pushu1980");

    // Send messages
    document.querySelector('#submit').onclick = () => {
        socket.emit('incoming-msg', {'msg': document.querySelector('#message').value,
            'username': username, 'room': room});

        document.querySelector('#message').value = '';
    };

    // Display all incoming messages
    socket.on('message', data => {

        // Display current message
        if (data.msg) {
            const p = document.createElement('p');
            const span_username = document.createElement('span');
            const span_timestamp = document.createElement('span');
            const br = document.createElement('br')
            // Display user's own message
            if (data.username == username) {
                    p.setAttribute("class", "my-msg");

                    // Username
                    span_username.setAttribute("class", "my-username");
                    span_username.innerText = data.username;

                    // Timestamp
                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = data.time_stamp;

                    // HTML to append
                    p.innerHTML += span_username.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML

                    //Append
                    document.querySelector('#now-send').append(p);
            }
            // Display other users' messages
            else if (typeof data.username !== 'undefined') {
                p.setAttribute("class", "others-msg");

                // Username
                span_username.setAttribute("class", "other-username");
                span_username.innerText = data.username;

                // Timestamp
                span_timestamp.setAttribute("class", "timestamp");
                span_timestamp.innerText = data.time_stamp;

                // HTML to append
                p.innerHTML += span_username.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML;

                //Append
                document.querySelector('#now-send').append(p);
            }
            // Display system message
            else {
                printSysMsg(data.msg);
            }


        }
        scrollDownChatWindow();
    });

    // Select a room
    // document.querySelectorAll('.friends').forEach(p => {
    //     p.onclick = () => {
    //         let newRoom = p.innerHTML
    //         // Check if user already in the room
    //         if (newRoom === room) {
    //             msg = `You are already in ${room} room.`;
    //             printSysMsg(msg);
    //         } else {
    //             leaveRoom(room);
    //             joinRoom(newRoom);
    //             room = newRoom;
    //         }
    //     };
    // });
    socket.on('connected', function() {
        // get path from current URL
        let newRoom = window.location.pathname.slice(6);
        let pos = room.indexOf('/');
        if (pos !== -1) {
            newRoom = newRoom.slice(0, pos);
        }
        if (newRoom === room) {
                         msg = `You are already in ${room} room.`;
                        printSysMsg(msg);
                    } else {
                        leaveRoom(room);
                        joinRoom(newRoom);
                        room = newRoom;
                    }
        console.log('a user connected');
    });

    // Logout from chat
    document.querySelector("#logout-btn").onclick = () => {
        leaveRoom(room);
    };

    // Trigger 'leave' event if user was previously on a room
    function leaveRoom(room) {
        socket.emit('leave', {'username': username, 'room': room});

        document.querySelectorAll('.select-room').forEach(p => {
            p.style.color = "black";
        });
    }

    // Trigger 'join' event
    function joinRoom(room) {

        // Join room
        socket.emit('join', {'username': username, 'room': room});

        // Highlight selected room
        document.querySelector('#' + CSS.escape(room)).style.color = "#ffc107";
        document.querySelector('#' + CSS.escape(room)).style.backgroundColor = "white";

        // Clear message area
        document.querySelector('#message').innerHTML = '';

        // Autofocus on text box
        document.querySelector("#now-send").focus();
    }

    // Scroll chat window down
    function scrollDownChatWindow() {
        const chatWindow = document.querySelector("#chat-scroll");
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Print system messages
    function printSysMsg(msg) {
        const p = document.createElement('p');
        p.setAttribute("class", "system-msg");
        p.innerHTML = msg;
        document.querySelector('#chat-scroll').append(p);
        scrollDownChatWindow()

        // Autofocus on text box
        document.querySelector("#user_message").focus();
    }
});