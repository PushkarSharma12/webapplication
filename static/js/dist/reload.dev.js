"use strict";

$(document).ready(function () {
  setInterval(function () {
    var someval = Math.floor(Math.random() * 100);
    $('#chat-scroll').reload();
  }, 5000); //Delay here = 5 seconds 
});