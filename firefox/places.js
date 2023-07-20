if (document.readyState !== "complete") {
  window.addEventListener("load", afterWindowLoaded);
} else {
  afterWindowLoaded();
}

function afterWindowLoaded() {
  var page = "<html>" + document.documentElement.innerHTML + "</html>";
  browser.runtime.sendMessage({
    url: window.location.href,
    text: page,
    webext_version: "0.4.0",
  });
}
