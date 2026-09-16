import React, { useState, useEffect } from 'react';
import './App.css';
import WorkflowBuilder from './components/WorkflowBuilder';
import axios from 'axios';

function App() {
  const [config, setConfig] = useState(null);
  const [ollamaConnected, setOllamaConnected] = useState(false);
  const [ollamaModels, setOllamaModels] = useState([]);
  const [showConnectionModal, setShowConnectionModal] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState('local');
  const [customUrl, setCustomUrl] = useState('');
  const [detectedNgrokUrl, setDetectedNgrokUrl] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState('');

  const CUSTOM_NGROK_DOMAIN = 'exaliotech.ngrok.app';

  useEffect(() => {
    loadConfig();
    detectNgrok();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await axios.get('/api/config');
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const detectNgrok = async () => {
    try {
      const response = await axios.get('/api/ngrok/detect');
      if (response.data.detected) {
        setDetectedNgrokUrl(response.data.url);
        console.log('Ngrok detected:', response.data.url);
      }
    } catch (error) {
      console.log('Ngrok not detected');
    }
  };

  const getEndpointUrl = () => {
    switch (selectedEndpoint) {
      case 'local':
        return 'http://localhost:11434';
      case 'custom-domain':
        return `https://${CUSTOM_NGROK_DOMAIN}`;
      case 'detected-ngrok':
        return detectedNgrokUrl;
      case 'custom':
        return customUrl;
      default:
        return 'http://localhost:11434';
    }
  };

  const connectToOllama = async (retryCount = 0) => {
    const maxRetries = 3;
    const retryDelay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s

    setConnecting(true);
    setConnectionError('');

    const url = getEndpointUrl();

    try {
      const response = await axios.post('/api/ollama/connect', {
        url: url,
        model: config?.llm_providers?.ollama?.default_model || 'llama3.2:3b'
      }, {
        timeout: 30000, // 30 second timeout
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.data.status === 'success') {
        setOllamaConnected(true);

        // Load available models
        try {
          const modelsResponse = await axios.get(`/api/ollama/models?url=${encodeURIComponent(url)}`, {
            timeout: 10000
          });
          setOllamaModels(modelsResponse.data.models || []);
        } catch (modelError) {
          console.error('Failed to load models:', modelError);
        }

        setShowConnectionModal(false);
      }
    } catch (error) {
      console.error('Failed to connect to Ollama:', error);

      // Check if it's a connection reset or network error
      const isNetworkError = error.code === 'ECONNRESET' ||
                           error.code === 'ERR_NETWORK' ||
                           error.message?.includes('Network Error') ||
                           error.message?.includes('ECONNRESET');

      // Retry on network errors
      if (isNetworkError && retryCount < maxRetries) {
        console.log(`Connection failed, retrying in ${retryDelay/1000}s... (attempt ${retryCount + 1}/${maxRetries})`);
        setConnectionError(`Connection interrupted. Retrying (attempt ${retryCount + 1}/${maxRetries})...`);

        setTimeout(() => {
          connectToOllama(retryCount + 1);
        }, retryDelay);
        return; // Don't set connecting to false yet
      }

      // Final error message
      let errorMsg = error.response?.data?.error || error.response?.data?.message || error.message;

      if (isNetworkError) {
        errorMsg = 'Connection to backend failed. Flask server may be restarting. Please wait a moment and try again.';
      } else if (!errorMsg || errorMsg === 'Network Error') {
        errorMsg = 'Failed to connect. Please check that Ollama is running and the URL is correct.';
      }

      setConnectionError(errorMsg);
      setConnecting(false);
    }
  };

  const endpointOptions = [
    { value: 'local', label: '🏠 Local (localhost:11434)', url: 'http://localhost:11434' },
    { value: 'custom-domain', label: `🌐 Custom Domain (${CUSTOM_NGROK_DOMAIN})`, url: `https://${CUSTOM_NGROK_DOMAIN}` },
  ];

  if (detectedNgrokUrl) {
    endpointOptions.push({
      value: 'detected-ngrok',
      label: '🔗 Detected Ngrok',
      url: detectedNgrokUrl
    });
  }

  endpointOptions.push({
    value: 'custom',
    label: '✏️ Custom URL',
    url: 'custom'
  });

  return (
    <div className="App">
      <nav className="top-nav">
        <div className="nav-brand">
          <img src="/exalio-logo.svg" alt="Exalio Logo" className="brand-logo" />
          <span className="brand-name">Agentic Workflow Builder</span>
        </div>

        <div className="nav-actions">
          {!ollamaConnected && (
            <button
              className="connect-button"
              onClick={() => setShowConnectionModal(true)}
            >
              🔗 Connect to Ollama
            </button>
          )}
          {ollamaConnected && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span className="status-badge connected">
                ✅ Ollama Connected
              </span>
              {ollamaModels.length > 0 && (
                <span style={{ fontSize: '13px', color: '#666' }}>
                  {ollamaModels.length} models available
                </span>
              )}
            </div>
          )}
        </div>
      </nav>

      <div className="main-container">
        <WorkflowBuilder
          config={config}
          ollamaConnected={ollamaConnected}
          ollamaModels={ollamaModels}
        />
      </div>

      {/* Connection Modal */}
      {showConnectionModal && (
        <div className="modal-overlay" onClick={() => setShowConnectionModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Connect to Ollama</h2>
            <p className="modal-subtitle">Select your Ollama server endpoint</p>

            <div className="form-group">
              <label>Ollama Endpoint</label>
              <select
                value={selectedEndpoint}
                onChange={(e) => setSelectedEndpoint(e.target.value)}
                className="endpoint-select"
              >
                {endpointOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {selectedEndpoint !== 'custom' && (
              <div className="url-display">
                <strong>URL:</strong> <code>{getEndpointUrl()}</code>
              </div>
            )}

            {selectedEndpoint === 'custom' && (
              <div className="form-group">
                <label>Custom URL</label>
                <input
                  type="text"
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  placeholder="https://your-ngrok-url.ngrok.app"
                  className="custom-url-input"
                />
              </div>
            )}

            {connectionError && (
              <div className="error-message">
                ⚠️ {connectionError}
              </div>
            )}

            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setShowConnectionModal(false)}
                disabled={connecting}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={connectToOllama}
                disabled={connecting || (selectedEndpoint === 'custom' && !customUrl)}
              >
                {connecting ? 'Connecting...' : 'Connect'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
