# Firebase Setup Guide for Admin Dashboard

## Overview
The admin dashboard now features real-time data synchronization with Firebase, including:
- ✅ Live statistics updates
- ✅ Interactive charts (Line & Pie charts)
- ✅ Detection history with search & filter
- ✅ Real-time activity feed
- ✅ Toast notifications
- ✅ CSV export functionality
- ✅ Clickable stat cards

## Firebase Configuration

### Step 1: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Add project" or select an existing project
3. Follow the setup wizard

### Step 2: Enable Firestore Database

1. In your Firebase project, go to **Build** → **Firestore Database**
2. Click **Create database**
3. Choose **Start in test mode** (for development)
4. Select a location closest to you
5. Click **Enable**

### Step 3: Enable Firebase Storage (Optional)

1. Go to **Build** → **Storage**
2. Click **Get started**
3. Use default security rules for now
4. Click **Done**

### Step 4: Get Your Firebase Config

1. Go to **Project Settings** (gear icon)
2. Scroll down to **Your apps**
3. Click the **Web** icon (`</>`)
4. Register your app with a nickname (e.g., "AgriVision Admin")
5. Copy the `firebaseConfig` object

### Step 5: Add Config to Your Project

Create or update `.env.local` in your project root:

```env
VITE_FIREBASE_API_KEY=your_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

## Seeding Sample Data

To populate your Firestore with demo data for testing:

1. Open your browser console on the admin dashboard
2. Run the following command:

```javascript
import { seedSampleData } from './src/utils/seedData';
seedSampleData();
```

Or create a temporary button in your app to trigger the seeding.

### Manual Data Entry

You can also manually add data through the Firebase Console:

#### Detections Collection
```
Collection: detections
Document fields:
- filename: string
- timestamp: timestamp
- weedsDetected: number
- cropsDetected: number
- status: string ('processed', 'pending', or 'failed')
- userId: string
- cropType: string
```

#### Users Collection
```
Collection: users
Document fields:
- name: string
- email: string
- role: string ('admin' or 'user')
- lastActive: timestamp
- detectionsCount: number
```

#### Activities Collection
```
Collection: activities
Document fields:
- type: string
- description: string
- timestamp: timestamp
- userId: string
- userName: string
```

## Features Guide

### 1. Real-Time Statistics
- Stats automatically update when new data is added to Firestore
- Click on any stat card to trigger actions (filtering, notifications)

### 2. Interactive Charts
- **Line Chart**: Shows detection trends over the last 7 days
- **Pie Chart**: Displays weed vs crop distribution
- Hover over data points for detailed information

### 3. Detection History
- **Search**: Type in the search box to filter by filename
- **Filter**: Use the dropdown to filter by status (All, Processed, Pending, Failed)
- **Export**: Click "Export CSV" to download filtered data
- **Delete**: Click the trash icon to remove a detection

### 4. Activity Feed
- Shows the 5 most recent activities
- Updates in real-time as new activities are logged

### 5. To-Do List
- Add tasks by typing and pressing Enter or clicking the + button
- Click the circle to mark tasks as complete
- Hover over a task to see the delete button

## Firestore Security Rules

For production, update your Firestore security rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write for authenticated users
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## Troubleshooting

### "Firebase not configured" error
- Make sure your `.env.local` file exists and has all the required variables
- Restart your dev server after adding environment variables

### No data showing
- Check Firebase Console to ensure collections exist
- Run the sample data seeder
- Check browser console for errors

### Real-time updates not working
- Verify Firestore is enabled in your Firebase project
- Check that your security rules allow read access
- Ensure you're using the correct project ID

## Next Steps

1. **Authentication**: Integrate Firebase Authentication for user login
2. **User Management**: Add CRUD operations for users
3. **Advanced Filtering**: Add date range pickers and more filter options
4. **Notifications**: Set up Firebase Cloud Messaging for push notifications
5. **Analytics**: Integrate Firebase Analytics for usage tracking

## Support

For issues or questions, check:
- [Firebase Documentation](https://firebase.google.com/docs)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- Project GitHub issues
