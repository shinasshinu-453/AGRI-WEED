# Remote Access Setup with Ngrok

## Quick Start (Without Authentication)

1. **Install pyngrok:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start server with ngrok:**
   ```bash
   python server.py --ngrok
   ```

3. **Copy the public URL** from the console output and share it with anyone!

---

## With Ngrok Account (Recommended)

For better reliability and custom subdomains, create a free ngrok account:

1. **Sign up at:** https://ngrok.com/signup
2. **Get your auth token:** https://dashboard.ngrok.com/auth/your-authtoken
3. **Set environment variable:**

   **Windows (PowerShell):**
   ```powershell
   $env:NGROK_AUTH_TOKEN="your-token-here"
   python server.py --ngrok
   ```

   **Windows (CMD):**
   ```cmd
   set NGROK_AUTH_TOKEN=your-token-here
   python server.py --ngrok
   ```

   **Linux/Mac:**
   ```bash
   export NGROK_AUTH_TOKEN="your-token-here"
   python server.py --ngrok
   ```

---

## Access Methods

| Method | URL | Range |
|--------|-----|-------|
| **Local** | `http://localhost:5000` | Same device only |
| **Network** | `http://<your-ip>:5000` | Same WiFi network |
| **Ngrok** | Check console output | **Anywhere in the world** |

---

## Example Output

```
============================================================
🌐 NGROK TUNNEL ACTIVE!
============================================================
🔗 Public URL: https://abc123-45.ngrok.io
📱 Share this link to access from any device!
============================================================

Starting Flask server on http://0.0.0.0:5000
Local access: http://localhost:5000
Network access: http://<your-ip>:5000
```

Share the **Public URL** with anyone to access your app remotely!

---

## Troubleshooting

- **"pyngrok not installed"** → Run `pip install -r requirements.txt`
- **"Connection refused"** → Make sure server is running before using ngrok
- **URL keeps changing** → Use ngrok account for static subdomains
- **Rate limited** → Ngrok free tier has limits; upgrade for more
