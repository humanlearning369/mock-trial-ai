*** Overview ***

Mock Trial AI is an enterprise-grade legal technology platform that combines multiple AI models, federal court data, and advanced analytics to deliver comprehensive mock trial analysis and case preparation tools.
This is not designed as a fully autonomous AI solution out of the box. Instead, think of it as a training and augmentation tool; a foundation for building legal AI workflows. To perform effectively, the AI components must be trained with a clear understanding of legal processes and decision-making.
Once tailored to a specific area of law, the AI can handle most of the work required for mock trials and pre-trial preparation, dramatically reducing reliance on OpenAI/ClaudeAI APIs and minimizing the need for engineering personnel to set up and participate in mock trial environments.

- Architecture

•	Frontend: Streamlit-based web interface

•	AI Models: Claude (Anthropic), OpenAI Embeddings, Custom LegalBERT

•	Databases: PostgreSQL, MongoDB, Pinecone Vector DB

•	Data Sources: Federal court cases, expert documents, case law

•	Analytics: Real-time case similarity, outcome prediction, strategy recommendations

- Features

•	Case Input & Management: Comprehensive patent (core edition only), contract, and employment case forms, etc. (license edition only).

•	AI-Powered Analysis: Multi-perspective legal analysis using state-of-the-art AI

•	Similar Case Discovery: Vector-based similarity search across federal court data

•	Strategy Recommendations: Timeline analysis, success probability, settlement insights

•	Multi-Role Chat: Attorney, Judge, Expert, and Opposing counsel perspectives

•	Document Processing: Upload and analyze case documents with AI extraction

•	Visual Analytics: Interactive charts and strategic planning tools (Utilize PowerBI and/or Tableau).

- Quick Start (Prerequisites)

•	Python 3.9+

•	PostgreSQL 12+

•	MongoDB 4.4+

•	Pinecone

•	Git

- Installation

1.	Clone the Repository
git clone https://github.com/humanlearning369/mock-trial-ai.git
cd mock-trial-ai

2.	Set Up Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3.	Install Dependencies
pip install -r minimal_reqs.txt

4.	Database Setup

# PostgreSQL - Create database and run schema
createdb mock_trial_db
psql mock_trial_db < database/schema.sql
(Please contact me for schema – mocktrialapp@gmail.com)

# MongoDB - Start service
mongod --dbpath /your/mongodb/path

5.	Configuration
# Copy configuration templates
cp config.env.example config.env
cp backend/config.env.example backend/config.env
(Note: The reason for two config.env files (root/backend) is because the backend config.env runs a separate agent for VR integration and API processing. Which are not included in the core edition.)

# Edit configuration files with your credentials
6.	Run the Application
streamlit run app.py
Configuration
Environment Variables
Create config.env in the root directory

# Database Configuration
DB_NAME=mock_trial_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=mock_trial_analytics

# API Keys (Required for full functionality)
OPENAI_API_KEY=your_openai_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENV=your_pinecone_environment
Backend Configuration
Create backend/config.env

# Additional backend services configuration
PINECONE_INDEX=mtc
CLAUDE_MODEL=claude-3-opus-20240229
OPENAI_MODEL=text-embedding-ada-002

- AI Model Options
This application supports two AI analysis backends:

Option 1: OpenAI Embeddings (Default)
Uses OpenAI's text-embedding-ada-002 for case similarity analysis.
Pros: No model training required, high-quality embeddings
Cons: Requires API key, internet connection, usage costs
Setup: Just add your OpenAI API key to config.env

Option 2: Custom LegalBERT (Advanced)
Uses a custom-trained LegalBERT model on court data.
Pros: Specialized for legal text, no API costs, offline operation 
Cons: Requires model training/download, larger resource requirements, recursive chunking.

- Switching to LegalBERT
1.	Train or Download LegalBERT Model
# Option A: Train your own model (requires court data)
python backend/train_legalbert_json.py

# Option B: Download pre-trained model (if available)
# Contact repository maintainer for lightweight model access (core edition only).

2.	Update Import Statements
In the following files, change the import:
Files to modify:

•	frontend/components/analysis.py

•	frontend/components/chat.py

•	frontend/components/strategy.py

•	frontend/utils/connection.py

Change from:
from mock_trial_analysis import MockTrialAnalyzer

Change to:
from mocktrialanalyzer import MockTrialAnalyzer

3.	Ensure Model Path
Verify your LegalBERT model is saved to:

./legalbertmt/
├── config.json
├── pytorch_model.bin
├── tokenizer.json
├── vocab.txt
└── special_tokens_map.json

- Technology Stack
*** Frontend

•	Streamlit - Web application framework

•	Plotly - Interactive visualizations

•	Python-docx - Document processing

*** Backend & AI

•	Claude (Anthropic) - Advanced legal analysis

•	OpenAI API - Text embeddings

•	LegalBERT - Custom legal language model

•	scikit-learn - Similarity calculations

•	Transformers - Model loading and inference

- Databases

•	PostgreSQL - Primary case data storage

•	MongoDB - Analytics and document storage

•	Pinecone - Vector similarity search

