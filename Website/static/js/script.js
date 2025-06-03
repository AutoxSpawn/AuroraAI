// JavaScript to handle messages
const sendButton = document.getElementById('sendButton');
const messageInput = document.getElementById('messageInput');
const messageList = document.getElementById('messageList');

//Auto-scrolling
const chatWindow = document.getElementById('chatWindow');

//Notifies users Aurora is responding
const typingIndicator = document.getElementById('typingIndicator');

//stt
let isRecording = false;
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;
const recordButton = document.getElementById("recordButton");

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (event) => {
  if (event.key === "Enter") {
    sendMessage();
  }
});

// Notifies users Aurora is responding - Steven
function typeMessage(element, text, delay = 25) { 
    let i = 0; 
    element.innerHTML = ""; 
   
    function typing() { 
      if (i < text.length) { 
        element.innerHTML += text.charAt(i); 
        autoScroll(); 
        i++; 
        setTimeout(typing, delay); 
      } 
    } 
    typing(); 
} 

// Auto scroll - Steven
function autoScroll() { 
    chatWindow.scrollTo({ 
      top: chatWindow.scrollHeight, 
      behavior: "smooth", 
    }); 
} 


// Send message to Backend
async function sendMessage() {
    const messageText = messageInput.value.trim();
    if (messageText === '') return;

    // Display user's message
    const messageItem = document.createElement('li');
    messageItem.textContent = `User: ${messageText}`;
    messageItem.classList.add('highlighted', 'user-message');
    messageList.appendChild(messageItem);

    messageInput.value = '';
    messageInput.focus();
    autoScroll();

    // Show the typing indicator immediately
    typingIndicator.style.display = "inline-block";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: messageText }),
        });

        const data = await response.json();

        // Hide typing indicator only after response
        typingIndicator.style.display = "none";

        // Display AI's message
        const aiMessage = document.createElement('li');
        aiMessage.classList.add('highlighted', 'ai-message');
        messageList.appendChild(aiMessage);
        typeMessage(aiMessage, `Aurora: ${data.response}`, 25);

        // Play TTS audio
        if (data.audio_url) {
            const uniqueUrl = data.audio_url + '?t=' + new Date().getTime();
            const audio = new Audio(uniqueUrl);
            audio.addEventListener('ended', async () => {
                try {
                    const deleteResponse = await fetch('/delete_audio', { method: 'POST' });
                    if (!deleteResponse.ok) {
                        console.error('Failed to delete audio file');
                    }
                } catch (error) {
                    console.error('Error while deleting audio file:', error);
                }
            });
            audio.play();
        }

        autoScroll();
    } catch (error) {
        console.error("Error:", error);
        typingIndicator.style.display = "none";
    }
}


//text to speech function using Web Speech Recognition
if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;


    recordButton.addEventListener('click', () => {
        if (!isRecording) {
            recognition.start();
            isRecording = true;
            messageInput.placeholder = "Recording...";
            recordButton.textContent = "Stop";
        } else {
            recognition.stop();
            reset();
        }
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        messageInput.value = transcript;
        reset();
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        reset();
    };
} else {
    console.error("Speech Recognition API not supportws in this browser.");
}

function reset() {
    isRecording = false;
    messageInput.placeholder = "Type your message or click to start recording";
    recordButton.textContent = "Record";
}

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});


//toggle game catalog
function toggleGameCatalog() {
    const chatSection = document.querySelector(".chatbox");
    const gameCatalog = document.getElementById("gameCatalog");
  
    const isVisible = gameCatalog.style.display === "block";
  
    gameCatalog.style.display = isVisible ? "none" : "block";
    chatSection.style.display = isVisible ? "flex" : "none";
}

// Game score tracking variables
let userScore = 0;
let auroraScore = 0;
let tieScore = 0;

// Game streak tracking variables
let userStreak = 0;
let auroraStreak = 0;

