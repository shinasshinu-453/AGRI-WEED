import {
    collection,
    addDoc,
    updateDoc,
    deleteDoc,
    doc,
    getDocs,
    getDoc,
    query,
    where,
    orderBy,
    limit,
    onSnapshot,
    Timestamp,
    QueryConstraint,
    startAfter,
    DocumentSnapshot,
} from 'firebase/firestore';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { db, storage } from '../lib/firebase';

// Types
export interface Detection {
    id?: string;
    filename: string;
    timestamp: Timestamp;
    weedsDetected: number;
    cropsDetected: number;
    status: 'pending' | 'processed' | 'failed';
    userId: string;
    imageUrl?: string;
    cropType?: string;
}

export interface User {
    id?: string;
    name: string;
    email: string;
    role: 'admin' | 'user';
    lastActive: Timestamp;
    detectionsCount: number;
}

export interface Activity {
    id?: string;
    type: string;
    description: string;
    timestamp: Timestamp;
    userId: string;
    userName?: string;
}

export interface Statistics {
    totalDetections: number;
    weedsDetected: number;
    cropsDetected: number;
    photosUploaded: number;
    activeUsers: number;
}

// Detection Operations
export const addDetection = async (detection: Omit<Detection, 'id' | 'timestamp'>): Promise<string> => {
    try {
        const docRef = await addDoc(collection(db, 'detections'), {
            ...detection,
            timestamp: Timestamp.now(),
        });

        // Log activity
        await logActivity({
            type: 'detection',
            description: `New detection: ${detection.filename}`,
            userId: detection.userId,
        });

        return docRef.id;
    } catch (error) {
        console.error('Error adding detection:', error);
        throw error;
    }
};

export const updateDetection = async (id: string, updates: Partial<Detection>): Promise<void> => {
    try {
        const docRef = doc(db, 'detections', id);
        await updateDoc(docRef, updates);
    } catch (error) {
        console.error('Error updating detection:', error);
        throw error;
    }
};

export const deleteDetection = async (id: string): Promise<void> => {
    try {
        await deleteDoc(doc(db, 'detections', id));
    } catch (error) {
        console.error('Error deleting detection:', error);
        throw error;
    }
};

export const getDetections = async (
    pageSize: number = 10,
    lastDoc?: DocumentSnapshot,
    filters?: { status?: string; userId?: string }
): Promise<{ detections: Detection[]; lastDoc: DocumentSnapshot | null }> => {
    try {
        const constraints: QueryConstraint[] = [orderBy('timestamp', 'desc'), limit(pageSize)];

        if (filters?.status) {
            constraints.unshift(where('status', '==', filters.status));
        }
        if (filters?.userId) {
            constraints.unshift(where('userId', '==', filters.userId));
        }
        if (lastDoc) {
            constraints.push(startAfter(lastDoc));
        }

        const q = query(collection(db, 'detections'), ...constraints);
        const snapshot = await getDocs(q);

        const detections = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
        })) as Detection[];

        const lastVisible = snapshot.docs[snapshot.docs.length - 1] || null;

        return { detections, lastDoc: lastVisible };
    } catch (error) {
        console.error('Error getting detections:', error);
        throw error;
    }
};

// Real-time listener for detections
export const subscribeToDetections = (
    callback: (detections: Detection[]) => void,
    filters?: { status?: string; limit?: number }
): (() => void) => {
    const constraints: QueryConstraint[] = [orderBy('timestamp', 'desc')];

    if (filters?.status) {
        constraints.unshift(where('status', '==', filters.status));
    }
    if (filters?.limit) {
        constraints.push(limit(filters.limit));
    }

    const q = query(collection(db, 'detections'), ...constraints);

    return onSnapshot(q, (snapshot) => {
        const detections = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
        })) as Detection[];
        callback(detections);
    });
};

