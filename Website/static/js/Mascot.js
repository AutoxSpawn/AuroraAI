function changeCharacter(filename, buttonElement) {
  const mascots = document.getElementById('mascots');
  const buttons = document.querySelectorAll('.character-button');

  mascots.src = "../static/images/" + filename;

  const buttonImage = buttonElement.querySelector('img');
  if (buttonImage) {
    buttonImage.classList.add('spin');
    buttonImage.addEventListener('animationend', () => {
    buttonImage.classList.remove('spin');
    }, { once: true });
  }

  // Mascot resizing
  if (filename === 'blinkchibi.gif') {
    mascots.style.maxWidth = '500px';
    mascots.style.bottom = '200px';
  } else {
    mascots.style.maxWidth = '750px';
    mascots.style.bottom = '0';
  }

  // Hover changes per selection
  mascots.onmouseenter = () => {
  if (filename === 'blink.gif') {
    mascots.src = "../static/images/smile.gif";
  } else if (filename === 'blinkchibi.gif') {
    mascots.src = "../static/images/smilechibi.gif";
  }
};

mascots.onmouseleave = () => {
  mascots.src = "../static/images/" + filename;
};

  // Update selected button
  buttons.forEach(btn => btn.classList.remove('selected'));
  buttonElement.classList.add('selected');
}