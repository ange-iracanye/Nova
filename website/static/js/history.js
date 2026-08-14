let conversations = JSON.parse(localStorage.getItem("nova_conversations")) || [];

let current = JSON.parse(localStorage.getItem("nova_current")) || [];

function saveConversation(){

    localStorage.setItem(
        "nova_current",
        JSON.stringify(current)
    );

}

function archiveConversation(){

    if(current.length===0) return;

    conversations.unshift({

        date:new Date().toLocaleString(),

        messages:current

    });

    localStorage.setItem(

        "nova_conversations",

        JSON.stringify(conversations)

    );

    current=[];

    saveConversation();

}