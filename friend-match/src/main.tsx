
import React from 'react';

import ReactDOM from 'react-dom/client';

import App from './App.tsx';

// 4️⃣ Optional: global CSS (if you want styling)
//import './style.css';

// 5️⃣ Create the root for React to render into
ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement  // 👈 find <div id="root"> in index.html
).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
