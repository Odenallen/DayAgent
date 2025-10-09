# DayAgent 🤖

A sophisticated AI-powered personal assistant that creates comprehensive daily briefings by integrating calendar events, emails, weather forecasts, transportation routes, and location data into beautifully formatted markdown reports.

## 🌟 Introduction

DayAgent is an intelligent automation system designed to streamline your daily routine by automatically collecting and organizing all essential information you need for the day. It leverages multiple MCP (Model Context Protocol) servers and AI agents to gather data from various sources and generate personalized daily briefings.

The system checks your calendar events, retrieves new emails, calculates transportation routes between locations, fetches weather forecasts, and compiles everything into a readable markdown format that can be easily converted to PDF or shared via email.

## 🧠 What are MCP Servers?

MCP (Model Context Protocol) servers are specialized services that provide tools and resources to AI agents through a standardized protocol. They act as bridges between AI systems and external data sources or services. In DayAgent, we utilize multiple MCP servers to access different APIs and services seamlessly.

### 🛠️ MCP Servers Used in DayAgent

1. **Google Calendar MCP Server** (`@cocal/google-calendar-mcp`)
   - Purpose: Fetches your calendar events for today
   - Provides: Event details including times, locations, and descriptions
   - Auth: Requires `google_keys.json` and `token.json` for OAuth2

2. **Google Maps MCP Server** (`mcp/google-maps`)
   - Purpose: Calculates public transportation routes and travel times
   - Provides: Transit directions, travel durations, and route details
   - Auth: Requires Google Maps API key

3. **Gmail MCP Server** (`@gongrzhe/server-gmail-autoauth-mcp`)
   - Purpose: Retrieves your daily unread emails
   - Provides: Email subjects, senders, and brief content summaries
   - Auth: Uses auto-authentication with Google credentials

4. **Weather MCP Server** (`weatherxm-pro`)
   - Purpose: Fetches accurate weather forecasts
   - Provides: Hourly temperature and precipitation data
   - Auth: Requires WeatherXM Pro API key

5. **Time MCP Server** (`mcp-server-time`)
   - Purpose: Handles timezone conversions and date/time operations
   - Provides: Current time information for scheduling

6. **Markdown-to-PDF MCP Server** (`md-pdf-mcp`)
   - Purpose: Converts generated markdown reports to PDF format
   - Provides: Document generation capabilities
   - Setup: Requires local MCP server installation

## 📁 File Structure

```
DayAgent/
├── app/
│   ├── bot.py                 # Main agent logic and LangGraph workflow
│   ├── classStructs.py        # Data models and type definitions
│   ├── my_mcp.py              # MCP configuration loader
│   ├── user_conf/
│   │   └── config.json        # User configuration file
│   ├── templates/
│   │   ├── email-template.md  # Jinja2 template for daily briefs
│   │   └── prompts.py         # LLM prompts for different tasks
│   ├── mcp_config.json        # MCP server definitions and settings
│   ├── google_keys.json       # Google OAuth2 credentials
│   └── token.json            # Google authentication tokens
├── result/
│   ├── results.json           # Generated data from each run
│   └── generatedMD.md       # Final markdown output
├── main.py                    # Entry point - runs async bot main function
├── pyproject.toml            # Project dependencies (using uv)
├── uv.lock                   # Locked dependencies
├── .python-version          # Python version specification
└── .gitignore               # Git ignore rules
```

## ⚙️ Configuration

### User Settings (`app/user_conf/config.json`)
```json
{
    "name": "Your Name",
    "location": "Stockholm",
    "work_location": [{"address": "Address", "city": "City", "postal code": "123 45"}],
    "home_location": [{"address": "Home Address", "city": "City", "postal code": "123 45"}],
    "dentist_location": [{"address": null, "city": null, "postal code": null}],
    "calendar_ids": null,
    "local_weather_station": null,
    "default_meeting_location": null
}
```

### Authentication Files
- **Google OAuth Credentials** (`app/google_keys.json`): OAuth2 client credentials from Google Cloud Console
- **Google Auth Token** (`app/token.json`): Generated authentication tokens (auto-created after first login)

### MCP Server Configuration (`app/mcp_config.json`)
The MCP servers are configured with specific environment variables, API keys, and OAuth credentials. Each server requires appropriate authentication tokens and API keys to function properly.

## 🔧 How It Works

### Core Architecture
DayAgent uses a **LangGraph-based workflow** that orchestrates multiple AI agents to gather and process daily information:

1. **DataCollector Agent**: Fetches data from various sources using MCP tools
2. **ContentProcessor Agent**: Processes and formats the collected data
3. **PDFGenerator Agent**: Converts markdown output to PDF (optional)

### Workflow Process

The agent follows this sequential process:

