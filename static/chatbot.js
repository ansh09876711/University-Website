function sendMessage(){

let msg = document.getElementById("userInput").value;

let chat = document.getElementById("chat-messages");

chat.innerHTML += `<div class="user">${msg}</div>`;

fetch("/chatbot",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({message:msg})
})
.then(res=>res.json())
.then(data=>{

chat.innerHTML += `<div class="bot">${data.reply}</div>`;

});

}
