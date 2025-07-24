import React, { createContext, useContext, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

interface NavigationHistoryContextType {
  canGoBack: boolean;
  canGoForward: boolean;
  goBack: () => void;
  goForward: () => void;
  goHome: () => void;
}

const NavigationHistoryContext = createContext<NavigationHistoryContextType | undefined>(undefined);

export const useNavigationHistory = () => {
  const context = useContext(NavigationHistoryContext);
  if (!context) {
    throw new Error('useNavigationHistory must be used within a NavigationHistoryProvider');
  }
  return context;
};

interface NavigationHistoryProviderProps {
  children: React.ReactNode;
}

export const NavigationHistoryProvider: React.FC<NavigationHistoryProviderProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [history, setHistory] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState(-1);

  // Initialize with current location
  useEffect(() => {
    if (history.length === 0) {
      setHistory([location.pathname]);
      setCurrentIndex(0);
    }
  }, []);

  // Track location changes
  useEffect(() => {
    const currentPath = location.pathname;
    
    // Don't add duplicate consecutive entries
    if (history[currentIndex] !== currentPath) {
      // If we're not at the end of history, remove forward history
      const newHistory = history.slice(0, currentIndex + 1);
      newHistory.push(currentPath);
      setHistory(newHistory);
      setCurrentIndex(newHistory.length - 1);
    }
  }, [location.pathname]);

  const canGoBack = currentIndex > 0;
  const canGoForward = currentIndex < history.length - 1;

  const goBack = () => {
    if (canGoBack) {
      const newIndex = currentIndex - 1;
      setCurrentIndex(newIndex);
      navigate(history[newIndex]);
    }
  };

  const goForward = () => {
    if (canGoForward) {
      const newIndex = currentIndex + 1;
      setCurrentIndex(newIndex);
      navigate(history[newIndex]);
    }
  };

  const goHome = () => {
    navigate('/');
  };

  const value = {
    canGoBack,
    canGoForward,
    goBack,
    goForward,
    goHome,
  };

  return (
    <NavigationHistoryContext.Provider value={value}>
      {children}
    </NavigationHistoryContext.Provider>
  );
};