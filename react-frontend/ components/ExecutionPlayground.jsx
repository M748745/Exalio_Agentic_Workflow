import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import './ExecutionPlayground.css';

const NodeInspectionPanel = ({ node, result, workflow }) => {
  if (!node) {
    return (
      <div className="inspection-panel empty">
        <div className="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4M12 8h.01"/>
          </svg>
          <p>Click on a node to inspect its output</p>
        </div>
      </div>
    );
  }

  // Find node data from workflow
  const nodeData = workflow?.nodes?.find(n => n.id === node.id);

  return (
    <div className="inspection-panel">
      <div className="panel-header">
        <h3>{nodeData?.data?.label || node.id}</h3>
        <span className={`node-type-badge ${nodeData?.type}`}>
          {nodeData?.type || 'unknown'}
        </span>
      </div>

      <div className="panel-sections">
        <section className="panel-section">
          <h4>Configuration</h4>
          <pre className="config-display">
            {JSON.stringify(nodeData?.data?.config || nodeData?.data || {}, null, 2)}
          </pre>
        </section>

        <section className="panel-section">
          <h4>Output</h4>
          {result ? (
            <pre className="result-output success">
              {typeof result === 'string'
                ? result
                : JSON.stringify(result, null, 2)}
            </pre>
          ) : (
            <div className="not-executed">
              <span>⏸</span>
              <p>Not executed yet</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

const PlaygroundControls = ({ status, onStart, onStep, onPlayAll, onPause, onResume, onClose, progress }) => {
  return (
    <div className="playground-controls">
      <div className="controls-left">
        {status === 'idle' && (
          <button className="btn-primary btn-large" onClick={onStart}>
            <span>▶</span> Start Session
          </button>
        )}

        {(status === 'ready' || status === 'running') && (
          <>
            <button className="btn-step" onClick={onStep} title="Execute next step">
              <span>⏭</span> Next Step
            </button>
            <button className="btn-secondary" onClick={onPlayAll} title="Execute all remaining steps">
              <span>⏯</span> Play All
            </button>
            <button className="btn-pause" onClick={onPause} title="Pause execution">
              <span>⏸</span> Pause
            </button>
          </>
        )}

        {status === 'paused' && (
          <button className="btn-primary" onClick={onResume}>
            <span>▶</span> Resume
          </button>
        )}

        {status === 'completed' && (
          <div className="completion-message">
            <span className="check-icon">✓</span>
            <span>Workflow execution completed!</span>
          </div>
        )}

        {status === 'error' && (
          <div className="error-message">
            <span className="error-icon">✗</span>
            <span>Execution failed</span>
          </div>
        )}
      </div>

      <div className="controls-right">
        {progress && (
          <div className="progress-indicator">
            <span className="progress-text">
              {progress.current} / {progress.total} nodes
            </span>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress.percentage || 0}%` }}
              />
            </div>
          </div>
        )}

        <button className="btn-close" onClick={onClose} title="Close playground">
          ✕
        </button>
      </div>
    </div>
  );
};

const ExecutionPlayground = ({ workflow, inputs = {}, onClose }) => {
  const [sessionId, setSessionId] = useState(null);
  const [executionState, setExecutionState] = useState({
    status: 'idle',  // idle, ready, running, paused, completed, error
    currentNode: null,
    executedNodes: [],
    pendingNodes: [],
    results: {},
    progress: { current: 0, total: 0, percentage: 0 },
    error: null
  });

  const [inspectedNode, setInspectedNode] = useState(null);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  // Create visual nodes with execution state styling
  const getNodeStyle = useCallback((nodeId) => {
    if (nodeId === executionState.currentNode) {
      return {
        border: '3px solid #FFA500',
        backgroundColor: '#FFF4E6',
        boxShadow: '0 0 20px rgba(255, 165, 0, 0.4)'
      };
    }
    if (executionState.executedNodes.includes(nodeId)) {
      return {
        border: '2px solid #4CAF50',
        backgroundColor: '#E8F5E9'
      };
    }
    return {
      border: '2px solid #E0E0E0',
      backgroundColor: '#FFFFFF'
    };
  }, [executionState.currentNode, executionState.executedNodes]);

  const visualNodes = workflow?.nodes?.map(node => ({
    ...node,
    style: {
      ...node.style,
      ...getNodeStyle(node.id),
      padding: '10px',
      borderRadius: '8px',
      minWidth: '150px'
    },
    data: {
      ...node.data,
      onClick: () => setInspectedNode(node)
    }
  })) || [];

  // Start new session
  const startSession = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/playground/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow, inputs })
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }

      const data = await response.json();
      setSessionId(data.session_id);

      setExecutionState(prev => ({
        ...prev,
        status: 'ready',
        progress: { current: 0, total: data.total_nodes, percentage: 0 }
      }));
    } catch (error) {
      console.error('Error starting session:', error);
      setExecutionState(prev => ({
        ...prev,
        status: 'error',
        error: error.message
      }));
    }
  };

  // Execute next step
  const executeNextStep = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`http://localhost:5000/api/playground/session/${sessionId}/step`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Failed to execute step');
      }

      const data = await response.json();

      setExecutionState(prev => ({
        ...prev,
        currentNode: data.node_id,
        executedNodes: data.node_id ? [...prev.executedNodes, data.node_id] : prev.executedNodes,
        results: data.node_id ? { ...prev.results, [data.node_id]: data.result } : prev.results,
        progress: data.progress || prev.progress,
        status: data.completed ? 'completed' : data.status || 'running'
      }));

      // Auto-select the just-executed node for inspection
      if (data.node_id) {
        const node = workflow?.nodes?.find(n => n.id === data.node_id);
        if (node) {
          setInspectedNode(node);
        }
      }

      return data.completed;
    } catch (error) {
      console.error('Error executing step:', error);
      setExecutionState(prev => ({
        ...prev,
        status: 'error',
        error: error.message
      }));
      return true; // Stop auto-play
    }
  };

  // Auto-execute all steps
  const executeAllSteps = async () => {
    setIsAutoPlaying(true);

    while (executionState.status !== 'completed') {
      const completed = await executeNextStep();
      if (completed) break;

      // Small delay between steps for visual feedback
      await new Promise(resolve => setTimeout(resolve, 800));
    }

    setIsAutoPlaying(false);
  };

  // Pause session
  const pauseSession = async () => {
    if (!sessionId) return;

    try {
      await fetch(`http://localhost:5000/api/playground/session/${sessionId}/pause`, {
        method: 'POST'
      });

      setExecutionState(prev => ({ ...prev, status: 'paused' }));
      setIsAutoPlaying(false);
    } catch (error) {
      console.error('Error pausing session:', error);
    }
  };

  // Resume session
  const resumeSession = async () => {
    if (!sessionId) return;

    try {
      await fetch(`http://localhost:5000/api/playground/session/${sessionId}/resume`, {
        method: 'POST'
      });

      setExecutionState(prev => ({ ...prev, status: 'running' }));
    } catch (error) {
      console.error('Error resuming session:', error);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (sessionId) {
        fetch(`http://localhost:5000/api/playground/session/${sessionId}`, {
          method: 'DELETE'
        }).catch(console.error);
      }
    };
  }, [sessionId]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === ' ' && executionState.status === 'ready') {
        e.preventDefault();
        executeNextStep();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose, executionState.status, sessionId]);

  return (
    <div className="execution-playground">
      <div className="playground-header">
        <div className="header-title">
          <h2>Interactive Playground</h2>
          <span className={`status-badge status-${executionState.status}`}>
            {executionState.status}
          </span>
        </div>
      </div>

      <div className="playground-content">
        <div className="workflow-canvas-container">
          <ReactFlow
            nodes={visualNodes}
            edges={workflow?.edges || []}
            onNodeClick={(event, node) => setInspectedNode(node)}
            fitView
            className="workflow-canvas"
          >
            <Background color="#f0f0f0" gap={16} />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>

        <NodeInspectionPanel
          node={inspectedNode}
          result={executionState.results[inspectedNode?.id]}
          workflow={workflow}
        />
      </div>

      <PlaygroundControls
        status={executionState.status}
        onStart={startSession}
        onStep={executeNextStep}
        onPlayAll={executeAllSteps}
        onPause={pauseSession}
        onResume={resumeSession}
        onClose={onClose}
        progress={executionState.progress}
      />
    </div>
  );
};

export default ExecutionPlayground;
