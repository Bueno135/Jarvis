"""
Advanced Natural Language Processing for Jarvis.
Provides intent recognition, entity extraction, and context-aware processing.
"""
import re
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging

class IntentType(Enum):
    """Types of intents that can be recognized."""
    QUERY = "query"
    COMMAND = "command"
    QUESTION = "question"
    CONVERSATION = "conversation"
    UNKNOWN = "unknown"

class EntityType(Enum):
    """Types of entities that can be extracted."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    TIME = "time"
    DATE = "date"
    NUMBER = "number"
    APPLICATION = "application"
    FILE = "file"
    WEBSITE = "website"
    DEVICE = "device"

@dataclass
class Entity:
    """Named entity extracted from text."""
    text: str
    type: EntityType
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = None

@dataclass
class Intent:
    """Recognized intent from user input."""
    type: IntentType
    name: str
    confidence: float
    parameters: Dict[str, Any]
    entities: List[Entity]

@dataclass
class Context:
    """Conversation context for NLP processing."""
    user_id: str
    session_id: str
    previous_intents: List[Intent]
    entities_memory: Dict[str, List[Entity]]
    conversation_history: List[Dict[str, Any]]
    timestamp: float

class NLPProcessor:
    """Advanced NLP processor for Jarvis."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger("Jarvis.NLP")
        
        # Load patterns and models
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.context_memory = {}
        
        # Language settings
        self.language = self.config.get("language", "pt-BR")
        self.confidence_threshold = self.config.get("confidence_threshold", 0.6)
        
        self.logger.info(f"NLP Processor initialized for {self.language}")
    
    def process_text(self, text: str, context: Optional[Context] = None) -> Intent:
        """Process text and extract intent and entities."""
        start_time = time.time()
        
        # Preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Extract entities first (helps with intent recognition)
        entities = self._extract_entities(cleaned_text)
        
        # Recognize intent
        intent = self._recognize_intent(cleaned_text, entities, context)
        
        # Apply context-aware processing
        if context:
            intent = self._apply_context(intent, context)
        
        # Update context
        if context:
            self._update_context(context, intent, entities)
        
        processing_time = time.time() - start_time
        self.logger.debug(f"NLP processing completed in {processing_time:.3f}s")
        
        return intent
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better NLP processing."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-]', '', text)
        
        # Normalize common patterns
        replacements = {
            r'\b(q\s|quê)\b': 'o que',
            r'\b(p\s|por\s+que)\b': 'por que',
            r'\b(c\/|vc)\b': 'você',
            r'\b(tbm|tambem)\b': 'também',
            r'\b(pq|pq)\b': 'porque',
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from text."""
        entities = []
        
        # Extract entities using patterns
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = Entity(
                        text=match.group(),
                        type=EntityType(entity_type),
                        confidence=0.8,  # Base confidence for pattern matching
                        start_pos=match.start(),
                        end_pos=match.end(),
                        metadata={"pattern": pattern}
                    )
                    entities.append(entity)
        
        # Extract numbers
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        for match in re.finditer(number_pattern, text):
            entity = Entity(
                text=match.group(),
                type=EntityType.NUMBER,
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end(),
                metadata={"value": float(match.group())}
            )
            entities.append(entity)
        
        # Extract time expressions
        time_patterns = [
            r'\b(agora|já|imediatamente)\b',
            r'\b(depois|mais\s+tarde)\b',
            r'\b(antes|mais\s+cedo)\b',
            r'\b(\d{1,2}:\d{2})\b',
            r'\b(\d{1,2}\s*horas?)\b'
        ]
        
        for pattern in time_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = Entity(
                    text=match.group(),
                    type=EntityType.TIME,
                    confidence=0.7,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                entities.append(entity)
        
        # Remove overlapping entities (keep highest confidence)
        entities = self._remove_overlapping_entities(entities)
        
        return entities
    
    def _remove_overlapping_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities, keeping highest confidence."""
        if not entities:
            return entities
        
        # Sort by confidence (descending)
        entities.sort(key=lambda e: e.confidence, reverse=True)
        
        filtered = []
        for entity in entities:
            # Check if this entity overlaps with any already accepted entity
            overlapping = False
            for accepted in filtered:
                if (entity.start_pos < accepted.end_pos and 
                    entity.end_pos > accepted.start_pos):
                    overlapping = True
                    break
            
            if not overlapping:
                filtered.append(entity)
        
        return filtered
    
    def _recognize_intent(self, text: str, entities: List[Entity], context: Optional[Context] = None) -> Intent:
        """Recognize intent from text and entities."""
        best_intent = None
        best_confidence = 0.0
        best_parameters = {}
        
        # Try each intent pattern
        for intent_name, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    confidence = self._calculate_pattern_confidence(pattern, text, entities)
                    
                    if confidence > best_confidence and confidence >= self.confidence_threshold:
                        best_intent = intent_name
                        best_confidence = confidence
                        best_parameters = self._extract_parameters(match, entities)
        
        # Determine intent type
        if best_intent:
            intent_type = self._classify_intent_type(best_intent, text)
        else:
            intent_type = IntentType.UNKNOWN
            best_intent = "unknown"
        
        return Intent(
            type=intent_type,
            name=best_intent,
            confidence=best_confidence,
            parameters=best_parameters,
            entities=entities
        )
    
    def _calculate_pattern_confidence(self, pattern: str, text: str, entities: List[Entity]) -> float:
        """Calculate confidence score for a pattern match."""
        base_confidence = 0.7
        
        # Boost confidence based on pattern specificity
        pattern_complexity = len(re.findall(r'[\w\.\+\*\?\[\]\(\)]', pattern))
        complexity_boost = min(pattern_complexity * 0.05, 0.2)
        
        # Boost confidence based on entity matches
        entity_boost = 0.0
        for entity in entities:
            if re.search(pattern, entity.text, re.IGNORECASE):
                entity_boost += 0.1
        
        # Boost confidence based on text coverage
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            coverage = len(match.group()) / len(text)
            coverage_boost = coverage * 0.1
        else:
            coverage_boost = 0.0
        
        total_confidence = base_confidence + complexity_boost + entity_boost + coverage_boost
        return min(total_confidence, 1.0)
    
    def _extract_parameters(self, match: re.Match, entities: List[Entity]) -> Dict[str, Any]:
        """Extract parameters from regex match and entities."""
        parameters = {}
        
        # Extract named groups from match
        if match.groupdict():
            parameters.update(match.groupdict())
        
        # Add entities as parameters
        for entity in entities:
            param_name = f"{entity.type.value}_{entity.text.lower().replace(' ', '_')}"
            parameters[param_name] = {
                "text": entity.text,
                "confidence": entity.confidence,
                "metadata": entity.metadata
            }
        
        return parameters
    
    def _classify_intent_type(self, intent_name: str, text: str) -> IntentType:
        """Classify intent type based on name and text."""
        # Check for question patterns
        question_words = ['o que', 'qual', 'como', 'onde', 'quando', 'por que', 'quem']
        if any(word in text for word in question_words) or text.endswith('?'):
            return IntentType.QUESTION
        
        # Check for command patterns
        command_indicators = ['abra', 'feche', 'execute', 'inicie', 'pare', 'desligue', 'crie', 'delete']
        if any(word in text for word in command_indicators):
            return IntentType.COMMAND
        
        # Check for query patterns
        query_indicators = ['mostre', 'liste', 'busque', 'encontre', 'procure']
        if any(word in text for word in query_indicators):
            return IntentType.QUERY
        
        # Default to conversation
        return IntentType.CONVERSATION
    
    def _apply_context(self, intent: Intent, context: Context) -> Intent:
        """Apply context-aware processing to intent."""
        # Check for pronoun resolution
        if intent.entities:
            resolved_entities = self._resolve_pronouns(intent.entities, context)
            intent.entities = resolved_entities
        
        # Check for anaphora resolution
        intent = self._resolve_anaphora(intent, context)
        
        # Apply conversation history
        intent = self._apply_conversation_history(intent, context)
        
        return intent
    
    def _resolve_pronouns(self, entities: List[Entity], context: Context) -> List[Entity]:
        """Resolve pronouns to actual entities."""
        pronouns_map = {
            'ele': EntityType.PERSON,
            'ela': EntityType.PERSON,
            'ele': EntityType.PERSON,
            'ela': EntityType.PERSON,
            'isto': EntityType.OBJECT,
            'isso': EntityType.OBJECT,
            'aquilo': EntityType.OBJECT
        }
        
        resolved = []
        for entity in entities:
            if entity.text.lower() in pronouns_map:
                # Try to resolve from context
                resolved_entity = self._find_referenced_entity(entity, context)
                if resolved_entity:
                    resolved.append(resolved_entity)
                else:
                    resolved.append(entity)
            else:
                resolved.append(entity)
        
        return resolved
    
    def _find_referenced_entity(self, pronoun: Entity, context: Context) -> Optional[Entity]:
        """Find referenced entity from context."""
        # Look for entities of the same type in recent context
        recent_entities = []
        for entities_list in context.entities_memory.values():
            recent_entities.extend(entities_list[-5:])  # Last 5 entities of each type
        
        # Filter by type preference
        if pronoun.text.lower() in ['ele', 'ela']:
            candidates = [e for e in recent_entities if e.type == EntityType.PERSON]
        else:
            candidates = recent_entities
        
        # Return the most recent entity
        if candidates:
            return max(candidates, key=lambda e: e.metadata.get('timestamp', 0))
        
        return None
    
    def _resolve_anaphora(self, intent: Intent, context: Context) -> Intent:
        """Resolve anaphoric references."""
        # This is a simplified implementation
        # In practice, you'd use more sophisticated NLP techniques
        
        # Check if intent refers to previous conversation
        if context.previous_intents:
            last_intent = context.previous_intents[-1]
            
            # Simple anaphora detection
            if intent.name == "repeat" or "novamente" in intent.parameters.get("text", ""):
                # Repeat last intent
                intent = last_intent
                intent.confidence *= 0.8  # Reduce confidence for repeated intent
        
        return intent
    
    def _apply_conversation_history(self, intent: Intent, context: Context) -> Intent:
        """Apply conversation history to improve intent understanding."""
        # Look for patterns in conversation history
        if len(context.conversation_history) > 0:
            # Check for follow-up questions
            if intent.type == IntentType.QUESTION:
                # Might be a follow-up to previous answer
                previous_turn = context.conversation_history[-1]
                if previous_turn.get("type") == "answer":
                    intent.parameters["follow_up"] = True
        
        return intent
    
    def _update_context(self, context: Context, intent: Intent, entities: List[Entity]):
        """Update context with new information."""
        # Add intent to history
        context.previous_intents.append(intent)
        
        # Keep only recent intents (last 10)
        if len(context.previous_intents) > 10:
            context.previous_intents = context.previous_intents[-10:]
        
        # Update entities memory
        for entity in entities:
            entity_type = entity.type.value
            if entity_type not in context.entities_memory:
                context.entities_memory[entity_type] = []
            
            # Add timestamp
            entity.metadata = entity.metadata or {}
            entity.metadata["timestamp"] = time.time()
            
            context.entities_memory[entity_type].append(entity)
            
            # Keep only recent entities (last 20 per type)
            if len(context.entities_memory[entity_type]) > 20:
                context.entities_memory[entity_type] = context.entities_memory[entity_type][-20:]
        
        # Update timestamp
        context.timestamp = time.time()
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent recognition patterns."""
        patterns = {
            # Application control
            "open_app": [
                r'abre\s+(?P<app_name>.+)',
                r'abra\s+(?P<app_name>.+)',
                r'inicie\s+(?P<app_name>.+)',
                r'execute\s+(?P<app_name>.+)'
            ],
            "close_app": [
                r'fecha\s+(?P<app_name>.+)',
                r'feche\s+(?P<app_name>.+)',
                r'pare\s+(?P<app_name>.+)',
                r'desligue\s+(?P<app_name>.+)'
            ],
            
            # File operations
            "create_file": [
                r'crie\s+(?P<file_name>.+)\s+(?:arquivo|file)',
                r'criar\s+(?P<file_name>.+)\s+(?:arquivo|file)',
                r'novo\s+(?:arquivo|file)\s+(?P<file_name>.+)'
            ],
            "delete_file": [
                r'apague\s+(?P<file_name>.+)',
                r'delete\s+(?P<file_name>.+)',
                r'remova\s+(?P<file_name>.+)'
            ],
            
            # Information queries
            "time_query": [
                r'que\s+horas?s?',
                r'horas?',
                r'tempo\s+agora'
            ],
            "date_query": [
                r'que\s+dia\s+é\s+hoje',
                r'data\s+de\s+hoje',
                r'hoje\s+é\s+que\s+dia'
            ],
            
            # Web operations
            "open_website": [
                r'abra\s+(?P<website>.+)',
                r'navegue\s+para\s+(?P<website>.+)',
                r'visite\s+(?P<website>.+)'
            ],
            "search_web": [
                r'pesquise\s+(?P<query>.+)',
                'busque\s+(?P<query>.+)',
                r'procure\s+(?P<query>.+)'
            ],
            
            # System operations
            "shutdown": [
                r'desligue\s+o\s+computador',
                r'desligar\s+computador',
                r'shutdown'
            ],
            "restart": [
                r'reinicie\s+o\s+computador',
                r'reiniciar\s+computador',
                r'reboot'
            ],
            
            # Conversation
            "greeting": [
                r'oi',
                r'olá',
                r'bom\s+dia',
                r'boa\s+tarde',
                r'boa\s+noite'
            ],
            "farewell": [
                r'tchau',
                r'adeus',
                r'até\s+logo',
                r'até\s+mais'
            ],
            "thanks": [
                r'obrigado',
                r'obrigada',
                r'valeu'
            ]
        }
        
        return patterns
    
    def _load_entity_patterns(self) -> Dict[str, List[str]]:
        """Load entity extraction patterns."""
        patterns = {
            "application": [
                r'\b(notepad|bloco\s+de\s+notas|calculadora|calculator|chrome|firefox|explorer|word|excel|powerpoint)\b',
                r'\b(app\s+\w+|\w+\s+app)\b'
            ],
            "website": [
                r'\b(https?://[^\s]+)\b',
                r'\b(www\.[^\s]+)\b',
                r'\b([a-zA-Z0-9-]+\.(com|br|org|net|gov))\b'
            ],
            "file": [
                r'\b([\w\-]+\.(txt|doc|pdf|jpg|png|mp3|mp4))\b',
                r'\b(arquivo\s+[\w\-]+)\b'
            ],
            "person": [
                r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
                r'\b(joão|maria|pedro|ana|carlos|paulo)\b'
            ],
            "location": [
                r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\b(são\s+paulo|rio\s+de\s+janeiro|brasília|salvador)\b'
            ]
        }
        
        return patterns
    
    def create_context(self, user_id: str, session_id: str) -> Context:
        """Create a new conversation context."""
        return Context(
            user_id=user_id,
            session_id=session_id,
            previous_intents=[],
            entities_memory={},
            conversation_history=[],
            timestamp=time.time()
        )
    
    def get_context(self, user_id: str, session_id: str) -> Optional[Context]:
        """Get existing conversation context."""
        key = f"{user_id}:{session_id}"
        return self.context_memory.get(key)
    
    def save_context(self, context: Context):
        """Save conversation context."""
        key = f"{context.user_id}:{context.session_id}"
        self.context_memory[key] = context
        
        # Clean up old contexts (older than 1 hour)
        current_time = time.time()
        expired_keys = []
        for key, ctx in self.context_memory.items():
            if current_time - ctx.timestamp > 3600:  # 1 hour
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.context_memory[key]

# Global NLP processor instance
_nlp_processor = None

def get_nlp_processor() -> NLPProcessor:
    """Get global NLP processor instance."""
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = NLPProcessor()
    return _nlp_processor

def configure_nlp(config: Dict[str, Any]):
    """Configure global NLP processor."""
    global _nlp_processor
    _nlp_processor = NLPProcessor(config)
