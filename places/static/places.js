
function get_answer(uuid) {
  fetch(`http://localhost:8080/answer/${uuid}`).then(
    response => response.json()
  ).then(jsonResponse => {
    console.log(jsonResponse);
    document.getElementById('answer-answer').textContent = jsonResponse.answer;
    document.getElementById('answer-extract').innerHTML = jsonResponse.extract;
    document.getElementById('answer-url').href = jsonResponse.url;
    document.getElementById('answer-url').innerHTML = jsonResponse.url;
    document.getElementById('answer').style.display = "initial";
    document.getElementById('answer-anime').style.display = "none";
  });
}


