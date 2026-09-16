"""
Visual Chatbot Builder Agents
Complete chatbot building system with drag-and-drop nodes

Nodes Provided (11 total):
1. Intent Recognition - Classify user intent
2. Entity Extraction - Extract names, dates, locations, etc.
3. Dialog State - Track conversation state and context
4. Slot Filling - Collect required information step-by-step
5. Response Template - Generate responses from templates
6. Context Switch - Switch between conversation topics
7. Fallback Handler - Handle unknown intents/errors
8. Clarification - Ask for clarification when ambiguous
9. Multi-Turn Handler - Manage multi-turn conversations
10. Small Talk - Handle greetings and chitchat
11. Handoff - Transfer to human agent

Usage:
    Create conversational AI without code by connecting these nodes visually
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Detected intent"""
    name: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DialogContext:
    """Conversation context"""
    user_id: str
    conversation_id: str
    current_intent: Optional[str] = None
    current_state: str = "initial"
    slots: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentRecognitionAgent:
    """
    Classify user intent from input
    Uses pattern matching + optional LLM classification
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_provider = config.get('llm_provider')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recognize intent from user message

        Config:
            intents: List of intent definitions with patterns
            use_llm: Whether to use LLM for classification
            confidence_threshold: Minimum confidence (default: 0.7)
            fallback_intent: Intent to use if confidence too low

        Inputs:
            user_message: Text from user
            context: Optional conversation context

        Returns:
            intent: Detected intent name
            confidence: Confidence score (0-1)
            entities: Extracted entities
        """
        user_message = inputs.get('user_message', '').lower().strip()
        intents = self.config.get('intents', [])
        use_llm = self.config.get('use_llm', False)
        confidence_threshold = self.config.get('confidence_threshold', 0.7)
        fallback_intent = self.config.get('fallback_intent', 'unknown')

        # Try pattern matching first
        detected_intent, confidence = self._pattern_match(user_message, intents)

        # If confidence low and LLM available, use LLM
        if confidence < confidence_threshold and use_llm and self.llm_provider:
            detected_intent, confidence = await self._llm_classify(user_message, intents)

        # If still low confidence, use fallback
        if confidence < confidence_threshold:
            detected_intent = fallback_intent
            confidence = 0.5

        return {
            'intent': detected_intent,
            'confidence': confidence,
            'user_message': inputs.get('user_message'),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _pattern_match(self, message: str, intents: List[Dict]) -> Tuple[str, float]:
        """Pattern-based intent matching"""
        best_match = None
        best_score = 0.0

        for intent_def in intents:
            intent_name = intent_def.get('name')
            patterns = intent_def.get('patterns', [])
            keywords = intent_def.get('keywords', [])

            score = 0.0
            matches = 0

            # Check patterns
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    matches += 1
                    score += 0.5

            # Check keywords
            for keyword in keywords:
                if keyword.lower() in message:
                    matches += 1
                    score += 0.3

            # Normalize score
            if matches > 0:
                score = min(score / len(patterns + keywords), 1.0)

            if score > best_score:
                best_score = score
                best_match = intent_name

        return best_match or 'unknown', best_score

    async def _llm_classify(self, message: str, intents: List[Dict]) -> Tuple[str, float]:
        """LLM-based intent classification"""
        intent_list = [intent['name'] for intent in intents]
        intent_descriptions = {
            intent['name']: intent.get('description', '')
            for intent in intents
        }

        prompt = f"""Classify the user's intent from this message.

User message: "{message}"

Available intents:
{chr(10).join(f"- {name}: {intent_descriptions.get(name, '')}" for name in intent_list)}

Respond with ONLY the intent name and confidence (0-1) in format: intent_name,confidence

Example: product_inquiry,0.95"""

        try:
            response = await self.llm_provider.query(prompt=prompt, temperature=0.1, max_tokens=50)
            parts = response.strip().split(',')
            if len(parts) == 2:
                intent = parts[0].strip()
                confidence = float(parts[1].strip())
                return intent, confidence
        except Exception as e:
            logger.error(f"LLM intent classification failed: {e}")

        return 'unknown', 0.5


class EntityExtractionAgent:
    """
    Extract entities from user message
    Supports: names, dates, locations, numbers, emails, phones, custom patterns
    """

    # Predefined entity patterns
    ENTITY_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'url': r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+',
        'number': r'\b\d+\.?\d*\b',
        'currency': r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
        'date': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_provider = config.get('llm_provider')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities from message

        Config:
            entities: List of entity types to extract
            custom_patterns: Custom regex patterns for entities
            use_llm: Use LLM for complex entity extraction

        Inputs:
            user_message: Text to extract from

        Returns:
            entities: Dict of entity_type -> values
        """
        user_message = inputs.get('user_message', '')
        entity_types = self.config.get('entities', [])
        custom_patterns = self.config.get('custom_patterns', {})
        use_llm = self.config.get('use_llm', False)

        entities = {}

        # Pattern-based extraction
        for entity_type in entity_types:
            # Check predefined patterns
            if entity_type in self.ENTITY_PATTERNS:
                pattern = self.ENTITY_PATTERNS[entity_type]
                matches = re.findall(pattern, user_message)
                if matches:
                    entities[entity_type] = matches[0] if len(matches) == 1 else matches

            # Check custom patterns
            elif entity_type in custom_patterns:
                pattern = custom_patterns[entity_type]
                matches = re.findall(pattern, user_message, re.IGNORECASE)
                if matches:
                    entities[entity_type] = matches[0] if len(matches) == 1 else matches

        # LLM-based extraction for complex entities
        if use_llm and self.llm_provider:
            llm_entities = await self._llm_extract(user_message, entity_types)
            entities.update(llm_entities)

        return {
            'entities': entities,
            'entity_count': len(entities),
            'user_message': user_message
        }

    async def _llm_extract(self, message: str, entity_types: List[str]) -> Dict[str, Any]:
        """LLM-based entity extraction"""
        prompt = f"""Extract the following entities from this message:

Message: "{message}"

Entities to extract: {', '.join(entity_types)}

Respond in JSON format: {{"entity_type": "value", ...}}
If an entity is not found, omit it from the response.

JSON:"""

        try:
            response = await self.llm_provider.query(prompt=prompt, temperature=0.1, max_tokens=200)
            import json
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")

        return {}


class DialogStateAgent:
    """
    Track conversation state and context
    Maintains state machine for conversation flow
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update and track dialog state

        Config:
            states: Dict of state -> next_states mapping
            initial_state: Starting state
            max_history: Max conversation turns to keep

        Inputs:
            current_state: Current conversation state
            intent: Detected intent
            context: Conversation context
            event: State transition event

        Returns:
            new_state: Updated state
            context: Updated context
            transitions_available: List of possible next states
        """
        current_state = inputs.get('current_state', self.config.get('initial_state', 'initial'))
        intent = inputs.get('intent')
        event = inputs.get('event')
        context = inputs.get('context', {})

        states = self.config.get('states', {})
        max_history = self.config.get('max_history', 10)

        # Determine next state
        new_state = current_state

        if event:
            # Event-driven transition
            state_config = states.get(current_state, {})
            transitions = state_config.get('transitions', {})
            new_state = transitions.get(event, current_state)

        elif intent:
            # Intent-driven transition
            state_config = states.get(current_state, {})
            intent_transitions = state_config.get('intent_transitions', {})
            new_state = intent_transitions.get(intent, current_state)

        # Update context
        if 'history' not in context:
            context['history'] = []

        # Add to history
        context['history'].append({
            'state': current_state,
            'intent': intent,
            'event': event,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Trim history
        if len(context['history']) > max_history:
            context['history'] = context['history'][-max_history:]

        # Get available transitions
        new_state_config = states.get(new_state, {})
        transitions_available = list(new_state_config.get('transitions', {}).keys())

        return {
            'current_state': new_state,
            'previous_state': current_state,
            'context': context,
            'transitions_available': transitions_available,
            'state_changed': new_state != current_state
        }


class SlotFillingAgent:
    """
    Collect required information step-by-step
    Manages slot collection with prompts and validation
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill conversation slots

        Config:
            required_slots: List of required slot definitions
            optional_slots: List of optional slots
            prompts: Dict of slot -> prompt text

        Inputs:
            slots: Current slot values
            entities: Extracted entities from message
            intent: Current intent

        Returns:
            slots: Updated slot values
            next_slot: Next slot to fill (if any)
            all_filled: Boolean indicating if all required slots filled
            prompt: Prompt to ask user for next slot
        """
        required_slots = self.config.get('required_slots', [])
        prompts = self.config.get('prompts', {})
        validations = self.config.get('validations', {})

        slots = inputs.get('slots', {})
        entities = inputs.get('entities', {})

        # Fill slots from entities
        for entity_type, value in entities.items():
            if entity_type in [slot['name'] for slot in required_slots]:
                # Validate if validation defined
                if entity_type in validations:
                    is_valid = self._validate_slot(value, validations[entity_type])
                    if not is_valid:
                        continue
                slots[entity_type] = value

        # Find next unfilled required slot
        next_slot = None
        next_prompt = None

        for slot_def in required_slots:
            slot_name = slot_def['name']
            if slot_name not in slots or slots[slot_name] is None:
                next_slot = slot_name
                next_prompt = prompts.get(slot_name, f"Please provide {slot_name}")
                break

        # Check if all required slots filled
        all_filled = all(
            slot['name'] in slots and slots[slot['name']] is not None
            for slot in required_slots
        )

        # Calculate progress
        filled_count = sum(1 for slot in required_slots if slot['name'] in slots and slots[slot['name']] is not None)
        progress = (filled_count / len(required_slots) * 100) if required_slots else 100

        return {
            'slots': slots,
            'next_slot': next_slot,
            'all_filled': all_filled,
            'prompt': next_prompt,
            'progress': progress,
            'filled_count': filled_count,
            'total_slots': len(required_slots)
        }

    def _validate_slot(self, value: Any, validation: Dict) -> bool:
        """Validate slot value"""
        validation_type = validation.get('type')

        if validation_type == 'regex':
            pattern = validation.get('pattern')
            return bool(re.match(pattern, str(value)))

        elif validation_type == 'range':
            min_val = validation.get('min')
            max_val = validation.get('max')
            try:
                num_val = float(value)
                if min_val is not None and num_val < min_val:
                    return False
                if max_val is not None and num_val > max_val:
                    return False
                return True
            except (ValueError, TypeError):
                return False

        elif validation_type == 'choices':
            valid_choices = validation.get('choices', [])
            return value in valid_choices

        return True


class ResponseTemplateAgent:
    """
    Generate responses from templates
    Supports variable interpolation and conditional content
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_provider = config.get('llm_provider')

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate response from template

        Config:
            template_type: 'simple', 'variable', 'llm'
            template: Template string with {variables}
            llm_prompt: Prompt for LLM generation

        Inputs:
            variables: Dict of variable values
            context: Conversation context

        Returns:
            response: Generated response text
        """
        template_type = self.config.get('template_type', 'variable')
        template = self.config.get('template', '')
        variables = inputs.get('variables', {})

        if template_type == 'simple':
            response = template

        elif template_type == 'variable':
            # Replace variables in template
            response = template
            for key, value in variables.items():
                response = response.replace(f'{{{key}}}', str(value))

        elif template_type == 'llm' and self.llm_provider:
            # Generate using LLM
            llm_prompt = self.config.get('llm_prompt', template)
            # Fill prompt with variables
            for key, value in variables.items():
                llm_prompt = llm_prompt.replace(f'{{{key}}}', str(value))

            response = await self.llm_provider.query(prompt=llm_prompt, temperature=0.7, max_tokens=200)

        else:
            response = template

        return {
            'response': response.strip(),
            'template_used': template,
            'variables': variables
        }


class ContextSwitchAgent:
    """
    Handle topic switching in conversations
    Detects when user changes topic and manages context transition
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect and handle context switches

        Config:
            topics: List of topic definitions
            save_previous_context: Whether to save context for resume

        Inputs:
            current_topic: Current conversation topic
            intent: Detected intent
            context: Current context

        Returns:
            new_topic: New topic if switched
            context_switched: Boolean
            saved_context: Previous context (if saved)
        """
        current_topic = inputs.get('current_topic', 'general')
        intent = inputs.get('intent')
        context = inputs.get('context', {})

        topics = self.config.get('topics', {})
        save_previous = self.config.get('save_previous_context', True)

        # Detect topic change
        new_topic = current_topic
        topic_changed = False

        # Check if intent indicates topic change
        for topic_name, topic_def in topics.items():
            trigger_intents = topic_def.get('trigger_intents', [])
            if intent in trigger_intents:
                new_topic = topic_name
                topic_changed = True
                break

        # Save previous context if switching
        saved_context = None
        if topic_changed and save_previous:
            saved_context = {
                'topic': current_topic,
                'context': context.copy(),
                'timestamp': datetime.utcnow().isoformat()
            }

        return {
            'current_topic': new_topic,
            'previous_topic': current_topic,
            'context_switched': topic_changed,
            'saved_context': saved_context,
            'can_resume': saved_context is not None
        }


class FallbackHandlerAgent:
    """
    Handle unknown intents and errors
    Provides fallback responses and escalation logic
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle fallback scenarios

        Config:
            fallback_responses: List of fallback messages
            max_fallbacks: Max fallbacks before escalation
            escalate_to: Where to escalate (e.g., 'human')

        Inputs:
            intent_confidence: Confidence of intent detection
            fallback_count: Number of consecutive fallbacks
            context: Conversation context

        Returns:
            response: Fallback response
            should_escalate: Whether to escalate
            fallback_count: Updated count
        """
        fallback_responses = self.config.get('fallback_responses', [
            "I didn't quite understand that. Could you rephrase?",
            "I'm having trouble understanding. Can you try explaining differently?",
            "I'm not sure I can help with that. Would you like to speak with a specialist?"
        ])
        max_fallbacks = self.config.get('max_fallbacks', 3)

        fallback_count = inputs.get('fallback_count', 0) + 1

        # Select response based on count
        response_index = min(fallback_count - 1, len(fallback_responses) - 1)
        response = fallback_responses[response_index]

        # Check if should escalate
        should_escalate = fallback_count >= max_fallbacks

        return {
            'response': response,
            'fallback_count': fallback_count,
            'should_escalate': should_escalate,
            'escalate_to': self.config.get('escalate_to', 'human') if should_escalate else None
        }


class ClarificationAgent:
    """
    Ask clarifying questions when input is ambiguous
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate clarification question

        Config:
            ambiguous_fields: Fields that need clarification
            clarification_prompts: Prompts for each field

        Inputs:
            ambiguous_input: The ambiguous user input
            missing_slots: Slots that need values

        Returns:
            clarification_question: Question to ask user
            options: Multiple choice options (if applicable)
        """
        missing_slots = inputs.get('missing_slots', [])
        clarification_prompts = self.config.get('clarification_prompts', {})

        if missing_slots:
            first_missing = missing_slots[0]
            question = clarification_prompts.get(first_missing, f"Could you specify {first_missing}?")

            # Check if options defined
            options = self.config.get('options', {}).get(first_missing, [])

            return {
                'clarification_question': question,
                'options': options,
                'clarifying_field': first_missing
            }

        return {
            'clarification_question': "Could you provide more details?",
            'options': [],
            'clarifying_field': None
        }


class MultiTurnHandlerAgent:
    """
    Manage multi-turn conversations
    Handles coreference resolution and context tracking
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle multi-turn conversation

        Config:
            max_history: Max turns to keep
            enable_coreference: Enable pronoun resolution

        Inputs:
            current_message: Current user message
            history: Conversation history
            context: Current context

        Returns:
            resolved_message: Message with resolved references
            context: Updated context
            turn_count: Current turn number
        """
        current_message = inputs.get('current_message', '')
        history = inputs.get('history', [])
        context = inputs.get('context', {})
        max_history = self.config.get('max_history', 10)
        enable_coreference = self.config.get('enable_coreference', True)

        # Add current turn to history
        history.append({
            'message': current_message,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Trim history
        if len(history) > max_history:
            history = history[-max_history:]

        # Resolve coreferences if enabled
        resolved_message = current_message
        if enable_coreference:
            resolved_message = self._resolve_coreferences(current_message, context)

        return {
            'resolved_message': resolved_message,
            'original_message': current_message,
            'history': history,
            'context': context,
            'turn_count': len(history)
        }

    def _resolve_coreferences(self, message: str, context: Dict[str, Any]) -> str:
        """Simple coreference resolution"""
        # Replace pronouns with context values
        resolved = message

        # "it" → last mentioned product
        if context.get('last_product'):
            resolved = resolved.replace(' it ', f" {context['last_product']} ")
            resolved = resolved.replace(' It ', f" {context['last_product']} ")

        # "cheaper ones" → implicit budget change
        if 'cheaper' in resolved.lower() and context.get('budget'):
            # This would trigger a budget update in the workflow
            pass

        return resolved


class SmallTalkAgent:
    """
    Handle greetings, chitchat, and casual conversation
    """

    SMALL_TALK_PATTERNS = {
        'greeting': [r'\b(hi|hello|hey|howdy)\b', r'\bgood (morning|afternoon|evening)\b'],
        'how_are_you': [r'\bhow are you\b', r'\bhow\'s it going\b'],
        'thank_you': [r'\bthank(s| you)\b', r'\bappreciate\b'],
        'goodbye': [r'\b(bye|goodbye|see you)\b', r'\btalk to you later\b'],
        'name_question': [r'\bwhat\'s your name\b', r'\bwho are you\b'],
    }

    SMALL_TALK_RESPONSES = {
        'greeting': ["Hi! How can I help you today?", "Hello! What can I do for you?"],
        'how_are_you': ["I'm doing great, thanks for asking! How can I assist you?"],
        'thank_you': ["You're welcome!", "Happy to help!"],
        'goodbye': ["Goodbye! Have a great day!", "See you later!"],
        'name_question': ["I'm an AI assistant here to help you!"],
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle small talk

        Inputs:
            user_message: User's message

        Returns:
            is_small_talk: Boolean
            small_talk_type: Type of small talk
            response: Response to small talk
        """
        user_message = inputs.get('user_message', '').lower()

        # Check each pattern
        for talk_type, patterns in self.SMALL_TALK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_message, re.IGNORECASE):
                    import random
                    responses = self.SMALL_TALK_RESPONSES.get(talk_type, ["Thanks!"])
                    response = random.choice(responses)

                    return {
                        'is_small_talk': True,
                        'small_talk_type': talk_type,
                        'response': response
                    }

        return {
            'is_small_talk': False,
            'small_talk_type': None,
            'response': None
        }


