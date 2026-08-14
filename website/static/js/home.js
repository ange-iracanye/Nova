const cards=document.querySelectorAll(".card");

cards.forEach(card=>{

card.addEventListener("mouseenter",()=>{

card.style.boxShadow="0 0 30px rgba(37,99,235,.45)";

});

card.addEventListener("mouseleave",()=>{

card.style.boxShadow="none";

});

});