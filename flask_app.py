"""
Flask REST API Backend for Agentic Workflow Builder
Production-ready API matching AI Planet architecture
"""

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
import sys
from pathlib import Path
import json
import asyncio
import traceback
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from core.workflow_engine import WorkflowEngine, WorkflowDefinition, WorkflowNode, WorkflowEdge
from core.ollama_service import OllamaService, verify_ollama_health
from core.agent_loader import create_agent_registry
from core.workflow_storage import WorkflowStorage, HITLTaskManager
from core.workflow_scheduler import WorkflowScheduler
from backend.workflow_executor import execute_workflow_sync
from services.memory_service import memory_service
from services.trace_service import trace_service
from services.step_executor import step_executor
from services.workflow_storage import workflow_storage as persistent_storage
from services.email_service import EmailService
from services.analytics_service import analytics_service
from services.logging_service import logging_service, get_logger, get_context_logger
from backend.errors import (
    WorkflowError, WorkflowNotFoundError, WorkflowValidationError,
    NodeError, NodeNotFoundError, TemplateNotFoundError,
    error_to_response
)

app = Flask(__name__, static_folder='react-frontend/build', static_url_path='')
CORS(app)  # Enable CORS for React frontend

# Initialize logging service
logger = get_logger(__name__)
logger.info("Initializing Flask application")

# Initialize services (legacy Streamlit storage)
workflow_storage = WorkflowStorage(db_path="backend/database/workflows_legacy.db")
hitl_manager = HITLTaskManager()
scheduler = WorkflowScheduler(workflow_storage)

# Global instances (will be initialized on first use)
ollama_service = None
workflow_engine = None


# ============================================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================================

@app.before_request
def before_request():
    """Log all incoming requests and track request timing"""
    g.start_time = time.time()
    g.request_id = f"req_{int(time.time() * 1000)}"

    logger.info(
        f"Incoming request: {request.method} {request.path}",
        extra={
            'request_id': g.request_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr
        }
    )

@app.after_request
def after_request(response):
    """Log request completion with timing"""
    if hasattr(g, 'start_time'):
        duration_ms = int((time.time() - g.start_time) * 1000)

        logger.info(
            f"Request completed: {request.method} {request.path} - {response.status_code}",
            extra={
                'request_id': getattr(g, 'request_id', 'unknown'),
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms
            }
        )

    return response


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(WorkflowError)
def handle_workflow_error(error):
    """Handle custom workflow errors"""
    logger.error(
        f"Workflow error: {error.message}",
        extra={
            'error_code': error.error_code,
            'context': error.context,
            'request_id': getattr(g, 'request_id', 'unknown')
        }
    )
    return jsonify(error.to_dict()), error.status_code

@app.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    logger.warning(
        f"Resource not found: {request.path}",
        extra={
            'request_id': getattr(g, 'request_id', 'unknown'),
            'path': request.path
        }
    )
    return jsonify({
        'error': True,
        'error_code': 'NOT_FOUND',
        'message': f'Resource not found: {request.path}',
        'status_code': 404
    }), 404

@app.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 errors"""
    logger.error(
        f"Internal server error: {str(error)}",
        extra={
            'request_id': getattr(g, 'request_id', 'unknown')
        },
        exc_info=True
    )
    return jsonify({
        'error': True,
        'error_code': 'INTERNAL_ERROR',
        'message': 'An internal server error occurred',
        'status_code': 500
    }), 500

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle any unexpected errors"""
    logger.error(
        f"Unexpected error: {str(error)}",
        extra={
            'request_id': getattr(g, 'request_id', 'unknown'),
            'error_type': type(error).__name__
        },
        exc_info=True
    )

    # Check if it's a custom workflow error
    if isinstance(error, WorkflowError):
        return jsonify(error.to_dict()), error.status_code

    # Generic error response
    return jsonify({
        'error': True,
        'error_code': 'INTERNAL_ERROR',
        'message': str(error),
        'status_code': 500
    }), 500


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get platform configuration"""
    config_path = Path(__file__).parent / "backend" / "config.json"

    default_config = {
        "ollama": {"url": "http://localhost:11434", "default_model": "llama3.2:3b"},
        "platform": {"name": "Agentic Workflow Builder", "version": "2.0.0", "vendor": "Exalio"}
    }

    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            # Ensure required keys
            if "ollama" not in config:
                config["ollama"] = default_config["ollama"]
    else:
        config = default_config

    return jsonify(config)


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update platform configuration"""
    config_path = Path(__file__).parent / "backend" / "config.json"
    new_config = request.json

    with open(config_path, 'w') as f:
        json.dump(new_config, f, indent=2)

    return jsonify({"status": "success", "message": "Configuration updated"})


