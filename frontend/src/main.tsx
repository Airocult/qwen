import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import './index.css';

import { SchematicImportScreen } from './screens/SchematicImportScreen';
import { PlacementOptimizationScreen } from './screens/PlacementOptimizationScreen';
import { RoutingScreen } from './screens/RoutingScreen';
import { ValidationScreen } from './screens/ValidationScreen';
import { GerberExportScreen } from './screens/GerberExportScreen';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen">
          <Routes>
            <Route path="/" element={<SchematicImportScreen />} />
            <Route path="/placement" element={<PlacementOptimizationScreen />} />
            <Route path="/routing" element={<RoutingScreen />} />
            <Route path="/validation" element={<ValidationScreen />} />
            <Route path="/gerber" element={<GerberExportScreen />} />
          </Routes>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
                borderRadius: '8px',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
