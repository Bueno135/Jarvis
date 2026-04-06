"""
Continuous learning system for Jarvis.
Adapts to user preferences and improves over time.
"""
import json
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque
import logging
from core.interfaces import CommandContext, CommandResult
from core.cache import cache_result, get_cache_instance

@dataclass
class LearningData:
    """Data point for learning."""
    input_text: str
    intent: str
    plugin_used: str
    success: bool
    response_time: float
    user_feedback: Optional[int] = None  # 1-5 rating
    timestamp: float = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.context is None:
            self.context = {}

@dataclass
class UserPreference:
    """User preference data."""
    user_id: str
    preference_type: str
    value: Any
    confidence: float
    created_at: float
    updated_at: float
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()

class ContinuousLearning:
    """Continuous learning system for Jarvis."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger("Jarvis.ContinuousLearning")
        
        # Configuration
        self.learning_rate = self.config.get("learning_rate", 0.1)
        self.min_samples = self.config.get("min_samples", 5)
        self.max_history = self.config.get("max_history", 1000)
        self.adaptation_threshold = self.config.get("adaptation_threshold", 0.7)
        
        # Storage
        self.learning_data: List[LearningData] = []
        self.user_preferences: Dict[str, List[UserPreference]] = defaultdict(list)
        self.intent_patterns: Dict[str, List[str]] = defaultdict(list)
        self.plugin_performance: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Files
        self.data_file = Path(self.config.get("data_file", "data/learning.json"))
        self.preferences_file = Path(self.config.get("preferences_file", "data/preferences.json"))
        self.patterns_file = Path(self.config.get("patterns_file", "data/patterns.json"))
        
        # Ensure data directory exists
        self.data_file.parent.mkdir(exist_ok=True)
        
        # Cache
        self.cache = get_cache_instance()
        
        # Load existing data
        self._load_learning_data()
        
        self.logger.info("Continuous learning system initialized")
    
    def record_interaction(self, context: CommandContext, result: CommandResult, 
                          response_time: float, user_id: str = "default"):
        """Record a user interaction for learning."""
        learning_data = LearningData(
            input_text=context.raw_text,
            intent=context.command_name,
            plugin_used=context.command_name,
            success=result.success,
            response_time=response_time,
            context={
                "user_id": user_id,
                "params": context.params,
                "kernel_state": getattr(context.kernel, 'state', None)
            }
        )
        
        self.learning_data.append(learning_data)
        
        # Limit history size
        if len(self.learning_data) > self.max_history:
            self.learning_data = self.learning_data[-self.max_history:]
        
        # Update plugin performance
        self._update_plugin_performance(learning_data)
        
        # Trigger learning if enough data
        if len(self.learning_data) >= self.min_samples:
            self._trigger_learning()
        
        # Save periodically
        if len(self.learning_data) % 10 == 0:
            self._save_learning_data()
    
    def record_user_feedback(self, interaction_id: int, feedback: int, 
                           user_id: str = "default"):
        """Record user feedback for an interaction."""
        if 0 <= interaction_id < len(self.learning_data):
            self.learning_data[interaction_id].user_feedback = feedback
            
            # Update preferences based on feedback
            self._update_preferences_from_feedback(
                self.learning_data[interaction_id], feedback, user_id
            )
    
    def get_user_preferences(self, user_id: str = "default") -> Dict[str, Any]:
        """Get learned user preferences."""
        preferences = {}
        
        for pref in self.user_preferences[user_id]:
            if pref.confidence >= self.adaptation_threshold:
                preferences[pref.preference_type] = pref.value
        
        return preferences
    
    def adapt_command_parsing(self, input_text: str, user_id: str = "default") -> Dict[str, Any]:
        """Adapt command parsing based on learned patterns."""
        # Get user preferences
        preferences = self.get_user_preferences(user_id)
        
        # Apply learned adaptations
        adaptations = {
            "preferred_plugins": preferences.get("preferred_plugins", {}),
            "response_style": preferences.get("response_style", "normal"),
            "verbosity": preferences.get("verbosity", "normal"),
            "correction_patterns": self._get_correction_patterns(user_id)
        }
        
        return adaptations
    
    def suggest_improvements(self) -> List[Dict[str, Any]]:
        """Suggest system improvements based on learning data."""
        suggestions = []
        
        if len(self.learning_data) < self.min_samples:
            return suggestions
        
        # Analyze failure patterns
        failures = [d for d in self.learning_data if not d.success]
        if len(failures) > len(self.learning_data) * 0.2:  # More than 20% failures
            common_failures = defaultdict(int)
            for failure in failures:
                common_failures[failure.intent] += 1
            
            for intent, count in common_failures.items():
                if count > 2:
                    suggestions.append({
                        "type": "high_failure_rate",
                        "intent": intent,
                        "failure_rate": count / len(failures),
                        "suggestion": f"Consider improving {intent} plugin or adding more patterns"
                    })
        
        # Analyze slow responses
        slow_responses = [d for d in self.learning_data if d.response_time > 2.0]
        if len(slow_responses) > len(self.learning_data) * 0.1:  # More than 10% slow
            suggestions.append({
                "type": "slow_response",
                "avg_response_time": np.mean([d.response_time for d in slow_responses]),
                "suggestion": "Consider optimizing slow plugins or adding caching"
            })
        
        # Analyze user preferences
        if len(self.user_preferences) > 0:
            suggestions.append({
                "type": "user_adaptation",
                "adapted_preferences": len(self.user_preferences),
                "suggestion": "User preferences are being learned and applied"
            })
        
        return suggestions
    
    def learn_new_patterns(self) -> bool:
        """Learn new patterns from user interactions."""
        if len(self.learning_data) < self.min_samples * 2:
            return False
        
        # Group successful interactions by intent
        successful_by_intent = defaultdict(list)
        for data in self.learning_data:
            if data.success and data.user_feedback and data.user_feedback >= 4:
                successful_by_intent[data.intent].append(data)
        
        # Extract patterns
        new_patterns = {}
        for intent, interactions in successful_by_intent.items():
            if len(interactions) >= 3:
                patterns = self._extract_patterns(interactions)
                if patterns:
                    new_patterns[intent] = patterns
        
        # Update patterns
        for intent, patterns in new_patterns.items():
            if intent not in self.intent_patterns:
                self.intent_patterns[intent] = []
            
            for pattern in patterns:
                if pattern not in self.intent_patterns[intent]:
                    self.intent_patterns[intent].append(pattern)
                    self.logger.info(f"Learned new pattern for {intent}: {pattern}")
        
        return len(new_patterns) > 0
    
    def _update_plugin_performance(self, data: LearningData):
        """Update plugin performance metrics."""
        plugin = data.plugin_used
        
        if plugin not in self.plugin_performance:
            self.plugin_performance[plugin] = {
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "total_executions": 0,
                "successful_executions": 0
            }
        
        perf = self.plugin_performance[plugin]
        perf["total_executions"] += 1
        
        if data.success:
            perf["successful_executions"] += 1
        
        # Update success rate (exponential moving average)
        current_rate = perf["successful_executions"] / perf["total_executions"]
        perf["success_rate"] = (perf["success_rate"] * (1 - self.learning_rate) + 
                               current_rate * self.learning_rate)
        
        # Update average response time
        current_time = data.response_time
        perf["avg_response_time"] = (perf["avg_response_time"] * (1 - self.learning_rate) + 
                                    current_time * self.learning_rate)
    
    def _update_preferences_from_feedback(self, data: LearningData, feedback: int, user_id: str):
        """Update user preferences from feedback."""
        # High feedback indicates preference for this type of interaction
        if feedback >= 4:
            # Learn preferred plugins
            self._add_preference(user_id, "preferred_plugins", data.plugin_used, 
                               feedback / 5.0)
            
            # Learn response style preferences
            if data.response_time < 1.0:
                self._add_preference(user_id, "response_style", "fast", 
                                   feedback / 5.0)
            
            # Learn verbosity preferences
            if len(data.input_text) > 50:
                self._add_preference(user_id, "verbosity", "detailed", 
                                   feedback / 5.0)
        
        # Low feedback indicates dislike
        elif feedback <= 2:
            # Learn to avoid this plugin for similar contexts
            self._add_preference(user_id, "avoid_plugins", data.plugin_used, 
                               (5 - feedback) / 5.0)
    
    def _add_preference(self, user_id: str, pref_type: str, value: Any, confidence: float):
        """Add or update a user preference."""
        # Check if preference already exists
        existing = None
        for i, pref in enumerate(self.user_preferences[user_id]):
            if pref.preference_type == pref_type and pref.value == value:
                existing = i
                break
        
        if existing is not None:
            # Update existing preference
            pref = self.user_preferences[user_id][existing]
            pref.confidence = (pref.confidence * 0.7 + confidence * 0.3)  # Weighted average
            pref.updated_at = time.time()
        else:
            # Add new preference
            pref = UserPreference(
                user_id=user_id,
                preference_type=pref_type,
                value=value,
                confidence=confidence,
                created_at=time.time(),
                updated_at=time.time()
            )
            self.user_preferences[user_id].append(pref)
    
    def _get_correction_patterns(self, user_id: str) -> List[str]:
        """Get correction patterns for a user."""
        # Analyze common mistakes and corrections
        corrections = []
        
        # This would be implemented based on actual correction data
        # For now, return empty list
        
        return corrections
    
    def _extract_patterns(self, interactions: List[LearningData]) -> List[str]:
        """Extract common patterns from interactions."""
        # Simple pattern extraction - in practice, you'd use more sophisticated NLP
        patterns = []
        
        # Extract common prefixes/suffixes
        texts = [d.input_text.lower() for d in interactions]
        
        # Find common starting words
        starting_words = defaultdict(int)
        for text in texts:
            words = text.split()
            if len(words) >= 2:
                start_phrase = " ".join(words[:2])
                starting_words[start_phrase] += 1
        
        # Return patterns that appear in at least 50% of interactions
        threshold = len(interactions) * 0.5
        for phrase, count in starting_words.items():
            if count >= threshold:
                patterns.append(f"{phrase} *")
        
        return patterns
    
    def _trigger_learning(self):
        """Trigger learning process."""
        # Learn new patterns
        if self.learn_new_patterns():
            self.logger.info("New patterns learned from user interactions")
        
        # Update user models
        self._update_user_models()
        
        # Save learning data
        self._save_learning_data()
    
    def _update_user_models(self):
        """Update user-specific models."""
        # Group interactions by user
        user_interactions = defaultdict(list)
        for data in self.learning_data:
            user_id = data.context.get("user_id", "default")
            user_interactions[user_id].append(data)
        
        # Update models for each user
        for user_id, interactions in user_interactions.items():
            if len(interactions) >= self.min_samples:
                self._update_user_model(user_id, interactions)
    
    def _update_user_model(self, user_id: str, interactions: List[LearningData]):
        """Update model for a specific user."""
        # Calculate user-specific metrics
        success_rate = sum(1 for d in interactions if d.success) / len(interactions)
        avg_response_time = np.mean([d.response_time for d in interactions])
        
        # Cache user model
        model_key = f"user_model_{user_id}"
        model_data = {
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "preferred_intents": self._get_preferred_intents(interactions),
            "last_updated": time.time()
        }
        
        self.cache.set(model_key, model_data, ttl=3600)  # Cache for 1 hour
    
    def _get_preferred_intents(self, interactions: List[LearningData]) -> List[str]:
        """Get preferred intents for a user."""
        intent_counts = defaultdict(int)
        for data in interactions:
            if data.success:
                intent_counts[data.intent] += 1
        
        # Return top 3 intents
        sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        return [intent for intent, count in sorted_intents[:3]]
    
    def _save_learning_data(self):
        """Save learning data to files."""
        try:
            # Save learning data
            learning_data = [asdict(d) for d in self.learning_data]
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, indent=2, default=str)
            
            # Save preferences
            preferences_data = {}
            for user_id, prefs in self.user_preferences.items():
                preferences_data[user_id] = [asdict(p) for p in prefs]
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences_data, f, indent=2, default=str)
            
            # Save patterns
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.intent_patterns, f, indent=2)
            
            self.logger.debug("Learning data saved")
            
        except Exception as e:
            self.logger.error(f"Failed to save learning data: {e}")
    
    def _load_learning_data(self):
        """Load learning data from files."""
        try:
            # Load learning data
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learning_data = [LearningData(**d) for d in data]
            
            # Load preferences
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, prefs in data.items():
                        self.user_preferences[user_id] = [UserPreference(**p) for p in prefs]
            
            # Load patterns
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    self.intent_patterns = json.load(f)
            
            self.logger.info(f"Loaded {len(self.learning_data)} learning data points")
            
        except Exception as e:
            self.logger.error(f"Failed to load learning data: {e}")

# Global learning instance
_continuous_learning = None

def get_continuous_learning() -> ContinuousLearning:
    """Get global continuous learning instance."""
    global _continuous_learning
    if _continuous_learning is None:
        _continuous_learning = ContinuousLearning()
    return _continuous_learning

def configure_learning(config: Dict[str, Any]):
    """Configure global continuous learning."""
    global _continuous_learning
    _continuous_learning = ContinuousLearning(config)

# Decorator for automatic learning integration
def learn_from_interaction(user_id: str = "default"):
    """Decorator to automatically learn from function interactions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
                raise
            finally:
                # Record interaction for learning
                learning = get_continuous_learning()
                
                # Create mock context and result for learning
                # In practice, this would be integrated with the actual command execution
                response_time = time.time() - start_time
                
                # This is a simplified version - you'd integrate this with the actual
                # command execution flow in the kernel
                
            return result
        
        return wrapper
    return decorator
