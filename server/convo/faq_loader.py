"""
FAQ knowledge base loader.
Loads FAQ data and formats it for LLM context.
"""
import json
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class FAQKnowledgeBase:
    """Manages FAQ knowledge base."""
    
    def __init__(self, faq_file: str = "data/faq.json"):
        self.faq_file = faq_file
        self.faqs: Dict[str, Any] = {}
        self.load_faqs()
    
    def load_faqs(self) -> None:
        """Load FAQs from JSON file."""
        try:
            faq_path = Path(self.faq_file)
            if faq_path.exists():
                with open(faq_path, 'r') as f:
                    self.faqs = json.load(f)
                logger.info(f"Loaded {len(self.faqs)} FAQ entries")
            else:
                logger.warning(f"FAQ file not found: {self.faq_file}")
        except Exception as e:
            logger.error(f"Error loading FAQs: {e}")
    
    def get_faq_context(self) -> str:
        """
        Format FAQs as context for LLM system prompt.
        
        Returns:
            Formatted FAQ text
        """
        if not self.faqs:
            return ""
        
        context = "\n\nKnowledge Base (use this to answer common questions):\n"
        context += "=" * 60 + "\n\n"
        
        for category, data in self.faqs.items():
            question = data.get("question", "")
            answer = data.get("answer", "")
            context += f"Q: {question}\n"
            context += f"A: {answer}\n\n"
        
        return context
    
    def search_faq(self, query: str) -> str:
        """
        Search for FAQ answer (simple keyword matching).
        
        Args:
            query: User's question
            
        Returns:
            Best matching answer or empty string
        """
        query_lower = query.lower()
        
        # Simple keyword matching
        best_match = None
        best_score = 0
        
        for category, data in self.faqs.items():
            question = data.get("question", "").lower()
            answer = data.get("answer", "")
            
            # Count keyword matches
            score = sum(1 for word in question.split() if word in query_lower)
            
            if score > best_score:
                best_score = score
                best_match = answer
        
        return best_match or ""
    
    def add_faq(self, category: str, question: str, answer: str) -> None:
        """
        Add new FAQ entry.
        
        Args:
            category: FAQ category/key
            question: Question text
            answer: Answer text
        """
        self.faqs[category] = {
            "question": question,
            "answer": answer
        }
        self.save_faqs()
    
    def save_faqs(self) -> None:
        """Save FAQs back to JSON file."""
        try:
            with open(self.faq_file, 'w') as f:
                json.dump(self.faqs, f, indent=2)
            logger.info("FAQs saved successfully")
        except Exception as e:
            logger.error(f"Error saving FAQs: {e}")


# Global instance
faq_kb = FAQKnowledgeBase()


def get_faq_enhanced_prompt(base_prompt: str) -> str:
    """
    Enhance system prompt with FAQ knowledge base.
    
    Args:
        base_prompt: Base system prompt
        
    Returns:
        Enhanced prompt with FAQ context
    """
    return base_prompt + faq_kb.get_faq_context()

