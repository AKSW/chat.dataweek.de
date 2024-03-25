'use strict';

const socket = io();

socket.on('connect', () => {
  console.log(`connect ${socket.id}`);
});

socket.on('disconnect', () => {
  console.log(`disconnect ${socket.id}`);
});

socket.on('server_message', (message) => {
  console.log("message received");
  console.log(message);
  let e = document.createElement('p');
  if (message.type == 'message') {
    let sp_nick = document.createElement('span');
    let sp_time = document.createElement('span');
    let sp_message = document.createElement('span');
    sp_nick.innerHTML = message.nickname;
    sp_time.innerHTML = message.time;
    sp_time.setAttribute("class", "date");
    sp_message.innerHTML = message.body;
    e.append(sp_time);
    e.append(" ");
    e.append(sp_nick);
    e.append(": ");
    e.append(sp_message);
  }
  if (message.type == 'topic') {
    let sp_nick = document.createElement('span');
    let sp_message = document.createElement('span');
    sp_nick.innerHTML = "topic";
    sp_message.innerHTML = message.body;
    e.append(sp_nick);
    e.append(": ");
    e.append(sp_message);
    let topicData = JSON.decode(message.body);
    updateVideo(topicData.video);
  }

  document.getElementById('message-box').prepend(e);
});

function updateVideo(videoUrl) {
  currentUrl = document.getElementById('videoframe').getAttribute("src");
  if (currentUrl != videoUrl) {
    document.getElementById('videoframe').setAttribute("src", videoUrl);
  }
}

function sendMessage() {
  console.log("send message");

  const nickname = htmlEntities(document.getElementById('nickname-input').value);
  const message_body = htmlEntities(document.getElementById('message-input').value);

  if (nickname.trim() == "" || message_body.trim() == "") {
    console.log("nickname or message body not set, will not send message");
    if (nickname.trim() == "") {
      document.getElementById('nickname-input').required = "true";
    }
    if (message_body.trim() == "") {
      document.getElementById('message-input').required = "true";
    }
  } else {
    // TODO channel
    const message = {
      body: message_body,
      nickname: nickname
    };
    console.log(message);
    if (message) {
      socket.emit('client_message', message);
    }
    document.getElementById('message-input').value = '';
  }
  return false;
}

function htmlEntities(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function isPressingEnter(e){
  let k;
  if(window.event){
    k = e.keyCode;
    if(k===13){
      sendMessage();
    }
  } else if(e.which){
    k = e.which;
    if(k===13){
      sendMessage();
    }
  }
}

window.isPressingEnter = isPressingEnter;
window.sendMessage = sendMessage;
