"use strict";

function likePost() {
  var like = document.getElementById("like");
  var id = like.getAttribute("data-index-number");
  var id = like.getAttribute("data-parent");
  like.addEventListener('click', function () {
    fetch("/like?post=".concat(id, "&type=").concat(type)).then(function (like) {
      like.json().then(function (likes) {
        console.log(likes);

        if (type == 'like') {
          like.setAttribute("src", "./static/images/Media-Icon-25-512.webp?v=1.2");
        } else {
          like.setAttribute("src", "./static/images/Liked.webp?v=1.2");
        }
      });
    });
  });
}

likePost();