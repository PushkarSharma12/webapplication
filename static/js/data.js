function likePost(){
    var like = document.getElementById("like");
    var id = like.getAttribute("data-index-number");
    var id = like.getAttribute("data-parent");
    like.addEventListener('click', ()=>{
    fetch(`/like?post=${id}&type=${type}`).then((like)=>{
      like.json().then((likes) => {
        console.log(likes);
        if(type == 'like'){
          like.setAttribute("src","./static/images/Media-Icon-25-512.webp?v=1.2");
        }else{
          like.setAttribute("src","./static/images/Liked.webp?v=1.2");
        }
    })
  })
  })
  }
likePost();