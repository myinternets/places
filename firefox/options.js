function saveOptions(e) {
  e.preventDefault();
  browser.storage.sync.set({
    server: document.querySelector("#server").value
  });
}

function askNotificationPermission() {
  // function to actually ask the permissions
  function handlePermission(permission) {
    // set the button to shown or hidden, depending on what the user answers
    //notificationBtn.style.display =
      //Notification.permission === "granted" ? "none" : "block";

  }

  // Let's check if the browser supports notifications
  if (!("Notification" in window)) {
    console.log("This browser does not support notifications.");
  } else {
   console.log("Requesting permission");
    Notification.requestPermission().then((permission) => {
      handlePermission(permission);
    });
  }
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

