

if(document.readyState !== 'complete') {
    window.addEventListener('load',afterWindowLoaded);
} else {
    afterWindowLoaded();
}

function afterWindowLoaded() {
  var page = '<html>' + document.documentElement.innerHTML + '</html>';
  const data = { url: window.location.href, text: page};
  postJSON(data);
}


var service= browser.runtime.connect({name:"port-from-cs"});

service.postMessage({location: document.URL});


async function postJSON(data) {
  try {
    const response = await fetch("http://localhost:8080/index", {
      method: "POST", // or 'PUT'
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



