# Quick Setup Guide - OpenAI Integration

## For Users (Browser-based Setup)

### Step 1: Install Dependencies
First, install the new OpenAI package:
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Get Your API Keys

#### Google Gemini (Free tier available)
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API key"
3. Copy the key

#### OpenAI (Paid service)
1. Visit: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key immediately (you won't see it again!)

### Step 3: Configure in the App
1. Start the application
2. Go to the **Settings** tab
3. Scroll to "Google Gemini API Configuration"
   - Paste your Gemini API key
   - Click "Apply"
4. Scroll to "OpenAI API Configuration"
   - Paste your OpenAI API key
   - Click "Apply"

### Step 4: Use the AI Assistant
1. Go to the **Code** tab
2. In the AI Assistant sidebar (right side):
   - Select your preferred **AI Provider** (Google Gemini or OpenAI)
   - Select your desired **Model**
3. Start chatting!

## For Developers (Docker Setup)

### Option 1: Using .env file (Recommended)
1. Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_actual_gemini_key_here
OPENAI_API_KEY=your_actual_openai_key_here
```

2. Make sure `.env` is in your `.gitignore`:
```
.env
```

3. Start with docker-compose:
```bash
docker-compose up --build
```

### Option 2: Using environment variables
```bash
export GOOGLE_API_KEY="your_actual_gemini_key_here"
export OPENAI_API_KEY="your_actual_openai_key_here"
docker-compose up --build
```

## Model Comparison

### When to Use Gemini
- ✅ Free tier available (generous limits)
- ✅ Good for testing and development
- ✅ Supports image analysis
- ✅ Fast response times with flash-lite
- 💰 Cost: Free tier, then pay-per-use

**Best for**: General development, prototyping, image analysis

### When to Use OpenAI
- ✅ Consistent, high-quality responses
- ✅ Well-documented and widely supported
- ✅ GPT-4o offers best reasoning
- ❌ No free tier (all usage is paid)
- 💰 Cost: Pay-per-token (gpt-4o-mini is most affordable)

**Best for**: Production applications, complex reasoning tasks

## Recommended Model Choices

### For Daily Development
- **Gemini**: `gemini-2.5-flash-lite` (fast, free)
- **OpenAI**: `gpt-4o-mini` (fast, affordable)

### For Complex Tasks
- **Gemini**: `gemini-2.5-pro` (best quality)
- **OpenAI**: `gpt-4o` or `gpt-4.1` (highest intelligence)

## Cost Estimates (OpenAI)

### gpt-4o-mini
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- **Best for**: Most use cases, very affordable

### gpt-4o
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- **Best for**: Complex reasoning, highest quality

### gpt-4.1 / gpt-4.1-mini
- Similar pricing to gpt-4o variants
- Latest models with improved capabilities

*Note: Prices as of 2026-01. Check OpenAI's pricing page for current rates.*

## Troubleshooting

### "API key required" error
- Make sure you've entered the API key in Settings
- Check that you selected the correct provider
- Try clicking "Apply" again

### "Invalid API key" error
- Double-check you copied the entire key (no spaces)
- Gemini keys start with: `AIza...`
- OpenAI keys start with: `sk-...`
- Try generating a new key

### Model not working
- Ensure you have the correct provider selected
- Some models may not be available in all regions
- Check your API account has access to the model

### Rate limiting
- Gemini: Free tier has generous limits
- OpenAI: Check your usage limits and billing
- Consider upgrading your API plan if needed

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use .env files** for local development (add to .gitignore)
3. **Use environment variables** in production
4. **Rotate keys regularly** if they may have been exposed
5. **Set usage limits** in your API provider's dashboard

## Getting Help

- Check the `OPENAI_INTEGRATION.md` for technical details
- Visit the respective API documentation:
  - [Google Gemini Docs](https://ai.google.dev/docs)
  - [OpenAI API Docs](https://platform.openai.com/docs)
