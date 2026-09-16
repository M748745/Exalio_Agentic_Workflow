// ========================================================================
// NODE CONFIGURATION SCHEMAS
// Defines what configuration fields each node type needs
// ========================================================================

export const NODE_CONFIG_SCHEMAS = {
  // ===== INPUT NODES =====
  file_upload: {
    fields: [
      { name: 'file', label: 'Upload File', type: 'file', placeholder: 'Select a file' },
      { name: 'fileType', label: 'Expected File Type', type: 'select', options: ['auto', 'pdf', 'txt', 'json', 'csv', 'xml', 'docx', 'xlsx', 'image'], default: 'auto' },
      { name: 'maxSize', label: 'Max File Size (MB)', type: 'number', placeholder: '10', default: 10 },
      { name: 'encoding', label: 'Text Encoding', type: 'select', options: ['utf-8', 'ascii', 'latin-1'], default: 'utf-8' }
    ]
  },

  text_input: {
    fields: [
      { name: 'prompt', label: 'Input Prompt', type: 'text', placeholder: 'Enter your text...' },
      { name: 'placeholder', label: 'Placeholder Text', type: 'text', placeholder: 'Placeholder for user input' },
      { name: 'defaultValue', label: 'Default Value', type: 'textarea', placeholder: 'Default text value', rows: 4 },
      { name: 'required', label: 'Required', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'validation', label: 'Validation Pattern (Regex)', type: 'text', placeholder: '^[A-Za-z0-9]+$' }
    ]
  },

  api_input: {
    fields: [
      { name: 'url', label: 'API URL', type: 'url', placeholder: 'https://api.example.com/endpoint' },
      { name: 'method', label: 'HTTP Method', type: 'select', options: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], default: 'GET' },
      { name: 'headers', label: 'Headers (JSON)', type: 'textarea', placeholder: '{"Authorization": "Bearer token"}', rows: 4 },
      { name: 'body', label: 'Request Body (JSON)', type: 'textarea', placeholder: '{"key": "value"}', rows: 4 },
      { name: 'timeout', label: 'Timeout (seconds)', type: 'number', default: 30 }
    ]
  },

  database_query: {
    fields: [
      { name: 'dbType', label: 'Database Type', type: 'select', options: ['mysql', 'postgresql', 'mongodb', 'sqlite'], default: 'mysql' },
      { name: 'connectionString', label: 'Connection String', type: 'text', placeholder: 'mysql://user:pass@localhost/db' },
      { name: 'query', label: 'Query', type: 'textarea', placeholder: 'SELECT * FROM users WHERE active = 1', rows: 4 }
    ]
  },

  // ===== DATA LOADERS =====
  mysql: {
    fields: [
      { name: 'host', label: 'Host', type: 'text', placeholder: 'localhost', default: 'localhost' },
      { name: 'port', label: 'Port', type: 'number', placeholder: '3306', default: 3306 },
      { name: 'database', label: 'Database Name', type: 'text', placeholder: 'mydb' },
      { name: 'username', label: 'Username', type: 'text', placeholder: 'root' },
      { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
      { name: 'query', label: 'SQL Query', type: 'textarea', placeholder: 'SELECT * FROM users', rows: 4 }
    ]
  },

  postgresql: {
    fields: [
      { name: 'host', label: 'Host', type: 'text', placeholder: 'localhost', default: 'localhost' },
      { name: 'port', label: 'Port', type: 'number', placeholder: '5432', default: 5432 },
      { name: 'database', label: 'Database Name', type: 'text', placeholder: 'postgres' },
      { name: 'username', label: 'Username', type: 'text', placeholder: 'postgres' },
      { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
      { name: 'query', label: 'SQL Query', type: 'textarea', placeholder: 'SELECT * FROM users', rows: 4 }
    ]
  },

  mongodb: {
    fields: [
      { name: 'connectionString', label: 'Connection String', type: 'text', placeholder: 'mongodb://localhost:27017' },
      { name: 'database', label: 'Database Name', type: 'text', placeholder: 'mydb' },
      { name: 'collection', label: 'Collection', type: 'text', placeholder: 'users' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['find', 'findOne', 'insert', 'update', 'delete'], default: 'find' },
      { name: 'query', label: 'Query (JSON)', type: 'textarea', placeholder: '{"active": true}', rows: 4 }
    ]
  },

  s3: {
    fields: [
      { name: 'bucketName', label: 'S3 Bucket Name', type: 'text', placeholder: 'my-bucket' },
      { name: 'region', label: 'AWS Region', type: 'text', placeholder: 'us-east-1', default: 'us-east-1' },
      { name: 'accessKeyId', label: 'Access Key ID', type: 'text', placeholder: 'AKIA...' },
      { name: 'secretAccessKey', label: 'Secret Access Key', type: 'password', placeholder: '••••••••' },
      { name: 'filePath', label: 'File Path in Bucket', type: 'text', placeholder: 'folder/file.txt' }
    ]
  },

  azure_blob: {
    fields: [
      { name: 'connectionString', label: 'Connection String', type: 'text', placeholder: 'DefaultEndpointsProtocol=https;...' },
      { name: 'containerName', label: 'Container Name', type: 'text', placeholder: 'my-container' },
      { name: 'blobPath', label: 'Blob Path', type: 'text', placeholder: 'folder/file.txt' }
    ]
  },

  gcs: {
    fields: [
      { name: 'projectId', label: 'GCP Project ID', type: 'text', placeholder: 'my-project-id' },
      { name: 'bucketName', label: 'Bucket Name', type: 'text', placeholder: 'my-bucket' },
      { name: 'credentialsJson', label: 'Service Account JSON', type: 'textarea', placeholder: '{"type": "service_account", ...}', rows: 6 },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: 'folder/file.txt' }
    ]
  },

  notion: {
    fields: [
      { name: 'apiKey', label: 'Notion API Key', type: 'password', placeholder: 'secret_...' },
      { name: 'databaseId', label: 'Database ID', type: 'text', placeholder: 'abc123...' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['query', 'create', 'update', 'delete'], default: 'query' },
      { name: 'filter', label: 'Filter (JSON)', type: 'textarea', placeholder: '{"property": "Status", "select": {"equals": "Done"}}', rows: 4 }
    ]
  },

  trello: {
    fields: [
      { name: 'apiKey', label: 'Trello API Key', type: 'password', placeholder: 'Your API key' },
      { name: 'token', label: 'Trello Token', type: 'password', placeholder: 'Your token' },
      { name: 'boardId', label: 'Board ID', type: 'text', placeholder: 'Board ID' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['get_cards', 'create_card', 'update_card', 'delete_card'], default: 'get_cards' }
    ]
  },

  confluence: {
    fields: [
      { name: 'baseUrl', label: 'Confluence Base URL', type: 'url', placeholder: 'https://your-domain.atlassian.net/wiki' },
      { name: 'username', label: 'Username/Email', type: 'text', placeholder: 'user@example.com' },
      { name: 'apiToken', label: 'API Token', type: 'password', placeholder: 'Your API token' },
      { name: 'spaceKey', label: 'Space Key', type: 'text', placeholder: 'SPACE' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['get_page', 'search', 'create_page'], default: 'search' }
    ]
  },

  slack: {
    fields: [
      { name: 'token', label: 'Slack Bot Token', type: 'password', placeholder: 'xoxb-...' },
      { name: 'channel', label: 'Channel ID', type: 'text', placeholder: 'C1234567890' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['get_messages', 'send_message', 'get_users'], default: 'get_messages' },
      { name: 'query', label: 'Search Query (optional)', type: 'text', placeholder: 'from:@user in:#channel' }
    ]
  },

  jira: {
    fields: [
      { name: 'baseUrl', label: 'Jira Base URL', type: 'url', placeholder: 'https://your-domain.atlassian.net' },
      { name: 'username', label: 'Username/Email', type: 'text', placeholder: 'user@example.com' },
      { name: 'apiToken', label: 'API Token', type: 'password', placeholder: 'Your API token' },
      { name: 'jql', label: 'JQL Query', type: 'textarea', placeholder: 'project = PROJ AND status = "In Progress"', rows: 3 },
      { name: 'operation', label: 'Operation', type: 'select', options: ['search', 'create_issue', 'update_issue'], default: 'search' }
    ]
  },

  // ===== FILE PARSERS =====
  pdf_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path', 'url'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path (if file_path)', type: 'text', placeholder: '/path/to/file.pdf' },
      { name: 'url', label: 'URL (if url)', type: 'url', placeholder: 'https://example.com/doc.pdf' },
      { name: 'outputFormat', label: 'Output Format', type: 'select', options: ['text', 'markdown', 'json'], default: 'text' },
      { name: 'extractImages', label: 'Extract Images', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'ocrEnabled', label: 'OCR for Scanned PDFs', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  image_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path', 'url'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/image.jpg' },
      { name: 'url', label: 'URL', type: 'url', placeholder: 'https://example.com/image.jpg' },
      { name: 'ocrEnabled', label: 'Extract Text (OCR)', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'visionAnalysis', label: 'Vision Understanding', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'prompt', label: 'Vision Prompt', type: 'textarea', placeholder: 'Describe this image in detail', rows: 3 }
    ]
  },

  json_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path', 'text'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/data.json' },
      { name: 'jsonText', label: 'JSON Text (if text)', type: 'textarea', placeholder: '{"key": "value"}', rows: 6 },
      { name: 'jsonPath', label: 'JSON Path Filter (Optional)', type: 'text', placeholder: '$.data.items[*]' }
    ]
  },

  xml_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path', 'text'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/data.xml' },
      { name: 'xmlText', label: 'XML Text (if text)', type: 'textarea', placeholder: '<root><item>...</item></root>', rows: 6 },
      { name: 'xpathFilter', label: 'XPath Filter (Optional)', type: 'text', placeholder: '//items/item' }
    ]
  },

  csv_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/data.csv' },
      { name: 'delimiter', label: 'Delimiter', type: 'text', placeholder: ',', default: ',' },
      { name: 'hasHeader', label: 'Has Header Row', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'encoding', label: 'Encoding', type: 'select', options: ['utf-8', 'latin-1', 'ascii'], default: 'utf-8' }
    ]
  },

  txt_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/file.txt' },
      { name: 'encoding', label: 'Encoding', type: 'select', options: ['utf-8', 'latin-1', 'ascii'], default: 'utf-8' },
      { name: 'splitLines', label: 'Split into Lines', type: 'select', options: ['false', 'true'], default: 'false' }
    ]
  },

  excel_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/data.xlsx' },
      { name: 'sheetName', label: 'Sheet Name (Optional)', type: 'text', placeholder: 'Sheet1 (leave empty for all)' },
      { name: 'hasHeader', label: 'Has Header Row', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  docx_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/document.docx' },
      { name: 'outputFormat', label: 'Output Format', type: 'select', options: ['text', 'markdown', 'json'], default: 'text' },
      { name: 'extractImages', label: 'Extract Images', type: 'select', options: ['false', 'true'], default: 'false' }
    ]
  },

  // ===== CONTROL FLOW =====
  if_else: {
    fields: [
      { name: 'condition', label: 'Condition', type: 'textarea', placeholder: 'data.score > 0.8', rows: 3 }
    ]
  },

  switch_case: {
    fields: [
      { name: 'switchVariable', label: 'Switch Variable', type: 'text', placeholder: 'data.status' },
      { name: 'cases', label: 'Cases (JSON)', type: 'textarea', placeholder: '{"success": "path1", "error": "path2"}', rows: 6 }
    ]
  },

  for_loop: {
    fields: [
      { name: 'arraySource', label: 'Array Source', type: 'text', placeholder: 'data.items or data' },
      { name: 'loopVariable', label: 'Loop Variable Name', type: 'text', placeholder: 'item', default: 'item' },
      { name: 'maxIterations', label: 'Max Iterations', type: 'number', default: 100 }
    ]
  },

  while_loop: {
    fields: [
      { name: 'whileCondition', label: 'While Condition', type: 'textarea', placeholder: 'iteration < 10 && data.hasMore', rows: 3 },
      { name: 'maxIterations', label: 'Max Iterations', type: 'number', default: 100 }
    ]
  },

  // ===== OUTPUT NODES =====
  send_email: {
    fields: [
      { name: 'fromEmail', label: 'From Email', type: 'email', placeholder: 'noreply@example.com' },
      { name: 'toEmail', label: 'To Email(s)', type: 'text', placeholder: 'user@example.com (comma-separated)' },
      { name: 'emailSubject', label: 'Subject', type: 'text', placeholder: 'Workflow Notification' },
      { name: 'emailBody', label: 'Email Body', type: 'textarea', placeholder: 'Email content...', rows: 6 },
      { name: 'smtpServer', label: 'SMTP Server', type: 'text', placeholder: 'smtp.gmail.com:587' },
      { name: 'smtpUsername', label: 'SMTP Username', type: 'text', placeholder: 'username' },
      { name: 'smtpPassword', label: 'SMTP Password', type: 'password', placeholder: '••••••••' }
    ]
  },

  // ===== DATA TRANSFORMATION =====
  json_transform: {
    fields: [
      { name: 'inputJson', label: 'Input JSON', type: 'textarea', placeholder: '{"data": {...}}', rows: 6 },
      { name: 'transformation', label: 'JMESPath/JSONPath Expression', type: 'textarea', placeholder: 'data.items[*].{name: name, value: value}', rows: 4 }
    ]
  },

  data_mapper: {
    fields: [
      { name: 'sourceSchema', label: 'Source Schema (JSON)', type: 'textarea', placeholder: '{"old_field": "value"}', rows: 4 },
      { name: 'targetSchema', label: 'Target Schema (JSON)', type: 'textarea', placeholder: '{"new_field": "{{old_field}}"}', rows: 4 },
      { name: 'mappingRules', label: 'Mapping Rules (JSON)', type: 'textarea', placeholder: '{"new_field": "source.old_field"}', rows: 4 }
    ]
  },

  filter_node: {
    fields: [
      { name: 'arrayInput', label: 'Array Input', type: 'textarea', placeholder: '[{"name": "item1", "value": 10}, ...]', rows: 4 },
      { name: 'filterCondition', label: 'Filter Condition', type: 'text', placeholder: 'item.value > 5' },
      { name: 'filterType', label: 'Filter Type', type: 'select', options: ['include', 'exclude'], default: 'include' }
    ]
  },

  aggregation: {
    fields: [
      { name: 'arrayInput', label: 'Array Input', type: 'textarea', placeholder: '[1, 2, 3, 4, 5] or [{value: 10}, ...]', rows: 4 },
      { name: 'operation', label: 'Aggregation Operation', type: 'select', options: ['sum', 'avg', 'min', 'max', 'count', 'group'], default: 'sum' },
      { name: 'field', label: 'Field to Aggregate (for objects)', type: 'text', placeholder: 'value' },
      { name: 'groupBy', label: 'Group By Field (optional)', type: 'text', placeholder: 'category' }
    ]
  },

  string_ops: {
    fields: [
      { name: 'inputText', label: 'Input Text', type: 'textarea', placeholder: 'Text to manipulate...', rows: 4 },
      { name: 'operation', label: 'Operation', type: 'select', options: ['uppercase', 'lowercase', 'trim', 'replace', 'split', 'concat', 'substring', 'regex'], default: 'trim' },
      { name: 'parameters', label: 'Operation Parameters (JSON)', type: 'textarea', placeholder: '{"find": "old", "replace": "new"}', rows: 3 }
    ]
  },

  math_ops: {
    fields: [
      { name: 'expression', label: 'Math Expression', type: 'text', placeholder: '(a + b) * c / 2' },
      { name: 'variables', label: 'Variables (JSON)', type: 'textarea', placeholder: '{"a": 10, "b": 20, "c": 5}', rows: 4 }
    ]
  },

  variable_assign: {
    fields: [
      { name: 'variableName', label: 'Variable Name', type: 'text', placeholder: 'myVariable' },
      { name: 'value', label: 'Value', type: 'textarea', placeholder: 'Value to store...', rows: 4 },
      { name: 'scope', label: 'Scope', type: 'select', options: ['workflow', 'global', 'local'], default: 'workflow' }
    ]
  },

  data_validation: {
    fields: [
      { name: 'inputData', label: 'Input Data (JSON)', type: 'textarea', placeholder: '{"name": "John", "age": 30}', rows: 4 },
      { name: 'validationSchema', label: 'Validation Schema (JSON Schema)', type: 'textarea', placeholder: '{"type": "object", "required": ["name"], ...}', rows: 6 },
      { name: 'onFailure', label: 'On Validation Failure', type: 'select', options: ['throw_error', 'return_errors', 'skip'], default: 'throw_error' }
    ]
  },

  array_ops: {
    fields: [
      { name: 'arrayInput', label: 'Array Input', type: 'textarea', placeholder: '[1, 2, 3, 4, 5]', rows: 4 },
      { name: 'operation', label: 'Array Operation', type: 'select', options: ['push', 'pop', 'shift', 'unshift', 'sort', 'reverse', 'slice', 'splice', 'map', 'filter', 'reduce'], default: 'map' },
      { name: 'operationParams', label: 'Operation Parameters (JSON)', type: 'textarea', placeholder: '{"callback": "item * 2"}', rows: 3 }
    ]
  },

  format_converter: {
    fields: [
      { name: 'inputData', label: 'Input Data', type: 'textarea', placeholder: 'Data to convert...', rows: 6 },
      { name: 'inputFormat', label: 'Input Format', type: 'select', options: ['json', 'xml', 'csv', 'yaml', 'toml'], default: 'json' },
      { name: 'outputFormat', label: 'Output Format', type: 'select', options: ['json', 'xml', 'csv', 'yaml', 'toml'], default: 'json' }
    ]
  },

  universal_parser: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path', 'url', 'text'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/file' },
      { name: 'url', label: 'URL', type: 'url', placeholder: 'https://example.com/file' },
      { name: 'outputFormat', label: 'Output Format', type: 'select', options: ['text', 'json', 'markdown', 'structured'], default: 'text' },
      { name: 'intelligentParsing', label: 'Intelligent Parsing', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  // ===== CHATBOT BUILDER =====
  intent_recognition: {
    fields: [
      { name: 'userInput', label: 'User Input', type: 'textarea', placeholder: 'User message to classify...', rows: 3 },
      { name: 'intents', label: 'Intent List (comma-separated)', type: 'text', placeholder: 'greeting, booking, cancel, help, complaint' },
      { name: 'confidenceThreshold', label: 'Confidence Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.7 }
    ]
  },

  entity_extraction_chat: {
    fields: [
      { name: 'userInput', label: 'User Input', type: 'textarea', placeholder: 'User message...', rows: 3 },
      { name: 'entityTypes', label: 'Entity Types', type: 'text', placeholder: 'date, time, location, person_name' },
      { name: 'extractionSchema', label: 'Extraction Schema (JSON)', type: 'textarea', placeholder: '{"date": "string", "time": "string"}', rows: 4 }
    ]
  },

  dialog_state: {
    fields: [
      { name: 'contextId', label: 'Conversation Context ID', type: 'text', placeholder: 'conversation_123' },
      { name: 'stateVariables', label: 'State Variables (JSON)', type: 'textarea', placeholder: '{"stage": "booking", "step": 1}', rows: 4 },
      { name: 'updateStrategy', label: 'Update Strategy', type: 'select', options: ['merge', 'replace'], default: 'merge' }
    ]
  },

  slot_filling: {
    fields: [
      { name: 'requiredSlots', label: 'Required Slots (JSON)', type: 'textarea', placeholder: '["name", "email", "phone"]', rows: 3 },
      { name: 'currentSlots', label: 'Current Slot Values (JSON)', type: 'textarea', placeholder: '{"name": "John"}', rows: 3 },
      { name: 'promptTemplate', label: 'Prompt for Missing Slots', type: 'text', placeholder: 'Please provide your {slot_name}' }
    ]
  },

  response_template: {
    fields: [
      { name: 'templateType', label: 'Template Type', type: 'select', options: ['static', 'dynamic', 'llm_generated'], default: 'dynamic' },
      { name: 'template', label: 'Response Template', type: 'textarea', placeholder: 'Hello {{user_name}}, your booking for {{date}} is confirmed.', rows: 4 },
      { name: 'variables', label: 'Template Variables (JSON)', type: 'textarea', placeholder: '{"user_name": "John", "date": "2024-12-25"}', rows: 3 }
    ]
  },

  context_switch: {
    fields: [
      { name: 'currentTopic', label: 'Current Topic', type: 'text', placeholder: 'booking' },
      { name: 'userInput', label: 'User Input', type: 'textarea', placeholder: 'User message...', rows: 3 },
      { name: 'availableTopics', label: 'Available Topics (comma-separated)', type: 'text', placeholder: 'booking, cancellation, support, feedback' }
    ]
  },

  fallback_handler: {
    fields: [
      { name: 'defaultResponse', label: 'Default Fallback Response', type: 'textarea', placeholder: "I'm sorry, I didn't understand that...", rows: 3 },
      { name: 'suggestAlternatives', label: 'Suggest Alternatives', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'escalateAfterAttempts', label: 'Escalate After N Attempts', type: 'number', default: 3 }
    ]
  },

  clarification: {
    fields: [
      { name: 'ambiguousInput', label: 'Ambiguous User Input', type: 'textarea', placeholder: 'User message to clarify...', rows: 3 },
      { name: 'clarificationQuestion', label: 'Clarification Question Template', type: 'text', placeholder: 'Did you mean {{option1}} or {{option2}}?' },
      { name: 'options', label: 'Clarification Options (JSON)', type: 'textarea', placeholder: '["option1", "option2", "option3"]', rows: 3 }
    ]
  },

  multi_turn: {
    fields: [
      { name: 'conversationId', label: 'Conversation ID', type: 'text', placeholder: 'conversation_123' },
      { name: 'maxTurns', label: 'Max Conversation Turns', type: 'number', default: 10 },
      { name: 'maintainContext', label: 'Maintain Context', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  small_talk: {
    fields: [
      { name: 'userInput', label: 'User Input', type: 'textarea', placeholder: 'User greeting or small talk...', rows: 3 },
      { name: 'smallTalkType', label: 'Small Talk Type', type: 'select', options: ['greeting', 'goodbye', 'thanks', 'weather', 'general'], default: 'greeting' },
      { name: 'personalityTone', label: 'Personality Tone', type: 'select', options: ['friendly', 'professional', 'casual', 'formal'], default: 'friendly' }
    ]
  },

  handoff: {
    fields: [
      { name: 'reason', label: 'Handoff Reason', type: 'textarea', placeholder: 'Reason for transferring to human agent...', rows: 3 },
      { name: 'agentType', label: 'Agent Type', type: 'select', options: ['support', 'sales', 'technical', 'manager'], default: 'support' },
      { name: 'priority', label: 'Priority', type: 'select', options: ['low', 'medium', 'high', 'urgent'], default: 'medium' },
      { name: 'conversationHistory', label: 'Include Conversation History', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  // ===== SCHEDULING & TRIGGERS =====
  cron_scheduler: {
    fields: [
      { name: 'cronExpression', label: 'Cron Expression', type: 'text', placeholder: '0 9 * * MON-FRI (9 AM weekdays)' },
      { name: 'timezone', label: 'Timezone', type: 'text', placeholder: 'America/New_York', default: 'UTC' },
      { name: 'enabled', label: 'Enabled', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  event_trigger: {
    fields: [
      { name: 'eventType', label: 'Event Type', type: 'text', placeholder: 'user.created, order.completed' },
      { name: 'eventFilter', label: 'Event Filter (JSON)', type: 'textarea', placeholder: '{"status": "completed"}', rows: 3 },
      { name: 'debounceMs', label: 'Debounce (milliseconds)', type: 'number', placeholder: '1000' }
    ]
  },

  webhook_trigger: {
    fields: [
      { name: 'webhookPath', label: 'Webhook Path', type: 'text', placeholder: '/webhooks/my-webhook' },
      { name: 'httpMethod', label: 'HTTP Method', type: 'select', options: ['POST', 'GET', 'PUT', 'PATCH'], default: 'POST' },
      { name: 'authentication', label: 'Authentication', type: 'select', options: ['none', 'api_key', 'bearer_token', 'basic'], default: 'api_key' },
      { name: 'apiKey', label: 'API Key (if api_key auth)', type: 'password', placeholder: 'Your API key' }
    ]
  },

  file_watch: {
    fields: [
      { name: 'watchPath', label: 'Directory/File to Watch', type: 'text', placeholder: '/path/to/watch' },
      { name: 'events', label: 'Events to Watch', type: 'text', placeholder: 'created, modified, deleted (comma-separated)' },
      { name: 'filePattern', label: 'File Pattern (glob)', type: 'text', placeholder: '*.pdf' },
      { name: 'recursive', label: 'Recursive', type: 'select', options: ['false', 'true'], default: 'false' }
    ]
  },

  email_trigger: {
    fields: [
      { name: 'emailAddress', label: 'Email Address to Monitor', type: 'email', placeholder: 'inbox@example.com' },
      { name: 'imapServer', label: 'IMAP Server', type: 'text', placeholder: 'imap.gmail.com' },
      { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
      { name: 'subjectFilter', label: 'Subject Filter (regex)', type: 'text', placeholder: '.*Order.*' }
    ]
  },

  db_trigger: {
    fields: [
      { name: 'dbType', label: 'Database Type', type: 'select', options: ['mysql', 'postgresql', 'mongodb'], default: 'mysql' },
      { name: 'connectionString', label: 'Connection String', type: 'text', placeholder: 'mysql://user:pass@localhost/db' },
      { name: 'table', label: 'Table/Collection', type: 'text', placeholder: 'users' },
      { name: 'changeType', label: 'Change Type', type: 'select', options: ['insert', 'update', 'delete', 'any'], default: 'any' }
    ]
  },

  interval_trigger: {
    fields: [
      { name: 'intervalSeconds', label: 'Interval (seconds)', type: 'number', placeholder: '60', default: 60 },
      { name: 'enabled', label: 'Enabled', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  time_delay: {
    fields: [
      { name: 'delayType', label: 'Delay Type', type: 'select', options: ['seconds', 'minutes', 'hours', 'days', 'until_timestamp'], default: 'minutes' },
      { name: 'delayValue', label: 'Delay Value', type: 'number', placeholder: '5' },
      { name: 'timestamp', label: 'Timestamp (for until_timestamp)', type: 'text', placeholder: '2024-12-25T09:00:00Z' }
    ]
  },

  // ===== ADVANCED AGENT FEATURES =====
  // Design Pattern 1: Augmented LLM (Single-Shot)
  augmented_llm: {
    fields: [
      { name: 'prompt', label: 'Task Prompt', type: 'textarea', placeholder: 'Single-shot task: sorting, extraction, condensing...', rows: 4 },
      { name: 'retrievalEnabled', label: 'Enable Retrieval (RAG)', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'retrievalSource', label: 'Retrieval Source', type: 'text', placeholder: 'Vector store collection name' },
      { name: 'toolsEnabled', label: 'Enable Tools', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'availableTools', label: 'Available Tools (comma-separated)', type: 'text', placeholder: 'calculator, search, api_call' },
      { name: 'memoryEnabled', label: 'Enable Memory', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'model', label: 'Model', type: 'text', placeholder: 'llama3.2:3b', default: 'llama3.2:3b' }
    ]
  },

  // Design Pattern 2: ReAct Loop
  react_loop: {
    fields: [
      { name: 'task', label: 'Task Description', type: 'textarea', placeholder: 'Complex problem requiring iterative reasoning...', rows: 4 },
      { name: 'maxIterations', label: 'Max Reasoning Iterations', type: 'number', default: 5, min: 1, max: 20 },
      { name: 'tools', label: 'Available Tools (JSON)', type: 'textarea', placeholder: '["search", "calculator", "wikipedia", "api_call"]', rows: 3 },
      { name: 'thinkingPrompt', label: 'Thinking Prompt Template', type: 'textarea', placeholder: 'Think step by step...', rows: 2 },
      { name: 'stopCondition', label: 'Stop Condition', type: 'text', placeholder: 'goal_achieved or max_iterations' }
    ]
  },

  // Design Pattern 3: Router/Orchestrator-Worker
  router_orchestrator: {
    fields: [
      { name: 'routingPrompt', label: 'Initial Request', type: 'textarea', placeholder: 'User query to route to appropriate specialist...', rows: 3 },
      { name: 'routingStrategy', label: 'Routing Strategy', type: 'select', options: ['complexity_based', 'topic_based', 'cost_optimized', 'custom'], default: 'complexity_based' },
      { name: 'simpleModelPath', label: 'Simple Model/Path', type: 'text', placeholder: 'llama3.2:3b or worker_node_id' },
      { name: 'complexModelPath', label: 'Complex Model/Path', type: 'text', placeholder: 'llama3.1:70b or specialist_node_id' },
      { name: 'routingThreshold', label: 'Complexity Threshold', type: 'number', min: 0, max: 1, step: 0.1, default: 0.5 },
      { name: 'workerSpecialists', label: 'Worker Specialists (JSON)', type: 'textarea', placeholder: '{"sql": "sql_specialist", "api": "api_specialist"}', rows: 4 }
    ]
  },

  // Design Pattern 4: Planner-Executor (Enhanced)
  planner_executor: {
    fields: [
      { name: 'goal', label: 'High-Level Goal', type: 'textarea', placeholder: 'Complex workflow requiring decomposition...', rows: 4 },
      { name: 'planningPrompt', label: 'Planning Prompt', type: 'textarea', placeholder: 'Break down into parallel and sequential steps...', rows: 3 },
      { name: 'executionStrategy', label: 'Execution Strategy', type: 'select', options: ['sequential', 'parallel', 'adaptive', 'hybrid'], default: 'parallel' },
      { name: 'maxParallelTasks', label: 'Max Parallel Tasks', type: 'number', default: 5, min: 1, max: 20 },
      { name: 'integrationMethod', label: 'Result Integration', type: 'select', options: ['merge', 'summarize', 'structured'], default: 'summarize' },
      { name: 'replanOnFailure', label: 'Replan on Failure', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  // Design Pattern 5: Evaluator-Optimizer (Reflexive)
  evaluator_optimizer: {
    fields: [
      { name: 'task', label: 'Task to Produce', type: 'textarea', placeholder: 'High-quality task requiring refinement...', rows: 4 },
      { name: 'qualityStandards', label: 'Quality Standards', type: 'textarea', placeholder: 'Criteria: accuracy, completeness, clarity...', rows: 3 },
      { name: 'maxRounds', label: 'Max Refinement Rounds', type: 'number', default: 2, min: 1, max: 3 },
      { name: 'producerModel', label: 'Producer Model', type: 'text', placeholder: 'Model that generates output' },
      { name: 'criticModel', label: 'Critic Model', type: 'text', placeholder: 'Model that evaluates (can be same)' },
      { name: 'improvementPrompt', label: 'Improvement Prompt', type: 'textarea', placeholder: 'Based on critique, improve output...', rows: 2 },
      { name: 'acceptanceThreshold', label: 'Quality Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.85 }
    ]
  },

  // Design Pattern 6: Verifier-Gated
  verifier_gated: {
    fields: [
      { name: 'action', label: 'Action to Perform', type: 'textarea', placeholder: 'Irreversible action: payment, deletion, compliance...', rows: 3 },
      { name: 'verificationChecks', label: 'Verification Checks (JSON)', type: 'textarea', placeholder: '["amount_valid", "authorization_confirmed", "compliance_met"]', rows: 4 },
      { name: 'verifierType', label: 'Verifier Type', type: 'select', options: ['rule_based', 'llm_based', 'hybrid', 'human'], default: 'hybrid' },
      { name: 'verificationModel', label: 'Verification Model', type: 'text', placeholder: 'Independent model for verification' },
      { name: 'failureAction', label: 'On Verification Failure', type: 'select', options: ['block', 'escalate_human', 'log_and_notify'], default: 'block' },
      { name: 'requiresHumanApproval', label: 'Requires Human Approval', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'auditLogging', label: 'Full Audit Logging', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  // Design Pattern 7: Multi-Agent + Memory
  multi_agent_memory: {
    fields: [
      { name: 'agents', label: 'Specialized Agents (JSON)', type: 'textarea', placeholder: '[{"name": "researcher", "role": "...", "platform": "mcp"}]', rows: 6 },
      { name: 'coordinationProtocol', label: 'Coordination Protocol', type: 'select', options: ['mcp', 'a2a', 'custom'], default: 'mcp' },
      { name: 'sharedMemory', label: 'Shared Memory Store', type: 'text', placeholder: 'Persistent memory collection' },
      { name: 'memoryStrategy', label: 'Memory Strategy', type: 'select', options: ['episodic', 'semantic', 'procedural', 'hybrid'], default: 'hybrid' },
      { name: 'crossPlatform', label: 'Cross-Platform Operation', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'orchestrationMode', label: 'Orchestration Mode', type: 'select', options: ['centralized', 'distributed', 'peer_to_peer'], default: 'centralized' }
    ]
  },

  // Legacy pattern (keep for compatibility)

  plan_execute: {
    fields: [
      { name: 'goal', label: 'Goal Description', type: 'textarea', placeholder: 'High-level goal for the agent...', rows: 4 },
      { name: 'planningPrompt', label: 'Planning Prompt (optional)', type: 'textarea', placeholder: 'Custom planning instructions...', rows: 3 },
      { name: 'executionStrategy', label: 'Execution Strategy', type: 'select', options: ['sequential', 'parallel', 'adaptive'], default: 'sequential' }
    ]
  },

  tool_calling: {
    fields: [
      { name: 'toolName', label: 'Tool/Function Name', type: 'text', placeholder: 'get_weather' },
      { name: 'toolDescription', label: 'Tool Description', type: 'textarea', placeholder: 'Gets current weather for a location', rows: 3 },
      { name: 'parameters', label: 'Parameters (JSON Schema)', type: 'textarea', placeholder: '{"location": {"type": "string", "description": "City name"}}', rows: 4 }
    ]
  },

  multi_agent: {
    fields: [
      { name: 'agents', label: 'Agent Definitions (JSON)', type: 'textarea', placeholder: '[{"name": "researcher", "role": "..."}]', rows: 6 },
      { name: 'collaborationMode', label: 'Collaboration Mode', type: 'select', options: ['sequential', 'parallel', 'hierarchical', 'debate'], default: 'sequential' },
      { name: 'sharedMemory', label: 'Shared Memory', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  agent_router: {
    fields: [
      { name: 'routingPrompt', label: 'Routing Prompt', type: 'textarea', placeholder: 'Query to route to appropriate agent...', rows: 3 },
      { name: 'availableAgents', label: 'Available Agents (JSON)', type: 'textarea', placeholder: '{"sales": "Handles sales", "support": "Handles support"}', rows: 4 },
      { name: 'routingStrategy', label: 'Routing Strategy', type: 'select', options: ['llm_based', 'keyword', 'embedding_similarity'], default: 'llm_based' }
    ]
  },

  self_reflection: {
    fields: [
      { name: 'agentOutput', label: 'Agent Output to Evaluate', type: 'textarea', placeholder: 'Previous agent response...', rows: 4 },
      { name: 'evaluationCriteria', label: 'Evaluation Criteria', type: 'text', placeholder: 'accuracy, completeness, clarity' },
      { name: 'improvementPrompt', label: 'Improvement Prompt', type: 'textarea', placeholder: 'How can this be improved?', rows: 3 }
    ]
  },

  agent_memory: {
    fields: [
      { name: 'agentId', label: 'Agent ID', type: 'text', placeholder: 'agent_123' },
      { name: 'memoryType', label: 'Memory Type', type: 'select', options: ['episodic', 'semantic', 'procedural', 'all'], default: 'all' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['store', 'retrieve', 'search', 'clear'], default: 'store' },
      { name: 'content', label: 'Memory Content', type: 'textarea', placeholder: 'Content to store/search...', rows: 4 }
    ]
  },

  agent_supervisor: {
    fields: [
      { name: 'supervisedAgents', label: 'Supervised Agents (JSON)', type: 'textarea', placeholder: '["agent1", "agent2", "agent3"]', rows: 3 },
      { name: 'orchestrationMode', label: 'Orchestration Mode', type: 'select', options: ['round_robin', 'priority', 'dynamic'], default: 'dynamic' },
      { name: 'performanceMonitoring', label: 'Performance Monitoring', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  // ===== OUTPUT NODES =====
  display: {
    fields: [
      { name: 'content', label: 'Content to Display', type: 'textarea', placeholder: 'Results to show to user...', rows: 6 },
      { name: 'format', label: 'Display Format', type: 'select', options: ['text', 'json', 'markdown', 'html'], default: 'text' }
    ]
  },

  save_file: {
    fields: [
      { name: 'content', label: 'File Content', type: 'textarea', placeholder: 'Content to save...', rows: 6 },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/output.txt' },
      { name: 'format', label: 'File Format', type: 'select', options: ['text', 'json', 'csv', 'xml', 'pdf'], default: 'text' },
      { name: 'overwrite', label: 'Overwrite if Exists', type: 'select', options: ['false', 'true'], default: 'false' }
    ]
  },

  api_call: {
    fields: [
      { name: 'url', label: 'API URL', type: 'url', placeholder: 'https://api.example.com/endpoint' },
      { name: 'method', label: 'HTTP Method', type: 'select', options: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], default: 'POST' },
      { name: 'headers', label: 'Headers (JSON)', type: 'textarea', placeholder: '{"Authorization": "Bearer token"}', rows: 3 },
      { name: 'body', label: 'Request Body (JSON)', type: 'textarea', placeholder: '{"key": "value"}', rows: 4 }
    ]
  },

  database_write: {
    fields: [
      { name: 'dbType', label: 'Database Type', type: 'select', options: ['mysql', 'postgresql', 'mongodb', 'sqlite'], default: 'mysql' },
      { name: 'connectionString', label: 'Connection String', type: 'text', placeholder: 'mysql://user:pass@localhost/db' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['insert', 'update', 'delete', 'upsert'], default: 'insert' },
      { name: 'table', label: 'Table/Collection', type: 'text', placeholder: 'users' },
      { name: 'data', label: 'Data (JSON)', type: 'textarea', placeholder: '{"name": "John", "email": "john@example.com"}', rows: 4 }
    ]
  },

  // ===== INTEGRATION & CONNECTIVITY =====
  http_request: {
    fields: [
      { name: 'url', label: 'URL', type: 'url', placeholder: 'https://api.example.com/endpoint' },
      { name: 'method', label: 'HTTP Method', type: 'select', options: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'], default: 'GET' },
      { name: 'headers', label: 'Headers (JSON)', type: 'textarea', placeholder: '{"Authorization": "Bearer token", "Content-Type": "application/json"}', rows: 3 },
      { name: 'body', label: 'Request Body (JSON)', type: 'textarea', placeholder: '{"key": "value"}', rows: 4 },
      { name: 'timeout', label: 'Timeout (seconds)', type: 'number', default: 30 }
    ]
  },

  webhook_sender: {
    fields: [
      { name: 'webhookUrl', label: 'Webhook URL', type: 'url', placeholder: 'https://hooks.example.com/webhook' },
      { name: 'payload', label: 'Payload (JSON)', type: 'textarea', placeholder: '{"event": "workflow.completed", "data": {...}}', rows: 6 },
      { name: 'headers', label: 'Custom Headers (JSON)', type: 'textarea', placeholder: '{"X-Custom-Header": "value"}', rows: 3 },
      { name: 'retryOnFailure', label: 'Retry on Failure', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  webhook_receiver: {
    fields: [
      { name: 'webhookPath', label: 'Webhook Path', type: 'text', placeholder: '/webhooks/my-webhook' },
      { name: 'httpMethod', label: 'Accepted HTTP Method', type: 'select', options: ['POST', 'GET', 'PUT', 'ANY'], default: 'POST' },
      { name: 'authentication', label: 'Authentication', type: 'select', options: ['none', 'api_key', 'bearer_token', 'hmac_signature'], default: 'api_key' },
      { name: 'secret', label: 'Secret Key', type: 'password', placeholder: 'Your secret key' }
    ]
  },

  discord_node: {
    fields: [
      { name: 'botToken', label: 'Discord Bot Token', type: 'password', placeholder: 'Your bot token' },
      { name: 'channelId', label: 'Channel ID', type: 'text', placeholder: '1234567890123456789' },
      { name: 'message', label: 'Message', type: 'textarea', placeholder: 'Message to send...', rows: 4 },
      { name: 'embed', label: 'Use Embed', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'embedConfig', label: 'Embed Config (JSON)', type: 'textarea', placeholder: '{"title": "Title", "description": "..."}', rows: 4 }
    ]
  },

  whatsapp_node: {
    fields: [
      { name: 'provider', label: 'Provider', type: 'select', options: ['twilio', 'whatsapp_business_api'], default: 'twilio' },
      { name: 'accountSid', label: 'Account SID (Twilio)', type: 'text', placeholder: 'AC...' },
      { name: 'authToken', label: 'Auth Token', type: 'password', placeholder: 'Your auth token' },
      { name: 'from', label: 'From Number', type: 'text', placeholder: 'whatsapp:+1234567890' },
      { name: 'to', label: 'To Number', type: 'text', placeholder: 'whatsapp:+1234567890' },
      { name: 'message', label: 'Message', type: 'textarea', placeholder: 'WhatsApp message...', rows: 4 }
    ]
  },

  teams_node: {
    fields: [
      { name: 'webhookUrl', label: 'Teams Webhook URL', type: 'url', placeholder: 'https://outlook.office.com/webhook/...' },
      { name: 'title', label: 'Message Title', type: 'text', placeholder: 'Notification' },
      { name: 'text', label: 'Message Text', type: 'textarea', placeholder: 'Message content...', rows: 4 },
      { name: 'color', label: 'Theme Color (hex)', type: 'text', placeholder: '0078D4', default: '0078D4' }
    ]
  },

  file_ops: {
    fields: [
      { name: 'operation', label: 'File Operation', type: 'select', options: ['read', 'write', 'append', 'delete', 'move', 'copy', 'list'], default: 'read' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/file.txt' },
      { name: 'content', label: 'Content (for write/append)', type: 'textarea', placeholder: 'File content...', rows: 6 },
      { name: 'destinationPath', label: 'Destination Path (for move/copy)', type: 'text', placeholder: '/path/to/destination' },
      { name: 'encoding', label: 'Encoding', type: 'select', options: ['utf-8', 'ascii', 'latin-1'], default: 'utf-8' }
    ]
  },

  ftp_node: {
    fields: [
      { name: 'host', label: 'FTP Host', type: 'text', placeholder: 'ftp.example.com' },
      { name: 'port', label: 'Port', type: 'number', placeholder: '21', default: 21 },
      { name: 'username', label: 'Username', type: 'text', placeholder: 'ftpuser' },
      { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
      { name: 'protocol', label: 'Protocol', type: 'select', options: ['ftp', 'sftp', 'ftps'], default: 'sftp' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['upload', 'download', 'list', 'delete'], default: 'download' },
      { name: 'remotePath', label: 'Remote Path', type: 'text', placeholder: '/path/to/file' },
      { name: 'localPath', label: 'Local Path', type: 'text', placeholder: '/local/path/file' }
    ]
  },

  database_ops: {
    fields: [
      { name: 'dbType', label: 'Database Type', type: 'select', options: ['mysql', 'postgresql', 'mongodb', 'sqlite', 'mssql'], default: 'mysql' },
      { name: 'connectionString', label: 'Connection String', type: 'text', placeholder: 'mysql://user:pass@localhost:3306/dbname' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['select', 'insert', 'update', 'delete', 'raw_query'], default: 'select' },
      { name: 'query', label: 'Query/Statement', type: 'textarea', placeholder: 'SELECT * FROM users WHERE active = 1', rows: 4 },
      { name: 'parameters', label: 'Query Parameters (JSON)', type: 'textarea', placeholder: '{"user_id": 123}', rows: 3 }
    ]
  },

  graphql_node: {
    fields: [
      { name: 'endpoint', label: 'GraphQL Endpoint', type: 'url', placeholder: 'https://api.example.com/graphql' },
      { name: 'query', label: 'GraphQL Query', type: 'textarea', placeholder: 'query { users { id name email } }', rows: 6 },
      { name: 'variables', label: 'Variables (JSON)', type: 'textarea', placeholder: '{"userId": 123}', rows: 3 },
      { name: 'headers', label: 'Headers (JSON)', type: 'textarea', placeholder: '{"Authorization": "Bearer token"}', rows: 3 }
    ]
  },

  websocket_node: {
    fields: [
      { name: 'url', label: 'WebSocket URL', type: 'url', placeholder: 'wss://example.com/ws' },
      { name: 'operation', label: 'Operation', type: 'select', options: ['connect', 'send', 'listen', 'disconnect'], default: 'send' },
      { name: 'message', label: 'Message to Send', type: 'textarea', placeholder: '{"type": "message", "data": "..."}', rows: 4 },
      { name: 'timeout', label: 'Timeout (seconds)', type: 'number', default: 30 }
    ]
  },

  email_node: {
    fields: [
      { name: 'provider', label: 'Email Provider', type: 'select', options: ['gmail', 'outlook', 'yahoo', 'custom'], default: 'gmail' },
      { name: 'from_email', label: 'From Email Address', type: 'email', placeholder: 'your.email@gmail.com' },
      { name: 'from_password', label: 'App Password', type: 'password', placeholder: 'App-specific password (not regular password)' },
      { name: 'to_emails', label: 'To Email(s)', type: 'text', placeholder: 'recipient@example.com (comma-separated for multiple)' },
      { name: 'subject', label: 'Subject', type: 'text', placeholder: 'Email Subject' },
      { name: 'body', label: 'Email Body', type: 'textarea', placeholder: 'Email content here...', rows: 8 },
      { name: 'html', label: 'HTML Email', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'cc_emails', label: 'CC (Optional)', type: 'text', placeholder: 'cc@example.com (comma-separated)' },
      { name: 'bcc_emails', label: 'BCC (Optional)', type: 'text', placeholder: 'bcc@example.com (comma-separated)' },
      { name: 'smtp_host', label: 'Custom SMTP Host (Optional)', type: 'text', placeholder: 'smtp.yourserver.com (only for custom provider)' },
      { name: 'smtp_port', label: 'Custom SMTP Port (Optional)', type: 'number', placeholder: '587' }
    ]
  },

  sms_node: {
    fields: [
      { name: 'provider', label: 'SMS Provider', type: 'select', options: ['twilio', 'aws_sns', 'vonage'], default: 'twilio' },
      { name: 'from_number', label: 'From Phone Number', type: 'text', placeholder: '+1234567890 (E.164 format)' },
      { name: 'to_numbers', label: 'To Phone Number(s)', type: 'text', placeholder: '+1234567890 (comma-separated for multiple)' },
      { name: 'message', label: 'Message', type: 'textarea', placeholder: 'SMS message (max 160 chars for standard SMS)', rows: 4 },
      { name: 'account_sid', label: 'Account SID (Twilio)', type: 'text', placeholder: 'Twilio Account SID' },
      { name: 'auth_token', label: 'Auth Token (Twilio)', type: 'password', placeholder: 'Twilio Auth Token' },
      { name: 'api_key', label: 'API Key (AWS/Vonage)', type: 'text', placeholder: 'API Key for AWS SNS or Vonage' },
      { name: 'api_secret', label: 'API Secret (AWS/Vonage)', type: 'password', placeholder: 'API Secret for AWS SNS or Vonage' }
    ]
  },

  slack_node: {
    fields: [
      { name: 'method', label: 'Authentication Method', type: 'select', options: ['webhook', 'bot_token'], default: 'webhook' },
      { name: 'webhook_url', label: 'Webhook URL (for webhook method)', type: 'text', placeholder: 'https://hooks.slack.com/services/...' },
      { name: 'bot_token', label: 'Bot Token (for bot method)', type: 'password', placeholder: 'xoxb-...' },
      { name: 'channel', label: 'Channel (for bot method)', type: 'text', placeholder: '#general or C1234567890' },
      { name: 'message', label: 'Message', type: 'textarea', placeholder: 'Slack message content...', rows: 6 },
      { name: 'username', label: 'Bot Username (Optional)', type: 'text', placeholder: 'Workflow Bot', default: 'Workflow Bot' },
      { name: 'icon_emoji', label: 'Bot Icon (Optional)', type: 'text', placeholder: ':robot_face:', default: ':robot_face:' }
    ]
  },

  // ===== LLM NODES =====
  ollama_llm: {
    fields: [
      { name: 'model', label: 'Model', type: 'text', placeholder: 'llama3.2:3b' },
      { name: 'systemPrompt', label: 'System Prompt', type: 'textarea', placeholder: 'You are a helpful assistant.', rows: 4 },
      { name: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1, default: 0.7 },
      { name: 'maxTokens', label: 'Max Tokens', type: 'number', default: 2000 }
    ]
  },

  openai_llm: {
    fields: [
      { name: 'apiKey', label: 'OpenAI API Key', type: 'password', placeholder: 'sk-...' },
      { name: 'model', label: 'Model', type: 'select', options: ['gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-3.5-turbo', 'o1-preview', 'o1-mini'], default: 'gpt-4o' },
      { name: 'systemPrompt', label: 'System Prompt', type: 'textarea', placeholder: 'You are a helpful assistant.', rows: 4 },
      { name: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1, default: 0.7 },
      { name: 'maxTokens', label: 'Max Tokens', type: 'number', default: 4000 }
    ]
  },

  anthropic_llm: {
    fields: [
      { name: 'apiKey', label: 'Anthropic API Key', type: 'password', placeholder: 'sk-ant-...' },
      { name: 'model', label: 'Model', type: 'select', options: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'], default: 'claude-3-5-sonnet-20241022' },
      { name: 'systemPrompt', label: 'System Prompt', type: 'textarea', placeholder: 'You are a helpful assistant.', rows: 4 },
      { name: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 1, step: 0.1, default: 0.7 },
      { name: 'maxTokens', label: 'Max Tokens', type: 'number', default: 4096 }
    ]
  },

  cohere_llm: {
    fields: [
      { name: 'apiKey', label: 'Cohere API Key', type: 'password', placeholder: 'Your API key' },
      { name: 'model', label: 'Model', type: 'select', options: ['command', 'command-light', 'command-r', 'command-r-plus'], default: 'command-r' },
      { name: 'prompt', label: 'Prompt', type: 'textarea', placeholder: 'Your query...', rows: 4 },
      { name: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1, default: 0.7 }
    ]
  },

  huggingface_llm: {
    fields: [
      { name: 'apiKey', label: 'HuggingFace API Key', type: 'password', placeholder: 'hf_...' },
      { name: 'model', label: 'Model ID', type: 'text', placeholder: 'meta-llama/Llama-2-7b-chat-hf' },
      { name: 'prompt', label: 'Prompt', type: 'textarea', placeholder: 'Your query...', rows: 4 },
      { name: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1, default: 0.7 }
    ]
  },

  vertexai_llm: {
    fields: [
      { name: 'projectId', label: 'GCP Project ID', type: 'text', placeholder: 'my-project-id' },
      { name: 'location', label: 'Location', type: 'text', placeholder: 'us-central1', default: 'us-central1' },
      { name: 'model', label: 'Model', type: 'select', options: ['gemini-pro', 'gemini-pro-vision', 'gemini-1.5-pro', 'gemini-1.5-flash'], default: 'gemini-1.5-pro' },
      { name: 'prompt', label: 'Prompt', type: 'textarea', placeholder: 'Your query...', rows: 4 },
      { name: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 1, step: 0.1, default: 0.7 }
    ]
  },

  vision_llm: {
    fields: [
      { name: 'provider', label: 'Vision LLM Provider', type: 'select', options: ['openai_gpt4v', 'anthropic_claude', 'google_gemini'], default: 'openai_gpt4v' },
      { name: 'apiKey', label: 'API Key', type: 'password', placeholder: 'Your API key' },
      { name: 'imageSource', label: 'Image Source', type: 'select', options: ['file_upload', 'url', 'base64'], default: 'file_upload' },
      { name: 'imageUrl', label: 'Image URL (if url)', type: 'url', placeholder: 'https://example.com/image.jpg' },
      { name: 'prompt', label: 'Vision Prompt', type: 'textarea', placeholder: 'Describe this image in detail...', rows: 4 },
      { name: 'maxTokens', label: 'Max Tokens', type: 'number', default: 1000 }
    ]
  },

  text_to_image: {
    fields: [
      { name: 'provider', label: 'Image Generation Provider', type: 'select', options: ['openai_dalle', 'stability_ai', 'midjourney'], default: 'openai_dalle' },
      { name: 'apiKey', label: 'API Key', type: 'password', placeholder: 'Your API key' },
      { name: 'prompt', label: 'Image Description Prompt', type: 'textarea', placeholder: 'A serene landscape with mountains and a lake at sunset...', rows: 4 },
      { name: 'negativePrompt', label: 'Negative Prompt (optional)', type: 'textarea', placeholder: 'blurry, low quality, distorted...', rows: 2 },
      { name: 'size', label: 'Image Size', type: 'select', options: ['256x256', '512x512', '1024x1024', '1024x1792', '1792x1024'], default: '1024x1024' },
      { name: 'quality', label: 'Quality', type: 'select', options: ['standard', 'hd'], default: 'standard' },
      { name: 'style', label: 'Style', type: 'select', options: ['natural', 'vivid'], default: 'natural' }
    ]
  },

  text_to_speech: {
    fields: [
      { name: 'provider', label: 'TTS Provider', type: 'select', options: ['openai', 'google_cloud', 'amazon_polly', 'elevenlabs'], default: 'openai' },
      { name: 'apiKey', label: 'API Key', type: 'password', placeholder: 'Your API key' },
      { name: 'text', label: 'Text to Convert', type: 'textarea', placeholder: 'Text that will be converted to speech...', rows: 6 },
      { name: 'voice', label: 'Voice', type: 'select', options: ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'], default: 'alloy' },
      { name: 'speed', label: 'Speed', type: 'number', min: 0.25, max: 4.0, step: 0.25, default: 1.0 },
      { name: 'outputFormat', label: 'Output Format', type: 'select', options: ['mp3', 'opus', 'aac', 'flac'], default: 'mp3' }
    ]
  },

  // ===== PROCESSING NODES =====
  llm_query: {
    fields: [
      { name: 'prompt', label: 'Prompt', type: 'textarea', placeholder: 'Ask the LLM anything...', rows: 6 },
      { name: 'model', label: 'Model (optional, uses default)', type: 'text', placeholder: 'llama3.2:3b' },
      { name: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1, default: 0.7 }
    ]
  },

  ocr: {
    fields: [
      { name: 'inputSource', label: 'Input Source', type: 'select', options: ['file_upload', 'file_path', 'url'], default: 'file_upload' },
      { name: 'filePath', label: 'File Path', type: 'text', placeholder: '/path/to/image.jpg' },
      { name: 'url', label: 'URL', type: 'url', placeholder: 'https://example.com/image.jpg' },
      { name: 'language', label: 'Language', type: 'text', placeholder: 'eng (Tesseract lang code)', default: 'eng' }
    ]
  },

  embeddings: {
    fields: [
      { name: 'text', label: 'Text to Embed', type: 'textarea', placeholder: 'Text that will be converted to vector...', rows: 4 },
      { name: 'model', label: 'Embedding Model', type: 'select', options: ['ollama', 'openai', 'cohere'], default: 'ollama' },
      { name: 'modelName', label: 'Model Name', type: 'text', placeholder: 'nomic-embed-text', default: 'nomic-embed-text' }
    ]
  },

  classification: {
    fields: [
      { name: 'text', label: 'Text to Classify', type: 'textarea', placeholder: 'Text to classify...', rows: 4 },
      { name: 'labels', label: 'Classification Labels', type: 'text', placeholder: 'positive, negative, neutral (comma-separated)' },
      { name: 'model', label: 'Model (optional)', type: 'text', placeholder: 'Leave empty for default' }
    ]
  },

  extraction: {
    fields: [
      { name: 'text', label: 'Text to Extract From', type: 'textarea', placeholder: 'Text containing entities...', rows: 4 },
      { name: 'entityTypes', label: 'Entity Types', type: 'text', placeholder: 'person, organization, location (comma-separated)' },
      { name: 'schema', label: 'Extraction Schema (JSON)', type: 'textarea', placeholder: '{"name": "string", "email": "string"}', rows: 4 }
    ]
  },

  // ===== ANALYSIS NODES =====
  similarity: {
    fields: [
      { name: 'text1', label: 'First Text', type: 'textarea', placeholder: 'First text to compare...', rows: 3 },
      { name: 'text2', label: 'Second Text', type: 'textarea', placeholder: 'Second text to compare...', rows: 3 },
      { name: 'method', label: 'Similarity Method', type: 'select', options: ['cosine', 'jaccard', 'levenshtein', 'semantic'], default: 'semantic' }
    ]
  },

  scoring: {
    fields: [
      { name: 'content', label: 'Content to Score', type: 'textarea', placeholder: 'Content to evaluate...', rows: 4 },
      { name: 'criteria', label: 'Scoring Criteria', type: 'text', placeholder: 'quality, relevance, accuracy (comma-separated)' },
      { name: 'scale', label: 'Scoring Scale', type: 'select', options: ['1-5', '1-10', '0-100', 'percentage'], default: '1-10' }
    ]
  },

  sentiment: {
    fields: [
      { name: 'text', label: 'Text to Analyze', type: 'textarea', placeholder: 'Text for sentiment analysis...', rows: 4 },
      { name: 'outputFormat', label: 'Output Format', type: 'select', options: ['label', 'score', 'both'], default: 'both' },
      { name: 'granularity', label: 'Granularity', type: 'select', options: ['document', 'sentence', 'aspect'], default: 'document' }
    ]
  },

  pattern_detection: {
    fields: [
      { name: 'text', label: 'Text to Analyze', type: 'textarea', placeholder: 'Text to check for AI generation...', rows: 4 },
      { name: 'detectionType', label: 'Detection Type', type: 'select', options: ['ai_generated', 'plagiarism', 'pattern'], default: 'ai_generated' },
      { name: 'threshold', label: 'Confidence Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.8 }
    ]
  },

  benchmarking: {
    fields: [
      { name: 'actualOutput', label: 'Actual Output', type: 'textarea', placeholder: 'Model/system output...', rows: 4 },
      { name: 'expectedOutput', label: 'Expected Output', type: 'textarea', placeholder: 'Ground truth/benchmark...', rows: 4 },
      { name: 'metrics', label: 'Metrics to Calculate', type: 'text', placeholder: 'accuracy, precision, recall, f1 (comma-separated)' }
    ]
  },

  // ===== RAG & EVALUATION =====
  hybrid_search: {
    fields: [
      { name: 'query', label: 'Search Query', type: 'text', placeholder: 'What are you looking for?' },
      { name: 'collection', label: 'Collection Name', type: 'text', placeholder: 'my_collection', default: 'default' },
      { name: 'nResults', label: 'Number of Results', type: 'number', default: 5, min: 1, max: 20 },
      { name: 'vectorWeight', label: 'Vector Search Weight', type: 'number', min: 0, max: 1, step: 0.1, default: 0.7 },
      { name: 'keywordWeight', label: 'Keyword Search Weight', type: 'number', min: 0, max: 1, step: 0.1, default: 0.3 }
    ]
  },

  rag_evaluator: {
    fields: [
      { name: 'question', label: 'Question', type: 'text', placeholder: 'User question' },
      { name: 'answer', label: 'Generated Answer', type: 'textarea', placeholder: 'RAG system answer...', rows: 4 },
      { name: 'retrievedContext', label: 'Retrieved Context', type: 'textarea', placeholder: 'Context from retrieval...', rows: 4 },
      { name: 'groundTruth', label: 'Ground Truth (optional)', type: 'textarea', placeholder: 'Expected answer...', rows: 3 },
      { name: 'metrics', label: 'Metrics to Evaluate', type: 'text', placeholder: 'faithfulness, relevance, context_precision, context_recall, answer_relevancy, correctness' }
    ]
  },

  embedding_evaluator: {
    fields: [
      { name: 'queries', label: 'Test Queries (JSON array)', type: 'textarea', placeholder: '["query1", "query2"]', rows: 3 },
      { name: 'retrievedDocs', label: 'Retrieved Documents (JSON)', type: 'textarea', placeholder: '[["doc1", "doc2"], ["doc3"]]', rows: 4 },
      { name: 'relevantDocs', label: 'Relevant Documents (JSON)', type: 'textarea', placeholder: '[["doc1"], ["doc3", "doc4"]]', rows: 4 },
      { name: 'metrics', label: 'Retrieval Metrics', type: 'text', placeholder: 'precision, recall, mrr, ndcg, map (comma-separated)' }
    ]
  },

  grounded_answer: {
    fields: [
      { name: 'question', label: 'Question', type: 'text', placeholder: 'User question' },
      { name: 'context', label: 'Context/Sources', type: 'textarea', placeholder: 'Retrieved context with sources...', rows: 6 },
      { name: 'citationStyle', label: 'Citation Style', type: 'select', options: ['inline', 'footnote', 'numbered'], default: 'inline' },
      { name: 'model', label: 'Model (optional)', type: 'text', placeholder: 'Leave empty for default' }
    ]
  },

  // ===== LLMOps & MONITORING =====
  cost_monitor: {
    fields: [
      { name: 'provider', label: 'LLM Provider', type: 'select', options: ['openai', 'anthropic', 'cohere', 'custom'], default: 'openai' },
      { name: 'model', label: 'Model', type: 'text', placeholder: 'gpt-4' },
      { name: 'inputTokens', label: 'Input Tokens', type: 'number', placeholder: 'Number of input tokens' },
      { name: 'outputTokens', label: 'Output Tokens', type: 'number', placeholder: 'Number of output tokens' },
      { name: 'customPricing', label: 'Custom Pricing (JSON)', type: 'textarea', placeholder: '{"input": 0.01, "output": 0.03}', rows: 3 }
    ]
  },

  latency_monitor: {
    fields: [
      { name: 'operationName', label: 'Operation Name', type: 'text', placeholder: 'LLM call, API request, etc.' },
      { name: 'threshold', label: 'Alert Threshold (ms)', type: 'number', placeholder: '1000', default: 1000 },
      { name: 'aggregation', label: 'Aggregation', type: 'select', options: ['average', 'p50', 'p95', 'p99', 'max'], default: 'p95' }
    ]
  },

  cache_check: {
    fields: [
      { name: 'cacheKey', label: 'Cache Key Template', type: 'text', placeholder: 'prompt:{{hash}}' },
      { name: 'query', label: 'Query/Prompt', type: 'textarea', placeholder: 'Query to check in cache...', rows: 4 },
      { name: 'ttl', label: 'Cache TTL (seconds)', type: 'number', default: 3600 },
      { name: 'similarityThreshold', label: 'Similarity Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.95 }
    ]
  },

  ab_test: {
    fields: [
      { name: 'variantA', label: 'Variant A Config (JSON)', type: 'textarea', placeholder: '{"model": "gpt-4", "temperature": 0.7}', rows: 4 },
      { name: 'variantB', label: 'Variant B Config (JSON)', type: 'textarea', placeholder: '{"model": "gpt-3.5-turbo", "temperature": 0.5}', rows: 4 },
      { name: 'splitRatio', label: 'Split Ratio (A:B)', type: 'text', placeholder: '50:50', default: '50:50' },
      { name: 'metrics', label: 'Metrics to Track', type: 'text', placeholder: 'latency, cost, quality (comma-separated)' }
    ]
  },

  // ===== LOGIC NODES =====
  condition: {
    fields: [
      { name: 'condition', label: 'Condition Expression', type: 'textarea', placeholder: 'data.score > 0.8 && data.status == "active"', rows: 3 },
      { name: 'trueLabel', label: 'True Branch Label', type: 'text', placeholder: 'Pass', default: 'True' },
      { name: 'falseLabel', label: 'False Branch Label', type: 'text', placeholder: 'Fail', default: 'False' }
    ]
  },

  loop: {
    fields: [
      { name: 'arraySource', label: 'Array/Collection', type: 'textarea', placeholder: '[item1, item2, item3] or data.items', rows: 3 },
      { name: 'loopVariable', label: 'Loop Variable Name', type: 'text', placeholder: 'item', default: 'item' },
      { name: 'maxIterations', label: 'Max Iterations', type: 'number', default: 100 },
      { name: 'breakCondition', label: 'Break Condition (optional)', type: 'text', placeholder: 'item.done == true' }
    ]
  },

  parallel: {
    fields: [
      { name: 'parallelBranches', label: 'Number of Parallel Branches', type: 'number', default: 2, min: 2, max: 10 },
      { name: 'waitForAll', label: 'Wait for All Branches', type: 'select', options: ['true', 'false'], default: 'true' },
      { name: 'timeout', label: 'Timeout (seconds)', type: 'number', placeholder: '60' }
    ]
  },

  merge: {
    fields: [
      { name: 'mergeStrategy', label: 'Merge Strategy', type: 'select', options: ['concat', 'union', 'intersection', 'custom'], default: 'concat' },
      { name: 'mergeKey', label: 'Merge Key (for objects)', type: 'text', placeholder: 'id' },
      { name: 'conflictResolution', label: 'Conflict Resolution', type: 'select', options: ['first_wins', 'last_wins', 'merge_deep'], default: 'last_wins' }
    ]
  },

  human_review: {
    fields: [
      { name: 'reviewPrompt', label: 'Review Prompt', type: 'textarea', placeholder: 'Please review this content...', rows: 4 },
      { name: 'reviewers', label: 'Reviewer Emails', type: 'text', placeholder: 'reviewer@example.com (comma-separated)' },
      { name: 'timeout', label: 'Review Timeout (hours)', type: 'number', default: 24 },
      { name: 'requiresApproval', label: 'Requires Explicit Approval', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  // ===== ERROR HANDLING =====
  try_catch: {
    fields: [
      { name: 'tryDescription', label: 'Try Block Description', type: 'text', placeholder: 'What operation to try' },
      { name: 'errorTypes', label: 'Error Types to Catch', type: 'text', placeholder: 'NetworkError, TimeoutError, ValidationError (comma-separated)' },
      { name: 'logErrors', label: 'Log Errors', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  retry: {
    fields: [
      { name: 'maxRetries', label: 'Max Retry Attempts', type: 'number', default: 3, min: 1, max: 10 },
      { name: 'retryStrategy', label: 'Retry Strategy', type: 'select', options: ['exponential', 'linear', 'immediate', 'fibonacci'], default: 'exponential' },
      { name: 'initialDelay', label: 'Initial Delay (seconds)', type: 'number', default: 1, min: 0, max: 60, step: 0.5 },
      { name: 'maxDelay', label: 'Max Delay (seconds)', type: 'number', default: 60, min: 1, max: 300 },
      { name: 'backoffMultiplier', label: 'Backoff Multiplier', type: 'number', default: 2, min: 1, max: 10, step: 0.1 }
    ]
  },

  fallback: {
    fields: [
      { name: 'primaryOperation', label: 'Primary Operation', type: 'text', placeholder: 'Main operation description' },
      { name: 'fallbackOperation', label: 'Fallback Operation', type: 'text', placeholder: 'Backup operation description' },
      { name: 'fallbackValue', label: 'Fallback Value (JSON)', type: 'textarea', placeholder: '{"default": "value"}', rows: 3 }
    ]
  },

  timeout: {
    fields: [
      { name: 'timeoutSeconds', label: 'Timeout (seconds)', type: 'number', placeholder: '30', default: 30 },
      { name: 'onTimeout', label: 'On Timeout Action', type: 'select', options: ['throw_error', 'return_null', 'use_default'], default: 'throw_error' },
      { name: 'defaultValue', label: 'Default Value (if use_default)', type: 'textarea', placeholder: '{"result": "timeout"}', rows: 3 }
    ]
  },

  error_logger: {
    fields: [
      { name: 'errorMessage', label: 'Error Message', type: 'textarea', placeholder: 'Error details...', rows: 3 },
      { name: 'errorLevel', label: 'Error Level', type: 'select', options: ['debug', 'info', 'warning', 'error', 'critical'], default: 'error' },
      { name: 'logDestination', label: 'Log Destination', type: 'select', options: ['console', 'file', 'database', 'external_service'], default: 'console' },
      { name: 'includeStackTrace', label: 'Include Stack Trace', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  // ===== CONTROL FLOW (remaining) =====
  parallel_exec: {
    fields: [
      { name: 'tasks', label: 'Tasks to Execute (JSON array)', type: 'textarea', placeholder: '["task1", "task2", "task3"]', rows: 4 },
      { name: 'maxConcurrency', label: 'Max Concurrent Tasks', type: 'number', default: 5, min: 1, max: 20 },
      { name: 'waitForAll', label: 'Wait for All to Complete', type: 'select', options: ['true', 'false'], default: 'true' }
    ]
  },

  wait_delay: {
    fields: [
      { name: 'delaySeconds', label: 'Delay (seconds)', type: 'number', placeholder: '5', default: 5 },
      { name: 'reason', label: 'Delay Reason (optional)', type: 'text', placeholder: 'Waiting for API rate limit' }
    ]
  },

  break_continue: {
    fields: [
      { name: 'action', label: 'Action', type: 'select', options: ['break', 'continue'], default: 'break' },
      { name: 'condition', label: 'Condition (optional)', type: 'text', placeholder: 'item.done == true' }
    ]
  },

  // ===== GUARDRAILS & SECURITY =====
  // Layer 1: Input Screening
  input_screening: {
    fields: [
      { name: 'inputText', label: 'Input to Screen', type: 'textarea', placeholder: 'User input before model sees it...', rows: 4 },
      { name: 'jailbreakDetection', label: 'Jailbreak Detection', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'promptInjectionCheck', label: 'Prompt Injection Check', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'piiMasking', label: 'PII Masking', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'sensitiveDataTypes', label: 'Sensitive Data Types', type: 'text', placeholder: 'email, phone, ssn, api_keys (comma-separated)' },
      { name: 'offScopeTopics', label: 'Off-Scope Topics (JSON)', type: 'textarea', placeholder: '["politics", "medical_advice", "financial_advice"]', rows: 3 },
      { name: 'blockOnDetection', label: 'Block on Detection', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  // Layer 2: Context Verification
  context_verification: {
    fields: [
      { name: 'retrievedData', label: 'Retrieved Context', type: 'textarea', placeholder: 'Data retrieved from RAG/search...', rows: 4 },
      { name: 'sanitization', label: 'Data Sanitization', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'permissionCheck', label: 'Permission Check', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'accessControl', label: 'Access Control Policy', type: 'select', options: ['least_privilege', 'role_based', 'attribute_based'], default: 'least_privilege' },
      { name: 'userPermissions', label: 'User Permissions (JSON)', type: 'textarea', placeholder: '{"read": ["public"], "write": ["admin"]}', rows: 3 },
      { name: 'corruptionDetection', label: 'Corruption Detection', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'verificationThreshold', label: 'Verification Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.9 }
    ]
  },

  // Layer 3: Response Generation (Monitoring)
  response_generation_guard: {
    fields: [
      { name: 'preVerifiedContext', label: 'Pre-Verified Context', type: 'textarea', placeholder: 'Context that passed verification...', rows: 4 },
      { name: 'modelMonitoring', label: 'Model Monitoring', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'contextIsolation', label: 'Context Isolation', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'preventCorruptedData', label: 'Prevent Corrupted Data', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'generationTimeout', label: 'Generation Timeout (seconds)', type: 'number', default: 30 }
    ]
  },

  // Layer 4: Output Validation
  output_validation: {
    fields: [
      { name: 'llmResponse', label: 'LLM Response to Validate', type: 'textarea', placeholder: 'Model output to check...', rows: 4 },
      { name: 'groundednessCheck', label: 'Groundedness Check', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'sourceContext', label: 'Source Context for Grounding', type: 'textarea', placeholder: 'Context used for generation...', rows: 3 },
      { name: 'formatValidation', label: 'Format Validation', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'expectedFormat', label: 'Expected Format', type: 'select', options: ['json', 'text', 'markdown', 'structured'], default: 'text' },
      { name: 'safetyCheck', label: 'Safety Check', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'maxRetries', label: 'Max Retry Attempts', type: 'number', default: 2, min: 0, max: 5 },
      { name: 'fallbackResponse', label: 'Fallback Safe Response', type: 'textarea', placeholder: 'Safe default response on validation failure...', rows: 2 },
      { name: 'hallucinationThreshold', label: 'Hallucination Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.15 }
    ]
  },

  // Layer 5: Operational Controls
  operational_controls: {
    fields: [
      { name: 'rateLimitEnabled', label: 'Rate Limiting', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'rateLimitPerUser', label: 'Rate Limit per User (req/min)', type: 'number', default: 60 },
      { name: 'rateLimitGlobal', label: 'Global Rate Limit (req/min)', type: 'number', default: 1000 },
      { name: 'auditLogging', label: 'Full Audit Logging', type: 'select', options: ['false', 'true'], default: 'true' },
      { name: 'logLevel', label: 'Log Detail Level', type: 'select', options: ['minimal', 'standard', 'detailed', 'full'], default: 'detailed' },
      { name: 'humanInLoopQueue', label: 'Human-in-Loop Queue', type: 'select', options: ['false', 'true'], default: 'false' },
      { name: 'highRiskActions', label: 'High-Risk Actions (JSON)', type: 'textarea', placeholder: '["payment", "deletion", "data_export", "user_modification"]', rows: 3 },
      { name: 'requireApprovalFor', label: 'Require Approval For', type: 'select', options: ['none', 'high_risk', 'irreversible', 'all'], default: 'high_risk' },
      { name: 'authorizationMode', label: 'Authorization Mode', type: 'select', options: ['deterministic', 'risk_based', 'always_approve'], default: 'deterministic' },
      { name: 'complianceMode', label: 'Compliance Mode', type: 'select', options: ['standard', 'hipaa', 'gdpr', 'sox', 'custom'], default: 'standard' }
    ]
  },

  // Legacy guardrails (keep for compatibility)
  pii_detection: {
    fields: [
      { name: 'text', label: 'Text to Scan', type: 'textarea', placeholder: 'Text that might contain PII...', rows: 4 },
      { name: 'action', label: 'Action', type: 'select', options: ['detect', 'redact', 'anonymize'], default: 'detect' },
      { name: 'piiTypes', label: 'PII Types', type: 'text', placeholder: 'email, phone, ssn, credit_card (comma-separated)' }
    ]
  },

  prompt_injection: {
    fields: [
      { name: 'userInput', label: 'User Input to Check', type: 'textarea', placeholder: 'User-provided text to check for injection attacks...', rows: 4 },
      { name: 'threshold', label: 'Detection Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.7 },
      { name: 'action', label: 'Action on Detection', type: 'select', options: ['block', 'warn', 'log'], default: 'block' }
    ]
  },

  content_filter: {
    fields: [
      { name: 'text', label: 'Text to Filter', type: 'textarea', placeholder: 'Text to check for toxic content...', rows: 4 },
      { name: 'categories', label: 'Filter Categories', type: 'text', placeholder: 'toxic, profane, offensive (comma-separated)' },
      { name: 'threshold', label: 'Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.7 },
      { name: 'action', label: 'Action', type: 'select', options: ['block', 'warn', 'sanitize'], default: 'block' }
    ]
  },

  hallucination_check: {
    fields: [
      { name: 'llmOutput', label: 'LLM Output to Check', type: 'textarea', placeholder: 'LLM-generated text...', rows: 4 },
      { name: 'sourceContext', label: 'Source Context/Facts', type: 'textarea', placeholder: 'Ground truth context...', rows: 4 },
      { name: 'threshold', label: 'Confidence Threshold', type: 'number', min: 0, max: 1, step: 0.05, default: 0.8 }
    ]
  },

  // ===== HUMAN-IN-THE-LOOP =====
  approval: {
    fields: [
      { name: 'message', label: 'Approval Request Message', type: 'textarea', placeholder: 'Please review and approve...', rows: 4 },
      { name: 'approvers', label: 'Approver Emails', type: 'text', placeholder: 'admin@example.com (comma-separated)' },
      { name: 'timeout', label: 'Timeout (hours)', type: 'number', default: 24 }
    ]
  },

  manual_input: {
    fields: [
      { name: 'prompt', label: 'Input Prompt', type: 'text', placeholder: 'Please provide additional information' },
      { name: 'inputType', label: 'Input Type', type: 'select', options: ['text', 'number', 'textarea', 'select'], default: 'text' },
      { name: 'required', label: 'Required', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  review: {
    fields: [
      { name: 'reviewPrompt', label: 'Review Prompt', type: 'textarea', placeholder: 'Please review the following...', rows: 4 },
      { name: 'reviewers', label: 'Reviewer Emails', type: 'text', placeholder: 'reviewer@example.com (comma-separated)' },
      { name: 'requiresApproval', label: 'Requires Approval', type: 'select', options: ['false', 'true'], default: 'true' }
    ]
  },

  escalation: {
    fields: [
      { name: 'reason', label: 'Escalation Reason', type: 'textarea', placeholder: 'Reason for escalation...', rows: 3 },
      { name: 'escalateTo', label: 'Escalate To', type: 'text', placeholder: 'supervisor@example.com' },
      { name: 'priority', label: 'Priority', type: 'select', options: ['low', 'medium', 'high', 'urgent'], default: 'medium' }
    ]
  },

  assignment: {
    fields: [
      { name: 'taskDescription', label: 'Task Description', type: 'textarea', placeholder: 'Task to assign...', rows: 4 },
      { name: 'assignTo', label: 'Assign To', type: 'text', placeholder: 'user@example.com' },
      { name: 'dueDate', label: 'Due Date', type: 'text', placeholder: '2024-12-31' }
    ]
  },

  notification: {
    fields: [
      { name: 'message', label: 'Notification Message', type: 'textarea', placeholder: 'Notification text...', rows: 4 },
      { name: 'recipients', label: 'Recipients', type: 'text', placeholder: 'user@example.com (comma-separated)' },
      { name: 'channel', label: 'Channel', type: 'select', options: ['email', 'slack', 'sms', 'webhook'], default: 'email' }
    ]
  },

  feedback: {
    fields: [
      { name: 'feedbackPrompt', label: 'Feedback Prompt', type: 'textarea', placeholder: 'Please provide your feedback...', rows: 4 },
      { name: 'feedbackType', label: 'Feedback Type', type: 'select', options: ['rating', 'text', 'both'], default: 'both' },
      { name: 'ratingScale', label: 'Rating Scale', type: 'number', placeholder: '5', default: 5 }
    ]
  },

  // ===== MEMORY NODES =====
  vector_store: {
    fields: [
      { name: 'collection', label: 'Collection Name', type: 'text', placeholder: 'my_collection', default: 'default' },
      { name: 'text', label: 'Text to Store', type: 'textarea', placeholder: 'Text will be embedded and stored', rows: 4 },
      { name: 'metadata', label: 'Metadata (JSON)', type: 'textarea', placeholder: '{"source": "document.pdf", "page": 1}', rows: 3 }
    ]
  },

  vector_search: {
    fields: [
      { name: 'collection', label: 'Collection Name', type: 'text', placeholder: 'my_collection', default: 'default' },
      { name: 'query', label: 'Search Query', type: 'text', placeholder: 'What is AI?' },
      { name: 'nResults', label: 'Number of Results', type: 'number', default: 5, min: 1, max: 20 }
    ]
  },

  cache_set: {
    fields: [
      { name: 'key', label: 'Cache Key', type: 'text', placeholder: 'api_response_123' },
      { name: 'value', label: 'Value (JSON)', type: 'textarea', placeholder: '{"result": "data"}', rows: 4 },
      { name: 'ttl', label: 'TTL (seconds)', type: 'number', placeholder: '3600 (1 hour)' }
    ]
  },

  cache_get: {
    fields: [
      { name: 'key', label: 'Cache Key', type: 'text', placeholder: 'api_response_123' }
    ]
  },

  context_append: {
    fields: [
      { name: 'contextId', label: 'Context ID', type: 'text', placeholder: 'conversation_1', default: 'default' },
      { name: 'role', label: 'Role', type: 'select', options: ['user', 'assistant', 'system'], default: 'user' },
      { name: 'content', label: 'Message Content', type: 'textarea', placeholder: 'Hello, how can I help?', rows: 4 }
    ]
  },

  context_get: {
    fields: [
      { name: 'contextId', label: 'Context ID', type: 'text', placeholder: 'conversation_1', default: 'default' },
      { name: 'lastN', label: 'Last N Messages', type: 'number', placeholder: '10 (0 = all)' }
    ]
  },

  // ===== DEFAULT FALLBACKS BY CATEGORY =====
  _categoryDefaults: {
    'Data Loaders': [
      { name: 'connectionString', label: 'Connection String', type: 'text', placeholder: 'Connection details' },
      { name: 'query', label: 'Query/Filter', type: 'textarea', rows: 4 }
    ],
    'LLM Providers': [
      { name: 'model', label: 'Model Name', type: 'text', placeholder: 'Model identifier' },
      { name: 'apiKey', label: 'API Key', type: 'password', placeholder: '••••••••' },
      { name: 'systemPrompt', label: 'System Prompt', type: 'textarea', rows: 4 },
      { name: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1, default: 0.7 }
    ],
    'File Parsers': [
      { name: 'inputFormat', label: 'Input Format', type: 'select', options: ['auto', 'pdf', 'docx', 'txt', 'json', 'xml', 'csv'], default: 'auto' },
      { name: 'outputFormat', label: 'Output Format', type: 'select', options: ['text', 'json', 'markdown'], default: 'text' },
      { name: 'encoding', label: 'Encoding', type: 'select', options: ['utf-8', 'ascii', 'latin-1'], default: 'utf-8' }
    ],
    'Integration & Connectivity': [
      { name: 'endpoint', label: 'Endpoint/URL', type: 'url', placeholder: 'https://api.example.com' },
      { name: 'method', label: 'HTTP Method', type: 'select', options: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], default: 'POST' },
      { name: 'headers', label: 'Headers (JSON)', type: 'textarea', placeholder: '{"Authorization": "Bearer token"}', rows: 4 }
    ],
    'Analysis': [
      { name: 'analysisType', label: 'Analysis Type', type: 'text', placeholder: 'Type of analysis' },
      { name: 'threshold', label: 'Threshold', type: 'number', min: 0, max: 1, step: 0.1, default: 0.7 }
    ],
    'Data Transformation': [
      { name: 'transformType', label: 'Transform Type', type: 'text', placeholder: 'Transformation to apply' },
      { name: 'expression', label: 'Expression/Script', type: 'textarea', rows: 6, placeholder: 'Transformation logic' }
    ]
  },

  // ===== RETRY CONFIGURATION (can be added to any node) =====
  _retryConfig: [
    { name: 'enableRetry', label: 'Enable Retry', type: 'select', options: ['false', 'true'], default: 'false' },
    { name: 'maxRetries', label: 'Max Retries', type: 'number', default: 3, min: 0, max: 10 },
    { name: 'retryStrategy', label: 'Retry Strategy', type: 'select',
      options: ['exponential', 'linear', 'immediate', 'fibonacci'], default: 'exponential' },
    { name: 'initialDelay', label: 'Initial Delay (seconds)', type: 'number', default: 1, min: 0, max: 60, step: 0.5 },
    { name: 'maxDelay', label: 'Max Delay (seconds)', type: 'number', default: 60, min: 1, max: 300 },
    { name: 'backoffMultiplier', label: 'Backoff Multiplier', type: 'number', default: 2, min: 1, max: 10, step: 0.1 }
  ]
};

// Helper function to get config schema for a node
export function getNodeConfigSchema(nodeType, category) {
  // Try to find exact match first
  if (NODE_CONFIG_SCHEMAS[nodeType]) {
    return NODE_CONFIG_SCHEMAS[nodeType].fields;
  }

  // Fall back to category defaults
  if (NODE_CONFIG_SCHEMAS._categoryDefaults[category]) {
    return NODE_CONFIG_SCHEMAS._categoryDefaults[category];
  }

  // Ultimate fallback - generic config
  return [
    { name: 'config', label: 'Configuration (JSON)', type: 'textarea', placeholder: '{}', rows: 6 }
  ];
}

// Helper function to get retry configuration fields
export function getRetryConfigFields() {
  return NODE_CONFIG_SCHEMAS._retryConfig;
}

// Helper function to check if a node should support retry
export function shouldSupportRetry(category) {
  // These categories commonly benefit from retry logic
  const retryableCategories = [
    'Data Loaders',
    'API Integration',
    'Integration & Connectivity',
    'LLM Providers',
    'Output'
  ];
  return retryableCategories.includes(category);
}
