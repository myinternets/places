

if (document.readyState !== 'complete') {
    window.addEventListener('load',afterWindowLoaded);
} else {
    afterWindowLoaded();
}

function afterWindowLoaded() {
  var page = '<html>' + document.documentElement.innerHTML + '</html>';
  const data = { url: window.location.href, text: page};
  postJSON(data);
}


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



