// Authentication functionality
let currentUser = JSON.parse(localStorage.getItem('currentUser'));
let users = JSON.parse(localStorage.getItem('users')) || [];

// Initialize demo users if none exist
if (users.length === 0) {
    users = [
        {
            name: "Demo Farmer",
            email: "demo@livestockcare.ai",
            password: "demo123",
            userType: "farmer",
            joinDate: new Date().toISOString()
        }
    ];
    localStorage.setItem('users', JSON.stringify(users));
}

// Function to show specific page and hide others
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    document.getElementById(pageId).classList.add('active');
    updateNavigation();
}

// Update navigation based on user authentication
function updateNavigation() {
    const authButtons = document.getElementById('authButtons');
    const userMenu = document.getElementById('userMenu');
    const userName = document.getElementById('userName');
    
    if (currentUser) {
        if (authButtons) authButtons.style.display = 'none';
        if (userMenu) userMenu.style.display = 'flex';
        if (userName) userName.textContent = currentUser.name;
        
        // Update dashboard if we're on that page
        if (document.getElementById('userGreeting')) {
            document.getElementById('userGreeting').textContent = currentUser.name;
        }
        if (document.getElementById('dashboardUserName')) {
            document.getElementById('dashboardUserName').textContent = currentUser.name;
        }
    } else {
        if (authButtons) authButtons.style.display = 'flex';
        if (userMenu) userMenu.style.display = 'none';
    }
}

// Login function
function loginUser(email, password) {
    const user = users.find(u => u.email === email && u.password === password);
    if (user) {
        currentUser = user;
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        updateNavigation();
        return true;
    }
    return false;
}

// Create account function
function createAccount(name, email, password, userType) {
    // Check if user already exists
    if (users.find(u => u.email === email)) {
        return false;
    }
    
    const newUser = {
        name,
        email,
        password,
        userType,
        joinDate: new Date().toISOString()
    };
    
    users.push(newUser);
    localStorage.setItem('users', JSON.stringify(users));
    
    currentUser = newUser;
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    updateNavigation();
    
    return true;
}

// Logout function
function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    updateNavigation();
    window.location.href = 'index.html';
}

// Password strength checker
function checkPasswordStrength(password) {
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    
    let strength = 0;
    let feedback = '';
    
    if (password.length >= 8) strength += 1;
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength += 1;
    if (password.match(/\d/)) strength += 1;
    if (password.match(/[^a-zA-Z\d]/)) strength += 1;
    
    switch(strength) {
        case 0:
        case 1:
            strengthBar.style.width = '25%';
            strengthBar.style.background = 'var(--danger)';
            strengthText.textContent = 'Weak password';
            strengthText.style.color = 'var(--danger)';
            break;
        case 2:
            strengthBar.style.width = '50%';
            strengthBar.style.background = 'var(--warning)';
            strengthText.textContent = 'Fair password';
            strengthText.style.color = 'var(--warning)';
            break;
        case 3:
            strengthBar.style.width = '75%';
            strengthBar.style.background = 'var(--secondary)';
            strengthText.textContent = 'Good password';
            strengthText.style.color = 'var(--secondary)';
            break;
        case 4:
            strengthBar.style.width = '100%';
            strengthBar.style.background = 'var(--success)';
            strengthText.textContent = 'Strong password';
            strengthText.style.color = 'var(--success)';
            break;
    }
}

// Check if user is logged in when accessing protected pages
function checkAuth() {
    if (!currentUser && (window.location.pathname.includes('dashboard.html') || 
                         window.location.pathname.includes('dashboard'))) {
        window.location.href = 'login.html';
    }
}

// Initialize auth check on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    updateNavigation();
});