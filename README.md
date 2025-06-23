
# Proposal Agents

An intelligent proposal generation platform that uses AI agents and Retrieval-Augmented Generation (RAG) to help organizations create high-quality technical proposals for RFQs (Request for Quotations).

## Key Features

**🤖 Multi-Agent Architecture**
- **Structure Agent**: Analyzes user queries to determine proposal type and structure
- **RAG Agent**: Retrieves relevant information from uploaded documents to generate contextual proposals
- **Reflexion Agent**: Provides critique and iterative improvement with human-in-the-loop feedback
- **Human Feedback Loop**: Interactive review and revision process

**📄 Document Processing**
- Upload PDF files and web links for knowledge ingestion
- Automatic text extraction and metadata generation
- Multi-tenant document storage with user isolation
- Intelligent prompt suggestions based on uploaded content

**🔍 Advanced RAG System**
- LightRAG integration for sophisticated document retrieval
- Multiple query modes (local, global, hybrid)
- Context-aware proposal generation using structured prompts
- Source document tracking and citation

**🔐 Authentication & Multi-Tenancy**
- Google OAuth integration for secure user authentication
- Isolated database and workspace per user
- Session management with secure cookie handling

**☁️ Google Workspace Integration**
- Save generated proposals directly to Google Docs
- Automatic folder organization by date
- Template-based document creation

**📊 Dashboard & Analytics**
- Recent RFQ tracking and management
- Proposal history and winning proposals view
- Activity monitoring and search functionality

**🌐 Modern Web Interface**
- Next.js frontend with TypeScript
- Real-time chat interface for proposal generation
- File upload with drag-and-drop support
- Responsive design with modern UI components

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript/React)
- **Database**: PostgreSQL with SQLAlchemy
- **AI/ML**: OpenAI GPT-4, LangChain, LightRAG
- **Authentication**: Google OAuth
- **Cloud Integration**: Google Drive/Docs APIs

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL database
- Google OAuth credentials
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd proposal-agents
```

2. Install Python dependencies:
```bash
pip install -r src/requirements.txt
```

3. Install Node.js dependencies:
```bash
cd src/UI
npm install
```

4. Set up environment variables:
```bash
# Create .env file with required variables
OPENAI_API_KEY=your_openai_key
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
DATABASE_URL=your_postgresql_url
```

5. Run the backend server:
```bash
cd src
python main.py
```

6. Run the frontend development server:
```bash
cd src/UI
npm run dev
```

## Usage

1. **Authentication**: Sign in with your Google account
2. **Upload Documents**: Add RFQ documents and reference materials
3. **Generate Proposals**: Use the chat interface to create tailored proposals
4. **Review & Refine**: Leverage the reflexion agent for iterative improvements
5. **Export**: Save final proposals to Google Docs

## Project Structure

```
src/
├── UI/                     # Next.js frontend
├── rag_agent/             # RAG implementation
├── structure_agent/       # Proposal structure analysis
├── reflexion_agent/       # Critique and improvement
├── google_doc_integration/ # Google Workspace integration
├── database/              # Database models and helpers
├── multi_tenant/          # User management
└── main.py               # FastAPI server
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or support, please open an issue in the repository or contact the development team.

---

This system streamlines the proposal creation process by combining AI intelligence with human expertise, making it easier for organizations to respond to RFQs with well-structured, contextually relevant proposals.
