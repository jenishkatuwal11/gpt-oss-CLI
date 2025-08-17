# gpt-oss-CLI

Efficient CLI-based LLM application with GPT-OSS-20B integration.

## Installation

1. Clone the repository:
   \\\ash
   git clone https://github.com/yourusername/gpt-oss-cli.git
   cd gpt-oss-cli
   \\\

2. Create and activate the virtual environment:
   \\\ash
   python -m venv .venv
   .\\.venv\\Scripts\\Activate # Windows
   source .venv/bin/activate # macOS/Linux
   \\\

3. Install dependencies:
   \\\ash
   pip install -e .
   \\\

4. Set up the \.env\ file from \.env.example\ and fill in your OpenRouter API key.

## Usage

### List available models:

\\\ash
python gpt-oss-CLI.py models
\\\

### Chat with the model:

\\\ash
python gpt-oss-CLI.py chat 'Tell me a joke.'
\\\

## Project Structure

\\\
gpt-oss-cli/
├── .venv/ # Virtual environment (created locally)
├── .env # Local secrets/config (not in git)
├── pyproject.toml # Project metadata & dependencies
├── README.md # Project documentation
└── gpt-oss-CLI.py # Single file for the CLI app
\\\

## License

MIT License © 2025 Your Name
