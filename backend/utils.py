import re
import uuid
from typing import Dict, List, Any
from datetime import datetime, timezone

def generate_project_name(prompt: str) -> str:
    """Generate a project name from user prompt"""
    # Extract meaningful words
    words = re.findall(r'\b[a-zA-Z]+\b', prompt.lower())
    
    # Remove common words
    stop_words = {
        'a', 'an', 'the', 'for', 'to', 'build', 'create', 'make', 'app', 'application',
        'web', 'website', 'system', 'platform', 'tool', 'service', 'using', 'with',
        'that', 'can', 'will', 'should', 'would', 'and', 'or', 'but', 'in', 'on', 'at'
    }
    
    meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Take first 2-3 words and create a name
    if len(meaningful_words) >= 3:
        name_words = meaningful_words[:3]
    elif len(meaningful_words) >= 2:
        name_words = meaningful_words[:2]
    else:
        name_words = meaningful_words[:1] if meaningful_words else ['generated']
    
    return '-'.join(name_words) + '-app'

def extract_technologies_from_prompt(prompt: str) -> List[str]:
    """Extract mentioned technologies from prompt"""
    prompt_lower = prompt.lower()
    
    base_technologies = ["React", "FastAPI", "MongoDB", "Tailwind CSS"]
    additional_technologies = []
    
    # Technology mapping
    tech_patterns = {
        'authentication': ['JWT Authentication'],
        'auth': ['JWT Authentication'],
        'login': ['JWT Authentication'],
        'real-time': ['WebSockets'],
        'websocket': ['WebSockets'],
        'live': ['WebSockets'],
        'payment': ['Stripe API'],
        'stripe': ['Stripe API'],
        'checkout': ['Stripe API'],
        'ai': ['Gemini API'],
        'artificial intelligence': ['Gemini API'],
        'machine learning': ['Gemini API'],
        'ml': ['Gemini API'],
        'chat': ['WebSockets', 'Gemini API'],
        'chatbot': ['Gemini API'],
        'email': ['SendGrid API'],
        'notification': ['SendGrid API'],
        'sms': ['Twilio API'],
        'file upload': ['AWS S3'],
        'image': ['AWS S3'],
        'storage': ['AWS S3'],
        'analytics': ['Google Analytics'],
        'tracking': ['Google Analytics']
    }
    
    for keyword, techs in tech_patterns.items():
        if keyword in prompt_lower:
            additional_technologies.extend(techs)
    
    # Remove duplicates while preserving order
    all_technologies = base_technologies + list(dict.fromkeys(additional_technologies))
    
    return all_technologies

def generate_project_structure(prompt: str, technologies: List[str]) -> Dict[str, List[str]]:
    """Generate project structure based on prompt and technologies"""
    prompt_lower = prompt.lower()
    
    # Base structure
    structure = {
        "frontend": [
            "src/App.js",
            "src/components/",
            "src/components/ui/",
            "src/pages/",
            "src/hooks/",
            "src/utils/",
            "src/styles/",
            "public/index.html",
            "package.json",
            "tailwind.config.js",
            "vite.config.js"
        ],
        "backend": [
            "main.py",
            "models.py",
            "auth.py",
            "database.py",
            "routes/",
            "routes/auth.py",
            "routes/api.py",
            "services/",
            "utils.py",
            "requirements.txt",
            ".env.example"
        ],
        "database": [
            "schemas/",
            "migrations/",
            "seeds/",
            "indexes.js"
        ],
        "config": [
            ".env",
            ".gitignore",
            "README.md",
            "docker-compose.yml",
            "Dockerfile"
        ],
        "tests": [
            "tests/",
            "tests/unit/",
            "tests/integration/",
            "tests/e2e/",
            "pytest.ini",
            "test_config.py"
        ],
        "docs": [
            "docs/",
            "docs/api.md",
            "docs/setup.md",
            "docs/deployment.md"
        ]
    }
    
    # Add specific files based on prompt content
    if any(keyword in prompt_lower for keyword in ['auth', 'login', 'register', 'user']):
        structure["frontend"].extend([
            "src/components/auth/Login.js",
            "src/components/auth/Register.js",
            "src/components/auth/ProtectedRoute.js",
            "src/contexts/AuthContext.js"
        ])
        structure["backend"].extend([
            "routes/users.py",
            "services/auth_service.py"
        ])
    
    if any(keyword in prompt_lower for keyword in ['dashboard', 'admin']):
        structure["frontend"].extend([
            "src/pages/Dashboard.js",
            "src/components/dashboard/",
            "src/components/dashboard/Stats.js",
            "src/components/dashboard/Navigation.js"
        ])
    
    if any(keyword in prompt_lower for keyword in ['blog', 'post', 'article']):
        structure["frontend"].extend([
            "src/components/blog/BlogPost.js",
            "src/components/blog/BlogList.js",
            "src/components/blog/Editor.js"
        ])
        structure["backend"].extend([
            "routes/posts.py",
            "routes/comments.py",
            "services/blog_service.py"
        ])
    
    if any(keyword in prompt_lower for keyword in ['ecommerce', 'shop', 'store', 'product']):
        structure["frontend"].extend([
            "src/components/products/ProductCard.js",
            "src/components/products/ProductList.js",
            "src/components/cart/Cart.js",
            "src/components/checkout/Checkout.js"
        ])
        structure["backend"].extend([
            "routes/products.py",
            "routes/orders.py",
            "services/payment_service.py"
        ])
    
    if any(keyword in prompt_lower for keyword in ['chat', 'message', 'real-time']):
        structure["frontend"].extend([
            "src/components/chat/ChatWindow.js",
            "src/components/chat/MessageList.js",
            "src/hooks/useWebSocket.js"
        ])
        structure["backend"].extend([
            "services/websocket_service.py",
            "routes/messages.py"
        ])
    
    # Add AI-specific files if AI technologies are included
    if any('ai' in tech.lower() or 'gemini' in tech.lower() for tech in technologies):
        structure["backend"].extend([
            "services/ai_service.py",
            "routes/ai.py"
        ])
        structure["frontend"].extend([
            "src/components/ai/AIChat.js",
            "src/services/aiService.js"
        ])
    
    return structure

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename

