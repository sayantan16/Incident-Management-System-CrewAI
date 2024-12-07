# Incident Management System CrewAI – Installation Guide (macOS & Windows)

Welcome to the **Incident Management System CrewAI** project, powered by [CrewAI](https://crewai.com) & [LangGraph](https://www.langchain.com/langgraph).  
This guide will help you set up and run the project on **macOS** or **Windows** systems, leveraging CrewAI's powerful framework & LangGraph's orchestration for incident management.

---

## 1. Download the Code

Download the repository from GitHub:

🔗 [Incident Management System CrewAI](https://github.com/sayantan16/Incident-Management-System-CrewAI)

---

## 2. Create an `.env` File

In the root folder of the project, create a file named `.env` with the following content:

```plaintext
MODEL=
OPENAI_API_KEY=
EXA_API_KEY=
```

Replace the placeholders with your actual API keys.

---

## 3. Install CrewAI

### **macOS:**

```bash
pip install crewai
```

### **Windows:**

Open **Command Prompt** or **PowerShell** and run:

```cmd
pip install crewai
```

---

## 4. Install Project Dependencies

### **macOS & Windows:**

Run the following command to install all project dependencies:

```bash
crewai install
```

---

## 5. Activate the Virtual Environment

### **macOS:**

```bash
source .venv/bin/activate
```

### **Windows:**

```cmd
.\venv\Scripts\activate
```

---

## 6. Run the CrewAI Application

### **macOS & Windows:**

Start the CrewAI application:

```bash
crewai run
```

---

## 7. Set Up MailHog for SMTP Testing

### **macOS:**

1. **Install MailHog** using Homebrew:

   ```bash
   brew install mailhog
   ```

2. **Run MailHog**:

   ```bash
   mailhog
   ```

### **Windows:**

1. **Download MailHog**:

   - Go to the [MailHog Releases Page](https://github.com/mailhog/MailHog/releases) and download the latest `.exe` file for Windows.

2. **Run MailHog**:

   Open a Command Prompt in the folder where `MailHog.exe` is located and run:

   ```cmd
   MailHog.exe
   ```

MailHog will be accessible at: [http://0.0.0.0:8025/](http://0.0.0.0:8025/)

---

## 8. Important Points for Running the Application

### 1. **Initial Logs Check**

After running `crewai run`, wait to see the following logs in the terminal:

```plaintext
Running the Crew
# Monitoring logs
## No new logs
## No new logs
## Waiting for 60 seconds
```

---

### 2. **Add Sample Log Files**

Place a sample log file from:

```plaintext
src/incident_management_crewai/bkup_data
```

into the `data` folder located at:

```plaintext
src/incident_management_crewai/data
```

---

### 3. **Processing Notifications**

The agent will process the log files, and notifications will appear in MailHog at:

[http://0.0.0.0:8025/](http://0.0.0.0:8025/)

---

### 4. **Continuous Monitoring**

- The agent continuously monitors the `data` folder.
- For testing, keep placing multiple log files in the `data` folder.
- To stop the agent, interrupt the process in the terminal

---