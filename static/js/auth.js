// Authentication JavaScript for IBM SSO Integration

// DOM Elements
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const loading = document.getElementById('loading');
const loginSection = document.getElementById('loginSection');
const userInfo = document.getElementById('userInfo');
const errorDiv = document.getElementById('error');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're returning from OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const w3Id = urlParams.get('w3_id');
    const name = urlParams.get('name');
    const error = urlParams.get('error');
    const errorDescription = urlParams.get('error_description');

    // Handle OAuth errors
    if (error) {
        let errorMessage = 'Authentication failed. ';
        
        if (errorDescription) {
            errorMessage += decodeURIComponent(errorDescription);
        } else {
            errorMessage += error;
        }
        
        // Show specific message for password blocking
        if (errorDescription && errorDescription.includes('password')) {
            errorMessage = '⚠️ IBM has blocked password authentication for your account. ' +
                          'You need to set up a passkey or contact IBM AccessHub to temporarily enable password login. ' +
                          'Visit the IBM Verify page for more information.';
        }
        
        showError(errorMessage);
        
        // Clean URL
        window.history.replaceState({}, document.title, '/');
        return;
    }

    if (token && w3Id) {
        // Store token in localStorage
        localStorage.setItem('access_token', token);
        localStorage.setItem('w3_id', w3Id);
        if (name) {
            localStorage.setItem('name', name);
        }

        // Clean URL
        window.history.replaceState({}, document.title, '/');

        // Fetch and display user info
        fetchUserInfo(w3Id);
    } else {
        // Check if user is already logged in
        const storedToken = localStorage.getItem('access_token');
        const storedW3Id = localStorage.getItem('w3_id');

        if (storedToken && storedW3Id) {
            fetchUserInfo(storedW3Id);
        }
    }
});

// Login button click handler
loginBtn.addEventListener('click', async () => {
    try {
        loginBtn.disabled = true;
        loading.classList.add('active');
        errorDiv.classList.remove('active');

        // Redirect to backend login endpoint
        // The backend will redirect to IBM SSO
        window.location.href = '/auth/login';
    } catch (error) {
        console.error('Login error:', error);
        showError('Failed to initiate login. Please try again.');
        loginBtn.disabled = false;
        loading.classList.remove('active');
    }
});

// Logout button click handler
logoutBtn.addEventListener('click', () => {
    // Clear stored data
    localStorage.removeItem('access_token');
    localStorage.removeItem('w3_id');
    localStorage.removeItem('name');

    // Hide user info and show login
    userInfo.classList.remove('active');
    loginSection.style.display = 'block';
    errorDiv.classList.remove('active');
});

// Fetch user information from backend
async function fetchUserInfo(w3Id) {
    // Clear any previous errors
    errorDiv.classList.remove('active');
    
    // Add cache busting parameter
    const cacheBuster = Date.now();
    const response = await fetch(`/auth/userinfo?w3_id=${encodeURIComponent(w3Id)}&_=${cacheBuster}`, {
        cache: 'no-cache',
        headers: {
            'Cache-Control': 'no-cache'
        }
    }).catch(err => {
        console.error('Network error:', err);
        return null;
    });

    if (!response || !response.ok) {
        console.error('Failed to fetch user info');
        // Just show logged in state anyway since we have the data from URL params
        loginSection.style.display = 'none';
        loading.classList.remove('active');
        userInfo.classList.add('active');
        return;
    }

    const userData = await response.json().catch(err => {
        console.error('JSON parse error:', err);
        return null;
    });
    
    console.log('Fetched user data:', userData);
    
    // Store user data in localStorage (don't display in UI)
    if (userData && userData.w3_id) {
        localStorage.setItem('w3_id', userData.w3_id);
    }
    if (userData && userData.name) {
        localStorage.setItem('name', userData.name);
    }
    
    // Show logged in state
    loginSection.style.display = 'none';
    loading.classList.remove('active');
    userInfo.classList.add('active');
    
    console.log('User info fetched and stored successfully');
}

// Show error message
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.add('active');
}

// Logout helper
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('w3_id');
    localStorage.removeItem('name');
    userInfo.classList.remove('active');
    loginSection.style.display = 'block';
}

// Helper function to make authenticated API calls
async function makeAuthenticatedRequest(url, options = {}) {
    const token = localStorage.getItem('access_token');

    if (!token) {
        throw new Error('No access token found');
    }

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Token expired or invalid
        logout();
        showError('Session expired. Please login again.');
        throw new Error('Unauthorized');
    }

    return response;
}

// Export for use in other scripts
window.authUtils = {
    makeAuthenticatedRequest,
    getToken: () => localStorage.getItem('access_token'),
    getW3Id: () => localStorage.getItem('w3_id'),
    isAuthenticated: () => !!localStorage.getItem('access_token')
};

// Made with Bob
