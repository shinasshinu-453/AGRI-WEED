# Roboflow Integration Configuration

## Add these to your .env file:

```
# Roboflow Configuration
ROBOFLOW_API_KEY=your_roboflow_api_key_here
ROBOFLOW_WORKSPACE=your_workspace_name_here
ROBOFLOW_PROJECT=weed-ryn8z
ROBOFLOW_VERSION=1
```

## Where to get these values:

1. **ROBOFLOW_API_KEY**: 
   - Go to https://app.roboflow.com/settings/api
   - Copy your **Private API Key**

2. **ROBOFLOW_WORKSPACE**:
   - When you're logged into Roboflow, look at the URL
   - Format: `https://app.roboflow.com/YOUR_WORKSPACE/...`
   - Copy the workspace name from the URL

3. **ROBOFLOW_PROJECT**:
   - Already set to `weed-ryn8z` (your project)

4. **ROBOFLOW_VERSION**:
   - The version of your model (default is 1)

## After adding these:
1. Restart your backend server
2. The system will use Roboflow instead of Gemini for crop detection
