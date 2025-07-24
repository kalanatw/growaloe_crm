import React from 'react';
import { ChevronLeft, ChevronRight, Home } from 'lucide-react';
import { useNavigationHistory } from '../contexts/NavigationHistoryContext';

export const NavigationButtons: React.FC = () => {
    const { canGoBack, canGoForward, goBack, goForward, goHome } = useNavigationHistory();

    return (
        <div className="flex items-center space-x-1">
            {/* Back Button */}
            <button
                onClick={goBack}
                disabled={!canGoBack}
                className={`p-2 rounded-lg transition-colors ${canGoBack
                    ? 'text-gray-600 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700'
                    : 'text-gray-300 cursor-not-allowed dark:text-gray-600'
                    }`}
                aria-label="Go back"
                title="Go back"
            >
                <ChevronLeft className="h-5 w-5" />
            </button>

            {/* Forward Button */}
            <button
                onClick={goForward}
                disabled={!canGoForward}
                className={`p-2 rounded-lg transition-colors ${canGoForward
                    ? 'text-gray-600 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700'
                    : 'text-gray-300 cursor-not-allowed dark:text-gray-600'
                    }`}
                aria-label="Go forward"
                title="Go forward"
            >
                <ChevronRight className="h-5 w-5" />
            </button>

            {/* Home Button */}
            <button
                onClick={goHome}
                className="p-2 rounded-lg text-primary-600 hover:text-primary-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                aria-label="Go to Dashboard"
                title="Go to Dashboard"
            >
                <Home className="h-5 w-5" />
            </button>
        </div>
    );
};