class HandoffAgent:
    """
    Transfer conversation to human agent
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handoff to human

        Config:
            handoff_triggers: Conditions that trigger handoff
            handoff_team: Which team to transfer to
            notify_channels: How to notify (email, slack, etc.)

        Inputs:
            reason: Reason for handoff
            context: Conversation context to pass
            sentiment: User sentiment (optional)

        Returns:
            handoff_initiated: Boolean
            handoff_team: Team assigned
            ticket_id: Support ticket ID
            context_passed: Context data passed to human
        """
        reason = inputs.get('reason', 'user_request')
        context = inputs.get('context', {})
        handoff_team = self.config.get('handoff_team', 'general_support')

        # Generate ticket ID
        import uuid
        ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"

        # Prepare context for human
        context_to_pass = {
            'conversation_history': context.get('history', []),
            'user_intent': context.get('current_intent'),
            'slots_filled': context.get('slots', {}),
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Log handoff
        logger.info(f"Handoff initiated: {ticket_id} to {handoff_team}")

        return {
            'handoff_initiated': True,
            'handoff_team': handoff_team,
            'ticket_id': ticket_id,
            'context_passed': context_to_pass,
            'response': f"I've connected you with our {handoff_team} team. Your ticket number is {ticket_id}. Someone will assist you shortly."
        }
