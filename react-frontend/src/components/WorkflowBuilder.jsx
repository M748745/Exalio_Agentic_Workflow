import React, { useState, useCallback, useRef } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ArrowLeft, Settings, Activity, Play, Trash2, X } from 'lucide-react';
import DynamicNodeConfig from './DynamicNodeConfig';
import TemplateGallery from './TemplateGallery';
import ExecutionPlayground from './ExecutionPlayground';

// Complete node library from Streamlit - ALL 20 categories, 132+ nodes
const nodeLibrary = {
  "Input": [
    { type: "file_upload", name: "File Upload", icon: "📁", desc: "Upload any file" },
    { type: "text_input", name: "Text Input", icon: "✏️", desc: "Free text input" },
    { type: "api_input", name: "REST API", icon: "🌐", desc: "Call REST API" },
    { type: "database_query", name: "Database Query", icon: "🗄️", desc: "Query SQL/NoSQL" }
  ],
  "Data Loaders": [
    { type: "mysql", name: "MySQL", icon: "🐬", desc: "Connect to MySQL" },
    { type: "postgresql", name: "PostgreSQL", icon: "🐘", desc: "Connect to PostgreSQL" },
    { type: "mongodb", name: "MongoDB", icon: "🍃", desc: "Connect to MongoDB" },
    { type: "s3", name: "AWS S3", icon: "☁️", desc: "Load from S3" },
    { type: "azure_blob", name: "Azure Blob", icon: "☁️", desc: "Load from Azure" },
    { type: "gcs", name: "Google Cloud", icon: "☁️", desc: "Load from GCS" },
    { type: "notion", name: "Notion", icon: "📝", desc: "Load from Notion" },
    { type: "trello", name: "Trello", icon: "📋", desc: "Load from Trello" },
    { type: "confluence", name: "Confluence", icon: "📚", desc: "Load from Confluence" },
    { type: "slack", name: "Slack", icon: "💬", desc: "Load from Slack" },
    { type: "jira", name: "Jira", icon: "🎯", desc: "Load from Jira" }
  ],
  "File Parsers": [
    { type: "pdf_parser", name: "PDF Parser", icon: "📄", desc: "Parse PDF files" },
    { type: "image_parser", name: "Image Parser", icon: "🖼️", desc: "OCR + vision understanding" },
    { type: "json_parser", name: "JSON Parser", icon: "📊", desc: "Parse JSON files" },
    { type: "xml_parser", name: "XML Parser", icon: "📑", desc: "Parse XML files" },
    { type: "csv_parser", name: "CSV Parser", icon: "📈", desc: "Parse CSV files" },
    { type: "txt_parser", name: "TXT Parser", icon: "📝", desc: "Parse text files" },
    { type: "excel_parser", name: "Excel Parser", icon: "📊", desc: "Parse XLS/XLSX files" },
    { type: "docx_parser", name: "DOCX Parser", icon: "📘", desc: "Parse Word documents" }
  ],
  "LLM Providers": [
    { type: "ollama_llm", name: "Ollama", icon: "🦙", desc: "Local models (free)" },
    { type: "openai_llm", name: "OpenAI", icon: "🤖", desc: "GPT-4, GPT-4o, o1" },
    { type: "anthropic_llm", name: "Claude", icon: "🎭", desc: "Claude 3 family" },
    { type: "cohere_llm", name: "Cohere", icon: "🔮", desc: "Command models" },
    { type: "huggingface_llm", name: "HuggingFace", icon: "🤗", desc: "300k+ models" },
    { type: "vertexai_llm", name: "Gemini", icon: "💎", desc: "Google Gemini" }
  ],
  "Processing": [
    { type: "llm_query", name: "LLM Query", icon: "🧠", desc: "Query any LLM" },
    { type: "ocr", name: "OCR", icon: "👁️", desc: "Extract text from images" },
    { type: "embeddings", name: "Generate Embeddings", icon: "🔢", desc: "Create vectors" },
    { type: "classification", name: "Classification", icon: "🏷️", desc: "Classify content" },
    { type: "extraction", name: "Entity Extraction", icon: "🔍", desc: "Extract entities" }
  ],
  "Analysis": [
    { type: "similarity", name: "Similarity Match", icon: "🔄", desc: "Find similar content" },
    { type: "scoring", name: "Scoring", icon: "⭐", desc: "Score content" },
    { type: "sentiment", name: "Sentiment Analysis", icon: "😊", desc: "Analyze sentiment" },
    { type: "pattern_detection", name: "AI Detection", icon: "🔎", desc: "Detect AI content" },
    { type: "benchmarking", name: "Benchmarking", icon: "📊", desc: "Compare to benchmarks" }
  ],
  "RAG & Evaluation": [
    { type: "vector_search", name: "Vector Search", icon: "🔍", desc: "Semantic search" },
    { type: "hybrid_search", name: "Hybrid Search", icon: "🔎", desc: "Vector + keyword" },
    { type: "rag_evaluator", name: "RAG Evaluator", icon: "✅", desc: "6 RAG metrics" },
    { type: "embedding_evaluator", name: "Embedding Eval", icon: "📈", desc: "5 retrieval metrics" },
    { type: "grounded_answer", name: "Grounded Answer", icon: "📝", desc: "RAG with citations" }
  ],
  "LLMOps & Monitoring": [
    { type: "cost_monitor", name: "Cost Monitor", icon: "💰", desc: "Track spending" },
    { type: "latency_monitor", name: "Latency Monitor", icon: "⏱️", desc: "Track speed" },
    { type: "cache_check", name: "Cache Check", icon: "⚡", desc: "60x cost reduction" },
    { type: "ab_test", name: "A/B Test", icon: "🧪", desc: "Compare models" }
  ],
  "Memory": [
    { type: "vector_store", name: "Vector Store", icon: "🧠", desc: "Store in vector DB" },
    { type: "vector_search", name: "Vector Search", icon: "🔍", desc: "Semantic search" },
    { type: "cache_set", name: "Cache Set", icon: "💾", desc: "Store in cache" },
    { type: "cache_get", name: "Cache Get", icon: "📥", desc: "Retrieve from cache" },
    { type: "context_append", name: "Context Append", icon: "💬", desc: "Add to conversation" },
    { type: "context_get", name: "Context Get", icon: "📖", desc: "Get conversation history" }
  ],
  "Guardrails & Security": [
    { type: "input_screening", name: "Input Screening", icon: "🔍", desc: "Layer 1: Scan before model sees" },
    { type: "context_verification", name: "Context Verification", icon: "✓", desc: "Layer 2: Sanitize & permission-check" },
    { type: "response_generation_guard", name: "Response Guard", icon: "🛡️", desc: "Layer 3: Monitor generation" },
    { type: "output_validation", name: "Output Validation", icon: "✅", desc: "Layer 4: Check groundedness/safety" },
    { type: "operational_controls", name: "Operational Controls", icon: "⚙️", desc: "Layer 5: Rate limits & audit logs" },
    { type: "pii_detection", name: "PII Detection", icon: "🔒", desc: "Detect/redact PII" },
    { type: "prompt_injection", name: "Prompt Injection Guard", icon: "🛡️", desc: "Block attacks" },
    { type: "content_filter", name: "Content Filter", icon: "🚫", desc: "Filter toxic content" },
    { type: "hallucination_check", name: "Hallucination Check", icon: "✨", desc: "Prevent hallucinations" }
  ],
  "Logic": [
    { type: "condition", name: "Conditional Branch", icon: "🔀", desc: "If/else routing" },
    { type: "loop", name: "Loop", icon: "🔁", desc: "Iterate collection" },
    { type: "parallel", name: "Parallel", icon: "⚡", desc: "Run concurrent" },
    { type: "merge", name: "Merge", icon: "🔗", desc: "Combine branches" },
    { type: "human_review", name: "Human Review", icon: "👤", desc: "Pause for human" }
  ],
  "Error Handling": [
    { type: "try_catch", name: "Try/Catch", icon: "🛡️", desc: "Graceful error handling" },
    { type: "retry", name: "Retry", icon: "🔄", desc: "Retry failed operations" },
    { type: "fallback", name: "Fallback", icon: "↩️", desc: "Alternative on failure" },
    { type: "timeout", name: "Timeout", icon: "⏱️", desc: "Time limit enforcement" },
    { type: "error_logger", name: "Error Logger", icon: "📝", desc: "Log errors for debugging" }
  ],
  "Control Flow": [
    { type: "if_else", name: "If/Else", icon: "🔀", desc: "Conditional branching" },
    { type: "switch_case", name: "Switch/Case", icon: "🔄", desc: "Multi-way branching" },
    { type: "for_loop", name: "For Loop", icon: "🔁", desc: "Iterate over arrays" },
    { type: "while_loop", name: "While Loop", icon: "⭕", desc: "Loop until condition" },
    { type: "parallel_exec", name: "Parallel Execution", icon: "⚡", desc: "Run branches simultaneously" },
    { type: "wait_delay", name: "Wait/Delay", icon: "⏱️", desc: "Pause execution" },
    { type: "break_continue", name: "Break/Continue", icon: "⏯️", desc: "Control loop flow" }
  ],
  "Data Transformation": [
    { type: "json_transform", name: "JSON Transform", icon: "📋", desc: "Extract/modify JSON" },
    { type: "data_mapper", name: "Data Mapper", icon: "🗺️", desc: "Map fields between schemas" },
    { type: "filter_node", name: "Filter", icon: "🔍", desc: "Filter arrays by condition" },
    { type: "aggregation", name: "Aggregation", icon: "📊", desc: "Sum, avg, min, max, group" },
    { type: "string_ops", name: "String Operations", icon: "🔤", desc: "Text manipulation" },
    { type: "math_ops", name: "Math Operations", icon: "🔢", desc: "Calculations + expressions" },
    { type: "variable_assign", name: "Variable Assignment", icon: "💾", desc: "Store/retrieve variables" },
    { type: "data_validation", name: "Data Validation", icon: "✅", desc: "Validate schema/rules" },
    { type: "array_ops", name: "Array Operations", icon: "📚", desc: "Push, pop, sort, filter, map" },
    { type: "format_converter", name: "Format Converter", icon: "🔄", desc: "Convert data formats" }
  ],
  "Universal Parser": [
    { type: "universal_parser", name: "Universal Parser", icon: "🔄", desc: "Parse JSON/XML/CSV/Excel/Word/PDF/HTML/Images to any format" }
  ],
  "Chatbot Builder": [
    { type: "intent_recognition", name: "Intent Recognition", icon: "🎯", desc: "Classify user intent" },
    { type: "entity_extraction_chat", name: "Entity Extraction", icon: "📝", desc: "Extract key info" },
    { type: "dialog_state", name: "Dialog State", icon: "💭", desc: "Track conversation state" },
    { type: "slot_filling", name: "Slot Filling", icon: "🔲", desc: "Collect info step-by-step" },
    { type: "response_template", name: "Response Template", icon: "💬", desc: "Generate responses" },
    { type: "context_switch", name: "Context Switch", icon: "🔄", desc: "Handle topic changes" },
    { type: "fallback_handler", name: "Fallback Handler", icon: "❓", desc: "Handle unknown intents" },
    { type: "clarification", name: "Clarification", icon: "🤔", desc: "Ask clarifying questions" },
    { type: "multi_turn", name: "Multi-Turn Handler", icon: "🔁", desc: "Multi-turn conversations" },
    { type: "small_talk", name: "Small Talk", icon: "💭", desc: "Greetings & chitchat" },
    { type: "handoff", name: "Handoff", icon: "👤", desc: "Transfer to human agent" }
  ],
  "Integration & Connectivity": [
    { type: "http_request", name: "HTTP Request", icon: "🌐", desc: "REST API calls" },
    { type: "webhook_sender", name: "Webhook Sender", icon: "📤", desc: "Send webhooks" },
    { type: "webhook_receiver", name: "Webhook Receiver", icon: "📥", desc: "Receive webhooks" },
    { type: "email_node", name: "Email", icon: "📧", desc: "Send emails (SMTP/SendGrid/Mailgun)" },
    { type: "sms_node", name: "SMS", icon: "📱", desc: "Send SMS via Twilio" },
    { type: "slack_node", name: "Slack", icon: "💬", desc: "Slack integration" },
    { type: "discord_node", name: "Discord", icon: "🎮", desc: "Discord bot" },
    { type: "whatsapp_node", name: "WhatsApp", icon: "📞", desc: "WhatsApp messaging" },
    { type: "teams_node", name: "Microsoft Teams", icon: "💼", desc: "Teams integration" },
    { type: "file_ops", name: "File Operations", icon: "📁", desc: "Read/write/move/delete files" },
    { type: "ftp_node", name: "FTP/SFTP", icon: "🔐", desc: "File transfer" },
    { type: "database_ops", name: "Database Operations", icon: "🗄️", desc: "SQL queries" },
    { type: "graphql_node", name: "GraphQL", icon: "⚡", desc: "GraphQL queries" },
    { type: "websocket_node", name: "WebSocket", icon: "🔌", desc: "Real-time communication" }
  ],
  "Human-in-the-Loop": [
    { type: "approval", name: "Approval", icon: "👍", desc: "Request human approval" },
    { type: "manual_input", name: "Manual Input", icon: "⌨️", desc: "Collect manual input" },
    { type: "review", name: "Review", icon: "📋", desc: "Human review process" },
    { type: "escalation", name: "Escalation", icon: "⬆️", desc: "Escalate to supervisor" },
    { type: "assignment", name: "Assignment", icon: "👤", desc: "Assign tasks to users" },
    { type: "notification", name: "Notification", icon: "🔔", desc: "Send notifications" },
    { type: "feedback", name: "Feedback Collection", icon: "💬", desc: "Collect user feedback" }
  ],
  "Scheduling & Triggers": [
    { type: "cron_scheduler", name: "Cron Scheduler", icon: "⏰", desc: "Time-based triggers (cron)" },
    { type: "event_trigger", name: "Event Trigger", icon: "⚡", desc: "System/custom events" },
    { type: "webhook_trigger", name: "Webhook Trigger", icon: "🔗", desc: "HTTP webhook triggers" },
    { type: "file_watch", name: "File Watch", icon: "👁️", desc: "File system monitoring" },
    { type: "email_trigger", name: "Email Trigger", icon: "📨", desc: "Email-based triggers" },
    { type: "db_trigger", name: "Database Trigger", icon: "💾", desc: "Database change monitoring" },
    { type: "interval_trigger", name: "Interval Trigger", icon: "🔄", desc: "Periodic execution" },
    { type: "time_delay", name: "Time Delay", icon: "⏱️", desc: "Scheduled one-time trigger" }
  ],
  "Advanced Agent Features": [
    { type: "augmented_llm", name: "Augmented LLM", icon: "⚡", desc: "Single-shot with tools/memory/RAG" },
    { type: "react_loop", name: "ReAct Loop", icon: "🔁", desc: "Iterative reasoning + acting" },
    { type: "router_orchestrator", name: "Router/Orchestrator", icon: "🚦", desc: "Route to specialist workers" },
    { type: "planner_executor", name: "Planner-Executor", icon: "📋", desc: "Plan then execute in parallel" },
    { type: "evaluator_optimizer", name: "Evaluator-Optimizer", icon: "🔄", desc: "Produce → critique → refine" },
    { type: "verifier_gated", name: "Verifier-Gated", icon: "✅", desc: "Verify before irreversible actions" },
    { type: "multi_agent_memory", name: "Multi-Agent + Memory", icon: "👥", desc: "Cross-platform agent teams" },
    { type: "plan_execute", name: "Plan-Execute (Legacy)", icon: "📋", desc: "Planning then execution" },
    { type: "tool_calling", name: "Tool Calling", icon: "🔧", desc: "Function/API calling" },
    { type: "multi_agent", name: "Multi-Agent Collab", icon: "👥", desc: "Agent teams" },
    { type: "agent_router", name: "Agent Router", icon: "🚦", desc: "Dynamic agent selection" },
    { type: "self_reflection", name: "Self-Reflection", icon: "🪞", desc: "Agent self-evaluation" },
    { type: "agent_memory", name: "Agent Memory", icon: "🧠", desc: "Episodic + semantic memory" },
    { type: "agent_supervisor", name: "Agent Supervisor", icon: "👨‍💼", desc: "Orchestration + monitoring" }
  ],
  "Output": [
    { type: "display", name: "Display Results", icon: "📺", desc: "Show to user" },
    { type: "save_file", name: "Save File", icon: "💾", desc: "Save output" },
    { type: "send_email", name: "Send Email", icon: "📧", desc: "Email notification" },
    { type: "api_call", name: "API Call", icon: "🚀", desc: "Call external API" },
    { type: "database_write", name: "Database Write", icon: "💿", desc: "Write to DB" }
  ],
  "Multimodal": [
    { type: "text_to_image", name: "Text-to-Image", icon: "🎨", desc: "Generate images" },
    { type: "text_to_speech", name: "Text-to-Speech", icon: "🔊", desc: "Generate audio" },
    { type: "vision_llm", name: "Vision LLM", icon: "👁️", desc: "Understand images" }
  ]
};