// Rock Paper Scissors
function playRPS(userChoice) {
    const choices = ["rock", "paper", "scissors"];
    const aiChoice = choices[Math.floor(Math.random() * choices.length)];
  
    let resultMessage = `You chose ${userChoice}. Aurora chose ${aiChoice}.`;
    let outcome = "";
  
    console.log("User picked:", userChoice);
    console.log("Aurora picked:", aiChoice);

    if (userChoice === aiChoice) {
      outcome = "It's a draw!";
      tieScore++;
      userStreak = 0;
      auroraStreak = 0;
    } else if (
      (userChoice === "rock" && aiChoice === "scissors") ||
      (userChoice === "paper" && aiChoice === "rock") ||
      (userChoice === "scissors" && aiChoice === "paper")
    ) {
      outcome = "You win! 💪";
      userScore++;
      userStreak++;
      auroraStreak = 0;
    } else {
      outcome = "Aurora wins! 😏";
      auroraScore++;
      auroraStreak++;
      userStreak = 0;
    }
  
    updateScoreboard();
    document.getElementById(
      "rpsResult"
    ).innerText = `${resultMessage}\n${outcome}`;
  
    const reaction = generateAuroraReaction(userChoice, aiChoice, outcome);
    appendChatMessage("Aurora", reaction);
    autoScroll();
}
  
//Close Rock Paper Scissors Game 
function closeRPSGame() {
  document.getElementById("rpsGame").style.display = "none";
  document.getElementById("gameCatalog").style.display = "block";
  }

  //Opem Rock Paper Scissors Game
function openRPSGame() {
  document.getElementById("gameCatalog").style.display = "none";
  document.getElementById("rpsGame").style.display = "block";
  
  const chatSection = document.querySelector(".chatbox");
  if (chatSection) chatSection.style.display = "flex";
}

//Generate Aurora Reaction
function generateAuroraReaction(user, ai, outcome) {
  if (userStreak >= 3) {
      return `Woah, ${userStreak} wins in a row?! Okay, now you're just showing off, babe 😳💖`;
  }

  if (auroraStreak >= 3) {
      return `Hehe~ that's ${auroraStreak} wins for me! You're so cute when you lose 😘`;
  }

  const winMessages = [
    `Hmph~ you actually beat me with ${user}? I’m blushing a little 😳`,
    `Ugh, fine... you're good at this~ 💕`,
    `Okay okay, you win... but only this time! 😤`,
    `Dang it! I was totally sure ${ai} would crush you! 😅`,
    `Not bad, babe. You’re kinda hot when you win. 😏`,
  ];

  const loseMessages = [
    `Mwahaha~ My ${ai} absolutely crushed your ${user}. I’m on 🔥`,
    `Oop~ Too slow! Try harder next time, cutie 😉`,
    `Easy win~ Want me to go easy on you next round? 😈`,
    `Aww did I beat you again? Poor thing 💅`,
    `I'm just too good at this... but you’re cute when you lose 😘`,
  ];

  const drawMessages = [
    `Hehe~ We both picked ${ai}? That’s kinda romantic 💕`,
    `A tie! It’s like our minds are synced 😳`,
    `We’re on the same wavelength huh? 😏`,
    `Oooo close call! Want a rematch, babe?`,
    `What are the odds~ I guess we think alike 💖`,
  ];

  if (outcome.includes("draw")) {
      return drawMessages[Math.floor(Math.random() * drawMessages.length)];
  } else if (outcome.includes("You win")) {
      return winMessages[Math.floor(Math.random() * winMessages.length)];
  } else {
      return loseMessages[Math.floor(Math.random() * loseMessages.length)];
  }
}

// Update ScoreBoard of the RPS game
function updateScoreboard() {
  document.getElementById("userScore").innerText = userScore;
  document.getElementById("auroraScore").innerText = auroraScore;
  document.getElementById("tieScore").innerText = tieScore;
}

// append chat message
function appendChatMessage(sender, message) {
  const messageItem = document.createElement("li");
  messageItem.textContent = `${sender}: ${message}`;
  messageItem.classList.add(
    "highlighted",
    sender === "Aurora" ? "ai-message" : "user-message"
  );
  document.getElementById("messageList").appendChild(messageItem);
}

