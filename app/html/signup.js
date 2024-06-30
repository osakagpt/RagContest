document.getElementById('signupForm').addEventListener('submit', function (event) {
    event.preventDefault();  // Prevent the default form submission

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    console.log(username);

    fetch('/signup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
    })
        .then(response => response.json())
        .then(data => alert('Your API KEY(メモっとけ): ' + data.message))
        .catch(error => alert('Error during signup: ' + error));
});
