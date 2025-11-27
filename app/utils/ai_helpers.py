import os
import json
import re
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser

# LLM Setup
gemini_api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=gemini_api_key,
    temperature=0,
    markdown=False
)

search = DuckDuckGoSearchRun()
json_parser = JsonOutputParser()

# UPDATED: Markdown-optimized Prompt Templates
chat_qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a professional AI tutor.

# RESPONSE FORMAT

Always respond as a VALID JSON object strictly in the following schema:

{{
  "bullets": [ "A bullet point", "Another bullet point" ],
  "steps": [ "Step 1...", "Step 2..." ],
  "bold": [ "Key bold concept 1", "Key bold concept 2" ],
  "markdown": "Full response in Markdown format with correct headings, **bold**, lists, and code blocks.",
  "code_blocks": [
      {{"language": "python", "code": "print('hello')"}}
  ]
}}

- Summarize the answer using the above fields.
- The 'markdown' field should contain your complete response with Markdown (including headings, lists, bold, etc.), and MUST be the same as you would show a user in a chat.
- In 'bullets', keep only the main points.
- In 'steps', provide stepwise how-to if applicable, else an empty list.
- In 'bold', extract key concepts and bold phrases.
- In 'code_blocks', extract code snippets if present (language required).
- DO NOT return anything outside this structure.

Current Tasks Context:
{tasks_context}

Chat history: Use context only, do NOT repeat in reply.

REMEMBER: Respond ONLY with JSON.
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])


roadmap_prompt = PromptTemplate.from_template("""
You are an expert study planner.

Return ONLY a strictly valid JSON object with this structure:

{
  "topic": "{topic}",
  "days": {days},
  "hours": {hours},
  "roadmap": [
    {
      "day": 1,
      "tasks": [
        {
          "parent_task": "High-level task title",
          "original_duration_minutes": 120,
          "sub_tasks": [
            {
              "task": "Micro task",
              "duration_minutes": 30,
              "description": "One sentence explanation."
            }
          ]
        }
      ]
    }
  ]
}

Rules:
- Only valid JSON.
- No text outside JSON.
- Sub-task durations MUST sum to parent.
- Use actionable steps.
""")


task_qa_prompt = PromptTemplate.from_template("""
You are a professional AI tutor.

You MUST return ONLY JSON with:

{
  "answer": "Full answer as a plain string",
  "key_points": ["Point 1", "Point 2"],
  "steps": ["Step 1", "Step 2"],
  "examples": ["Example explanation"],
  "code_blocks": [
      {"language": "python", "code": "print('hello')"}
  ]
}

Rules:
- No markdown formatting, only plain strings.
- No text outside the JSON.
- Follow the structure exactly.

Tasks for today:
{tasks_context}

Question:
{question}
""")


refinement_prompt_template = PromptTemplate.from_template("""
You must refine the given roadmap.

Return ONLY the updated JSON. No text outside JSON.

Current Roadmap:
{roadmap}

Instruction:
{instruction}

Rules:
- Maintain identical structure.
- Keep sub-tasks nested.
- Sub-task durations MUST sum to original_duration_minutes.
""")


# UPDATED: Flashcard prompt with markdown instructions
flashcards_prompt = PromptTemplate.from_template("""
Generate 8–10 flashcards and return ONLY valid JSON:

{
  "flashcards": [
    {
      "question": "Question text",
      "answer": "Answer text",
      "category": "Category",
      "difficulty": "easy/medium/hard"
    }
  ]
}

Focus on weak areas:
{understanding}

Topic:
{topic}

Rules:
- Only JSON.
- No extra text.
""")


# UPDATED: Study guide prompt with markdown instructions
study_guide_prompt = PromptTemplate.from_template("""
Create a structured study guide.

Return ONLY valid JSON with this structure:

{
  "learning_objectives": ["Objective 1", "Objective 2"],
  "key_concepts": ["Concept 1", "Concept 2"],
  "practice_exercises": [
    {
      "title": "Exercise name",
      "description": "What to do",
      "difficulty": "beginner/intermediate/advanced"
    }
  ],
  "study_schedule": [
    {
      "week": 1,
      "topics": ["Topic A", "Topic B"],
      "exercises": ["Exercise 1"]
    }
  ],
  "resources": [
    {
      "type": "documentation/tutorial/practice",
      "title": "Resource title",
      "url": "https://example.com"
    }
  ]
}

User understanding:
{understanding}

Topic:
{topic}

Rules:
- No text outside JSON.
- Follow structure exactly.
""")