const initialNodes = [];

const initialEdges = [];

// Custom Node Component with handles
const CustomNode = ({ data, id, selected }) => {
  return (
    <div className={`workflow-node ${selected ? 'selected' : ''}`}>
      {/* Input Handle (left side) */}
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#2e7d32', width: 12, height: 12 }}
      />

      <div className="node-header">
        <span className="node-title">{data.icon} {data.label}</span>
        <div className="node-actions">
          <Settings size={14} className="node-action-icon" />
          {data.onDelete && (
            <Trash2 size={14} className="node-action-icon delete" onClick={() => data.onDelete(id)} />
          )}
        </div>
      </div>

      <div className="node-content">
        {data.type === 'input' && data.fields?.map((field, idx) => (
          <div key={idx} className="node-field">
            ⋮⋮ {field.name} <span style={{float: 'right'}}>T</span>
          </div>
        ))}
        {data.type === 'agent' && (
          <>
            <div className="agent-name">{data.agentName}</div>
            <div className="model-badge">🧠 {data.model}</div>
          </>
        )}
        {data.type === 'output' && data.fields?.map((field, idx) => (
          <div key={idx} className="node-field">
            ⋮⋮ {field.name}
          </div>
        ))}
        {data.desc && !data.agentName && (
          <div className="node-desc">{data.desc}</div>
        )}
      </div>

      {/* Output Handle (right side) */}
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#2e7d32', width: 12, height: 12 }}
      />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

function WorkflowBuilder({ ollamaModels, ollamaConnected }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [expandedCategories, setExpandedCategories] = useState({
    "Input": true,
    "Data Transformation (CRITICAL)": true,
    "Control Flow (CRITICAL)": true,
    "Output": true
  });
  const [selectedNode, setSelectedNode] = useState(null);
  const [showConfigPanel, setShowConfigPanel] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [executionResults, setExecutionResults] = useState(null);
  const [showExecutionResults, setShowExecutionResults] = useState(false);
  const [workflowVariables, setWorkflowVariables] = useState({});
  const [showVariablesPanel, setShowVariablesPanel] = useState(true);
  const [showTestPanel, setShowTestPanel] = useState(false);
  const [testInput, setTestInput] = useState('{\n  "message": "Hello, test the workflow!"\n}');
  const [savedTestCases, setSavedTestCases] = useState([]);
  const [workflowVersions, setWorkflowVersions] = useState([]);
  const [showVersionsPanel, setShowVersionsPanel] = useState(false);
  const [currentVersionName, setCurrentVersionName] = useState('Untitled Workflow');
  const [showTemplateGallery, setShowTemplateGallery] = useState(false);
  const [showPlayground, setShowPlayground] = useState(false);
  const [currentWorkflowId, setCurrentWorkflowId] = useState(null);
  const [currentWorkflowName, setCurrentWorkflowName] = useState('Untitled Workflow');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showLoadDialog, setShowLoadDialog] = useState(false);
  const [savedWorkflows, setSavedWorkflows] = useState([]);
  const [saveWorkflowName, setSaveWorkflowName] = useState('');
  const [saveWorkflowDescription, setSaveWorkflowDescription] = useState('');
  const [showImportDialog, setShowImportDialog] = useState(false);
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const nodeId = useRef(4);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  );

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  const deleteNode = useCallback((nodeIdToDelete) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeIdToDelete));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeIdToDelete && edge.target !== nodeIdToDelete));
  }, [setNodes, setEdges]);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
    setShowConfigPanel(true);
  }, []);

  const updateNodeData = useCallback((nodeId, newData) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: { ...node.data, ...newData },
          };
        }
        return node;
      })
    );
  }, [setNodes]);

  const onDragStart = (event, nodeType, nodeData) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeData));
    event.dataTransfer.effectAllowed = 'move';
  };

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();

      // Get the data and validate it exists
      const dataString = event.dataTransfer.getData('application/reactflow');

      // If no data or empty string, it's not a valid workflow node drop (might be a file)
      if (!dataString || dataString.trim() === '') {
        console.log('No workflow node data found - ignoring drop');
        return;
      }

      // Try to parse the JSON data
      let nodeData;
      try {
        nodeData = JSON.parse(dataString);
      } catch (error) {
        console.error('Failed to parse node data:', error);
        return;
      }

      if (!nodeData || !nodeData.name || !nodeData.category) {
        console.log('Invalid node data - ignoring drop');
        return;
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      // Determine inputType based on node name
      let inputType = 'text';  // default
      if (nodeData.category === 'Input') {
        if (nodeData.name === 'File Upload') inputType = 'file';
        else if (nodeData.name === 'JSON Input') inputType = 'json';
        else if (nodeData.name === 'API Call') inputType = 'api';
        else inputType = 'text';
      }

      const newNode = {
        id: `node-${nodeId.current++}`,
        type: 'custom',
        position,
        data: {
          label: nodeData.name,
          type: nodeData.category.toLowerCase(),
          category: nodeData.category,  // Add category for configuration panel
          nodeType: nodeData.type,
          icon: nodeData.icon,
          desc: nodeData.desc,
          inputType: inputType,  // Set inputType based on node name
          fields: nodeData.category === 'Input' ? [{ name: 'input', type: 'text' }] :
                 nodeData.category === 'Output' ? [{ name: 'output', type: 'text' }] : undefined,
          agentName: nodeData.type === 'agent' ? 'New Agent' : undefined,
          model: nodeData.type === 'agent' ? 'Select model' : undefined,
          onDelete: deleteNode
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes, deleteNode]
  );

  // Keyboard shortcut for delete
  const onKeyDown = useCallback(
    (event) => {
      if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNode) {
        deleteNode(selectedNode.id);
        setShowConfigPanel(false);
        setSelectedNode(null);
      }
    },
    [selectedNode, deleteNode]
  );

  // Execute workflow
  const executeWorkflow = async () => {
    setExecuting(true);
    setExecutionResults(null);
    setShowExecutionResults(true);

    try {
      const workflowDefinition = {
        nodes: nodes,
        edges: edges
      };

      // Parse test input (use testInput if provided, otherwise default)
      let inputData = { message: "Hello from workflow!" };
      try {
        inputData = JSON.parse(testInput);
      } catch (parseError) {
        console.warn('Failed to parse test input, using default:', parseError);
      }

      const response = await fetch('/api/workflows/execute-visual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow: workflowDefinition,
          input: inputData  // Use test input from Test Panel
        }),
      });

      const result = await response.json();
      setExecutionResults(result);

      // Populate workflow variables from execution results
      if (result.status === 'success' && result.results) {
        const variables = {};

        Object.entries(result.results).forEach(([nodeId, nodeOutput]) => {
          const node = nodes.find(n => n.id === nodeId);
          const nodeName = node?.data?.label || nodeId;

          // Determine type from value
          let varType = 'unknown';
          if (typeof nodeOutput === 'string') varType = 'string';
          else if (typeof nodeOutput === 'number') varType = 'number';
          else if (typeof nodeOutput === 'boolean') varType = 'boolean';
          else if (Array.isArray(nodeOutput)) varType = 'array';
          else if (nodeOutput && typeof nodeOutput === 'object') varType = 'object';
          else if (nodeOutput === null) varType = 'null';

          variables[`${nodeId}_output`] = {
            type: varType,
            value: nodeOutput,
            source: nodeName
          };
        });

        setWorkflowVariables(variables);
      }

    } catch (error) {
      setExecutionResults({
        status: 'error',
        error: error.message,
        logs: [{ level: 'ERROR', message: `Failed to execute: ${error.message}` }]
      });
    } finally {
      setExecuting(false);
    }
  };

  // Save current workflow as a version (uses backend versioning)
  const saveVersion = async () => {
    if (!currentWorkflowId) {
      alert('Please save the workflow first before creating versions');
      return;
    }

    const changeDescription = prompt('Enter a description for this version (what changed?):', '');

    if (changeDescription === null) return; // User cancelled

    try {
      const workflowData = {
        nodes,
        edges
      };

      const metadata = {
        id: currentWorkflowId,
        name: currentWorkflowName,
        description: saveWorkflowDescription,
        category: 'Custom',
        author: 'User',
        tags: [],
        change_description: changeDescription || 'Version updated'
      };

      const response = await fetch('http://localhost:5000/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...workflowData, metadata })
      });

      if (!response.ok) throw new Error('Failed to save version');

      const data = await response.json();
      alert(`Version saved successfully!`);

      // Refresh version history
      fetchWorkflowVersions();
    } catch (error) {
      console.error('Error saving version:', error);
      alert('Failed to save version');
    }
  };

  // Fetch workflow versions from backend
  const fetchWorkflowVersions = async () => {
    if (!currentWorkflowId) return;

    try {
      const response = await fetch(`http://localhost:5000/api/workflows/${currentWorkflowId}/versions`);
      if (!response.ok) throw new Error('Failed to fetch versions');

      const data = await response.json();
      setWorkflowVersions(data.versions || []);
    } catch (error) {
      console.error('Error fetching versions:', error);
    }
  };

  // Load a specific version from backend
  const loadVersion = async (versionNumber) => {
    if (!currentWorkflowId) return;

    const confirm = window.confirm(`Load version ${versionNumber}? Current unsaved changes will be lost.`);

    if (!confirm) return;

    try {
      const response = await fetch(`http://localhost:5000/api/workflows/${currentWorkflowId}?version=${versionNumber}`);
      if (!response.ok) throw new Error('Failed to load version');

      const workflow = await response.json();
      const workflowData = workflow.workflow_data;

      if (workflowData && workflowData.nodes) {
        const loadedNodes = workflowData.nodes.map(node => ({
          ...node,
          position: node.position || { x: 0, y: 0 }
        }));
        const loadedEdges = workflowData.edges || [];

        setNodes(loadedNodes);
        setEdges(loadedEdges);
        setShowVersionsPanel(false);

        alert(`Version ${versionNumber} loaded successfully!`);
      }
    } catch (error) {
      console.error('Error loading version:', error);
      alert('Failed to load version');
    }
  };

  // Delete a version (legacy localStorage function - can be removed)
  const deleteVersion = (versionId) => {
    const confirm = window.confirm('Delete this version? This action cannot be undone.');

    if (!confirm) return;

    const updatedVersions = workflowVersions.filter(v => v.id !== versionId);
    setWorkflowVersions(updatedVersions);
    localStorage.setItem('workflow_versions', JSON.stringify(updatedVersions));

    alert('Version deleted successfully!');
  };

  // Export all versions as JSON
  const exportVersions = () => {
    const dataStr = JSON.stringify(workflowVersions, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workflow-versions-${Date.now()}.json`;
    link.click();
  };

  // Handle template import from gallery
  const handleTemplateImport = (template) => {
    if (!template || !template.nodes || !template.edges) {
      alert('Invalid template data');
      return;
    }

    const confirm = window.confirm(`Import "${template.name}"? Current unsaved changes will be lost.`);
    if (!confirm) return;

    // Convert template nodes to ReactFlow format
    const importedNodes = template.nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        onDelete: deleteNode
      }
    }));

    setNodes(importedNodes);
    setEdges(template.edges || []);
    setCurrentVersionName(template.name || 'Imported Template');
    setShowTemplateGallery(false);

    alert(`Template "${template.name}" imported successfully!`);
  };

  // Export current workflow
  const exportWorkflow = () => {
    const workflowData = {
      metadata: {
        name: currentWorkflowName || 'Untitled Workflow',
        description: saveWorkflowDescription || 'Exported workflow',
        exportedAt: new Date().toISOString(),
        version: 1
      },
      nodes,
      edges
    };

    const dataStr = JSON.stringify(workflowData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${(currentWorkflowName || 'workflow').replace(/\s+/g, '_')}_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Import workflow from file
  const importWorkflow = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result;
        const workflowData = JSON.parse(content);

        // Validate workflow structure
        if (!workflowData.nodes || !Array.isArray(workflowData.nodes)) {
          alert('Invalid workflow file: missing or invalid nodes');
          return;
        }

        const confirmMsg = `Import workflow "${workflowData.metadata?.name || 'Unnamed'}"? Current unsaved changes will be lost.`;
        if (!window.confirm(confirmMsg)) return;

        // Import nodes with proper data structure
        const importedNodes = workflowData.nodes.map(node => ({
          ...node,
          data: {
            ...node.data,
            onDelete: deleteNode
          }
        }));

        setNodes(importedNodes);
        setEdges(workflowData.edges || []);
        setCurrentWorkflowName(workflowData.metadata?.name || 'Imported Workflow');
        setSaveWorkflowDescription(workflowData.metadata?.description || '');
        setCurrentWorkflowId(null); // Reset ID as this is a new workflow

        setShowImportDialog(false);
        alert(`Workflow "${workflowData.metadata?.name || 'Unnamed'}" imported successfully!`);
      } catch (error) {
        console.error('Import error:', error);
        alert(`Failed to import workflow: ${error.message}`);
      }
    };

    reader.readAsText(file);
    // Reset file input
    event.target.value = '';
  };

  // Fetch saved workflows
  const fetchSavedWorkflows = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/workflows');
      if (!response.ok) throw new Error('Failed to fetch workflows');
      const data = await response.json();
      setSavedWorkflows(data.workflows || []);
    } catch (error) {
      console.error('Error fetching workflows:', error);
      alert('Failed to load saved workflows');
    }
  };

  // Save workflow
  const handleSaveWorkflow = async () => {
    if (!saveWorkflowName.trim()) {
      alert('Please enter a workflow name');
      return;
    }

    try {
      const workflowData = {
        nodes,
        edges
      };

      const metadata = {
        id: currentWorkflowId,
        name: saveWorkflowName,
        description: saveWorkflowDescription,
        category: 'Custom',
        author: 'User',
        tags: [],
        change_description: currentWorkflowId ? 'Workflow updated' : 'Initial version'
      };

      const response = await fetch('http://localhost:5000/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...workflowData, metadata })
      });

      if (!response.ok) throw new Error('Failed to save workflow');

      const data = await response.json();
      setCurrentWorkflowId(data.workflow_id);
      setCurrentWorkflowName(saveWorkflowName);
      setShowSaveDialog(false);
      alert(`Workflow "${saveWorkflowName}" saved successfully!`);
    } catch (error) {
      console.error('Error saving workflow:', error);
      alert('Failed to save workflow');
    }
  };

  // Load workflow
  const handleLoadWorkflow = async (workflowId) => {
    try {
      const response = await fetch(`http://localhost:5000/api/workflows/${workflowId}`);
      if (!response.ok) throw new Error('Failed to load workflow');

      const workflow = await response.json();
      const workflowData = workflow.workflow_data;

      if (!workflowData || !workflowData.nodes) {
        alert('Invalid workflow data');
        return;
      }

      const confirm = window.confirm(`Load "${workflow.name}"? Current unsaved changes will be lost.`);
      if (!confirm) return;

      const loadedNodes = workflowData.nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          onDelete: deleteNode
        }
      }));

      setNodes(loadedNodes);
      setEdges(workflowData.edges || []);
      setCurrentWorkflowId(workflow.id);
      setCurrentWorkflowName(workflow.name);
      setCurrentVersionName(workflow.name);
      setShowLoadDialog(false);

      alert(`Workflow "${workflow.name}" loaded successfully!`);
    } catch (error) {
      console.error('Error loading workflow:', error);
      alert('Failed to load workflow');
    }
  };

  // Delete workflow
  const handleDeleteWorkflow = async (workflowId, workflowName) => {
    const confirm = window.confirm(`Delete workflow "${workflowName}"? This cannot be undone.`);
    if (!confirm) return;

    try {
      const response = await fetch(`http://localhost:5000/api/workflows/${workflowId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete workflow');

      alert(`Workflow "${workflowName}" deleted successfully!`);
      fetchSavedWorkflows();
    } catch (error) {
      console.error('Error deleting workflow:', error);
      alert('Failed to delete workflow');
    }
  };

  return (
    <div className="workflow-builder" onKeyDown={onKeyDown} tabIndex={0}>
      {/* Toolbar */}
      <div className="workflow-toolbar">
        <button className="toolbar-btn">
          <ArrowLeft size={18} /> Back
        </button>
        <span className="workflow-title">{currentWorkflowName}</span>
        <div className="toolbar-actions">
          <button
            className="toolbar-btn"
            onClick={() => {
              setSaveWorkflowName(currentWorkflowName);
              setSaveWorkflowDescription('');
              setShowSaveDialog(true);
            }}
            title="Save current workflow to database"
          >
            💾 Save
          </button>
          <button
            className="toolbar-btn"
            onClick={() => {
              fetchSavedWorkflows();
              setShowLoadDialog(true);
            }}
            title="Load a saved workflow"
          >
            📂 Load
          </button>
          <button
            className="toolbar-btn"
            onClick={exportWorkflow}
            disabled={nodes.length === 0}
            title="Export current workflow as JSON file"
          >
            📤 Export
          </button>
          <button
            className="toolbar-btn"
            onClick={() => setShowImportDialog(true)}
            title="Import workflow from JSON file"
          >
            📥 Import
          </button>
          <button
            className="toolbar-btn"
            onClick={() => setShowTemplateGallery(true)}
            title="Browse and import pre-built workflow templates"
          >
            📚 Templates
          </button>
          <button
            className="toolbar-btn"
            onClick={() => setShowPlayground(true)}
            title="Run workflow step-by-step with live inspection"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              fontWeight: '600'
            }}
          >
            ⚡ Playground
          </button>
          <button className="toolbar-btn" onClick={() => setShowTestPanel(true)}>
            🧪 Test
          </button>
          <button
            className="toolbar-btn"
            onClick={saveVersion}
            disabled={nodes.length === 0}
            title="Save current workflow as a version"
          >
            💾 Save Version
          </button>
          <button
            className="toolbar-btn"
            onClick={() => {
              fetchWorkflowVersions();
              setShowVersionsPanel(true);
            }}
            title="View and load saved versions"
          >
            📋 Versions ({workflowVersions.length})
          </button>
          <button className="toolbar-btn">
            <Settings size={18} /> Workflow Settings
          </button>
          <button className="toolbar-btn">
            <Activity size={18} /> View Traces
          </button>
          <button
            className="toolbar-btn-primary"
            onClick={executeWorkflow}
            disabled={executing || nodes.length === 0}
            style={{marginRight: '8px'}}
          >
            {executing ? '⏳ Running...' : '▶️ Run Workflow'}
          </button>
          <button className="toolbar-btn-primary">
            <Play size={18} /> Deploy
          </button>
        </div>
      </div>

      {/* Main Layout */}
      <div className="builder-layout">
        {/* Sidebar */}
        <div className="components-sidebar">
          <h3>Components</h3>
          <p className="sidebar-subtitle">Drag and drop to canvas</p>

          <div className="component-library">
            {Object.entries(nodeLibrary).map(([category, categoryNodes]) => (
              <div key={category} className="category-section">
                <div
                  className="category-header"
                  onClick={() => toggleCategory(category)}
                >
                  <span className="category-icon">{expandedCategories[category] ? '▼' : '▶'}</span>
                  <span className="category-name">{category}</span>
                  <span className="category-count">{categoryNodes.length}</span>
                </div>

                {expandedCategories[category] && (
                  <div className="category-nodes">
                    {categoryNodes.map((node) => (
                      <div
                        key={node.type}
                        className="component-item"
                        draggable
                        onDragStart={(e) => onDragStart(e, node.type, { ...node, category })}
                      >
                        <span className="component-icon">{node.icon}</span>
                        <div className="component-info">
                          <span className="component-name">{node.name}</span>
                          <span className="component-desc">{node.desc}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Canvas */}
        <div className="workflow-canvas" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes.map(node => ({
              ...node,
              data: { ...node.data, onDelete: deleteNode }
            }))}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            deleteKeyCode="Delete"
            fitView
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={20} size={1} color="#e0e0e0" />
          </ReactFlow>
        </div>

        {/* Variables Panel (Dify-like) */}
        {showVariablesPanel && (
          <div className="variables-panel">
            <div className="variables-header">
              <h3>📊 Workflow Variables</h3>
              <X
                size={18}
                className="close-icon"
                onClick={() => setShowVariablesPanel(false)}
                style={{ cursor: 'pointer' }}
              />
            </div>

            <div className="variables-content">
              {Object.keys(workflowVariables).length === 0 ? (
                <div className="variables-empty">
                  <div style={{ fontSize: '40px', marginBottom: '12px', opacity: 0.4 }}>📊</div>
                  <p style={{ color: '#999', fontSize: '13px' }}>
                    No variables yet. Variables will appear here during workflow execution.
                  </p>
                  <p style={{ color: '#bbb', fontSize: '12px', marginTop: '8px' }}>
                    Each node's output becomes a variable that can be used by other nodes.
                  </p>
                </div>
              ) : (
                <div className="variables-list">
                  {Object.entries(workflowVariables).map(([varName, varData]) => (
                    <div key={varName} className="variable-item">
                      <div className="variable-header">
                        <span className="variable-name">{varName}</span>
                        <span className={`variable-type ${varData.type}`}>
                          {varData.type || 'unknown'}
                        </span>
                      </div>

                      <div className="variable-meta">
                        <span className="variable-source">
                          📍 {varData.source || 'Unknown Node'}
                        </span>
                      </div>

                      <div className="variable-value">
                        <div className="value-label">Value:</div>
                        <pre className="value-content">
                          {typeof varData.value === 'object'
                            ? JSON.stringify(varData.value, null, 2)
                            : String(varData.value || 'null')}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="variables-footer">
              <button
                className="variables-btn"
                onClick={() => setWorkflowVariables({})}
                disabled={Object.keys(workflowVariables).length === 0}
              >
                🗑️ Clear All
              </button>
              <button
                className="variables-btn"
                onClick={() => {
                  const dataStr = JSON.stringify(workflowVariables, null, 2);
                  const blob = new Blob([dataStr], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = 'workflow-variables.json';
                  link.click();
                }}
                disabled={Object.keys(workflowVariables).length === 0}
              >
                💾 Export
              </button>
            </div>
          </div>
        )}

        {/* Toggle Variables Panel Button (when hidden) */}
        {!showVariablesPanel && (
          <button
            className="toggle-variables-btn"
            onClick={() => setShowVariablesPanel(true)}
            title="Show Variables Panel"
          >
            📊
          </button>
        )}

        {/* Test/Debug Panel Modal */}
        {showTestPanel && (
          <div className="execution-modal-overlay">
            <div className="test-panel-modal">
              <div className="test-panel-header">
                <h3>🧪 Test Workflow</h3>
                <X size={20} className="close-icon" onClick={() => setShowTestPanel(false)} />
              </div>

              <div className="test-panel-content">
                <div className="test-section">
                  <div className="test-section-header">
                    <h4>📝 Input Data (JSON)</h4>
                    <div className="test-actions-inline">
                      <button
                        className="test-btn-small"
                        onClick={() => {
                          try {
                            const parsed = JSON.parse(testInput);
                            setTestInput(JSON.stringify(parsed, null, 2));
                          } catch (e) {
                            alert('Invalid JSON format');
                          }
                        }}
                      >
                        Format JSON
                      </button>
                      <button
                        className="test-btn-small"
                        onClick={() => {
                          setTestInput('{\n  "message": "Hello, test the workflow!"\n}');
                        }}
                      >
                        Reset
                      </button>
                    </div>
                  </div>

                  <textarea
                    className="test-input-editor"
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    placeholder='{\n  "message": "Your test input here"\n}'
                    rows={12}
                  />

                  {/* JSON Validation Indicator */}
                  <div className="test-validation">
                    {(() => {
                      try {
                        JSON.parse(testInput);
                        return <span className="validation-success">✅ Valid JSON</span>;
                      } catch (e) {
                        return <span className="validation-error">❌ Invalid JSON: {e.message}</span>;
                      }
                    })()}
                  </div>
                </div>

                {/* Saved Test Cases */}
                <div className="test-section">
                  <h4>💾 Saved Test Cases ({savedTestCases.length})</h4>

                  {savedTestCases.length === 0 ? (
                    <div className="test-empty">
                      <p>No saved test cases yet.</p>
                      <p style={{fontSize: '12px', color: '#999'}}>Save your current input as a test case to reuse it later.</p>
                    </div>
                  ) : (
                    <div className="test-cases-list">
                      {savedTestCases.map((testCase, index) => (
                        <div key={index} className="test-case-item">
                          <div className="test-case-header">
                            <span className="test-case-name">{testCase.name}</span>
                            <div className="test-case-actions">
                              <button
                                className="test-case-btn"
                                onClick={() => setTestInput(testCase.input)}
                                title="Load this test case"
                              >
                                ↻
                              </button>
                              <button
                                className="test-case-btn delete"
                                onClick={() => {
                                  setSavedTestCases(prev => prev.filter((_, i) => i !== index));
                                }}
                                title="Delete"
                              >
                                ×
                              </button>
                            </div>
                          </div>
                          <pre className="test-case-preview">
                            {testCase.input.substring(0, 80)}
                            {testCase.input.length > 80 ? '...' : ''}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="test-panel-footer">
                <button
                  className="test-btn"
                  onClick={() => {
                    const name = prompt('Enter a name for this test case:');
                    if (name) {
                      setSavedTestCases(prev => [...prev, { name, input: testInput }]);
                    }
                  }}
                  disabled={(() => {
                    try {
                      JSON.parse(testInput);
                      return false;
                    } catch {
                      return true;
                    }
                  })()}
                >
                  💾 Save Test Case
                </button>
                <button
                  className="test-btn-primary"
                  onClick={() => {
                    setShowTestPanel(false);
                    executeWorkflow();
                  }}
                  disabled={(() => {
                    try {
                      JSON.parse(testInput);
                      return nodes.length === 0;
                    } catch {
                      return true;
                    }
                  })()}
                >
                  ▶️ Run with Test Data
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Workflow Versions Panel */}
        {showVersionsPanel && (
          <div className="execution-modal-overlay">
            <div className="versions-panel-modal">
              <div className="versions-panel-header">
                <h3>📋 Workflow Versions</h3>
                <X size={20} className="close-icon" onClick={() => setShowVersionsPanel(false)} />
              </div>

              <div className="versions-panel-content">
                <div className="versions-info">
                  <p className="versions-current">
                    Current: <strong>{currentVersionName}</strong>
                  </p>
                  <p className="versions-count">
                    {workflowVersions.length} saved version{workflowVersions.length !== 1 ? 's' : ''}
                  </p>
                </div>

                {workflowVersions.length === 0 ? (
                  <div className="versions-empty">
                    <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.4 }}>📋</div>
                    <p style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>No saved versions yet</p>
                    <p style={{ fontSize: '14px', color: '#999' }}>
                      Click "💾 Save Version" in the toolbar to save your first version.
                    </p>
                    <p style={{ fontSize: '13px', color: '#bbb', marginTop: '12px' }}>
                      Versions allow you to experiment safely and restore previous states of your workflow.
                    </p>
                  </div>
                ) : (
                  <div className="versions-list">
                    {workflowVersions
                      .slice()
                      .reverse()
                      .map((versionInfo, index) => (
                        <div key={versionInfo.id} className="version-item">
                          <div className="version-header">
                            <div className="version-info">
                              <span className="version-name">Version {versionInfo.version}</span>
                              <span className="version-meta">
                                {new Date(versionInfo.created_at).toLocaleString()}
                              </span>
                              {versionInfo.change_description && (
                                <span className="version-description" style={{display: 'block', marginTop: '4px', fontSize: '13px', color: '#888'}}>
                                  {versionInfo.change_description}
                                </span>
                              )}
                            </div>
                            {index === 0 && (
                              <span className="version-badge-latest">Latest</span>
                            )}
                          </div>

                          <div className="version-actions">
                            <button
                              className="version-btn load"
                              onClick={() => loadVersion(versionInfo.version)}
                              title="Load this version"
                            >
                              ↻ Load
                            </button>
                            <button
                              className="version-btn export"
                              onClick={async () => {
                                try {
                                  const response = await fetch(`http://localhost:5000/api/workflows/${currentWorkflowId}?version=${versionInfo.version}`);
                                  const data = await response.json();
                                  const dataStr = JSON.stringify(data, null, 2);
                                  const blob = new Blob([dataStr], { type: 'application/json' });
                                  const url = URL.createObjectURL(blob);
                                  const link = document.createElement('a');
                                  link.href = url;
                                  link.download = `${currentWorkflowName}_v${versionInfo.version}.json`;
                                  link.click();
                                } catch (error) {
                                  console.error('Export failed:', error);
                                  alert('Failed to export version');
                                }
                              }}
                              title="Export this version"
                            >
                              ⬇️ Export
                            </button>
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </div>

              <div className="versions-panel-footer">
                <button
                  className="versions-footer-btn"
                  onClick={exportVersions}
                  disabled={workflowVersions.length === 0}
                >
                  📦 Export All Versions
                </button>
                <button
                  className="versions-footer-btn primary"
                  onClick={() => {
                    setShowVersionsPanel(false);
                    saveVersion();
                  }}
                >
                  💾 Save Current as New Version
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Execution Results Modal */}
        {showExecutionResults && (
          <div className="execution-modal-overlay">
            <div className="execution-modal">
              <div className="execution-header">
                <h3>
                  {executing ? '⏳ Workflow Executing...' :
                   executionResults?.status === 'success' ? '✅ Workflow Execution Complete' :
                   executionResults?.status === 'error' ? '❌ Workflow Execution Failed' :
                   '📊 Workflow Results'}
                </h3>
                <X size={20} className="close-icon" onClick={() => setShowExecutionResults(false)} />
              </div>

              <div className="execution-content">
                {executing && (
                  <div className="execution-loading">
                    <div className="spinner"></div>
                    <p>Executing workflow nodes...</p>
                  </div>
                )}

                {!executing && executionResults && (
                  <>
                    {/* Status Summary */}
                    <div className={`execution-status ${executionResults.status}`}>
                      <strong>Status:</strong> {executionResults.status.toUpperCase()}
                      {executionResults.error && (
                        <div className="error-message">
                          <strong>Error:</strong> {executionResults.error}
                        </div>
                      )}
                    </div>

                    {/* Execution Logs */}
                    {executionResults.logs && executionResults.logs.length > 0 && (
                      <div className="execution-section">
                        <h4>📋 Execution Logs</h4>
                        <div className="logs-container">
                          {executionResults.logs.map((log, idx) => (
                            <div key={idx} className={`log-entry ${log.level.toLowerCase()}`}>
                              <span className="log-level">[{log.level}]</span>
                              <span className="log-timestamp">{new Date(log.timestamp).toLocaleTimeString()}</span>
                              <span className="log-message">{log.message}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Node Results */}
                    {executionResults.results && Object.keys(executionResults.results).length > 0 && (
                      <div className="execution-section">
                        <h4>🔍 Node Results</h4>
                        <div className="results-container">
                          {Object.entries(executionResults.results).map(([nodeId, result]) => {
                            const node = nodes.find(n => n.id === nodeId);
                            return (
                              <div key={nodeId} className="node-result">
                                <div className="node-result-header">
                                  <strong>{node?.data?.icon} {node?.data?.label || nodeId}</strong>
                                  <span className="node-id">({nodeId})</span>
                                </div>
                                <pre className="node-result-data">
                                  {typeof result === 'object'
                                    ? JSON.stringify(result, null, 2)
                                    : String(result)}
                                </pre>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Final Output */}
                    {executionResults.status === 'success' && (
                      <div className="execution-section">
                        <h4>🎯 Final Output</h4>
                        <div className="final-output">
                          {Object.keys(executionResults.results).length > 0 ? (
                            <pre>
                              {JSON.stringify(
                                executionResults.results[
                                  Object.keys(executionResults.results)[Object.keys(executionResults.results).length - 1]
                                ],
                                null,
                                2
                              )}
                            </pre>
                          ) : (
                            <p>No output generated</p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Traceback (if error) */}
                    {executionResults.traceback && (
                      <div className="execution-section">
                        <h4>🐛 Error Traceback</h4>
                        <pre className="traceback">{executionResults.traceback}</pre>
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="execution-actions">
                <button className="close-btn" onClick={() => setShowExecutionResults(false)}>
                  Close
                </button>
                {!executing && executionResults && (
                  <button
                    className="run-again-btn"
                    onClick={() => {
                      setShowExecutionResults(false);
                      setTimeout(executeWorkflow, 100);
                    }}
                  >
                    ▶️ Run Again
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Configuration Panel */}
        {showConfigPanel && selectedNode && (
          <div className="config-panel">
            <div className="config-header">
              <h3>Configure Node</h3>
              <X size={20} className="close-icon" onClick={() => setShowConfigPanel(false)} />
            </div>

            <div className="config-content">
              {/* DEBUG INFO - TEMPORARY */}
              <div style={{
                background: '#ffeb3b',
                padding: '12px',
                marginBottom: '16px',
                borderRadius: '8px',
                border: '2px solid #f57f17',
                fontFamily: 'monospace',
                fontSize: '12px'
              }}>
                <strong>🔍 DEBUG INFO:</strong><br/>
                Category: <strong>{selectedNode.data.category || 'UNDEFINED'}</strong><br/>
                Node Type: {selectedNode.data.nodeType || 'UNDEFINED'}<br/>
                Type: {selectedNode.data.type || 'UNDEFINED'}
              </div>

              {/* Basic Info */}
              <div className="config-field">
                <label>Node Name</label>
                <input
                  type="text"
                  value={selectedNode.data.label || ''}
                  onChange={(e) => updateNodeData(selectedNode.id, { label: e.target.value })}
                />
              </div>

              <div className="config-field">
                <label>Description</label>
                <textarea
                  value={selectedNode.data.desc || ''}
                  onChange={(e) => updateNodeData(selectedNode.id, { desc: e.target.value })}
                  rows={2}
                />
              </div>


              {/* Dynamic Node Configuration - Works for ALL 136 nodes! */}
              <DynamicNodeConfig
                node={selectedNode}
                updateNodeData={updateNodeData}
              />

              {/* Save & Delete Actions */}
              <div className="config-actions">
                <button
                  className="save-node-btn"
                  onClick={() => {
                    setShowConfigPanel(false);
                  }}
                >
                  ✓ Save Configuration
                </button>

                <button
                  className="delete-node-btn"
                  onClick={() => {
                    deleteNode(selectedNode.id);
                    setShowConfigPanel(false);
                    setSelectedNode(null);
                  }}
                >
                  <Trash2 size={16} /> Delete Node
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Template Gallery Modal */}
      {showTemplateGallery && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '1400px',
            height: '90vh',
            backgroundColor: 'white',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <TemplateGallery
              onImportTemplate={handleTemplateImport}
              onClose={() => setShowTemplateGallery(false)}
            />
          </div>
        </div>
      )}

      {/* Interactive Playground Modal */}
      {showPlayground && (
        <ExecutionPlayground
          workflow={{ nodes, edges }}
          inputs={{}}
          onClose={() => setShowPlayground(false)}
        />
      )}

      {/* Save Workflow Dialog */}
      {showSaveDialog && (
        <div className="modal-overlay" onClick={() => setShowSaveDialog(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{
            maxWidth: '500px',
            padding: '30px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
          }}>
            <h2 style={{ marginBottom: '20px', fontSize: '24px', fontWeight: 'bold' }}>💾 Save Workflow</h2>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                Workflow Name *
              </label>
              <input
                type="text"
                value={saveWorkflowName}
                onChange={(e) => setSaveWorkflowName(e.target.value)}
                placeholder="Enter workflow name..."
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none'
                }}
                autoFocus
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                Description (Optional)
              </label>
              <textarea
                value={saveWorkflowDescription}
                onChange={(e) => setSaveWorkflowDescription(e.target.value)}
                placeholder="Describe what this workflow does..."
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '8px',
                  fontSize: '16px',
                  outline: 'none',
                  minHeight: '100px',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowSaveDialog(false)}
                style={{
                  padding: '12px 24px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '8px',
                  background: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveWorkflow}
                style={{
                  padding: '12px 24px',
                  border: 'none',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                💾 Save Workflow
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Workflow Dialog */}
      {showLoadDialog && (
        <div className="modal-overlay" onClick={() => setShowLoadDialog(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{
            maxWidth: '800px',
            maxHeight: '80vh',
            overflowY: 'auto',
            padding: '30px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
          }}>
            <h2 style={{ marginBottom: '20px', fontSize: '24px', fontWeight: 'bold' }}>📂 Load Workflow</h2>

            {savedWorkflows.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                <p style={{ fontSize: '18px', marginBottom: '10px' }}>No saved workflows found</p>
                <p style={{ fontSize: '14px' }}>Create and save a workflow to see it here</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '16px' }}>
                {savedWorkflows.map(workflow => (
                  <div
                    key={workflow.id}
                    style={{
                      border: '2px solid #e0e0e0',
                      borderRadius: '12px',
                      padding: '20px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      ':hover': { borderColor: '#667eea' }
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <div style={{ flex: 1 }}>
                        <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>
                          {workflow.name}
                        </h3>
                        {workflow.description && (
                          <p style={{ color: '#666', marginBottom: '12px', fontSize: '14px' }}>
                            {workflow.description}
                          </p>
                        )}
                        <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: '#888' }}>
                          <span>Version {workflow.version}</span>
                          <span>Updated: {new Date(workflow.updated_at).toLocaleDateString()}</span>
                          {workflow.category && <span>Category: {workflow.category}</span>}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={() => handleLoadWorkflow(workflow.id)}
                          style={{
                            padding: '8px 16px',
                            border: 'none',
                            borderRadius: '6px',
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: 'white',
                            fontSize: '14px',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          Load
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteWorkflow(workflow.id, workflow.name);
                          }}
                          style={{
                            padding: '8px 16px',
                            border: '2px solid #ff4444',
                            borderRadius: '6px',
                            background: 'white',
                            color: '#ff4444',
                            fontSize: '14px',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowLoadDialog(false)}
                style={{
                  padding: '12px 24px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '8px',
                  background: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Workflow Dialog */}
      {showImportDialog && (
        <div className="modal-overlay" onClick={() => setShowImportDialog(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{
            maxWidth: '500px',
            padding: '30px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
          }}>
            <h2 style={{ marginBottom: '20px', fontSize: '24px', fontWeight: 'bold' }}>📥 Import Workflow</h2>

            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#666', marginBottom: '16px', fontSize: '14px' }}>
                Import a workflow from a JSON file. The file should contain nodes, edges, and metadata exported from this system.
              </p>

              <label
                htmlFor="workflow-import-file"
                style={{
                  display: 'block',
                  padding: '40px',
                  border: '2px dashed #667eea',
                  borderRadius: '12px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  backgroundColor: '#f8f9ff',
                  transition: 'all 0.2s'
                }}
              >
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>📁</div>
                <div style={{ fontSize: '16px', fontWeight: '600', color: '#667eea', marginBottom: '4px' }}>
                  Click to select JSON file
                </div>
                <div style={{ fontSize: '13px', color: '#999' }}>
                  or drag and drop here
                </div>
              </label>
              <input
                id="workflow-import-file"
                type="file"
                accept=".json"
                onChange={importWorkflow}
                style={{ display: 'none' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowImportDialog(false)}
                style={{
                  padding: '12px 24px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '8px',
                  background: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowBuilder;
