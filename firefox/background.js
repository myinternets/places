browser.omnibox.setDefaultSuggestion({
  description: `Search Your History. Finish with a question mark (?) to get an answer`
});


browser.omnibox.onInputEntered.addListener((text, disposition) => {
  browser.storage.sync.get("server", function (result) {
  let url = `${result.server}/search?q=${text}`;

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

});

function notify(message) {
  browser.notifications.create('places', {
    "type": "basic",
    "iconUrl": browser.runtime.getURL("icons/magnifying_glass_16.png"),
    "title": "Places",
    "message": "message"
  });
}

async function postJSON(data) {
  let server = (await browser.storage.sync.get("server"))['server'];
  let url = `${server}/index`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

   const result = await response.json();

   if (result.message) {
     chrome.notifications.create('places', {
       "type": "basic",
       "iconUrl": browser.runtime.getURL("icons/magnifying_glass_16.png"),
       "title": "Places",
       "message": result.message,
       "priority": 2
    },
    function(id) { console.log("Last error:", chrome.runtime.lastError); }
    );
  }
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

function logDownloads(downloads) {
  for (const download of downloads) {
    console.log(download.id);
    console.log(download.url);
    console.log(download.filename);
    postJSON({
      url: download.url,
      filename: download.filename,
      webext_version: "0.4.0"
    });
  }
}

function onError(error) {
  console.log(`Error: ${error}`);
}

function handleChanged(delta) {
  if (delta.state && delta.state.current === "complete") {
    const id = delta.id;
    browser.downloads.search({ id }).then(logDownloads, onError);
  }
}

browser.downloads.onChanged.addListener(handleChanged);

