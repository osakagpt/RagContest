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
        body: JSON.stringify({ username, email, password }),
        redirect: 'manual'
    })
    .then(response => {
        if (response.type === 'opaqueredirect') {
            // This means we received a redirect response
            window.location.href = '/login'; // Manually redirect to dashboard
        } else if (!response.ok) {
            throw new Error('Signup Failed');
        } else {
            // Handle successful non-redirect response here if needed
            alert('Temporarily Registered. Please check your email for veryfing your account in 1 hour');
        }
    })
    .catch(error => alert('Error during signup: ' + error));
});
