# DeltaP Discord Bot

A Discord bot for managing and tracking pledge points in a fraternity/organization setting. DeltaP automates point tracking, provides leaderboards, and includes administrative commands for managing the system.

[![Tests](https://github.com/warnervance/DeltaP/actions/workflows/tests.yml/badge.svg)](https://github.com/warnervance/DeltaP/actions/workflows/tests.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)](htmlcov/index.html)

## Features

### Point Management
- **Point Submissions**: Brothers can submit points for pledges with comments
- **Smart Parsing**: Accepts various formats like `+10 Eli Great job` or `+10 to Eli for great work`
- **Float Support**: Automatically rounds float values to integers (e.g., `+10.7` → `11`)
- **Nickname Aliases**: Recognizes common nicknames and maps them to official names
- **Validation**: Ensures only valid pledge names and point values are accepted

### Point Tracking
- **Approval System**: Point submissions require admin approval before counting
- **Rankings**: View real-time leaderboards with medal emojis for top 3
- **History**: Track all point entries with timestamps and comments
- **Filtering**: View pending, approved, or rejected points

### Administrative Features
- **Approve/Reject**: Admins can review and approve or reject point submissions
- **Delete Messages Logging**: Tracks deleted messages in a dedicated channel
- **Role-based Permissions**: Certain commands restricted to Info Systems role
- **Remote Shutdown**: Secure bot shutdown with permission checks
- **Ping Command**: Check bot responsiveness and latency

## Installation

### Prerequisites

1. Install UV (Python Package Manager)

On Mac and Linux:

```bash

curl -LsSf https://astral.sh/uv/install.sh | sh
```

UV will install the needed Python version and dependencies when needed.

2. Install Git

Use whatever package manager you prefer for your OS.

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/warnervance/DeltaP.git
   cd DeltaP
   ```

2. **Install dependencies using uv**
   ```bash
   uv sync
   ```

3. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   # Discord Bot Configuration
   DISCORD_TOKEN=your_discord_bot_token_here

   # Database Configuration
   CSV_NAME=pledge_points.db
   TABLE_NAME=pledge_points

   # Discord Channel Configuration
   CHANNEL_ID=your_points_submission_channel_id
   ```

Get details from Warner.

4. **Update pledge configuration**

   Edit `PledgePoints/constants.py` to add current semester pledges:
   ```python
   VALID_PLEDGES: List[str] = [
       "Joe",
       "Yo",
       # ... add your pledges
   ]

   PLEDGE_ALIASES: Dict[str, str] = {
       "Matt": "Matthew",
       # ... add nickname mappings
   }
   ```

5**Run the bot**
   ```bash
   uv run python main.py
   ```

The sqlite database will be created in the project root automatically.
## Development

### Project Structure

```
DeltaP/
├── commands/           # Bot command modules
│   ├── admin.py       # Administrative commands
│   └── points.py      # Point management commands
├── config/            # Configuration management
│   └── settings.py    # Environment and config loading
├── PledgePoints/      # Core business logic
│   ├── constants.py   # Pledge names, aliases, constants
│   ├── models.py      # Data models
│   ├── validators.py  # Input validation and parsing
│   ├── sqlutils.py    # Database operations
│   ├── pledges.py     # Pledge-specific logic
│   └── messages.py    # Message handling
├── role/              # Role checking utilities
│   └── role_checking.py
├── utils/             # Shared utilities
│   └── discord_helpers.py  # Discord formatting helpers
├── tests/             # Comprehensive test suite
│   ├── commands/
│   ├── config/
│   ├── PledgePoints/
│   └── utils/
├── main.py            # Bot entry point
├── pytest.ini         # Test configuration
└── pyproject.toml     # Project dependencies
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov

# Run specific test file
uv run pytest tests/PledgePoints/test_validators.py

# Run with verbose output
uv run pytest -v
```

## Database Schema

The bot uses SQLite with the following schema:

```sql
CREATE TABLE pledge_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT NOT NULL,
    brother TEXT NOT NULL,
    point_change INTEGER NOT NULL,
    pledge TEXT NOT NULL,
    comment TEXT NOT NULL,
    approval_status TEXT DEFAULT 'pending',
    approved_by TEXT,
    approval_timestamp TEXT
);
```

## Configuration

### Pledge Configuration

Update `PledgePoints/constants.py` each semester:

- `VALID_PLEDGES` - List of valid pledge names
- `PLEDGE_ALIASES` - Nickname to official name mapping
- `RANK_MEDALS` - Emoji medals for rankings
- `POINT_REGEX_PATTERN` - Point parsing regex


### Role Permissions

Configure in `role/role_checking.py`:

- Info Systems role ID for admin commands
- Custom role checks as needed

### Code Style

- Follow PEP 8 guidelines
- Add docstrings to all functions and classes
- Write tests for new features
- Maintain or improve code coverage


**Note**: Remember to update `VALID_PLEDGES` in `PledgePoints/constants.py` at the start of each semester!