1. **Configuration Loading**: Reads user settings and MCP configurations
2. **Calendar Check**: Retrieves today's events with times and locations
3. **Email Retrieval**: Fetches new unread emails from today
4. **Transportation Planning**: Calculates routes between event locations
5. **Weather Forecast**: Gets hourly weather data for the user's location
6. **Data Processing**: Compiles all information into structured format
7. **Template Rendering**: Generates final markdown report using Jinja2
8. **Output Generation**: Saves results as JSON and markdown files

### Key Components

#### **DataCollector Class**
Handles all data collection through MCP tools:
- `setLLM()`: Configures language models with MCP tool integration
- `check_calender()`: Calendar events retrieval
- `transportation_node()`: Public transit route calculation
- `mail_node()`: Email fetching and formatting
- `weather_node()`: Weather data collection
- `saveConf()`: Data persistence

#### **ContentProcessor Class**
Processes and formats the collected data:
- `generate_md()`: Renders Jinja2 template with collected data
- `load_template_from_file()`: Loads email template
- Template supports dynamic calendar events with integrated transportation info

#### **State Management**
Uses LangGraph's MemorySaver for conversation history and state management throughout the workflow.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- uv (modern Python package manager)
- Node.js and npm (for MCP servers)
- Docker (for Google Maps MCP server)
- Required API keys and OAuth credentials

### Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd DayAgent

# Install dependencies using uv
uv sync

# Install MCP dependencies
npm install -g @cocal/google-calendar-mcp
npm install -g @gongrzhe/server-gmail-autoauth-mcp

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and credentials

# Configure MCP servers
# Edit app/mcp_config.json with your settings

# Set up user configuration
# Edit app/user_conf/config.json with your personal details
```

### Running the Agent
```bash
# Install dependencies using uv
uv sync

# Run the agent
python main.py
```

## 🔐 Authentication & Security

### Google OAuth Setup
The Google Calendar and Gmail integrations require proper OAuth2 credentials:
1. Set up Google Cloud Console project
2. Enable Google Calendar API and Gmail API
3. Create OAuth2 credentials for a web application
4. Configure OAuth consent screen with appropriate scopes
5. Store credentials in `app/google_keys.json` in the format:
```json
{
  "installed": {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret"
  }
}
```
6. On first run, you'll be prompted to authorize via browser - credentials are saved to `app/token.json`

### API Keys
Required API keys for different services:
- Google Maps API key for transportation routing
- WeatherXM Pro API key for weather data
- MCP server environment variables

## 🎯 Features

### ✅ Implemented
- Calendar event retrieval with location integration and smart formatting
- Email fetching with content formatting and filtering
- Public transportation routing with detailed instructions
- Weather forecast gathering with hourly data
- Markdown template rendering with Jinja2
- Data persistence in JSON format
- Async/await architecture for better performance
- LangGraph-based workflow orchestration



## 🐛 Error Handling

The system includes comprehensive error handling for:
- MCP server connection failures
- API rate limiting
- Authentication issues
- Missing data scenarios
- Template rendering errors

## 📊 Output Examples

### Daily Brief Format
```markdown
# Daily Brief - 2025-10-09

## 📅 Today's Schedule

****: Take care of Mom
  - Location: Bjulevägen 19, 122 41 Enskede, Sverige
  - Travel: **Route 1:**
*   **Departure:** Kungsholms Strand 159, Stockholm
*   **Arrival:** Bjulevägen 19, 122 41 Enskede, Sverige
*   **Total Travel Time:** 52 minutes
*   **Instructions:**
    1.  Walk to S:t Eriksplan (14 mins, 0.9 km)
    2.  Take the Subway towards Hagsätra (23 mins, 10.1 km)
    3.  Walk to Bjulevägen 19, 122 41 Enskede, Sweden (15 mins, 1.1 km)

**10:15**: Team Meeting
  - Location: Stockholm Office
  - Travel: Walk 5 minutes → Bus 143

## Todays Weather Forecast.

- **11:00**: 10.92°C, precipitation 0mm
- **12:00**: 12.01°C, precipitation 0mm
- **13:00**: 13.00°C, precipitation 0mm

## 📧 Unread Emails.

- [SMR-boom article](Article about nuclear technology) - Ny Teknik Premium
- [Job alerts](New job postings) - LinkedIn Job Alerts
- [Daily.dev update](Personal update) - daily.dev
- [SALE notification](Up to 60% off) - ARKET

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for:
- New MCP server integrations
- Template improvements
- Performance optimizations
- Documentation enhancements

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with LangChain and LangGraph
- Powered by Google's Gemini AI
- Utilizing multiple advanced MCP servers
- Special thanks to the MCP ecosystem contributors

---

*DayAgent - Your intelligent daily companion that keeps you informed and organized.*