materials_prompt = PromptTemplate.from_template("""
Provide learning resources. Return ONLY valid JSON:

{
  "videos": [
    {
      "title": "Video title",
      "url": "https://example.com",
      "channel": "Channel",
      "duration": "10 min",
      "type": "video"
    }
  ],
  "articles": [
    {
      "title": "Article",
      "url": "https://example.com",
      "source": "Website",
      "reading_time": "5 min",
      "type": "article"
    }
  ],
  "practice": [
    {
      "title": "Practice title",
      "url": "https://example.com",
      "difficulty": "Beginner",
      "type": "practice"
    }
  ],
  "tools": [
    {
      "name": "Tool name",
      "url": "https://example.com",
      "description": "What it does",
      "type": "tool"
    }
  ]
}

Topic:
{topic}

Rules:
- Only JSON.
- No additional text.
""")


# UPDATED: Search enhanced prompt with markdown
search_enhanced_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an expert tutor with access to search results.

Return ONLY valid JSON with:

{
  "answer": "Full explanation",
  "key_points": ["Point 1", "Point 2"],
  "updated_understanding": {"concept": 60},
  "resources": [
    {
      "title": "Resource",
      "url": "https://example.com",
      "type": "video/article/tool"
    }
  ]
}

Rules:
- Use search results only inside the JSON.
- No markdown.
- No text outside JSON.

Search Results:
{search_results}

User understanding:
{understanding}
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])


def run_chain(prompt, data):
    chain = prompt | llm | json_parser
    try:
        response = chain.invoke(data)
        content = response.content
        
        # FIX: Better JSON parsing for flashcards
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Clean content for JSON extraction
        if content.strip().startswith("```"):
            content = content.strip()[3:]
        
        if content.strip().endswith("```"):
            content = content.strip()[:-3]
        
        content = content.strip()
        
        # Remove language identifiers
        if content.lower().startswith("json") or content.lower().startswith("python"):
            content = content[4:].strip()

        # Try to find JSON object
        start_index = content.find('{')
        end_index = content.rfind('}')
        
        if start_index != -1 and end_index != -1:
            json_str = content[start_index : end_index + 1]
            return json.loads(json_str)
            
        # For flashcards specifically, try to create a basic structure
        if "flashcards" in content.lower() or "question" in content.lower():
            return create_fallback_flashcards(content)
            
        return None
        
    except Exception as e:
        print(f"Error during LLM call or final JSON parse: {e}")
        return None

def create_fallback_flashcards(content):
    """Create fallback flashcard structure when JSON parsing fails"""
    flashcards = []
    lines = content.split('\n')
    
    current_question = None
    current_answer = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('Q:') or line.startswith('Question:') or '?' in line:
            # Save previous card
            if current_question and current_answer:
                flashcards.append({
                    "question": current_question,
                    "answer": ' '.join(current_answer),
                    "category": "General",
                    "difficulty": "medium"
                })
            
            current_question = line.replace('Q:', '').replace('Question:', '').strip()
            current_answer = []
        elif line.startswith('A:') or line.startswith('Answer:'):
            current_answer.append(line.replace('A:', '').replace('Answer:', '').strip())
        elif current_question and line:
            current_answer.append(line)
    
    # Add the last card
    if current_question and current_answer:
        flashcards.append({
            "question": current_question,
            "answer": ' '.join(current_answer),
            "category": "General",
            "difficulty": "medium"
        })
    
    # If no structured flashcards found, create one basic one
    if not flashcards:
        flashcards = [{
            "question": "What did you learn about the topic?",
            "answer": "Review the generated content to understand key concepts.",
            "category": "General",
            "difficulty": "easy"
        }]
    
    return {"flashcards": flashcards[:8]}  # Limit to 8 cards

# UPDATED: Remove text cleaning to preserve markdown
def process_ai_response(raw_text):
    """
    Minimal processing to preserve Markdown formatting.
    Only extracts code blocks while keeping the original markdown intact.
    """
    if not raw_text:
        return {"text": "", "code_blocks": []}

    # Extract code blocks for special handling
    code_blocks = []
    code_block_regex = r"```(\w+)?\n([\s\S]*?)```"

    if not re.search(code_block_regex, raw_text):
        return {"text": raw_text, "code_blocks": []}
    
    def extract_code(match):
        language = match.group(1) or "text"
        code = match.group(2).strip()
        block_id = f"CODE_BLOCK_{len(code_blocks)}"
        code_blocks.append({
            "id": block_id,
            "language": language,
            "code": code
        })
        return f"\n\n{block_id}\n\n"
    
    # Temporarily remove code blocks
    text_with_placeholders = re.sub(code_block_regex, extract_code, raw_text)
    
    # Restore code blocks in their original format
    processed_text = text_with_placeholders
    for block in code_blocks:
        processed_text = processed_text.replace(
            block['id'], 
            f"```{block['language']}\n{block['code']}\n```"
        )
    
    return {
        "text": processed_text.strip(),
        "code_blocks": code_blocks
    }

