# API Key Setup Instructions

This guide explains how to set up API keys for AI-powered report generation.

## Supported AI Providers

The system supports two AI providers:
- **OpenAI** (GPT-4, GPT-4 Turbo)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus)

## Option 1: Using OpenAI

### Step 1: Get an OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the API key (you won't be able to see it again!)

### Step 2: Set Environment Variable

#### Linux/macOS (bash/zsh):
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

To make it permanent, add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.zshrc

source ~/.bashrc
```

#### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

To make it permanent (PowerShell):
```powershell
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-your-api-key-here', 'User')
```

#### Using .env file (Recommended):
Create a `.env` file in the project root:
```
OPENAI_API_KEY=sk-your-api-key-here
```

Then load it in your Python code:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Step 3: Verify Setup

```python
import os
print(os.getenv("OPENAI_API_KEY"))  # Should print your key (be careful!)
```

## Option 2: Using Anthropic

### Step 1: Get an Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to [API Keys](https://console.anthropic.com/settings/keys)
4. Click "Create Key"
5. Copy the API key

### Step 2: Set Environment Variable

#### Linux/macOS:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
```

Add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
```

#### Using .env file:
```
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

## Option 3: Pass API Key Directly in Code

You can also pass the API key directly when initializing the service:

```python
from pdf_generator.ai_service import AIService, AIProvider

# OpenAI
ai_service = AIService(
    provider=AIProvider.OPENAI,
    api_key="sk-your-api-key-here"
)

# Anthropic
ai_service = AIService(
    provider=AIProvider.ANTHROPIC,
    api_key="sk-ant-your-api-key-here"
)
```

**Note:** This is less secure and not recommended for production. Use environment variables instead.

## Security Best Practices

1. **Never commit API keys to version control**
   - Add `.env` to `.gitignore`
   - Never commit files with hardcoded keys

2. **Use environment variables**
   - Prefer environment variables over hardcoded keys
   - Use `.env` files for local development (and add to `.gitignore`)

3. **Rotate keys regularly**
   - If a key is exposed, revoke it immediately
   - Generate new keys periodically

4. **Set usage limits**
   - Configure usage limits in your provider's dashboard
   - Monitor usage to detect unexpected activity

## Testing Your Setup

Run this test script to verify your API key is working:

```python
from pdf_generator.ai_service import AIService, AIProvider
import os

# Test OpenAI
try:
    service = AIService(provider=AIProvider.OPENAI)
    print("✅ OpenAI API key is configured correctly")
except ValueError as e:
    print(f"❌ OpenAI API key error: {e}")

# Test Anthropic
try:
    service = AIService(provider=AIProvider.ANTHROPIC)
    print("✅ Anthropic API key is configured correctly")
except ValueError as e:
    print(f"❌ Anthropic API key error: {e}")
```

## Troubleshooting

### Error: "OPENAI_API_KEY environment variable not set"

**Solution:** Make sure you've set the environment variable:
```bash
export OPENAI_API_KEY="sk-your-key"
```

Or use a `.env` file and load it with `python-dotenv`.

### Error: "Invalid API key"

**Solution:**
1. Verify the key is correct (no extra spaces)
2. Check if the key has expired or been revoked
3. Ensure you're using the correct provider's key format

### Error: "Rate limit exceeded"

**Solution:**
1. Wait a few minutes and try again
2. Upgrade your API plan for higher rate limits
3. Implement retry logic with exponential backoff

### Error: "Insufficient credits"

**Solution:**
1. Add credits to your OpenAI/Anthropic account
2. Check your billing settings

## Cost Considerations

### OpenAI Pricing (as of 2024):
- GPT-4o: ~$2.50-$10 per 1M input tokens, ~$10-$30 per 1M output tokens
- GPT-4 Turbo: ~$10 per 1M input tokens, ~$30 per 1M output tokens

### Anthropic Pricing (as of 2024):
- Claude 3.5 Sonnet: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- Claude 3 Opus: ~$15 per 1M input tokens, ~$75 per 1M output tokens

**Estimated cost per report:** ~$0.01-$0.05 depending on model and report complexity.

## Next Steps

Once your API key is set up, you can use the AI-powered report generator:

```python
from pdf_generator.report_generator import ReportGenerator
from pdf_generator.ai_service import AIProvider
from pdf_generator.enhanced_pdf_builder import EnhancedPDFBuilder

# Generate report from raw data
generator = ReportGenerator(ai_provider=AIProvider.OPENAI)
complete_report = generator.generate_complete_report(raw_weather_data)

# Generate PDF
pdf_builder = EnhancedPDFBuilder(complete_report)
pdf_path = pdf_builder.generate("output/report.pdf")
```

See `generate_ai_sample.py` for a complete example.
