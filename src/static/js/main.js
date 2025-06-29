// Main JavaScript for Crypto Trading SaaS

// Global state
window.AppState = {
    user: null,
    isAuthenticated: false,
    currentPage: 'landing',
    subscription: null,
    apiKeys: {},
    dashboardData: {}
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Hide loading screen after a short delay
        setTimeout(() => {
            const loadingScreen = document.getElementById('loading-screen');
            if (loadingScreen) {
                loadingScreen.style.opacity = '0';
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                }, 500);
            }
        }, 1500);

        // Check authentication status
        await checkAuthStatus();
        
        // Initialize navigation
        initializeNavigation();
        
        // Initialize forms
        initializeForms();
        
        // Initialize dashboard if authenticated
        if (AppState.isAuthenticated) {
            await initializeDashboard();
        }
        
        // Initialize page routing
        initializeRouting();
        
    } catch (error) {
        console.error('App initialization error:', error);
        showToast('Error', 'Failed to initialize application', 'error');
    }
}

// Authentication status check
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            AppState.user = data.user;
            AppState.isAuthenticated = data.authenticated;
            AppState.subscription = data.subscription;
            
            updateUIForAuthState();
        }
    } catch (error) {
        console.error('Auth status check failed:', error);
    }
}

// Update UI based on authentication state
function updateUIForAuthState() {
    const guestLinks = document.getElementById('nav-links-guest');
    const userLinks = document.getElementById('nav-links-user');
    
    if (AppState.isAuthenticated) {
        guestLinks.classList.add('hidden');
        userLinks.classList.remove('hidden');
        
        // Update user info
        const userInitials = document.getElementById('user-initials');
        const userName = document.getElementById('user-name');
        
        if (AppState.user) {
            const initials = (AppState.user.first_name?.[0] || '') + (AppState.user.last_name?.[0] || '');
            userInitials.textContent = initials || AppState.user.email[0].toUpperCase();
            
            if (userName) {
                userName.textContent = AppState.user.first_name || AppState.user.email;
            }
        }
        
        // Show dashboard if user has subscription
        if (AppState.subscription?.has_active_subscription) {
            showDashboard();
        } else {
            showSubscriptionNotice();
        }
    } else {
        guestLinks.classList.remove('hidden');
        userLinks.classList.add('hidden');
        showLandingPage();
    }
}

// Navigation functions
function initializeNavigation() {
    // User avatar dropdown
    const userAvatar = document.getElementById('user-avatar');
    const userDropdown = document.getElementById('user-dropdown');
    
    if (userAvatar && userDropdown) {
        userAvatar.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        document.addEventListener('click', () => {
            userDropdown.classList.remove('show');
        });
    }
    
    // Mobile navigation toggle
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('show');
        });
    }
}

// Page navigation functions
function showLandingPage() {
    hideAllPages();
    document.getElementById('landing-page').classList.remove('hidden');
    AppState.currentPage = 'landing';
}

function showLogin() {
    hideAllPages();
    document.getElementById('auth-page').classList.remove('hidden');
    document.getElementById('login-form').classList.remove('hidden');
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('forgot-password-form').classList.add('hidden');
    AppState.currentPage = 'login';
}

function showRegister() {
    hideAllPages();
    document.getElementById('auth-page').classList.remove('hidden');
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.remove('hidden');
    document.getElementById('forgot-password-form').classList.add('hidden');
    AppState.currentPage = 'register';
}

function showForgotPassword() {
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('forgot-password-form').classList.remove('hidden');
}

function showDashboard() {
    if (!AppState.isAuthenticated) {
        showLogin();
        return;
    }
    
    if (!AppState.subscription?.has_active_subscription) {
        showSubscriptionNotice();
        return;
    }
    
    hideAllPages();
    document.getElementById('dashboard-page').classList.remove('hidden');
    document.getElementById('dashboard-content').classList.remove('hidden');
    document.getElementById('subscription-notice').classList.add('hidden');
    AppState.currentPage = 'dashboard';
    
    // Load dashboard data
    loadDashboardData();
}

function showSubscriptionNotice() {
    hideAllPages();
    document.getElementById('dashboard-page').classList.remove('hidden');
    document.getElementById('dashboard-content').classList.add('hidden');
    document.getElementById('subscription-notice').classList.remove('hidden');
    AppState.currentPage = 'subscription-required';
}