// Statistics
export const getStatistics = async (): Promise<Statistics> => {
    try {
        const detectionsSnapshot = await getDocs(collection(db, 'detections'));
        const usersSnapshot = await getDocs(collection(db, 'users'));

        let totalDetections = 0;
        let weedsDetected = 0;
        let cropsDetected = 0;

        detectionsSnapshot.forEach(doc => {
            const data = doc.data();
            totalDetections++;
            weedsDetected += data.weedsDetected || 0;
            cropsDetected += data.cropsDetected || 0;
        });

        return {
            totalDetections,
            weedsDetected,
            cropsDetected,
            photosUploaded: totalDetections,
            activeUsers: usersSnapshot.size,
        };
    } catch (error) {
        console.error('Error getting statistics:', error);
        throw error;
    }
};

// Real-time statistics listener
export const subscribeToStatistics = (callback: (stats: Statistics) => void): (() => void) => {
    const unsubDetections = onSnapshot(collection(db, 'detections'), async () => {
        const stats = await getStatistics();
        callback(stats);
    });

    return unsubDetections;
};

// User Operations
export const getUsers = async (): Promise<User[]> => {
    try {
        const snapshot = await getDocs(query(collection(db, 'users'), orderBy('lastActive', 'desc')));
        return snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
        })) as User[];
    } catch (error) {
        console.error('Error getting users:', error);
        throw error;
    }
};

export const updateUser = async (id: string, updates: Partial<User>): Promise<void> => {
    try {
        const docRef = doc(db, 'users', id);
        await updateDoc(docRef, updates);
    } catch (error) {
        console.error('Error updating user:', error);
        throw error;
    }
};

// Activity Logging
export const logActivity = async (activity: Omit<Activity, 'id' | 'timestamp'>): Promise<void> => {
    try {
        await addDoc(collection(db, 'activities'), {
            ...activity,
            timestamp: Timestamp.now(),
        });
    } catch (error) {
        console.error('Error logging activity:', error);
    }
};

export const getActivities = async (limitCount: number = 10): Promise<Activity[]> => {
    try {
        const q = query(collection(db, 'activities'), orderBy('timestamp', 'desc'), limit(limitCount));
        const snapshot = await getDocs(q);
        return snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
        })) as Activity[];
    } catch (error) {
        console.error('Error getting activities:', error);
        throw error;
    }
};

// Real-time activities listener
export const subscribeToActivities = (
    callback: (activities: Activity[]) => void,
    limitCount: number = 10
): (() => void) => {
    const q = query(collection(db, 'activities'), orderBy('timestamp', 'desc'), limit(limitCount));

    return onSnapshot(q, (snapshot) => {
        const activities = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
        })) as Activity[];
        callback(activities);
    });
};

// Image Upload
export const uploadImage = async (file: File, path: string): Promise<string> => {
    try {
        const storageRef = ref(storage, path);
        await uploadBytes(storageRef, file);
        const url = await getDownloadURL(storageRef);
        return url;
    } catch (error) {
        console.error('Error uploading image:', error);
        throw error;
    }
};

// Export data to CSV
export const exportDetectionsToCSV = (detections: Detection[]): void => {
    const headers = ['Filename', 'Timestamp', 'Weeds Detected', 'Crops Detected', 'Status'];
    const rows = detections.map(d => [
        d.filename,
        d.timestamp.toDate().toLocaleString(),
        d.weedsDetected,
        d.cropsDetected,
        d.status,
    ]);

    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `detections_${new Date().toISOString()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
};

// Search detections
export const searchDetections = async (searchTerm: string): Promise<Detection[]> => {
    try {
        const snapshot = await getDocs(collection(db, 'detections'));
        const detections = snapshot.docs.map(doc => ({
            id: doc.id,
            ...doc.data(),
        })) as Detection[];

        return detections.filter(d =>
            d.filename.toLowerCase().includes(searchTerm.toLowerCase())
        );
    } catch (error) {
        console.error('Error searching detections:', error);
        throw error;
    }
};
