browser.omnibox.setDefaultSuggestion({
  description: `Search Your History. Finish with a question mark (?) to get an answer`
});


browser.omnibox.onInputEntered.addListener((text, disposition) => {
  let url = `http://localhost:8080/search?q=${text}`;
  switch (disposition) {
    case "currentTab":
      browser.tabs.update({url});
      break;
    case "newForegroundTab":
      browser.tabs.create({url});
      break;
    case "newBackgroundTab":
      browser.tabs.create({url, active: false});
      break;
  }
});



async function postJSON(data) {
  try {
    const response = await fetch("http://localhost:8080/index", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    console.log("Success:", result);
  } catch (error) {
    console.error("Error:", error);
  }
}

function handleMessage(request, sender, sendResponse) {
  if (request.url in statusCodes) {
    var code = statusCodes[request.url];
    if (code < 300) {
      postJSON(request);
    }
  }
}

browser.runtime.onMessage.addListener(handleMessage);

var statusCodes = {};

browser.webRequest.onCompleted.addListener(
  (e) => {
    if (e.tabId === -1 || e.type !== "main_frame") {
      return;
    }
    statusCodes[e.url] = e.statusCode;
  },
  { urls: ["<all_urls>"], types: ["main_frame"] },
  ["responseHeaders"]
);

function openPage() {
  browser.tabs.create({
    url: "http://localhost:8080",
  });
}

browser.browserAction.onClicked.addListener(openPage);
