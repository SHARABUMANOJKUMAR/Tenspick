// Check if the browser supports SpeechRecognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  const micBtn = document.getElementById("mic-btn");
  const voiceOutput = document.getElementById("voice-output");
  const userInput = document.getElementById("userInput");

  micBtn.addEventListener("click", () => {
    recognition.start();
    micBtn.innerText = "🎤 Listening...";
  });

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    voiceOutput.innerText = "You said: " + transcript;

    // Set voice input to chat input field
    userInput.value = transcript;

    // Call replyChat() to auto-send to chatbot
    replyChat();

    micBtn.innerText = "🎙️ Start Voice";
  };

  recognition.onerror = (event) => {
    voiceOutput.innerText = "Voice error: " + event.error;
    micBtn.innerText = "🎙️ Start Voice";
  };

  recognition.onend = () => {
    micBtn.innerText = "🎙️ Start Voice";
  };
} else {
  alert("Your browser doesn't support Speech Recognition.");
}
