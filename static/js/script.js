// ================= INITIALIZE SYSTEM =================

function initializeSystem() {
    try {
        let users = localStorage.getItem('bloodDonationUsers');

        // Dynamically generating users: maximum of 10 donors per blood group per location
        const sampleUsers = [
            { id: 'admin', password: 'admin123', name: 'Admin', email: 'admin@email.com', phone: '01765131604', bloodGroup: 'O+', location: 'Dhaka' }
        ];

        const bloodGroups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'];
        const locations = ['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi', 'Khulna', 'Barisal', 'Rangpur', 'Mymensingh'];
        
        let counter = 1;

        locations.forEach(loc => {
            bloodGroups.forEach(bg => {
                // Generate a random number from 5 to 10 donors per group per location
                const numDonors = Math.floor(Math.random() * 6) + 5; 
                for (let i = 0; i < numDonors; i++) {
                    const userId = `donor${counter}`;
                    sampleUsers.push({
                        id: userId,
                        password: 'password123',
                        name: `${loc} ${bg} Donor ${i + 1}`,
                        email: `${userId}@email.com`,
                        phone: `017${Math.floor(10000000 + Math.random() * 90000000)}`,
                        bloodGroup: bg,
                        location: loc,
                        lastDonation: i % 2 === 0 ? '2026-03-01' : null,
                        donations: i % 2 === 0 ? [{ date: '2026-03-01', location: `${loc} Hospital` }] : []
                    });
                    counter++;
                }
            });
        });

        if (!users) {
            localStorage.setItem('bloodDonationUsers', JSON.stringify(sampleUsers));
        } else {
            try {
                const parsedUsers = JSON.parse(users);

                if (!Array.isArray(parsedUsers) || parsedUsers.length === 0) {
                    localStorage.setItem('bloodDonationUsers', JSON.stringify(sampleUsers));
                } else {
                    const adminExists = parsedUsers.some(u => u.id === 'admin');

                    if (!adminExists) {
                        parsedUsers.unshift(sampleUsers[0]);
                        localStorage.setItem('bloodDonationUsers', JSON.stringify(parsedUsers));
                    }
                }
            } catch {
                localStorage.setItem('bloodDonationUsers', JSON.stringify(sampleUsers));
            }
        }
    } catch (e) {
        console.error('Init error:', e);
    }
}

initializeSystem();


// ================= AUTH =================

function login(id, password, phone) {
    const users = getAllUsers();

    const user = users.find(u =>
        u.id.toLowerCase() === id.toLowerCase() &&
        u.password === password &&
        u.phone === phone
    );

    if (user) {
        localStorage.setItem('currentUser', JSON.stringify(user));
        return true;
    } else {
        alert('Invalid Login! Please check your User ID, Password, and Phone Number.');
        return false;
    }
}

function logout() {
    localStorage.removeItem('currentUser');
}

function getCurrentUser() {
    const user = localStorage.getItem('currentUser');
    return user ? JSON.parse(user) : null;
}

function isLoggedIn() {
    return getCurrentUser() !== null;
}


// ================= REGISTER =================

function register(name, id, email, phone, bloodGroup, location, area, password) {
    const users = getAllUsers();

    if (users.find(u => u.id === id)) {
        alert('ID already exists!');
        return false;
    }

    if (users.find(u => u.email === email)) {
        alert('Email already exists!');
        return false;
    }

    if (users.find(u => u.phone === phone)) {
        alert('Phone already exists!');
        return false;
    }

    const newUser = {
        id,
        name,
        email,
        phone,
        bloodGroup,
        password,
        location: location || 'Unknown',
        area: area || '',
        date: new Date().toLocaleDateString(),
        lastDonation: null,
        donations: []
    };

    users.push(newUser);
    localStorage.setItem('bloodDonationUsers', JSON.stringify(users));

    return true;
}



// ================= USERS =================

function getAllUsers() {
    const users = localStorage.getItem('bloodDonationUsers');
    return users ? JSON.parse(users) : [];
}

