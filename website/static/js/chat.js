function addMessage(sender,text){

const chat=document.getElementById("chat");

const div=document.createElement("div");

div.className=sender;

div.innerHTML=text;

chat.appendChild(div);

chat.scrollTop=chat.scrollHeight;

}