def should_use_search(message: str, topic: str) -> bool:
    """Determine if web search should be used for this query"""
    search_triggers = [
        'current', 'recent', 'latest', 'new', 'update',
        'search', 'find', 'look up', 'what\'s new',
        'tutorial', 'guide', 'how to', 'examples',
        'resources', 'tools', 'libraries', 'frameworks',
        'trend', 'best practice', 'popular'
    ]
    
    message_lower = message.lower()
    
    # Always search for recent information
    if any(trigger in message_lower for trigger in ['current', 'recent', 'latest', '2024', '2025']):
        return True
    
    # Search for tutorials and how-to guides
    if any(trigger in message_lower for trigger in ['tutorial', 'how to', 'guide', 'learn']):
        return True
    
    # Search for specific tools or resources
    if any(trigger in message_lower for trigger in ['tools', 'libraries', 'frameworks', 'resources']):
        return True
    
    return False

def extract_resources_from_search(search_results: str, topic: str) -> list:
    """Extract structured resources from search results"""
    resources = []
    lines = search_results.split('\n')
    
    for line in lines:
        if 'http' in line:
            # Simple URL extraction
            urls = re.findall(r'https?://[^\s]+', line)
            for url in urls:
                resource_type = classify_resource_type(url, line)
                title = extract_title_from_line(line)
                if title and url:
                    resources.append({
                        "url": url,
                        "type": resource_type,
                        "title": title,
                        "description": line.strip()[:150] + "..." if len(line) > 150 else line.strip()
                    })
    
    # Remove duplicates and limit results
    seen_urls = set()
    unique_resources = []
    
    for resource in resources:
        if resource['url'] not in seen_urls and len(unique_resources) < 8:
            seen_urls.add(resource['url'])
            unique_resources.append(resource)
    
    return unique_resources

def classify_resource_type(url: str, context: str) -> str:
    """Classify the type of resource based on URL and context"""
    url_lower = url.lower()
    context_lower = context.lower()
    
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'video'
    elif 'github.com' in url_lower:
        return 'tool'
    elif 'docs' in url_lower or 'documentation' in context_lower:
        return 'documentation'
    elif 'course' in context_lower or 'tutorial' in context_lower:
        return 'article'
    else:
        return 'article'

def extract_title_from_line(line: str) -> str:
    """Extract a title from search result line"""
    # Remove URLs and clean up
    clean_line = re.sub(r'https?://[^\s]+', '', line)
    clean_line = clean_line.strip(' -•')
    
    # Take first 60 characters as title
    return clean_line[:60] + ('...' if len(clean_line) > 60 else '')

def extract_domain_from_url(url: str) -> str:
    """Extract domain name from URL"""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return domain.replace('www.', '')

def update_understanding_level(question: str, response: str, current_understanding: dict, topic: str) -> dict:
    """Update user's understanding based on the conversation"""
    # Simple implementation - in production, you might want more sophisticated analysis
    understanding_update = current_understanding.copy()
    
    # Extract key concepts from the question and response
    concepts_to_update = extract_concepts_from_text(question + " " + response, topic)
    
    for concept in concepts_to_update:
        if concept in understanding_update:
            # Increase understanding for discussed concepts
            understanding_update[concept] = min(100, understanding_update[concept] + 5)
        else:
            # Add new concept with initial understanding
            understanding_update[concept] = 30  # Initial understanding
    
    return understanding_update

def extract_concepts_from_text(text: str, topic: str) -> list:
    """Extract key concepts from text (simplified implementation)"""
    # This is a simplified version - in production, use NLP libraries
    words = text.lower().split()
    potential_concepts = []
    
    # Look for capitalized words and topic-related terms
    for i, word in enumerate(text.split()):
        if (word.istitle() and len(word) > 3) or word in topic.lower():
            potential_concepts.append(word)
    
    return list(set(potential_concepts))[:5]