function showAnalysis() {
    // TODO: Implement analysis page
    showToast('Coming Soon', 'Analysis page is under development', 'info');
}

function showPortfolio() {
    // TODO: Implement portfolio page
    showToast('Coming Soon', 'Portfolio page is under development', 'info');
}

function showSettings() {
    // TODO: Implement settings page
    showToast('Coming Soon', 'Settings page is under development', 'info');
}

function showProfile() {
    // TODO: Implement profile page
    showToast('Coming Soon', 'Profile page is under development', 'info');
}

function showSubscription() {
    // TODO: Implement subscription management page
    showToast('Coming Soon', 'Subscription management is under development', 'info');
}

function showPricing() {
    showLandingPage();
    setTimeout(() => {
        document.getElementById('pricing').scrollIntoView({ behavior: 'smooth' });
    }, 100);
}

function showDemo() {
    showToast('Demo', 'Demo functionality coming soon!', 'info');
}

function hideAllPages() {
    const pages = ['landing-page', 'auth-page', 'dashboard-page'];
    pages.forEach(pageId => {
        const page = document.getElementById(pageId);
        if (page) {
            page.classList.add('hidden');
        }
    });
}

// Form initialization
function initializeForms() {
    // Login form
    const loginForm = document.getElementById('login-form-element');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form
    const registerForm = document.getElementById('register-form-element');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Forgot password form
    const forgotForm = document.getElementById('forgot-password-form-element');
    if (forgotForm) {
        forgotForm.addEventListener('submit', handleForgotPassword);
    }
    
    // Password strength indicator
    const passwordInput = document.getElementById('register-password');
    if (passwordInput) {
        passwordInput.addEventListener('input', updatePasswordStrength);
    }
}

// Authentication handlers
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const remember = document.getElementById('login-remember').checked;
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ email, password, remember })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Success', 'Login successful!', 'success');
            AppState.user = data.user;
            AppState.isAuthenticated = true;
            AppState.subscription = data.subscription;
            updateUIForAuthState();
        } else {
            showToast('Error', data.error || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Error', 'Login failed. Please try again.', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const firstName = document.getElementById('register-first-name').value;
    const lastName = document.getElementById('register-last-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                email,
                password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Success', 'Registration successful! Please check your email to verify your account.', 'success');
            showLogin();
        } else {
            showToast('Error', data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Error', 'Registration failed. Please try again.', 'error');
    }
}

async function handleForgotPassword(e) {
    e.preventDefault();
    
    const email = document.getElementById('forgot-email').value;
    
    try {
        const response = await fetch('/api/auth/forgot-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Success', 'Password reset link sent to your email!', 'success');
            showLogin();
        } else {
            showToast('Error', data.error || 'Failed to send reset link', 'error');
        }
    } catch (error) {
        console.error('Forgot password error:', error);
        showToast('Error', 'Failed to send reset link. Please try again.', 'error');
    }
}

async function logout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            AppState.user = null;
            AppState.isAuthenticated = false;
            AppState.subscription = null;
            updateUIForAuthState();
            showToast('Success', 'Logged out successfully', 'success');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showToast('Error', 'Logout failed', 'error');
    }
}

// Password strength checker
function updatePasswordStrength() {
    const password = document.getElementById('register-password').value;
    const strengthIndicator = document.getElementById('password-strength');
    
    if (!strengthIndicator) return;
    
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    
    strengthIndicator.className = 'password-strength';
    
    if (strength <= 2) {
        strengthIndicator.classList.add('weak');
    } else if (strength <= 4) {
        strengthIndicator.classList.add('medium');
    } else {
        strengthIndicator.classList.add('strong');
    }
}

// Subscription management
async function selectPlan(planId) {
    if (!AppState.isAuthenticated) {
        showRegister();
        return;
    }
    
    try {
        const response = await fetch('/api/payments/create-checkout-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ plan_id: planId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            window.location.href = data.checkout_url;
        } else {
            showToast('Error', data.error || 'Failed to create checkout session', 'error');
        }
    } catch (error) {
        console.error('Checkout error:', error);
        showToast('Error', 'Failed to start checkout process', 'error');
    }
}

