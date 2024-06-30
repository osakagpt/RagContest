document.getElementById('loginForm').addEventListener('submit', function (event) {
    event.preventDefault();  // Prevent the default form submission

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Login Failed');
        }
        return response.json();
    })
    .then(data => {
        // localStorage.setItem('token', data.access_token);
        window.location.href = '/dashboard';
    })
    .catch(error => alert('Error during login: ' + error));
});

function accessDashboard(token) {
    window.history.pushState({}, '', '/dashboard');
    fetch('/dashboard', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Access Denied');
        }
        return response.text();
    })
    .then(html => {
        document.documentElement.innerHTML = html;
    })
    .catch(error => {
        alert('Error during dashboard access: ' + error);
        window.history.pushState({}, '', '/login');
    });
}
