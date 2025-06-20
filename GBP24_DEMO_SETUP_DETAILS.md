# GitBridge Phase 24 Demo Setup Details
**For:** Lukas Stakeholder Showcase  
**Date:** 2025-06-20  
**Status:** Verified and Ready ✅

---

## 🔍 Exact File Locations

### **Primary Launch Script**
- **File:** `app.py`
- **Full Path:** `/Users/zach/GitBridgev1/app.py`
- **Purpose:** Main Flask application entry point

### **Demo Landing Page**
- **File:** `demo_landing.html`
- **Full Path:** `/Users/zach/GitBridgev1/demo_landing.html`
- **Purpose:** Interactive landing page with "Start Demo" button

### **Demo Protocol Documentation**
- **File:** `GBP24_DEMO_PROTOCOL.md`
- **Full Path:** `/Users/zach/GitBridgev1/GBP24_DEMO_PROTOCOL.md`
- **Purpose:** Complete demo instructions and flow

### **Demo Data Script**
- **File:** `phase24_demo.py`
- **Full Path:** `/Users/zach/GitBridgev1/phase24_demo.py`
- **Purpose:** Generates demo data and runs standalone demo

---

## ✅ Verified Step-by-Step Startup Instructions

### **Prerequisites Check**
```bash
# Verify Python version (must be 3.13.3)
python --version
# Expected output: Python 3.13.3

# Verify current directory
pwd
# Expected output: /Users/zach/GitBridgev1
```

### **Step 1: Navigate to Project Directory**
```bash
cd /Users/zach/GitBridgev1
```

### **Step 2: Start the Flask Server**
```bash
python app.py
```

### **Expected Success Output:**
```
2025-06-20 XX:XX:XX - __main__ - INFO - Starting GitBridge Phase 24 server on port 5000
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://0.0.0.0:5000
```

### **Step 3: Open Browser**
**Option A: Manual Browser Opening**
```bash
open http://localhost:5000
```

**Option B: Direct Landing Page**
```bash
open /Users/zach/GitBridgev1/demo_landing.html
```

---

## 🌐 Browser and Port Details

### **Default Configuration**
- **Host:** `0.0.0.0` (accessible from any network interface)
- **Port:** `5000`
- **URL:** `http://localhost:5000`
- **Health Check:** `http://localhost:5000/health`

### **Auto-Open Behavior**
- **Flask App:** Does NOT auto-open browser
- **Landing Page:** Manual opening required
- **WebSocket:** Auto-connects when dashboard loads

### **Browser Compatibility**
- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

---

## 📁 Directory Map

```
/Users/zach/GitBridgev1/
├── app.py                          # 🚀 MAIN LAUNCH SCRIPT
├── demo_landing.html               # 🎨 LANDING PAGE
├── GBP24_DEMO_PROTOCOL.md          # 📋 DEMO INSTRUCTIONS
├── phase24_demo.py                 # 🧪 DEMO DATA GENERATOR
├── webui/
│   ├── templates/
│   │   ├── dashboard.html          # 📊 MAIN DASHBOARD
│   │   └── attribution_overview.html
│   └── routes.py                   # 🔗 WEB ROUTES
├── mas_core/                       # 🧠 CORE LOGIC
│   ├── attribution.py
│   ├── changelog.py
│   ├── diff_viewer.py
│   ├── activity_feed.py
│   └── task_display.py
├── attribution_data/               # 💾 ATTRIBUTION STORAGE
├── changelog_data/                 # 📝 CHANGELOG STORAGE
├── activity_data/                  # 📈 ACTIVITY STORAGE
├── demo_outputs/                   # 📤 EXPORT FILES
├── logs/                           # 📋 LOG FILES
└── requirements-frozen.txt         # 📦 DEPENDENCIES
```

---

## 🚀 Quick Start Commands

### **For Presenter (Copy-Paste Ready):**
```bash
# 1. Navigate to project
cd /Users/zach/GitBridgev1

# 2. Start server
python app.py

# 3. In new terminal or browser, open:
open http://localhost:5000
```

### **For Demo Data Generation (Optional):**
```bash
# Generate demo data
python phase24_demo.py

# Expected output: Demo completed with 558+ contributors
```

---

## 🔧 Troubleshooting

### **Port Already in Use**
```bash
# Check what's using port 5000
lsof -i :5000

# Kill process if needed
kill -9 <PID>
```

### **Python Version Issues**
```bash
# Use specific Python version
python3.13 app.py

# Or check available versions
which python
which python3
```

### **Permission Issues**
```bash
# Ensure execute permissions
chmod +x app.py
chmod +x phase24_demo.py
```

### **Missing Dependencies**
```bash
# Install requirements
pip install -r requirements-frozen.txt
```

---

## 📊 Demo Verification Checklist

### **Pre-Demo Checks**
- [ ] Python 3.13.3 installed and accessible
- [ ] Current directory is `/Users/zach/GitBridgev1`
- [ ] Port 5000 is available
- [ ] All files present in expected locations

### **Startup Verification**
- [ ] `python app.py` runs without errors
- [ ] Server starts on port 5000
- [ ] `http://localhost:5000` loads dashboard
- [ ] WebSocket connection established
- [ ] Demo data visible (558+ contributors)

### **Demo Features Verification**
- [ ] Real-time activity feed updates
- [ ] Agent avatars display correctly
- [ ] Attribution data shows for tasks
- [ ] Export functions work
- [ ] Diff viewer renders properly

---

## 🎯 Presenter Script Integration

### **Opening Lines for Presenter:**
> "Welcome to GitBridge Phase 24. I'll start by launching our collaboration engine. First, I'll navigate to our project directory and start the server..."

### **Commands to Execute Live:**
```bash
cd /Users/zach/GitBridgev1
python app.py
```

### **What Lukas Should See:**
1. **Terminal:** Server startup messages
2. **Browser:** Dashboard loading with collaboration stats
3. **Real-time:** Activity feed populating with agent actions

---

## 📞 Emergency Contacts

### **If Demo Fails:**
1. **Check logs:** `tail -f logs/gitbridge.log`
2. **Restart server:** `Ctrl+C` then `python app.py`
3. **Verify data:** `python phase24_demo.py --verify`

### **Backup Options:**
- **Standalone demo:** `python phase24_demo.py`
- **Landing page only:** Open `demo_landing.html` directly
- **Documentation:** Reference `GBP24_DEMO_PROTOCOL.md`

---

**✅ All paths and commands verified and tested successfully!**

*This document provides exact, tested instructions for a flawless Lukas demo experience.* 