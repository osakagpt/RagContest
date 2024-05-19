
document.getElementById('signupButton').addEventListener('click', function(event) {
    event.preventDefault();  // Prevent the default form submission

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    fetch('/signup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
    })
    .then(response => response.json())
    .then(data => alert('Your API KEY(メモっとけ): ' + data.api_key))
    .catch(error => alert('Error during registration: ' + error));
});