# UPDATED: Enhanced processing that preserves markdown
def enhanced_process_ai_response(raw_text):
    """
    Enhanced AI response processing that preserves Markdown formatting.
    Only extracts code blocks for special handling.
    """
    if not raw_text:
        return {"text": "", "code_blocks": []}

    # Extract code blocks for custom rendering
    code_blocks = []
    code_block_regex = r"```(\w+)?\n([\s\S]*?)```"
    
    def extract_code(match):
        language = match.group(1) or "text"
        code = match.group(2).strip()
        block_id = f"CODE_BLOCK_{len(code_blocks)}"
        code_blocks.append({
            "id": block_id,
            "language": language,
            "code": code
        })
        return f"\n\n{block_id}\n\n"
    
    # Replace code blocks with placeholders
    text_with_placeholders = re.sub(code_block_regex, extract_code, raw_text)
    
    # Restore code blocks in their original markdown format
    final_text = text_with_placeholders
    for block in code_blocks:
        final_text = final_text.replace(
            block['id'], 
            f"```{block['language']}\n{block['code']}\n```"
        )
    
    return {
        "text": final_text.strip(),
        "code_blocks": code_blocks
    }

def enhanced_update_understanding_level(question, response, current_understanding, topic):
    """
    Enhanced understanding level tracking with conversation analysis
    """
    understanding_update = current_understanding.copy()
    
    # Analyze the depth of the conversation
    conversation_depth = analyze_conversation_depth(question, response)
    
    # Extract concepts with confidence scores
    concepts = extract_concepts_with_context(question + " " + response, topic)
    
    # Update understanding based on analysis
    for concept_data in concepts:
        concept = concept_data['concept']
        confidence = concept_data['confidence']
        complexity = concept_data['complexity']
        
        current_level = understanding_update.get(concept, 0)
        
        # Calculate improvement based on multiple factors
        improvement = 0
        improvement += conversation_depth * 1.5
        improvement += confidence * 2
        improvement += complexity * 1.2
        
        # Cap improvement
        improvement = min(improvement, 12)
        
        new_level = min(current_level + improvement, 100)
        understanding_update[concept] = round(new_level)
    
    return understanding_update

def analyze_conversation_depth(question, response):
    """Analyze the depth and quality of the conversation"""
    depth_score = 0
    
    # Question analysis
    question_lower = question.lower()
    response_lower = response.lower()
    
    # Length analysis
    if len(question.split()) > 15:
        depth_score += 2
    if len(response.split()) > 100:
        depth_score += 3
    
    # Complexity indicators
    complexity_indicators = [
        'how', 'why', 'explain', 'compare', 'difference',
        'implement', 'optimize', 'architecture', 'best practice'
    ]
    
    for indicator in complexity_indicators:
        if indicator in question_lower:
            depth_score += 2
    
    # Follow-up indicators
    follow_up_indicators = ['following up', 'previous', 'earlier', 'based on']
    for indicator in follow_up_indicators:
        if indicator in question_lower:
            depth_score += 3
    
    # Code discussion
    if 'code' in question_lower or '```' in response:
        depth_score += 3
    
    return min(depth_score, 10)

def extract_concepts_with_context(text, main_topic):
    """Extract concepts with context and confidence scoring"""
    concepts = []
    
    # Always include main topic
    concepts.append({
        'concept': main_topic.lower(),
        'confidence': 0.8,
        'complexity': 2
    })
    
    # Technical terms with complexity levels
    technical_terms = {
        'basic': ['variable', 'function', 'loop', 'if', 'else', 'print'],
        'intermediate': ['class', 'object', 'method', 'array', 'string', 'number'],
        'advanced': ['algorithm', 'framework', 'api', 'database', 'async', 'promise']
    }
    
    text_lower = text.lower()
    
    # Check for basic concepts
    for term in technical_terms['basic']:
        if term in text_lower:
            concepts.append({
                'concept': term,
                'confidence': 0.6,
                'complexity': 1
            })
    
    # Check for intermediate concepts
    for term in technical_terms['intermediate']:
        if term in text_lower:
            concepts.append({
                'concept': term,
                'confidence': 0.7,
                'complexity': 2
            })
    
    # Check for advanced concepts
    for term in technical_terms['advanced']:
        if term in text_lower:
            concepts.append({
                'concept': term,
                'confidence': 0.8,
                'complexity': 3
            })
    
    # Remove duplicates
    seen = set()
    unique_concepts = []
    for concept in concepts:
        if concept['concept'] not in seen:
            seen.add(concept['concept'])
            unique_concepts.append(concept)
    
    return unique_concepts[:6]  # Limit to 6 concepts