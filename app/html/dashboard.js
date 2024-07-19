document.getElementById('logoutButton').addEventListener('click', async () => {
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            credentials: 'same-origin',
            redirect: 'manual'
        });

        if (response.type === 'opaqueredirect') {
            // リダイレクトレスポンスを受け取った場合
            await clearBrowserCache();
            window.location.href = '/login'; // 手動でログインページにリダイレクト
        } else if (!response.ok) {
            throw new Error('Logout Failed');
        } else {
            // 成功した非リダイレクトレスポンスを処理する必要がある場合
            console.log('Logout successful');
            await clearBrowserCache();
            window.location.href = '/login';
        }
    } catch (error) {
        alert('Error during logout: ' + error);
    }
});

async function clearBrowserCache() {
    if ('caches' in window) {
        // キャッシュAPIがサポートされている場合
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(cacheName => caches.delete(cacheName)));
        console.log('Browser cache cleared');
    } else {
        console.warn('Caches API not supported in this browser');
    }

    // ブラウザの標準キャッシュをクリア
    if ('serviceWorker' in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        for (const registration of registrations) {
            registration.unregister();
        }
        console.log('Service Worker unregistered');
    }
}