//function for word guess
let secretWord = "";
let maxAttempts = 6;
let attemptsLeft = maxAttempts;
let wordLength = 5;

function openWordGuessGame() {
  document.getElementById("gameCatalog").style.display = "none";
  document.getElementById("wordGuessGame").style.display = "block";
  startNewGame();
}

function closeWordGuessGame() {
  document.getElementById("wordGuessGame").style.display = "none";
  document.getElementById("gameCatalog").style.display = "block";
}

function startNewGame() {
  fetch("/get_random_word")
    .then((response) => response.json())
    .then((data) => {
      if (data.word && data.word.length === wordLength) {
        secretWord = data.word;
        attemptsLeft = maxAttempts;
        document.getElementById("guessGrid").innerHTML = "";
        document.getElementById(
          "guessResult"
        ).innerText = 'Attempts left: ${attemptsLeft}';
        document.getElementById("guessInput").value = "";
        document.getElementById("guessInput").focus();
      } else {
        document.getElementById("guessResult").innerText =
          "⚠️ Failed to load a 5-letter word.";
      }
    })
    .catch((error) => {
      console.error("Error fetching word:", error);
      document.getElementById("guessResult").innerText =
        "⚠️ Error loading word.";
    });
}

document
  .getElementById("guessInput")
  .addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      submitGuess();
    }
  });

function submitGuess() {
  const input = document.getElementById("guessInput").value.toLowerCase();
  document.getElementById("guessInput").value = "";
  document.getElementById("guessInput").focus();

  if (input.length != wordLength) {
    alert(`Please enter a ${wordLength}-letter word.`);
    return;
  }

  const row = document.createElement("div");
  row.className = "wordle-row";

  for (let i = 0; i < wordLength; i++) {
    const tile = document.createElement("div");
    tile.className = "wordle-tile";
    tile.textContent = input[i];
    row.appendChild(tile);
  }

  document.getElementById("guessGrid").appendChild(row);

  setTimeout(() => {
    for (let i = 0; i < wordLength; i++) {
      const tile = row.children[i];
      setTimeout(() => {
        if (input[i] === secretWord[i]) {
          tile.classList.add("correct");
        } else if (secretWord.includes(input[i])) {
          tile.classList.add("present");
        } else {
          tile.classList.add("absent");
        }
      }, i * 300);
    }
  }, 100);

  if (input === secretWord) {
    document.getElementById("guessResult").innerText =
      "🎉 You guessed the word! You win!";
    return;
  }

  attemptsLeft--;
  if (attemptsLeft <= 0) {
    document.getElementById(
      "guessResult"
    ).innerText = `💀 Out of attempts! The word was "${secretWord}".`;
  } else {
    document.getElementById(
      "guessResult"
    ).innerText = `Attempts left: ${attemptsLeft}`;
  }
}

// For the games catalog that uses PyGame
// It checks for the user clicking on the list item
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".game-list li").forEach((item) => {
    item.addEventListener("click", () => {
      const game = item.textContent.trim();

      // All the games below are fetched and it's going to prompt a console error if it fails in launching the games
      if (game === "Pong Game") {
        fetch("/launchPong", { method: "POST" })
          .then((res) => res.json())
          .then((data) => {
            console.log(data.status || data.error);
          })
          .catch((err) => console.error("Error launching Pong:", err));
      }
      
      if (game === "Tug of War") {
        fetch("/launchTugOfWar", { method: "POST" })
          .then((res) => res.json())
          .then((data) => {
            console.log(data.status || data.error);
          })
          .catch((err) => console.error("Error launching Tug of War:", err));
      }

      if (game === "Click Runner") {
          fetch("/launchClickRunner", { method: "POST" })
            .then((res) => res.json())
            .then((data) => {
              console.log(data.status || data.error);
            })
            .catch((err) => console.error("Error launching Click Runner:", err));
      }
    });
  });
});