- APIs & Integration

•	FastAPI - Backend API framework

•	CourtListener API - Federal court data (not included in community version)

•	Pacer

•	USPTO

- Project Structure

•	See app_structure.pdf file or readme file

- Usage Examples

*** Basic Case Analysis ***

1.	Navigate to Case Input tab

2.	Select "Patent Infringement" case type

3.	Fill in required case details

4.	Upload supporting documents (optional)

5.	Go to Analysis tab and click "Start Analysis"

6.	Review similar cases and AI-generated analysis

7.	Use Strategy tab for timeline and recommendations

8.	Interact with Chat for multi-perspective Q&A

- Advanced Features

•	Document Upload: Document Upload: Supports PDF and DOCX with automatic text extraction (Core Edition). The Licensed Edition extends support to additional formats, including audio and video files.

•	Multi-Role Chat: Switch between Attorney, Judge, Expert, and Opposing perspectives

•	Strategy Timeline: Visual Gantt charts for case planning

•	Similarity Search: Find relevant precedent cases using AI embeddings

- Development
Running Tests
python -m pytest tests/

- Database Migrations
# PostgreSQL
alembic upgrade head

# MongoDB collections are created automatically
Training Custom Models

# Train LegalBERT (requires court data)
Contact me for more information – mocktrialapp@gmail.com

# Test model performance
Contact me for more information – mocktrialapp@gmail.com

- Performance & Scaling

*** Recommended Hardware ***

•	RAM: 16GB+ (for LegalBERT model)

•	Storage: 10GB+ (for databases and models)

•	GPU: Optional (CUDA-compatible for faster LegalBERT inference)

- Production Considerations

Mock Trial AI – Community Core Edition is designed as a foundation for legal AI workflows. Deploying it in a production environment requires careful attention to both technical and legal factors.

- Technical Best Practices

•	Framework Options: Use Django or Flask for enterprise-grade services.

•	Database Optimization: Enable PostgreSQL connection pooling for efficient database performance under load.

•	Caching: Implement Redis for session caching and faster response times.

•	Containerization: Deploy with Docker containers for consistency across environments.

Environment Management: Set up environment-specific configurations to separate dev, staging, and production.

- AI and Model Considerations (IMPORTANT!)

•	Chunking Large Documents: Break long legal filings into smaller text segments before processing with pretrained models. This avoids token limit errors and ensures comprehensive analysis. Chunking involves recursively processing large legal documents in smaller segments, ensuring pretrained models analyze the entire text despite token limits.

•	Pretrained Models for Cost Savings: Start with pretrained legal language models (e.g., LegalBERT) for preliminary analysis to minimize reliance on expensive API calls (OpenAI/Claude).

•	Agent Compartmentalization: Create specialized AI agents for each legal domain (patents, trademarks, contracts, etc.) to improve accuracy and efficiency.

•	Centralized Agent Management: Use PostgreSQL to manage these agents, their configurations, and role-based access for attorneys.

- Legal and Ethical Guidelines

•	Auditability: Require document uploads for each analysis session to create an auditable trail of inputs and outputs. This supports ethical and evidentiary standards in legal practice.

•	Attorney-Led Model Training: AI model training requires deep legal domain expertise. It is strongly recommended to involve experienced attorneys in the process rather than relying on IT staff, engineers, or data scientists. Legal professionals care about their clients and understand the nuances of legal strategy, making them essential for building effective and trustworthy legal AI systems.

- Contributing

This is the core edition with core framework and UI components. The full implementation includes:

•	Trained LegalBERT models on 100,000 + court cases

•	Real-time CourtListener, Pacer, USPTO API integration

•	Advanced PowerBI analytics dashboards

•	VR courtroom simulation components

•	Production-grade security and scaling

- Community Contributions Welcome

•	Bug fixes and improvements

•	Additional case types and forms

•	UI/UX enhancements

•	Documentation improvements

- Commercial Implementation

For access to the complete system with trained models and full datasets, please contact:

•	Email: mocktrialapp@gmail.com

•	LinkedIn: frankgarcia1

•	Website: Under construction: Please see Linkedin.

- License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

- Commercial Licensing

Commercial licenses are available for enterprise use. Contact me for pricing and terms.

- Disclaimer

The Core Edition is provided for educational and research purposes only. It does not constitute legal advice or replace professional legal counsel. Always consult qualified attorneys for legal matters.

- Support

*** Community Support ***

•	Issues: Use GitHub Issues for bug reports

•	Discussions: GitHub Discussions for questions

•	Documentation: Check the /docs folder

- Enterprise Support

Professional support, training, and contract development are available for enterprise deployments.

- Roadmap

*** Core Edition ***

•	See README.md

- Enterprise Features (Available Separately)

•	Additional case type templates

•	Improved mobile responsiveness

•	API documentation

•	Docker containerization

•	Real-time court data feeds

•	Advanced ML model ensemble

•	Multi-tenant architecture

•	VR courtroom integration

•	Advanced security features

Mock Trial AI - Transforming Legal Practice with Artificial Intelligence

***** Star this repository if you find it useful!