function deleteUser(id) {
    const users = getAllUsers().filter(u => u.id !== id);
    localStorage.setItem('bloodDonationUsers', JSON.stringify(users));
}


// ================= SEARCH =================

function searchDonorsByBloodGroup(group) {
    return getAllUsers().filter(u => u.bloodGroup === group);
}

function searchDonorsByName(name) {
    return getAllUsers().filter(u =>
        u.name.toLowerCase().includes(name.toLowerCase())
    );
}


// ================= STATS =================

function getBloodGroupStats() {
    const users = getAllUsers();
    const groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'];

    const stats = {};

    groups.forEach(g => {
        stats[g] = users.filter(u => u.bloodGroup === g).length;
    });

    return stats;
}

function getTotalDonors() {
    return getAllUsers().length;
}


// ================= CONTACT =================

function saveContactMessage(name, email, phone, subject, bloodGroup, message) {
    let messages = localStorage.getItem('contactMessages');
    messages = messages ? JSON.parse(messages) : [];

    messages.push({
        id: Date.now(),
        name,
        email,
        phone,
        subject,
        bloodGroup,
        message,
        date: new Date().toLocaleString()
    });

    localStorage.setItem('contactMessages', JSON.stringify(messages));
    return true;
}

function getAllContactMessages() {
    const messages = localStorage.getItem('contactMessages');
    return messages ? JSON.parse(messages) : [];
}


// ================= EMERGENCY =================

function findEmergencyDonor(group) {
    const donors = searchDonorsByBloodGroup(group);
    return donors.length ? donors[0] : null;
}

function sendEmergencyAlert(group, message) {
    let alerts = localStorage.getItem('emergencyAlerts');
    alerts = alerts ? JSON.parse(alerts) : [];

    alerts.push({
        id: Date.now(),
        group,
        message,
        time: new Date().toLocaleString()
    });

    localStorage.setItem('emergencyAlerts', JSON.stringify(alerts));
}


// ================= VALIDATION =================

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhone(phone) {
    return /^01[0-9]{9}$/.test(phone);
}

function validatePassword(password) {
    return password.length >= 6;
}


// ================= RESET =================

function resetSystem() {
    localStorage.removeItem('bloodDonationUsers');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('contactMessages');
    localStorage.removeItem('emergencyAlerts');

    initializeSystem();
    alert('System Reset Done! Refresh page.');
}

// ================= EXPORT =================

window.bloodApp = {
    login,
    logout,
    register,
    getAllUsers,
    searchDonorsByBloodGroup,
    searchDonorsByName,
    getBloodGroupStats,
    getTotalDonors,
    saveContactMessage,
    findEmergencyDonor,
    sendEmergencyAlert,
    resetSystem
};

// ================= GLOBAL NAVBAR UPDATE =================
document.addEventListener('DOMContentLoaded', () => {
    if (isLoggedIn()) {
        const currentUser = getCurrentUser();
        const navDashboard = document.getElementById('navDashboard');
        const navLogout = document.getElementById('navLogout');
        const navLogin = document.getElementById('navLogin');
        
        if (navDashboard) navDashboard.style.display = 'inline-block';
        if (navLogout) navLogout.style.display = 'inline-block';
        if (navLogin) navLogin.style.display = 'none';
        
        // Hide login and register links from standalone components anywhere on page
        const authLinks = document.querySelectorAll('a[href="login.html"], a[href="register.html"]');
        authLinks.forEach(link => {
            // Don't hide links inside the navbar if they are in the menu block, because the parent li is already hidden.
            // Just generic links can be hidden or changed.
        });
    }

    // ================= DARK MODE =================
    const themeBtn = document.getElementById('themeToggleBtn');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    if (currentTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (themeBtn) themeBtn.textContent = '☀️';
    }

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            let theme = document.documentElement.getAttribute('data-theme');
            if (theme === 'dark') {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
                themeBtn.textContent = '🌙';
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                themeBtn.textContent = '☀️';
            }
        });
    }
});
