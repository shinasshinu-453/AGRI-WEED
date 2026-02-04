import { collection, addDoc, Timestamp } from 'firebase/firestore';
import { db } from '../lib/firebase';

/**
 * Sample Data Seeder for Firebase
 * Run this to populate your Firestore with demo data for testing
 */

export const seedSampleData = async () => {
    try {
        console.log('🌱 Seeding sample data...');

        // Sample detections
        const sampleDetections = [
            {
                filename: 'field_scan_001.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 28, 10, 30)),
                weedsDetected: 45,
                cropsDetected: 120,
                status: 'processed',
                userId: 'admin',
                cropType: 'Wheat',
            },
            {
                filename: 'wheat_field_002.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 28, 9, 15)),
                weedsDetected: 32,
                cropsDetected: 95,
                status: 'processed',
                userId: 'admin',
                cropType: 'Wheat',
            },
            {
                filename: 'cotton_scan_003.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 27, 16, 20)),
                weedsDetected: 18,
                cropsDetected: 78,
                status: 'pending',
                userId: 'user1',
                cropType: 'Cotton',
            },
            {
                filename: 'field_view_004.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 27, 14, 10)),
                weedsDetected: 67,
                cropsDetected: 145,
                status: 'processed',
                userId: 'admin',
                cropType: 'Wheat',
            },
            {
                filename: 'crop_analysis_005.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 26, 11, 45)),
                weedsDetected: 0,
                cropsDetected: 0,
                status: 'failed',
                userId: 'user2',
                cropType: 'Corn',
            },
            {
                filename: 'morning_scan_006.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 26, 8, 30)),
                weedsDetected: 23,
                cropsDetected: 88,
                status: 'processed',
                userId: 'admin',
                cropType: 'Wheat',
            },
            {
                filename: 'afternoon_check_007.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 25, 15, 20)),
                weedsDetected: 41,
                cropsDetected: 102,
                status: 'processed',
                userId: 'user1',
                cropType: 'Wheat',
            },
            {
                filename: 'field_survey_008.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 25, 10, 15)),
                weedsDetected: 29,
                cropsDetected: 76,
                status: 'processed',
                userId: 'admin',
                cropType: 'Cotton',
            },
            {
                filename: 'early_detection_009.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 24, 7, 45)),
                weedsDetected: 15,
                cropsDetected: 65,
                status: 'processed',
                userId: 'user2',
                cropType: 'Wheat',
            },
            {
                filename: 'weekly_scan_010.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 24, 12, 0)),
                weedsDetected: 38,
                cropsDetected: 110,
                status: 'processed',
                userId: 'admin',
                cropType: 'Wheat',
            },
        ];

        // Add detections
        for (const detection of sampleDetections) {
            await addDoc(collection(db, 'detections'), detection);
        }
        console.log(`✅ Added ${sampleDetections.length} sample detections`);

        // Sample users
        const sampleUsers = [
            {
                name: 'Admin User',
                email: 'admin@agrivision.com',
                role: 'admin',
                lastActive: Timestamp.now(),
                detectionsCount: 15,
            },
            {
                name: 'John Farmer',
                email: 'john@farm.com',
                role: 'user',
                lastActive: Timestamp.fromDate(new Date(2026, 0, 27, 14, 30)),
                detectionsCount: 8,
            },
            {
                name: 'Sarah Green',
                email: 'sarah@agri.com',
                role: 'user',
                lastActive: Timestamp.fromDate(new Date(2026, 0, 26, 9, 15)),
                detectionsCount: 12,
            },
        ];

        // Add users
        for (const user of sampleUsers) {
            await addDoc(collection(db, 'users'), user);
        }
        console.log(`✅ Added ${sampleUsers.length} sample users`);

        // Sample activities
        const sampleActivities = [
            {
                type: 'detection',
                description: 'New detection: field_scan_001.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 28, 10, 30)),
                userId: 'admin',
                userName: 'Admin User',
            },
            {
                type: 'detection',
                description: 'New detection: wheat_field_002.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 28, 9, 15)),
                userId: 'admin',
                userName: 'Admin User',
            },
            {
                type: 'user',
                description: 'User John Farmer logged in',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 27, 14, 30)),
                userId: 'user1',
                userName: 'John Farmer',
            },
            {
                type: 'detection',
                description: 'New detection: cotton_scan_003.jpg',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 27, 16, 20)),
                userId: 'user1',
                userName: 'John Farmer',
            },
            {
                type: 'system',
                description: 'System health check completed',
                timestamp: Timestamp.fromDate(new Date(2026, 0, 27, 12, 0)),
                userId: 'system',
                userName: 'System',
            },
        ];

        // Add activities
        for (const activity of sampleActivities) {
            await addDoc(collection(db, 'activities'), activity);
        }
        console.log(`✅ Added ${sampleActivities.length} sample activities`);

        console.log('🎉 Sample data seeding completed!');
        return true;
    } catch (error) {
        console.error('❌ Error seeding data:', error);
        throw error;
    }
};

// Helper function to clear all data (use with caution!)
export const clearAllData = async () => {
    console.warn('⚠️  This will delete all data from Firestore!');
    // Implementation would go here if needed
};
