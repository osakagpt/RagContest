document.getElementById('logoutButton').addEventListener('click', async () => {
    fetch('/logout', {
        method: 'POST',
        credentials: 'same-origin',
        redirect: 'manual'
    })
    .then(response => {
        console.log("response: ", response);
        if (response.type === 'opaqueredirect') {
            // This means we received a redirect response
            window.location.href = '/login'; // Manually redirect to dashboard
        } else if (!response.ok) {
            throw new Error('Logout Failed');
        } else {
            // Handle successful non-redirect response here if needed
            console.log('Logout successful');
        }
    })
    .catch(error => alert('Error during login: ' + error));  
});
