const navSlide = ()=>{
    const burger = document.querySelector('.burger');
    const nav = document.querySelector('.nav-links');
    const bod = document.querySelector('.bod')
    const navLinks = document.querySelectorAll('.nav-links li');
    
    burger.addEventListener('click',() => {
        //togle link

        nav.classList.toggle('nav-active');
        
        //Animate links
        navLinks.forEach((link, index) => {
            if(link.style.animation)
            {
                link.style.animation = "";
            }else{
                link.style.animation =  `navLinkFade 0.5s ease forwards ${index/7+0.4}s`;
            }
        });
        
        //burger Animation
        burger.classList.toggle('toggle');
        body.classList.toggle('change');
    });
    
    

}


navSlide();