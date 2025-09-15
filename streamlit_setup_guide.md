# Streamlit Cloud Setup Guide

## Environment Variables Required

You need to set these environment variables in Streamlit Cloud:

### Database Configuration (Neon PostgreSQL)
```
DB_HOST = ep-hidden-rain-adlq7a8p-pooler.c-2.us-east-1.aws.neon.tech
DB_PORT = 5432
DB_NAME = travel_assistant
DB_USER = neondb_owner
DB_PASSWORD = npg_5uoSBbv0TgDK
DB_SSLMODE = require
```

### Groq API Configuration
```
GROQ_API_KEY = gsk_your_actual_groq_api_key_here
```

## How to Set Environment Variables in Streamlit Cloud

1. Go to your Streamlit Cloud dashboard
2. Click on your travel app
3. Click "Manage app"
4. Go to "Settings" tab
5. Scroll down to "Secrets" section
6. Add each environment variable as a key-value pair

## Alternative: Use Streamlit Secrets

You can also create a `.streamlit/secrets.toml` file in your repository with:

```toml
[secrets]
DB_HOST = "ep-hidden-rain-adlq7a8p-pooler.c-2.us-east-1.aws.neon.tech"
DB_PORT = "5432"
DB_NAME = "travel_assistant"
DB_USER = "neondb_owner"
DB_PASSWORD = "npg_5uoSBbv0TgDK"
DB_SSLMODE = "require"
GROQ_API_KEY = "gsk_your_actual_groq_api_key_here"
```

## Troubleshooting

- Make sure all environment variables are set exactly as shown above
- The Groq API key should start with `gsk_`
- Database credentials should match your Neon database exactly
- After setting variables, reboot your app
