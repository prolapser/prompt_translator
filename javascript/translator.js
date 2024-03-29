function translate_ok() {
  let translatedText = translateTextarea.value;
  if (activeTextArea) {
    activeTextArea.focus();
    let selectionStart = activeTextArea.selectionStart;
    let selectionEnd = activeTextArea.selectionEnd;
    if (selectionStart === selectionEnd) {
      activeTextArea.value = translatedText;
    } else {
      activeTextArea.setRangeText(translatedText, selectionStart, selectionEnd, "end");
    }
    activeTextArea.dispatchEvent(new Event('input', { bubbles: true }));
  }
}
let svgButton = `<svg id="a" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4203.6 3812.81" style="fill: var(--button-secondary-text-color);width: 1.3em;"><path d="m3881.34,3812.81l-204.37-593.65h-1000.63l-214.1,593.65h-322.7l855.28-2255.68h353.52l855.28,2255.68h-322.27Zm-1116.69-854.27h813.84l-368.9-1043.47h-76.03l-368.9,1043.47Zm-2436.65,37.86l981.55-981.55-25.53-28.21c-121.18-133.93-228.66-274.54-319.46-417.91-80.25-126.7-152.04-261.31-213.84-400.87h323.33c55.91,109.46,116.15,210.07,179.28,299.38,67.12,94.95,149.18,196.09,243.89,300.6l29.47,32.52,29.65-32.35c144.06-157.15,265.32-320.8,360.42-486.41,94.85-165.18,176.1-343.42,241.49-529.77l18.68-53.24H0v-309.28h1362.48V0h309.28v389.28h1362.48v309.28h-554.34l-8.48,28.65c-67.03,226.62-159.3,450-274.24,663.92-57.35,106.74-122.39,211.76-193.29,312.14-70.95,100.44-149.78,199.08-234.3,293.17l-25.08,27.92,475.73,485.65-115.77,316.45-587.35-587.35-973.2,973.2-215.93-215.93Z"></path></svg>`;

function addTranslateButton(tabSelector, buttonId) {
  let buttonReference = document.querySelector(tabSelector + " #paste");
  let translatePrompt = buttonReference.cloneNode(true);
  translatePrompt.id = buttonId;
  buttonReference.parentNode.insertBefore(translatePrompt, buttonReference);
  translatePrompt.innerHTML = svgButton;
  translatePrompt.title = "перевод с русского на английский:\nнажми чтобы перевести весь русский текст в любом сфокусированном текстовом поле,\nили выдели только необходимое для перевода и затем кликни на эту кнопку\nработает с полями дополнений, а не только основного промпта/негатива";

  document.querySelector(tabSelector).addEventListener("focusin", function (event) {
    if (event.target.tagName.toLowerCase() === "textarea") {
      activeTextArea = event.target;
    }
  });

  document.querySelector(tabSelector).addEventListener("mousedown", function (event) {
    if (event.target.id === buttonId) {
      event.preventDefault();
    }
  });

  translatePrompt.addEventListener("click", function () {
    if (activeTextArea) {
      let selectedText = activeTextArea.value.substring(activeTextArea.selectionStart, activeTextArea.selectionEnd);
      translateTextarea.value = selectedText || activeTextArea.value;
      translateTextarea.dispatchEvent(new Event('input', { bubbles: true }));
      setTimeout(function () {
        document.querySelector("#translate_button").click();
      }, 100);
    }
  });
}

onUiLoaded(function () {
  window.activeTextArea = null;
  window.translateTextarea = document.querySelector("#text2translate > label > textarea");

  addTranslateButton("#tab_txt2img", "txtTranslatePrompt");
  addTranslateButton("#tab_img2img", "imgTranslatePrompt");
});
