import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  updateProfile
} from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { auth, db } from '../lib/firebase';

export type UserRole = 'user' | 'admin';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, role: UserRole) => Promise<void>;
  signup: (email: string, password: string, name: string, role: UserRole) => Promise<void>;
  logout: () => Promise<void>;
  initialize: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,

      initialize: () => {
        onAuthStateChanged(auth, async (firebaseUser) => {
          if (firebaseUser) {
            const token = await firebaseUser.getIdToken();
            const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
            
            if (userDoc.exists()) {
              const userData = userDoc.data();
              set({ 
                user: {
                  id: firebaseUser.uid,
                  email: firebaseUser.email || '',
                  name: userData.name || firebaseUser.displayName || '',
                  role: userData.role || 'user',
                  avatar: firebaseUser.photoURL || undefined,
                },
                token,
                isAuthenticated: true,
                isLoading: false
              });
            } else {
              // Handle case where user exists in Auth but not in Firestore
              set({ 
                user: {
                  id: firebaseUser.uid,
                  email: firebaseUser.email || '',
                  name: firebaseUser.displayName || '',
                  role: 'user',
                  avatar: firebaseUser.photoURL || undefined,
                },
                token,
                isAuthenticated: true,
                isLoading: false
              });
            }
          } else {
            set({ user: null, token: null, isAuthenticated: false, isLoading: false });
          }
        });
      },

      login: async (email: string, password: string, role: UserRole) => {
        try {
          const userCredential = await signInWithEmailAndPassword(auth, email, password);
          const firebaseUser = userCredential.user;
          const token = await firebaseUser.getIdToken();
          
          const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
          if (userDoc.exists()) {
            const userData = userDoc.data();
            if (userData.role !== role) {
              throw new Error(`Invalid role. This account is registered as ${userData.role}.`);
            }
            
            set({ 
              user: {
                id: firebaseUser.uid,
                email: firebaseUser.email || '',
                name: userData.name || firebaseUser.displayName || '',
                role: userData.role as UserRole,
                avatar: firebaseUser.photoURL || undefined,
              },
              token,
              isAuthenticated: true 
            });
          } else {
            // If doc doesn't exist, create it with requested role (fallback)
            const newUser = {
              name: firebaseUser.displayName || email.split('@')[0],
              role: role,
              email: email
            };
            await setDoc(doc(db, 'users', firebaseUser.uid), newUser);
            set({ 
              user: {
                id: firebaseUser.uid,
                email: firebaseUser.email || '',
                name: newUser.name,
                role: role,
              },
              token,
              isAuthenticated: true 
            });
          }
        } catch (error: any) {
          throw error;
        }
      },

      signup: async (email: string, password: string, name: string, role: UserRole) => {
        try {
          const userCredential = await createUserWithEmailAndPassword(auth, email, password);
          const firebaseUser = userCredential.user;
          
          await updateProfile(firebaseUser, { displayName: name });
          
          const userData = {
            name,
            email,
            role,
            createdAt: new Date().toISOString(),
          };
          
          await setDoc(doc(db, 'users', firebaseUser.uid), userData);
          
          const token = await firebaseUser.getIdToken();
          
          set({ 
            user: {
              id: firebaseUser.uid,
              email,
              name,
              role,
            },
            token,
            isAuthenticated: true 
          });
        } catch (error: any) {
          throw error;
        }
      },

      logout: async () => {
        await signOut(auth);
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);