def format_datetime(dt: datetime) -> str:
    """Format datetime for consistent API responses"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def prepare_for_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for MongoDB storage"""
    prepared_data = data.copy()
    
    # Convert datetime objects to ISO strings
    for key, value in prepared_data.items():
        if isinstance(value, datetime):
            prepared_data[key] = format_datetime(value)
    
    return prepared_data

def parse_from_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse data from MongoDB storage"""
    if not data:
        return data
    
    parsed_data = data.copy()
    
    # Convert ObjectId to string if present
    if '_id' in parsed_data:
        parsed_data['_id'] = str(parsed_data['_id'])
    
    # Convert ISO strings back to datetime for specific fields
    datetime_fields = ['created_at', 'updated_at', 'timestamp']
    for field in datetime_fields:
        if field in parsed_data and isinstance(parsed_data[field], str):
            try:
                parsed_data[field] = datetime.fromisoformat(parsed_data[field].replace('Z', '+00:00'))
            except:
                pass  # Keep as string if parsing fails
    
    return parsed_data

def calculate_project_complexity(prompt: str) -> str:
    """Calculate project complexity based on requirements"""
    prompt_lower = prompt.lower()
    
    complexity_indicators = {
        'simple': ['basic', 'simple', 'minimal', 'small'],
        'medium': ['dashboard', 'auth', 'user', 'management', 'crud'],
        'complex': ['real-time', 'ai', 'ml', 'analytics', 'ecommerce', 'payment', 'multi-tenant', 'microservice']
    }
    
    scores = {'simple': 0, 'medium': 0, 'complex': 0}
    
    for complexity, keywords in complexity_indicators.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                scores[complexity] += 1
    
    # Determine overall complexity
    if scores['complex'] >= 2:
        return 'complex'
    elif scores['medium'] >= 2 or scores['complex'] >= 1:
        return 'medium'
    else:
        return 'simple'

def estimate_development_time(complexity: str, technologies: List[str]) -> Dict[str, int]:
    """Estimate development time in hours"""
    base_times = {
        'simple': {'frontend': 20, 'backend': 15, 'database': 8, 'testing': 10},
        'medium': {'frontend': 40, 'backend': 30, 'database': 15, 'testing': 20},
        'complex': {'frontend': 80, 'backend': 60, 'database': 25, 'testing': 40}
    }
    
    times = base_times[complexity].copy()
    
    # Add time for specific technologies
    tech_multipliers = {
        'JWT Authentication': 1.2,
        'WebSockets': 1.3,
        'Stripe API': 1.4,
        'Gemini API': 1.3,
        'AWS S3': 1.2
    }
    
    for tech in technologies:
        if tech in tech_multipliers:
            multiplier = tech_multipliers[tech]
            for key in times:
                times[key] = int(times[key] * multiplier)
    
    times['total'] = sum(times.values())
    return times