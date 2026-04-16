"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/auth';
import { useRouter, usePathname } from 'next/navigation';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const initAuth = async () => {
            if (authService.isAuthenticated()) {
                try {
                    const userData = await authService.getCurrentUser();
                    setUser(userData);
                } catch (error) {
                    console.error("Auth initialization failed:", error);
                    authService.logout();
                }
            }
            setLoading(false);
        };
        initAuth();
    }, []);

    // Protection des routes (simple side-effect)
    useEffect(() => {
        if (!loading) {
            const publicRoutes = ['/connexion', '/', '/demande_compte', '/cgu'];
            const isPublicRoute = publicRoutes.includes(pathname);

            if (!user && !isPublicRoute) {
                router.push('/connexion');
            } else if (user && pathname === '/connexion') {
                router.push((user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') ? '/admin' : '/dashboard');
            }

        }
    }, [user, loading, pathname, router]);

    const login = async (username, password) => {
        const data = await authService.login(username, password);
        const userData = await authService.getCurrentUser();
        setUser(userData);
        return data;
    };

    const logout = () => {
        authService.logout();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, isAdmin: user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN' }}>

            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
