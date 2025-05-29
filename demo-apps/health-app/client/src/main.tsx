import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { RTVIProvider } from './providers/RTVIProvider';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RTVIProvider>
      <App />
    </RTVIProvider>
  </React.StrictMode>
);
