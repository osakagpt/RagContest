document.getElementById('loginForm').addEventListener('submit', function (event) {
    event.preventDefault();  // Prevent the default form submission

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password }),
        redirect: 'manual'
    })
    .then(response => {
        console.log("response: ", response);
        if (response.type === 'opaqueredirect') {
            // This means we received a redirect response
            window.location.href = '/dashboard'; // Manually redirect to dashboard
        } else if (!response.ok) {
            throw new Error('Login Failed');
        } else {
            // Handle successful non-redirect response here if needed
            alert('Login successful');
        }
    })
    .catch(error => alert('Error during login: ' + error));
});
