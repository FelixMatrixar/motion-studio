import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { createGlobalStyle } from 'styled-components';

// This strips away the default browser margins and sets the baseline for the app
const GlobalStyle = createGlobalStyle`
  :root {
    color-scheme: dark;
  }

  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #1a1a1a;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow: hidden; /* Prevents unwanted scrolling */
  }

  * {
    box-sizing: border-box;
  }
`;

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <GlobalStyle />
    <App />
  </React.StrictMode>
);