// Dashboard functions
async function initializeDashboard() {
    if (!AppState.isAuthenticated || !AppState.subscription?.has_active_subscription) {
        return;
    }
    
    try {
        await loadDashboardData();
        initializeCharts();
    } catch (error) {
        console.error('Dashboard initialization error:', error);
    }
}

async function loadDashboardData() {
    try {
        // Load portfolio data, market overview, recent analysis, etc.
        // This would typically make multiple API calls
        
        // For now, show placeholder data
        updateDashboardStats({
            portfolioValue: '$12,345',
            portfolioChange: '+5.67%',
            aiScore: '8.5/10',
            activeSignals: '3'
        });
        
        await loadRecentAnalysis();
        
    } catch (error) {
        console.error('Dashboard data loading error:', error);
        showToast('Error', 'Failed to load dashboard data', 'error');
    }
}

function updateDashboardStats(stats) {
    const elements = {
        'portfolio-value': stats.portfolioValue,
        'portfolio-change': stats.portfolioChange,
        'ai-score': stats.aiScore,
        'active-signals': stats.activeSignals
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

async function loadRecentAnalysis() {
    try {
        const response = await fetch('/api/cache', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            displayRecentAnalysis(data.cache_entries || []);
        }
    } catch (error) {
        console.error('Recent analysis loading error:', error);
    }
}

function displayRecentAnalysis(analyses) {
    const container = document.getElementById('recent-analysis');
    if (!container) return;
    
    if (analyses.length === 0) {
        container.innerHTML = '<p class="text-center">No recent analysis found. <a href="#" onclick="showAnalysis()" class="link">Run your first analysis</a></p>';
        return;
    }
    
    container.innerHTML = analyses.slice(0, 5).map(analysis => `
        <div class="analysis-item">
            <div class="analysis-symbol">${analysis.symbol}</div>
            <div class="analysis-type">${analysis.analysis_type}</div>
            <div class="analysis-date">${new Date(analysis.created_at).toLocaleDateString()}</div>
        </div>
    `).join('');
}

async function refreshDashboard() {
    showToast('Info', 'Refreshing dashboard...', 'info');
    await loadDashboardData();
    showToast('Success', 'Dashboard refreshed!', 'success');
}

// Chart initialization
function initializeCharts() {
    initializePortfolioChart();
    initializeMarketChart();
}

function initializePortfolioChart() {
    const ctx = document.getElementById('portfolio-chart');
    if (!ctx) return;
    
    // Sample data - replace with real data
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Portfolio Value',
                data: [10000, 11200, 10800, 12500, 11900, 12345],
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function initializeMarketChart() {
    const ctx = document.getElementById('market-chart');
    if (!ctx) return;
    
    // Sample data - replace with real data
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Bitcoin', 'Ethereum', 'Solana', 'Others'],
            datasets: [{
                data: [45, 25, 15, 15],
                backgroundColor: [
                    'rgb(99, 102, 241)',
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)',
                    'rgb(156, 163, 175)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Utility functions
function initializeRouting() {
    // Handle browser back/forward buttons
    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.page) {
            switch (e.state.page) {
                case 'landing':
                    showLandingPage();
                    break;
                case 'login':
                    showLogin();
                    break;
                case 'register':
                    showRegister();
                    break;
                case 'dashboard':
                    showDashboard();
                    break;
            }
        }
    });
    
    // Set initial state
    history.replaceState({ page: AppState.currentPage }, '', window.location.href);
}

// Modal functions
function showModal(title, content) {
    const modal = document.getElementById('modal-overlay');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    
    if (modal && modalTitle && modalContent) {
        modalTitle.textContent = title;
        modalContent.innerHTML = content;
        modal.classList.add('show');
    }
}

function closeModal() {
    const modal = document.getElementById('modal-overlay');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Toast notification system
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Export functions for global access
window.showLandingPage = showLandingPage;
window.showLogin = showLogin;
window.showRegister = showRegister;
window.showForgotPassword = showForgotPassword;
window.showDashboard = showDashboard;
window.showAnalysis = showAnalysis;
window.showPortfolio = showPortfolio;
window.showSettings = showSettings;
window.showProfile = showProfile;
window.showSubscription = showSubscription;
window.showPricing = showPricing;
window.showDemo = showDemo;
window.selectPlan = selectPlan;
window.logout = logout;
window.refreshDashboard = refreshDashboard;
window.showModal = showModal;
window.closeModal = closeModal;
window.showToast = showToast;

