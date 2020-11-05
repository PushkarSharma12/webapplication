function likePost(x){

  
  if(x.getAttribute("id") == "like"){
    x.setAttribute("src","/static/images/Liked.webp?v=1.2");
    x.setAttribute("id","unlike");
    var likes = document.querySelector(`.likesCount${x.getAttribute("post_id")}`);
    likes.innerHTML = parseInt(likes.innerHTML) + 1;
    fetch(`/like/${x.getAttribute("post_id")}/${"like"}`).then((liked)=>{
     
    })
  }
  else{
    var like = document.querySelector(`.likesCount${x.getAttribute("post_id")}`);
    like.innerHTML = parseInt(like.innerHTML)-1;
    x.setAttribute("id","like")
    x.setAttribute("src","/static/images/Media-Icon-25-512.webp?v=1.1");
    fetch(`/like/${x.getAttribute("post_id")}/${"unlike"}`).then((liked)=>{
    })
  }
}

function followUser(x){
  if(x.getAttribute("id") == "follow"){
    x.setAttribute("class","unfollow");
    x.setAttribute("id","unfollow");
    x.innerHTML = "UnFollow";
    fetch(`/follow/${x.getAttribute("user_id")}/${"follow"}`).then((follow)=>{
            followed.json().then((followed) => {
            
      })
    })
  }
  else{
    x.setAttribute("id","follow");
    x.setAttribute("class","follow");
    x.innerHTML = "Follow";
    fetch(`/follow/${x.getAttribute("user_id")}/${"unfollow"}`).then((follow)=>{
      followed.json().then((followed) => {
      
})
    })
  }
}
