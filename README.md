# Blood Donation System - Complete Web Application

A comprehensive web-based blood donation management system built with HTML, CSS, and JavaScript.

## Features

✅ **User Authentication System**
- Secure login with ID, Password, and Phone Number
- User registration with email verification
- Password confirmation matching

✅ **User Dashboard**
- Welcome message with user profile information
- Quick statistics and blood availability
- Quick action buttons
- Blood group statistics

✅ **Search Donor System**
- Search donors by blood group
- Search donors by name
- Display donor contact information
- Direct contact options

✅ **About Us Page**
- Mission and vision statements
- Eligibility criteria for blood donation
- Safety and privacy information
- Key features and benefits
- Impact statistics

✅ **Contact Us Page**
- Contact information with phone numbers
- Multiple email options
- Operating hours including 24/7 emergency
- Contact form for messages
- FAQ section
- Blood request functionality

✅ **Navigation Bar**
- Sticky navigation across all pages
- Easy navigation between sections
- Logout functionality
- Responsive design

## File Structure

```
blood-donation/
├── index.html              # Login page
├── register.html           # Registration page
├── dashboard.html          # Main dashboard
├── search-donor.html       # Donor search page
├── about-us.html           # About us information
├── contact-us.html         # Contact us form
├── styles.css              # All styling
└── script.js               # JavaScript logic
```

## Default Login Credentials

- **User ID**: admin
- **Password**: admin123
- **Phone Number**: 01765131604

## How to Use

1. **Start the Application**
   - Open `index.html` in a web browser
   - Or use any local web server

2. **Login**
   - Use the default credentials above
   - Or register a new account

3. **Navigate**
   - Dashboard: View user profile and statistics
   - Search Donor: Find donors by blood group or name
   - About Us: Learn about blood donation benefits
   - Contact Us: Send messages or request blood urgently

4. **Register New User**
   - Click "Register here" on login page
   - Fill in all required information
   - Password must be confirmed
   - User ID must be unique

## Data Storage

All data is stored in browser LocalStorage:
- User credentials and profiles
- Contact messages
- Emergency alerts
- Session information

## Blood Groups Supported

- O+ (Most Common)
- O- (Universal Donor)
- A+
- A-
- B+
- B-
- AB+ (Universal Recipient)
- AB-

## Key Functions (Accessible in Console)

```javascript
// Authentication
bloodDonationApp.login(id, password, phone)
bloodDonationApp.logout()
bloodDonationApp.isLoggedIn()

// User Management
bloodDonationApp.getAllUsers()
bloodDonationApp.register(name, id, email, phone, bloodGroup, password)

// Search
bloodDonationApp.searchDonorsByBloodGroup(bloodGroup)
bloodDonationApp.searchDonorsByName(name)

// Statistics
bloodDonationApp.getBloodGroupStats()
bloodDonationApp.getTotalDonors()
bloodDonationApp.getDonationStats()

// Messages
bloodDonationApp.saveContactMessage(name, email, phone, subject, bloodGroup, message)
bloodDonationApp.getAllContactMessages()

// Data Management
bloodDonationApp.backupData()
bloodDonationApp.restoreData(backupData)
bloodDonationApp.showAllData()
```

## How to Test

1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Type: `bloodDonationApp.showAllData()` to see all data
4. Type: `bloodDonationApp.getAllUsers()` to see all registered users
5. Type: `bloodDonationApp.getBloodGroupStats()` to see blood group statistics

## Registration Requirements

- Full Name: Required
- User ID: 3-20 characters, alphanumeric + underscore
- Email: Valid email format (unique)
- Phone Number: 11 digits (unique)
- Blood Group: Select from dropdown
- Password: Minimum 6 characters
- Password Confirmation: Must match password

## Security Features

- Password protection
- User ID uniqueness checking
- Email duplicate prevention
- Phone number duplicate prevention
- LocalStorage encryption ready
- Session management

## Responsive Design

- Mobile-friendly interface
- Tablet support
- Desktop optimization
- Flexible grid layouts
- Responsive navigation

## Customization

You can easily customize:
- Contact information in contact-us.html
- About information in about-us.html
- Colors and styles in styles.css
- Validation rules in script.js
- Blood group information in script.js

## Browser Support

- Chrome (Latest)
- Firefox (Latest)
- Safari (Latest)
- Edge (Latest)
- Mobile Browsers

## Tips for Development

1. Use browser console to debug: `bloodDonationApp.showAllData()`
2. Clear data: `localStorage.clear()`
3. Check specific user: `bloodDonationApp.getAllUsers()`
4. Backup before testing: `bloodDonationApp.backupData()`

## Future Enhancements

Possible features to add:
- Backend server integration
- Email notifications
- SMS alerts
- Calendar scheduling
- Real-time donor location
- Admin panel
- Donation history tracking
- Certificate generation
- Donation analytics
- Hospital integration

## License

This project is free to use and modify for educational and personal purposes.

## Support

For issues or questions, use the Contact Us page within the application.

---

**Save Lives, One Drop at a Time!** 🩸
