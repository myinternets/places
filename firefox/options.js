function saveOptions(e) {
  e.preventDefault();
  browser.storage.sync.set({
    server: document.querySelector("#server").value
  });
}

function restoreOptions() {
  function setCurrentChoice(result) {
    document.querySelector("#server").value = result.server || "http://localhost:8080";
  }

  function onError(error) {
    console.log(`Error: ${error}`);
  }

  let getting = browser.storage.sync.get("server");
  getting.then(setCurrentChoice, onError);
}

document.addEventListener("DOMContentLoaded", restoreOptions);
document.querySelector("form").addEventListener("submit", saveOptions);