# ============================================================================
# OLLAMA ENDPOINTS
# ============================================================================

@app.route('/api/ollama/health', methods=['GET'])
def check_ollama_health():
    """Check Ollama health status"""
    url = request.args.get('url', 'http://localhost:11434')
    health = verify_ollama_health(url)
    return jsonify(health)


@app.route('/api/ollama/models', methods=['GET'])
def get_ollama_models():
    """Get list of installed Ollama models"""
    url = request.args.get('url', 'http://localhost:11434')

    try:
        import requests
        response = requests.get(f"{url}/api/tags", timeout=3)
        if response.status_code == 200:
            models_data = response.json()
            models = [model['name'] for model in models_data.get('models', [])]
            return jsonify({"models": models, "count": len(models)})
        else:
            return jsonify({"error": "Failed to fetch models", "models": []}), 500
    except Exception as e:
        return jsonify({"error": str(e), "models": []}), 500


@app.route('/api/ollama/connect', methods=['POST'])
def connect_to_ollama():
    """Initialize Ollama connection"""
    global ollama_service, workflow_engine

    data = request.json
    ollama_url = data.get('url', 'http://localhost:11434')
    default_model = data.get('model', 'llama3.2:3b')

    try:
        # Check health first
        health = verify_ollama_health(ollama_url)
        if not health['connected']:
            return jsonify({"error": "Cannot connect to Ollama", "details": health}), 500

        # Initialize Ollama service
        ollama_service = OllamaService(ollama_url, default_model)
        ollama_service.start_monitoring(check_interval=30)

        # Try to create agent registry and workflow engine (optional)
        agent_count = 0
        try:
            agent_registry = create_agent_registry(ollama_service=ollama_service)
            workflow_engine = WorkflowEngine(agent_registry)
            agent_count = len(agent_registry.list_agents())
        except Exception as agent_error:
            # Log the error but don't fail the connection
            print(f"Warning: Failed to load all agents: {agent_error}")
            agent_count = 0

        return jsonify({
            "status": "success",
            "message": f"Connected to Ollama at {ollama_url}",
            "agent_count": agent_count,
            "health": health
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# NGROK DETECTION
# ============================================================================

@app.route('/api/ngrok/detect', methods=['GET'])
def detect_ngrok():
    """Detect ngrok tunnel"""
    try:
        import requests
        ngrok_api = requests.get("http://localhost:4040/api/tunnels", timeout=2).json()
        tunnels = ngrok_api.get('tunnels', [])
        if tunnels:
            return jsonify({
                "detected": True,
                "url": tunnels[0]['public_url'],
                "tunnels": tunnels
            })
        else:
            return jsonify({"detected": False})
    except:
        return jsonify({"detected": False})


# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@app.route('/api/legacy-workflows', methods=['GET'])
def list_workflows():
    """List all workflows (legacy endpoint)"""
    user_id = request.args.get('user_id', type=int)
    workflows = workflow_storage.list_workflows(user_id=user_id)
    return jsonify({"workflows": workflows, "count": len(workflows)})


@app.route('/api/workflows/execute', methods=['POST'])
def create_workflow():
    """Create a new workflow (legacy endpoint for execution)"""
    data = request.json
    user_id = data.get('user_id')

    # Create workflow definition
    nodes = [WorkflowNode(**node) for node in data.get('nodes', [])]
    edges = [WorkflowEdge(**edge) for edge in data.get('edges', [])]

    workflow = WorkflowDefinition(
        name=data['name'],
        description=data.get('description', ''),
        nodes=nodes,
        edges=edges,
        version=data.get('version', '1.0.0')
    )

    workflow_id = workflow_storage.save_workflow(workflow, user_id=user_id)

    return jsonify({
        "status": "success",
        "workflow_id": workflow_id,
        "message": "Workflow created successfully"
    }), 201


@app.route('/api/legacy-workflows/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id: str):
    """Get workflow by ID (legacy endpoint)"""
    workflow = workflow_storage.load_workflow(workflow_id)
    if workflow:
        return jsonify(workflow.dict())
    else:
        return jsonify({"error": "Workflow not found"}), 404


@app.route('/api/legacy-workflows/<workflow_id>', methods=['PUT'])
def update_workflow(workflow_id: str):
    """Update workflow (legacy endpoint)"""
    data = request.json

    nodes = [WorkflowNode(**node) for node in data.get('nodes', [])]
    edges = [WorkflowEdge(**edge) for edge in data.get('edges', [])]

    workflow = WorkflowDefinition(
        name=data['name'],
        description=data.get('description', ''),
        nodes=nodes,
        edges=edges,
        version=data.get('version', '1.0.0')
    )

    updated_id = workflow_storage.update_workflow(workflow_id, workflow)

    return jsonify({
        "status": "success",
        "workflow_id": updated_id,
        "message": "Workflow updated successfully"
    })


@app.route('/api/legacy-workflows/<workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id: str):
    """Delete workflow (legacy endpoint)"""
    workflow_storage.delete_workflow(workflow_id)
    return jsonify({"status": "success", "message": "Workflow deleted"})


@app.route('/api/workflows/<workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id: str):
    """Execute a workflow"""
    global workflow_engine

    if not workflow_engine:
        return jsonify({"error": "Ollama not connected. Connect first."}), 400

    data = request.json
    input_data = data.get('input_data', {})

    try:
        workflow = workflow_storage.load_workflow(workflow_id)
        if not workflow:
            return jsonify({"error": "Workflow not found"}), 404

        # Execute workflow
        import asyncio
        result = asyncio.run(workflow_engine.execute(workflow, input_data))

        # Save execution record
        execution_id = workflow_storage.save_execution(
            workflow_id=workflow_id,
            input_data=input_data,
            output_data=result,
            status='completed' if result.get('success') else 'failed'
        )

        return jsonify({
            "status": "success",
            "execution_id": execution_id,
            "result": result
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "failed"}), 500


@app.route('/api/workflows/<workflow_id>/export', methods=['GET'])
def export_workflow(workflow_id: str):
    """Export workflow as JSON"""
    workflow = workflow_storage.load_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "Workflow not found"}), 404

    return jsonify(workflow.dict())


@app.route('/api/workflows/execute-visual', methods=['POST'])
def execute_visual_workflow():
    """
    Execute a workflow directly from the visual builder
    Does NOT require saving the workflow first
    """
    global ollama_service

    data = request.json
    workflow_definition = data.get('workflow')  # {nodes: [], edges: []}
    initial_input = data.get('input', {})

    if not workflow_definition:
        return jsonify({"error": "No workflow definition provided"}), 400

    # Get Ollama URL from connected service or use default
    ollama_url = "http://localhost:11434"
    if ollama_service:
        ollama_url = ollama_service.ollama_url

    try:
        # Execute the workflow using our new executor
        result = execute_workflow_sync(
            workflow_definition=workflow_definition,
            initial_input=initial_input,
            ollama_url=ollama_url
        )

        return jsonify(result)

    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============================================================================
# MEMORY API ENDPOINTS
# ============================================================================

# Helper to run async functions in sync Flask routes
def run_async(coro):
    """Run async coroutine in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/api/memory/vector/store', methods=['POST'])
def memory_vector_store():
    """Store text in vector database"""
    data = request.json
    collection = data.get('collection', 'default')
    text = data.get('text')
    metadata = data.get('metadata', {})

    if not text:
        return jsonify({"success": False, "error": "Text is required"}), 400

    result = run_async(memory_service.store_vector(collection, text, metadata))
    return jsonify(result)

@app.route('/api/memory/vector/search', methods=['POST'])
def memory_vector_search():
    """Search vector database"""
    data = request.json
    collection = data.get('collection', 'default')
    query = data.get('query')
    n_results = data.get('n_results', 5)

    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400

    result = run_async(memory_service.search_vector(collection, query, n_results))
    return jsonify(result)

@app.route('/api/memory/cache/set', methods=['POST'])
def memory_cache_set():
    """Store in cache"""
    data = request.json
    key = data.get('key')
    value = data.get('value')
    ttl = data.get('ttl')

    if not key or value is None:
        return jsonify({"success": False, "error": "Key and value are required"}), 400

    result = run_async(memory_service.cache_set(key, value, ttl))
    return jsonify(result)

@app.route('/api/memory/cache/get/<key>', methods=['GET'])
def memory_cache_get(key):
    """Retrieve from cache"""
    result = run_async(memory_service.cache_get(key))
    return jsonify(result)

@app.route('/api/memory/context/append', methods=['POST'])
def memory_context_append():
    """Append to conversation context"""
    data = request.json
    context_id = data.get('context_id', 'default')
    message = data.get('message')

    if not message:
        return jsonify({"success": False, "error": "Message is required"}), 400

    result = run_async(memory_service.context_append(context_id, message))
    return jsonify(result)

@app.route('/api/memory/context/get/<context_id>', methods=['GET'])
def memory_context_get(context_id):
    """Get conversation context"""
    last_n = request.args.get('last_n', type=int)
    result = run_async(memory_service.context_get(context_id, last_n))
    return jsonify(result)

@app.route('/api/memory/stats', methods=['GET'])
def memory_stats():
    """Get memory service statistics"""
    stats = run_async(memory_service.get_stats())
    return jsonify(stats)

# ============================================================================
# TRACE API ENDPOINTS
# ============================================================================

@app.route('/api/trace/<trace_id>', methods=['GET'])
def get_trace(trace_id):
    """Get single trace"""
    trace = trace_service.get_trace(trace_id)
    if not trace:
        return jsonify({"error": "Trace not found"}), 404
    return jsonify(trace)

@app.route('/api/trace/workflow/<workflow_id>', methods=['GET'])
def get_workflow_traces(workflow_id):
    """Get recent traces for a workflow"""
    limit = request.args.get('limit', 10, type=int)
    traces = trace_service.get_workflow_traces(workflow_id, limit)
    return jsonify({"traces": traces})

@app.route('/api/trace/metrics/<workflow_id>', methods=['GET'])
def get_trace_metrics(workflow_id):
    """Get aggregated metrics for a workflow"""
    metrics = trace_service.get_metrics(workflow_id)
    return jsonify(metrics)

@app.route('/api/trace/performance/<workflow_id>', methods=['GET'])
def get_node_performance(workflow_id):
    """Get node performance stats"""
    performance = trace_service.get_node_performance(workflow_id)
    return jsonify({"performance": performance})

@app.route('/api/trace/costs/<workflow_id>', methods=['GET'])
def get_cost_breakdown(workflow_id):
    """Get cost breakdown"""
    costs = trace_service.get_cost_breakdown(workflow_id)
    return jsonify(costs)

# ============================================================================
# INTERACTIVE PLAYGROUND ENDPOINTS
# ============================================================================

@app.route('/api/playground/session', methods=['POST'])
def create_playground_session():
    """Create new execution session"""
    try:
        data = request.json
        workflow = data.get('workflow')
        inputs = data.get('inputs', {})

        if not workflow:
            return jsonify({"error": "Workflow is required"}), 400

        session_id = step_executor.create_session(workflow, inputs)

        return jsonify({
            "session_id": session_id,
            "status": "ready",
            "total_nodes": len(workflow.get('nodes', []))
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/playground/session/<session_id>/step', methods=['POST'])
def execute_playground_step(session_id):
    """Execute next step in workflow"""
    try:
        result = step_executor.execute_next_step(session_id)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/playground/session/<session_id>/run', methods=['POST'])
def execute_playground_all(session_id):
    """Execute all remaining steps"""
    try:
        result = step_executor.execute_all_steps(session_id)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/playground/session/<session_id>/pause', methods=['POST'])
def pause_playground_session(session_id):
    """Pause execution"""
    try:
        result = step_executor.pause_session(session_id)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/playground/session/<session_id>/resume', methods=['POST'])
def resume_playground_session(session_id):
    """Resume execution"""
    try:
        result = step_executor.resume_session(session_id)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/playground/session/<session_id>', methods=['GET'])
def get_playground_session(session_id):
    """Get session state"""
    try:
        state = step_executor.get_session_state(session_id)
        return jsonify(state)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/playground/session/<session_id>', methods=['DELETE'])
def delete_playground_session(session_id):
    """Delete session"""
    try:
        result = step_executor.delete_session(session_id)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/playground/sessions', methods=['GET'])
def list_playground_sessions():
    """List all active sessions"""
    try:
        sessions = step_executor.list_sessions()
        return jsonify({"sessions": sessions, "count": len(sessions)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/playground/stats', methods=['GET'])
def get_playground_stats():
    """Get executor statistics"""
    try:
        stats = step_executor.get_stats()
        return jsonify(stats)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# HITL (Human-in-the-Loop) ENDPOINTS
# ============================================================================

@app.route('/api/hitl/tasks', methods=['GET'])
def get_hitl_tasks():
    """Get pending HITL tasks"""
    status = request.args.get('status', 'pending')
    assigned_to = request.args.get('assigned_to', type=int)

    if status == 'pending':
        tasks = hitl_manager.get_pending_tasks(assigned_to=assigned_to)
    else:
        # Get all tasks with specific status
        tasks = hitl_manager.get_pending_tasks(assigned_to=assigned_to)
        tasks = [t for t in tasks if t.get('status') == status]

    return jsonify({"tasks": tasks, "count": len(tasks)})


@app.route('/api/hitl/tasks/<task_id>/respond', methods=['POST'])
def respond_to_hitl_task(task_id: str):
    """Respond to a HITL task"""
    data = request.json
    status = data.get('status', 'approved')
    response = data.get('response', {})

    hitl_manager.respond_to_task(task_id, status, response)

    return jsonify({"status": "success", "message": "Task response recorded"})


# ============================================================================
# SCHEDULER ENDPOINTS
# ============================================================================

@app.route('/api/scheduler/jobs', methods=['GET'])
def list_scheduled_jobs():
    """List all scheduled jobs"""
    jobs = scheduler.list_jobs()
    return jsonify({"jobs": jobs, "count": len(jobs)})


@app.route('/api/scheduler/jobs', methods=['POST'])
def schedule_workflow():
    """Schedule a workflow"""
    data = request.json
    workflow_id = data['workflow_id']
    schedule_type = data.get('schedule_type', 'cron')

    if schedule_type == 'cron':
        result = scheduler.schedule_cron(
            workflow_id=workflow_id,
            cron_expression=data['cron_expression'],
            input_data=data.get('input_data', {})
        )
    elif schedule_type == 'interval':
        result = scheduler.schedule_interval(
            workflow_id=workflow_id,
            seconds=data.get('seconds'),
            minutes=data.get('minutes'),
            hours=data.get('hours'),
            input_data=data.get('input_data', {})
        )
    else:
        return jsonify({"error": "Invalid schedule type"}), 400

    return jsonify(result), 201


@app.route('/api/scheduler/jobs/<job_id>', methods=['DELETE'])
def delete_scheduled_job(job_id: str):
    """Delete a scheduled job"""
    scheduler.remove_job(job_id)
    return jsonify({"status": "success", "message": "Job deleted"})


# ============================================================================
# TEMPLATE API ENDPOINTS
# ============================================================================

@app.route('/api/templates/list', methods=['GET'])
def list_templates():
    """List all available workflow templates"""
    try:
        templates_dir = Path(__file__).parent / "templates"

        if not templates_dir.exists():
            return jsonify({"templates": [], "count": 0})

        templates = []
        for template_file in templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)

                    # Extract metadata for list view
                    templates.append({
                        "id": template_data.get("id"),
                        "name": template_data.get("name"),
                        "description": template_data.get("description"),
                        "category": template_data.get("category"),
                        "difficulty": template_data.get("difficulty"),
                        "tags": template_data.get("tags", []),
                        "author": template_data.get("author"),
                        "version": template_data.get("version"),
                        "filename": template_file.name,
                        "nodeCount": len(template_data.get("nodes", [])),
                        "requirements": template_data.get("metadata", {}).get("requirements", [])
                    })
            except Exception as e:
                print(f"⚠️ Error reading template {template_file.name}: {e}")
                continue

        # Sort by category and name
        templates.sort(key=lambda x: (x.get("category", ""), x.get("name", "")))

        return jsonify({
            "templates": templates,
            "count": len(templates)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id: str):
    """Get a specific template by ID"""
    try:
        templates_dir = Path(__file__).parent / "templates"

        # Search for template by ID
        for template_file in templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)

                    if template_data.get("id") == template_id:
                        return jsonify(template_data)
            except Exception as e:
                print(f"⚠️ Error reading template {template_file.name}: {e}")
                continue

        return jsonify({"error": "Template not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/templates/import', methods=['POST'])
def import_template():
    """Import a template as a new workflow"""
    try:
        data = request.json
        template_id = data.get('template_id')

        if not template_id:
            return jsonify({"error": "template_id is required"}), 400

        # Get the template
        templates_dir = Path(__file__).parent / "templates"
        template_data = None

        for template_file in templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    temp_data = json.load(f)
                    if temp_data.get("id") == template_id:
                        template_data = temp_data
                        break
            except Exception as e:
                continue

        if not template_data:
            return jsonify({"error": "Template not found"}), 404

        # Return template data for frontend to use
        # Frontend will handle the actual workflow creation
        import uuid
        new_workflow_id = str(uuid.uuid4())

        # Return template with new ID for frontend
        imported_template = {
            **template_data,
            "id": new_workflow_id,
            "name": f"{template_data.get('name')} (from template)",
            "metadata": {
                **template_data.get("metadata", {}),
                "template_id": template_id,
                "template_name": template_data.get("name"),
                "imported_at": json.dumps(datetime.now().isoformat())
            }
        }

        return jsonify({
            "status": "success",
            "message": f"Template '{template_data.get('name')}' loaded successfully",
            "template": imported_template
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# WORKFLOW PERSISTENCE ENDPOINTS
# ============================================================================

@app.route('/api/workflows', methods=['POST'])
def save_workflow_to_db():
    """Save or update a workflow in the database"""
    try:
        data = request.json
        workflow_data = {
            'nodes': data.get('nodes', []),
            'edges': data.get('edges', [])
        }
        metadata = data.get('metadata', {})
        workflow_id = persistent_storage.save_workflow(workflow_data, metadata)
        return jsonify({
            'status': 'success',
            'workflow_id': workflow_id,
            'message': 'Workflow saved successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflows', methods=['GET'])
def list_saved_workflows():
    """List all saved workflows"""
    try:
        category = request.args.get('category')
        is_template = request.args.get('is_template')
        if is_template is not None:
            is_template = is_template.lower() == 'true'

        workflows = persistent_storage.list_workflows(category=category, is_template=is_template)
        return jsonify({
            'workflows': workflows,
            'count': len(workflows)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflows/<workflow_id>', methods=['GET'])
def get_saved_workflow(workflow_id: str):
    """Get a specific workflow by ID"""
    try:
        version = request.args.get('version')
        if version:
            version = int(version)

        workflow = persistent_storage.get_workflow(workflow_id, version=version)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404

        return jsonify(workflow)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflows/<workflow_id>', methods=['DELETE'])
def delete_saved_workflow(workflow_id: str):
    """Delete a workflow"""
    try:
        deleted = persistent_storage.delete_workflow(workflow_id)
        if deleted:
            return jsonify({
                'status': 'success',
                'workflow_id': workflow_id,
                'message': 'Workflow deleted successfully'
            })
        return jsonify({'error': 'Workflow not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflows/<workflow_id>/versions', methods=['GET'])
def get_saved_workflow_versions(workflow_id: str):
    """Get version history for a workflow"""
    try:
        versions = persistent_storage.get_workflow_versions(workflow_id)
        return jsonify({
            'versions': versions,
            'count': len(versions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflows/search', methods=['GET'])
def search_saved_workflows():
    """Search workflows by name or description"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400

        workflows = persistent_storage.search_workflows(query)
        return jsonify({
            'workflows': workflows,
            'count': len(workflows)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflows/<workflow_id>/executions', methods=['GET'])
def get_saved_workflow_executions(workflow_id: str):
    """Get execution history for a workflow"""
    try:
        limit = request.args.get('limit', 50, type=int)
        executions = persistent_storage.get_workflow_executions(workflow_id, limit=limit)
        return jsonify({
            'executions': executions,
            'count': len(executions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# WORKFLOW ANALYTICS ENDPOINTS
# ============================================================================

@app.route('/api/analytics/workflows/<workflow_id>', methods=['GET'])
def get_workflow_analytics_api(workflow_id: str):
    """Get comprehensive analytics for a specific workflow"""
    try:
        analytics = analytics_service.get_workflow_analytics(workflow_id)
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/executions/<execution_id>', methods=['GET'])
def get_execution_details_api(execution_id: str):
    """Get detailed information about a specific execution including node-level data"""
    try:
        execution_details = analytics_service.get_execution_details(execution_id)
        if not execution_details:
            return jsonify({'error': 'Execution not found'}), 404
        return jsonify(execution_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/global', methods=['GET'])
def get_global_analytics_api():
    """Get system-wide analytics across all workflows"""
    try:
        global_analytics = analytics_service.get_global_analytics()
        return jsonify(global_analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# WORKFLOW TEMPLATES ENDPOINTS
# ============================================================================

@app.route('/api/templates', methods=['GET'])
def get_workflow_templates():
    """Get all workflow templates or filter by category"""
    try:
        templates_path = Path('backend/templates/workflow_templates.json')

        if not templates_path.exists():
            return jsonify({'templates': [], 'count': 0})

        with open(templates_path, 'r') as f:
            templates = json.load(f)

        # Filter by category if provided
        category = request.args.get('category')
        if category:
            templates = [t for t in templates if t.get('category') == category]

        # Filter by difficulty if provided
        difficulty = request.args.get('difficulty')
        if difficulty:
            templates = [t for t in templates if t.get('difficulty') == difficulty]

        # Filter by tag if provided
        tag = request.args.get('tag')
        if tag:
            templates = [t for t in templates if tag in t.get('tags', [])]

        return jsonify({
            'templates': templates,
            'count': len(templates)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template_by_id(template_id: str):
    """Get a specific template by ID"""
    try:
        templates_path = Path('backend/templates/workflow_templates.json')

        if not templates_path.exists():
            return jsonify({'error': 'Templates not found'}), 404

        with open(templates_path, 'r') as f:
            templates = json.load(f)

        template = next((t for t in templates if t['id'] == template_id), None)

        if not template:
            return jsonify({'error': 'Template not found'}), 404

        return jsonify(template)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/templates/<template_id>/create', methods=['POST'])
def create_workflow_from_template(template_id: str):
    """Create a new workflow from a template"""
    try:
        templates_path = Path('backend/templates/workflow_templates.json')

        if not templates_path.exists():
            return jsonify({'error': 'Templates not found'}), 404

        with open(templates_path, 'r') as f:
            templates = json.load(f)

        template = next((t for t in templates if t['id'] == template_id), None)

        if not template:
            return jsonify({'error': 'Template not found'}), 404

        # Get custom name from request or use template name
        data = request.json or {}
        workflow_name = data.get('name', template['name'] + ' (Copy)')
        workflow_description = data.get('description', template['description'])

        # Create workflow from template
        workflow_data = {
            'nodes': template['nodes'],
            'edges': template['edges']
        }

        metadata = {
            'name': workflow_name,
            'description': workflow_description,
            'category': template.get('category', 'Custom'),
            'author': 'User',
            'tags': template.get('tags', []),
            'template_id': template_id,
            'created_from_template': True
        }

        # Save the new workflow
        result = persistent_storage.save_workflow(workflow_data, metadata)

        return jsonify({
            'workflow_id': result['workflow_id'],
            'version': result['version'],
            'message': 'Workflow created from template successfully',
            'workflow': {
                **workflow_data,
                'metadata': metadata
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/templates/categories', methods=['GET'])
def get_template_categories():
    """Get all unique template categories"""
    try:
        templates_path = Path('backend/templates/workflow_templates.json')

        if not templates_path.exists():
            return jsonify({'categories': []})

        with open(templates_path, 'r') as f:
            templates = json.load(f)

        categories = list(set(t.get('category', 'Uncategorized') for t in templates))
        categories.sort()

        # Get count for each category
        category_counts = {}
        for cat in categories:
            category_counts[cat] = sum(1 for t in templates if t.get('category') == cat)

        return jsonify({
            'categories': categories,
            'counts': category_counts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EMAIL INTEGRATION ENDPOINTS
# ============================================================================

@app.route('/api/email/send', methods=['POST'])
def send_email():
    """Send an email via SMTP"""
    try:
        data = request.json

        # Required fields
        from_email = data.get('from_email')
        from_password = data.get('from_password')
        to_emails = data.get('to_emails', [])
        subject = data.get('subject')
        body = data.get('body')

        if not all([from_email, from_password, to_emails, subject, body]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: from_email, from_password, to_emails, subject, body'
            }), 400

        # Optional fields
        provider = data.get('provider', 'gmail')
        smtp_host = data.get('smtp_host')
        smtp_port = data.get('smtp_port')
        use_tls = data.get('use_tls', True)
        html = data.get('html', False)
        cc_emails = data.get('cc_emails')
        bcc_emails = data.get('bcc_emails')
        attachments = data.get('attachments')

        # Initialize email service
        email_service = EmailService(
            provider=provider,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            use_tls=use_tls
        )

        # Send email
        result = email_service.send_email(
            from_email=from_email,
            from_password=from_password,
            to_emails=to_emails if isinstance(to_emails, list) else [to_emails],
            subject=subject,
            body=body,
            html=html,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            attachments=attachments
        )

        return jsonify(result), 200 if result['status'] == 'success' else 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/email/validate', methods=['POST'])
def validate_email_config():
    """Validate email configuration"""
    try:
        data = request.json

        from_email = data.get('from_email')
        from_password = data.get('from_password')
        provider = data.get('provider', 'gmail')
        smtp_host = data.get('smtp_host')
        smtp_port = data.get('smtp_port')
        use_tls = data.get('use_tls', True)

        if not all([from_email, from_password]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: from_email, from_password'
            }), 400

        # Initialize email service
        email_service = EmailService(
            provider=provider,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            use_tls=use_tls
        )

        # Validate configuration
        result = email_service.validate_config(from_email, from_password)

        return jsonify(result), 200 if result['status'] == 'success' else 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/email/templates', methods=['GET'])
def get_email_templates():
    """Get pre-defined email templates"""
    try:
        from services.template_service import TemplateService

        templates = TemplateService.create_email_templates()

        return jsonify({
            'status': 'success',
            'templates': templates,
            'count': len(templates)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ============================================================================
# FILE UPLOAD AND PARSING ENDPOINTS
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload a file and return file metadata and content
    Supports various file types: text, PDF, CSV, JSON, images, etc.
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': True,
                'message': 'No file provided in request'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'error': True,
                'message': 'No file selected'
            }), 400

        # Get file metadata
        filename = file.filename
        file_size = 0
        file_type = file.content_type or 'application/octet-stream'

        # Read file content
        file_content = file.read()
        file_size = len(file_content)

        # Determine how to process based on file type
        processed_content = None
        file_format = filename.split('.')[-1].lower() if '.' in filename else 'unknown'

        # Text files
        if file_format in ['txt', 'md', 'csv', 'log']:
            try:
                processed_content = file_content.decode('utf-8')
            except:
                processed_content = file_content.decode('latin-1')

        # JSON files
        elif file_format == 'json':
            try:
                processed_content = json.loads(file_content.decode('utf-8'))
            except Exception as e:
                processed_content = f"Error parsing JSON: {str(e)}"

        # CSV files
        elif file_format == 'csv':
            try:
                import io
                import csv
                content_str = file_content.decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(content_str))
                processed_content = list(csv_reader)
            except Exception as e:
                processed_content = f"Error parsing CSV: {str(e)}"

        # Binary files - convert to base64
        else:
            import base64
            processed_content = base64.b64encode(file_content).decode('utf-8')

        # Get last modified time (use current time)
        import time
        last_modified = int(time.time() * 1000)

        logger.info(
            f"File uploaded: {filename} ({file_size} bytes, {file_type})",
            extra={'request_id': getattr(g, 'request_id', 'unknown')}
        )

        return jsonify({
            'status': 'success',
            'file': {
                'name': filename,
                'size': file_size,
                'type': file_type,
                'format': file_format,
                'content': processed_content,
                'lastModified': last_modified,
                'uploaded_at': datetime.now().isoformat()
            }
        }), 200

    except Exception as e:
        logger.error(
            f"File upload error: {str(e)}",
            extra={'request_id': getattr(g, 'request_id', 'unknown')},
            exc_info=True
        )
        return jsonify({
            'error': True,
            'message': f'File upload failed: {str(e)}'
        }), 500


@app.route('/api/parse/file', methods=['POST'])
def parse_file():
    """
    Parse uploaded file content into structured data
    Supports: PDF, DOCX, XLSX, images (OCR), etc.
    """
    try:
        data = request.json
        file_content = data.get('content')
        file_type = data.get('type', '')
        file_format = data.get('format', '')

        if not file_content:
            return jsonify({
                'error': True,
                'message': 'No file content provided'
            }), 400

        result = {
            'status': 'success',
            'format': file_format,
            'parsed_content': None,
            'metadata': {}
        }

        # PDF parsing
        if file_format == 'pdf':
            result['parsed_content'] = "PDF parsing requires PyPDF2 or pdfplumber library"
            result['note'] = "Install with: pip install PyPDF2"

        # DOCX parsing
        elif file_format == 'docx':
            result['parsed_content'] = "DOCX parsing requires python-docx library"
            result['note'] = "Install with: pip install python-docx"

        # Excel parsing
        elif file_format in ['xlsx', 'xls']:
            result['parsed_content'] = "Excel parsing requires openpyxl or pandas library"
            result['note'] = "Install with: pip install openpyxl pandas"

        # Image OCR
        elif file_format in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            result['parsed_content'] = "Image OCR requires pytesseract or PaddleOCR library"
            result['note'] = "Install with: pip install pytesseract pillow"

        # Already parsed text/JSON
        elif file_format in ['txt', 'json', 'csv', 'md']:
            result['parsed_content'] = file_content
            result['note'] = "Already in parsed format"

        else:
            result['parsed_content'] = "Unknown file format"
            result['note'] = f"Format '{file_format}' is not supported"

        return jsonify(result), 200

    except Exception as e:
        logger.error(
            f"File parsing error: {str(e)}",
            extra={'request_id': getattr(g, 'request_id', 'unknown')},
            exc_info=True
        )
        return jsonify({
            'error': True,
            'message': f'File parsing failed: {str(e)}'
        }), 500


# ============================================================================
# SERVE REACT APP
# ============================================================================

@app.route('/')
def serve_react_app():
    """Serve React frontend"""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except:
        # React build folder doesn't exist
        return jsonify({
            "status": "ok",
            "message": "Agentic Workflow Builder API",
            "version": "2.0.0",
            "api_docs": "/api",
            "endpoints": {
                "config": "/api/config",
                "workflows": "/api/workflows",
                "memory": "/api/memory",
                "ollama": "/api/ollama/health",
                "playground": "/api/playground/sessions"
            },
            "note": "React frontend not built. Run 'npm run build' in react-frontend folder to build the UI."
        }), 200


@app.errorhandler(404)
def not_found(e):
    """Return React app for all routes (SPA support)"""
    # Check if it's an API request
    if str(e).startswith('/api'):
        return jsonify({
            'error': True,
            'error_code': 'NOT_FOUND',
            'message': f'Resource not found: {e}',
            'status_code': 404
        }), 404

    # Try to serve React app
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except:
        # React build folder doesn't exist
        return jsonify({
            "error": False,
            "message": "Agentic Workflow Builder API is running",
            "version": "2.0.0",
            "note": "React frontend not built. Access API endpoints directly or build the frontend."
        }), 200


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting Agentic Workflow Builder API...")
    print("📡 Backend: http://localhost:5000")
    print("🎨 Frontend: http://localhost:3000 (React dev server)")
    print()

    # Run with debug mode but disable auto-reloader to prevent connection resets
    # Use manual restart when code changes are made
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
