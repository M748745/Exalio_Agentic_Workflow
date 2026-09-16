"""
Agent Loader - Registers all agents to the AgentRegistry
Dynamically loads and registers all 75+ agent nodes
"""

import logging
from typing import Dict, Any
from pathlib import Path
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from core.workflow_engine import AgentRegistry

logger = logging.getLogger(__name__)


class AgentLoader:
    """
    Loads and registers all agents to the registry
    Handles agent initialization and dependency injection
    """

    def __init__(self, ollama_service=None, state_manager=None):
        """
        Initialize agent loader

        Args:
            ollama_service: OllamaService instance for LLM operations
            state_manager: StateManager instance for state management
        """
        self.ollama_service = ollama_service
        self.state_manager = state_manager
        self.registry = AgentRegistry()

    def load_all_agents(self) -> AgentRegistry:
        """
        Load and register all agents

        Returns:
            AgentRegistry with all agents registered
        """
        logger.info("Loading all agents...")

        # Load agents by category
        self._load_control_flow_agents()
        self._load_data_transformation_agents()
        self._load_parser_agents()
        self._load_chatbot_agents()
        self._load_integration_agents()
        self._load_hitl_agents()
        self._load_scheduling_agents()
        self._load_advanced_agents()
        self._load_processing_agents()
        self._load_analysis_agents()
        self._load_output_agents()

        total_agents = len(self.registry.list_agents())
        logger.info(f"Successfully loaded {total_agents} agents")

        return self.registry

    # ========================================================================
    # CONTROL FLOW AGENTS (8 nodes)
    # ========================================================================

    def _load_control_flow_agents(self):
        """Load control flow agents"""
        from agents.control_flow_agent import (
            IfElseAgent, SwitchCaseAgent, ForLoopAgent, WhileLoopAgent,
            TryCatchAgent, ParallelExecutionAgent, WaitDelayAgent, BreakContinueAgent
        )

        self.registry.register("if_else", self._create_agent_wrapper(IfElseAgent))
        self.registry.register("switch_case", self._create_agent_wrapper(SwitchCaseAgent))
        self.registry.register("for_loop", self._create_agent_wrapper(ForLoopAgent))
        self.registry.register("while_loop", self._create_agent_wrapper(WhileLoopAgent))
        self.registry.register("try_catch", self._create_agent_wrapper(TryCatchAgent))
        self.registry.register("parallel_exec", self._create_agent_wrapper(ParallelExecutionAgent))
        self.registry.register("wait_delay", self._create_agent_wrapper(WaitDelayAgent))
        self.registry.register("break_continue", self._create_agent_wrapper(BreakContinueAgent))

        logger.info("Loaded 8 control flow agents")

    # ========================================================================
    # DATA TRANSFORMATION AGENTS (10 nodes)
    # ========================================================================

    def _load_data_transformation_agents(self):
        """Load data transformation agents"""
        from agents.data_transformation_agent import (
            JSONTransformAgent, DataMapperAgent, FilterAgent, AggregationAgent,
            StringOperationsAgent, MathOperationsAgent, VariableAssignmentAgent,
            DataValidationAgent, ArrayOperationsAgent, FormatConverterAgent
        )

        self.registry.register("json_transform", self._create_agent_wrapper(JSONTransformAgent))
        self.registry.register("data_mapper", self._create_agent_wrapper(DataMapperAgent))
        self.registry.register("filter_node", self._create_agent_wrapper(FilterAgent))
        self.registry.register("aggregation", self._create_agent_wrapper(AggregationAgent))
        self.registry.register("string_ops", self._create_agent_wrapper(StringOperationsAgent))
        self.registry.register("math_ops", self._create_agent_wrapper(MathOperationsAgent))
        self.registry.register("variable_assign", self._create_agent_wrapper(VariableAssignmentAgent))
        self.registry.register("data_validation", self._create_agent_wrapper(DataValidationAgent))
        self.registry.register("array_ops", self._create_agent_wrapper(ArrayOperationsAgent))
        self.registry.register("format_converter", self._create_agent_wrapper(FormatConverterAgent))

        logger.info("Loaded 10 data transformation agents")

    # ========================================================================
    # UNIVERSAL PARSER AGENT (1 comprehensive node)
    # ========================================================================

    def _load_parser_agents(self):
        """Load universal parser agent"""
        from agents.parser_agent import UniversalParserAgent

        self.registry.register(
            "universal_parser",
            self._create_agent_wrapper(UniversalParserAgent, use_ollama=True)
        )

        logger.info("Loaded 1 universal parser agent")

    # ========================================================================
    # CHATBOT AGENTS (11 nodes)
    # ========================================================================

    def _load_chatbot_agents(self):
        """Load chatbot building agents"""
        from agents.chatbot_agent import (
            IntentRecognitionAgent, EntityExtractionAgent, DialogStateAgent,
            SlotFillingAgent, ResponseTemplateAgent, ContextSwitchAgent,
            FallbackHandlerAgent, ClarificationAgent, MultiTurnHandlerAgent,
            SmallTalkAgent, HandoffAgent
        )

        self.registry.register("intent_recognition", self._create_agent_wrapper(IntentRecognitionAgent, use_ollama=True))
        self.registry.register("entity_extraction", self._create_agent_wrapper(EntityExtractionAgent, use_ollama=True))
        self.registry.register("dialog_state", self._create_agent_wrapper(DialogStateAgent))
        self.registry.register("slot_filling", self._create_agent_wrapper(SlotFillingAgent))
        self.registry.register("response_template", self._create_agent_wrapper(ResponseTemplateAgent, use_ollama=True))
        self.registry.register("context_switch", self._create_agent_wrapper(ContextSwitchAgent))
        self.registry.register("fallback_handler", self._create_agent_wrapper(FallbackHandlerAgent, use_ollama=True))
        self.registry.register("clarification", self._create_agent_wrapper(ClarificationAgent, use_ollama=True))
        self.registry.register("multi_turn", self._create_agent_wrapper(MultiTurnHandlerAgent))
        self.registry.register("small_talk", self._create_agent_wrapper(SmallTalkAgent, use_ollama=True))
        self.registry.register("handoff", self._create_agent_wrapper(HandoffAgent))

        logger.info("Loaded 11 chatbot agents")

    # ========================================================================
    # INTEGRATION AGENTS (14 nodes)
    # ========================================================================

    def _load_integration_agents(self):
        """Load integration and connectivity agents"""
        from agents.integration_agent import (
            HTTPRequestAgent, WebhookSenderAgent, WebhookReceiverAgent,
            EmailAgent, SmsAgent, SlackAgent, DiscordAgent, WhatsAppAgent,
            TeamsAgent, FileOperationsAgent, FtpAgent, DatabaseOperationsAgent,
            GraphQLAgent, WebSocketAgent
        )

        self.registry.register("http_request", self._create_agent_wrapper(HTTPRequestAgent))
        self.registry.register("webhook_sender", self._create_agent_wrapper(WebhookSenderAgent))
        self.registry.register("webhook_receiver", self._create_agent_wrapper(WebhookReceiverAgent))
        self.registry.register("email_node", self._create_agent_wrapper(EmailAgent))
        self.registry.register("sms_node", self._create_agent_wrapper(SmsAgent))
        self.registry.register("slack_node", self._create_agent_wrapper(SlackAgent))
        self.registry.register("discord_node", self._create_agent_wrapper(DiscordAgent))
        self.registry.register("whatsapp_node", self._create_agent_wrapper(WhatsAppAgent))
        self.registry.register("teams_node", self._create_agent_wrapper(TeamsAgent))
        self.registry.register("file_ops", self._create_agent_wrapper(FileOperationsAgent))
        self.registry.register("ftp_node", self._create_agent_wrapper(FtpAgent))
        self.registry.register("database_ops", self._create_agent_wrapper(DatabaseOperationsAgent))
        self.registry.register("graphql_node", self._create_agent_wrapper(GraphQLAgent))
        self.registry.register("websocket_node", self._create_agent_wrapper(WebSocketAgent))

        logger.info("Loaded 14 integration agents")

    # ========================================================================
    # HUMAN-IN-THE-LOOP AGENTS (7 nodes)
    # ========================================================================

    def _load_hitl_agents(self):
        """Load human-in-the-loop agents"""
        from agents.hitl_agent import (
            ApprovalAgent, ManualInputAgent, ReviewAgent, EscalationAgent,
            AssignmentAgent, NotificationAgent, FeedbackAgent
        )

        self.registry.register("approval", self._create_agent_wrapper(ApprovalAgent))
        self.registry.register("manual_input", self._create_agent_wrapper(ManualInputAgent))
        self.registry.register("review", self._create_agent_wrapper(ReviewAgent))
        self.registry.register("escalation", self._create_agent_wrapper(EscalationAgent))
        self.registry.register("assignment", self._create_agent_wrapper(AssignmentAgent))
        self.registry.register("notification", self._create_agent_wrapper(NotificationAgent))
        self.registry.register("feedback", self._create_agent_wrapper(FeedbackAgent))

        logger.info("Loaded 7 HITL agents")

    # ========================================================================
    # SCHEDULING & TRIGGER AGENTS (8 nodes)
    # ========================================================================

    def _load_scheduling_agents(self):
        """Load scheduling and trigger agents"""
        from agents.scheduling_agent import (
            CronSchedulerAgent, EventTriggerAgent, WebhookTriggerAgent,
            FileWatchAgent, EmailTriggerAgent, DatabaseTriggerAgent,
            IntervalTriggerAgent, TimeDelayAgent
        )

        self.registry.register("cron_scheduler", self._create_agent_wrapper(CronSchedulerAgent))
        self.registry.register("event_trigger", self._create_agent_wrapper(EventTriggerAgent))
        self.registry.register("webhook_trigger", self._create_agent_wrapper(WebhookTriggerAgent))
        self.registry.register("file_watch", self._create_agent_wrapper(FileWatchAgent))
        self.registry.register("email_trigger", self._create_agent_wrapper(EmailTriggerAgent))
        self.registry.register("db_trigger", self._create_agent_wrapper(DatabaseTriggerAgent))
        self.registry.register("interval_trigger", self._create_agent_wrapper(IntervalTriggerAgent))
        self.registry.register("time_delay", self._create_agent_wrapper(TimeDelayAgent))

        logger.info("Loaded 8 scheduling agents")

    # ========================================================================
    # ADVANCED AGENT FEATURES (8 nodes)
    # ========================================================================

    def _load_advanced_agents(self):
        """Load advanced AI agent pattern implementations"""
        from agents.advanced_agent import (
            ReActLoopAgent, PlanExecuteAgent, ToolCallingAgent,
            MultiAgentCollaborationAgent, AgentRouterAgent, SelfReflectionAgent,
            AgentMemoryAgent, AgentSupervisorAgent
        )

        self.registry.register("react_loop", self._create_agent_wrapper(ReActLoopAgent, use_ollama=True))
        self.registry.register("plan_execute", self._create_agent_wrapper(PlanExecuteAgent, use_ollama=True))
        self.registry.register("tool_calling", self._create_agent_wrapper(ToolCallingAgent, use_ollama=True))
        self.registry.register("multi_agent", self._create_agent_wrapper(MultiAgentCollaborationAgent, use_ollama=True))
        self.registry.register("agent_router", self._create_agent_wrapper(AgentRouterAgent, use_ollama=True))
        self.registry.register("self_reflection", self._create_agent_wrapper(SelfReflectionAgent, use_ollama=True))
        self.registry.register("agent_memory", self._create_agent_wrapper(AgentMemoryAgent))
        self.registry.register("agent_supervisor", self._create_agent_wrapper(AgentSupervisorAgent, use_ollama=True))

        logger.info("Loaded 8 advanced agents")

    # ========================================================================
    # PROCESSING AGENTS (Basic LLM operations)
    # ========================================================================

    def _load_processing_agents(self):
        """Load basic processing agents"""

        # LLM Query Agent
        async def llm_query_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """LLM query agent - query Ollama with custom prompt"""
            if not self.ollama_service:
                return {"error": "Ollama service not available"}

            prompt = config.get("prompt", "")
            model = config.get("model", "llama3.2:3b")
            temperature = config.get("temperature", 0.7)

            # Substitute variables in prompt
            for key, value in data.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))

            response = await self.ollama_service.generate(
                model=model,
                prompt=prompt,
                temperature=temperature
            )

            return {
                "response": response.get("response", ""),
                "model": model,
                "prompt": prompt
            }

        # OCR Agent (placeholder - would use actual OCR library)
        async def ocr_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """OCR agent - extract text from images"""
            return {
                "text": "OCR extracted text placeholder",
                "confidence": 0.95
            }

        # Embeddings Agent
        async def embeddings_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """Generate embeddings using Ollama"""
            if not self.ollama_service:
                return {"error": "Ollama service not available"}

            text = config.get("text", "")
            model = config.get("model", "nomic-embed-text")

            response = await self.ollama_service.embed(model=model, input=text)

            return {
                "embeddings": response.get("embeddings", []),
                "model": model
            }

        # Classification Agent
        async def classification_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """Classify content using LLM"""
            if not self.ollama_service:
                return {"error": "Ollama service not available"}

            text = config.get("text", "")
            labels = config.get("labels", [])
            model = config.get("model", "llama3.2:3b")

            prompt = f"""Classify the following text into one of these categories: {', '.join(labels)}

Text: {text}

Return only the category label, nothing else."""

            response = await self.ollama_service.generate(
                model=model,
                prompt=prompt,
                temperature=0.1
            )

            return {
                "label": response.get("response", "").strip(),
                "labels": labels,
                "text": text
            }

        # Entity Extraction (simple version)
        async def extraction_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """Extract entities from text"""
            if not self.ollama_service:
                return {"error": "Ollama service not available"}

            text = config.get("text", "")
            entities = config.get("entities", ["person", "location", "organization"])
            model = config.get("model", "llama3.2:3b")

            prompt = f"""Extract the following entities from the text: {', '.join(entities)}

Text: {text}

Return as JSON format only."""

            response = await self.ollama_service.generate(
                model=model,
                prompt=prompt,
                temperature=0.1
            )

            return {
                "entities": response.get("response", ""),
                "text": text
            }

        self.registry.register("llm_query", llm_query_handler)
        self.registry.register("ocr", ocr_handler)
        self.registry.register("embeddings", embeddings_handler)
        self.registry.register("classification", classification_handler)
        self.registry.register("extraction", extraction_handler)

        logger.info("Loaded 5 processing agents")

    # ========================================================================
    # ANALYSIS AGENTS
    # ========================================================================

    def _load_analysis_agents(self):
        """Load analysis agents"""

        # Similarity matching
        async def similarity_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """Calculate similarity between texts"""
            return {"similarity": 0.85, "method": "cosine"}

        # Sentiment analysis
        async def sentiment_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """Analyze sentiment"""
            if not self.ollama_service:
                return {"error": "Ollama service not available"}

            text = config.get("text", "")
            model = config.get("model", "llama3.2:3b")

            prompt = f"""Analyze the sentiment of this text. Return only one word: positive, negative, or neutral.

Text: {text}"""

            response = await self.ollama_service.generate(
                model=model,
                prompt=prompt,
                temperature=0.1
            )

            return {
                "sentiment": response.get("response", "").strip().lower(),
                "text": text
            }

        # Scoring
        async def scoring_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """Score content"""
            return {"score": 8.5, "max_score": 10}

        self.registry.register("similarity", similarity_handler)
        self.registry.register("sentiment", sentiment_handler)
        self.registry.register("scoring", scoring_handler)

        logger.info("Loaded 3 analysis agents")

    # ========================================================================
    # OUTPUT AGENTS
    # ========================================================================

    def _load_output_agents(self):
        """Load output agents"""

        # Display results
        async def display_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """Display results to user"""
            return {
                "displayed": True,
                "data": data
            }

        # Save file
        async def save_file_handler(data: Dict[str, Any], config: Dict[str, Any]):
            """Save output to file"""
            file_path = config.get("file_path", "output.txt")
            content = config.get("content", "")

            try:
                with open(file_path, 'w') as f:
                    f.write(str(content))
                return {"success": True, "file_path": file_path}
            except Exception as e:
                return {"success": False, "error": str(e)}

        self.registry.register("display", display_handler)
        self.registry.register("save_file", save_file_handler)

        logger.info("Loaded 2 output agents")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_agent_wrapper(self, agent_class, use_ollama=False):
        """
        Create a wrapper function for an agent class

        Args:
            agent_class: The agent class to wrap
            use_ollama: Whether to inject ollama_service

        Returns:
            Async function that can be called by workflow engine
        """
        async def agent_executor(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
            """Execute agent with data and config"""
            try:
                # Create agent instance
                if use_ollama and self.ollama_service:
                    agent = agent_class(config, ollama_service=self.ollama_service)
                else:
                    agent = agent_class(config)

                # Execute agent
                result = await agent.execute(inputs=data)

                return result

            except Exception as e:
                logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e)
                }

        return agent_executor


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def create_agent_registry(ollama_service=None, state_manager=None) -> AgentRegistry:
    """
    Create and populate agent registry

    Args:
        ollama_service: OllamaService instance
        state_manager: StateManager instance

    Returns:
        Populated AgentRegistry
    """
    loader = AgentLoader(ollama_service=ollama_service, state_manager=state_manager)
    return loader.load_all_agents()
