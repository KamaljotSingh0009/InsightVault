# InsightVault 🩺🛡️: A Full-Stack Digital Health Archive & Predictive Analytics Platform

<img width="700" alt="Screenshot 2026-05-14 013457" src="https://github.com/user-attachments/assets/7cd4aa98-c771-4bc9-9962-dcf99904c97b" />

## 🌟 Executive Summary

InsightVault is an end-to-end intelligent health management system designed to bridge the gap between unstructured medical reports and proactive health analytics. Built as a full-stack Django application, it allows patients to securely store, visualize, and analyze their medical history.

The platform utilizes **Generative AI (Google Gemini)** to extract structured clinical data from uploaded physical reports and employs a customized **Machine Learning pipeline (Random Forest)** to predict chronic disease risks (Diabetes & Heart Disease) based on real-time patient metrics.

### 🎥 Live Demo

> **Check it out live:** [insightvault.pythonanywhere.com](http://insightvault.pythonanywhere.com) 

## 🎨 System Overview (Screenshots)

| 📂 Dynamic Dashboard | 🧠 AI Data Extraction | 📈 Predictive ML Results |
| :---: | :---: | :---: |
|<img width="870" height="864" alt="Screenshot 2026-05-14 022939" src="https://github.com/user-attachments/assets/1ae1c0d7-4898-4e91-a40c-6698520d5ec8" />| <img width="1920" height="1080" alt="Screenshot 2026-05-14 020514" src="https://github.com/user-attachments/assets/92a2b7dc-63e1-442a-894c-6fc02b01c86a" /> |(<img width="1918" height="848" alt="Screenshot 2026-05-14 021535" src="https://github.com/user-attachments/assets/46c7643f-d8fa-4aef-86a5-748156e8b330" /> |
| *Visualizing patient health trends and active metrics.* | *Raw PDF reports rasterized and parsed into structured JSON.* | *Real-time risk assessment using independent voting trees.* |

## User Dashboard:
<img width="700" alt="Screenshot 2026-05-14 014945" src="https://github.com/user-attachments/assets/7297c865-99c3-43e7-9fcf-11e97972b8d8" />

## Doctor's Views The Trends in the Reports Parameters, Thus gives Prescriptions and can also view the Lab reports Uploaded by the User:
<img width="700" alt="Screenshot 2026-05-14 022656" src="https://github.com/user-attachments/assets/ae337832-73a0-43c4-9a38-aadb9e974622" />
<br>
<img width="700" alt="Screenshot 2026-05-14 022830" src="https://github.com/user-attachments/assets/5577db7c-e270-4af0-9530-29f58d837052" />

## ✨ Key Features

* 🤖 **AI Medical Parser:** Rasterizes uploaded PDFs into memory (`io.BytesIO`) using `PyMuPDF` and utilizes the **Google Gemini 2.5 Flash Vision API** to extract numerical lab parameters from raw unstructured reports.
* 🌲 **Predictive Risk Analytics:** Separate classification models for Heart Disease and Diabetes prediction using **Random Forest Classifier** (`n_estimators=100`) achieving **82-87% accuracy** on Heart Disease and **76-81%** on Diabetes on test splits.
* 🔒 **Multi-Tenant Architecture & Data Isolation:** Designed in Django with relational integrity (`CASCADE`, `SET_NULL`) ensuring strict data isolation between Patient and Doctor portals via dynamic ORM filtering and role-based access control.
* 📊 **Interactive Health Visualization:** Parses raw numerical data using Python's `re` module and renders visual, real-time health trend graphs (blood glucose spikes, hemoglobin trends) via **Chart.js**.
* ⚡ **Asynchronous State Management:** Utilizes background **Fetch API (AJAX)** with CSRF-tokenized headers for secure, zero-reload state updates, notably used in the 31-day Habit Tracker.

## 🛠️ Technology Stack

| **Component** | **Technologies** |
| :--- | :--- |
| **Backend Framework** | ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) |
| **Machine Learning** | ![Scikit-Learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white) ![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white) |
| **Generative AI** | ![Google Gemini](https://img.shields.io/badge/Google%20Gemini-orange?style=for-the-badge&logo=google&logoColor=white) |
| **Database** | ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white) |
| **Frontend** | ![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23F7DF1E.svg?style=for-the-badge&logo=javascript&logoColor=black) ![Bootstrap](https://img.shields.io/badge/bootstrap-%238511FA.svg?style=for-the-badge&logo=bootstrap&logoColor=white) |
| **Libraries** | Chart.js, PyMuPDF, Regular Expressions (`re`) |

## ⚙️ Technical Deep Dive (The ML & AI Engineering Flex)

### 1. Robust Machine Learning Deployment
The primary engineering challenge was transitioning from statistical models to a low-latency production environment.
* **Overfitting Prevention:** I chose Random Forest (an ensemble method) over single Decision Trees because it uses majority voting from 100 independent conditional trees, naturally preventing overfitting and ensuring highly generalized predictions on unseen, real-world patient data.
* **Lazy Loading Optimization:** Loading `.joblib` model files on every request causes severe disk I/O latency. I implemented a **Lazy Loading pattern using Python's `global` keyword**. The model is loaded into the server's RAM *only once* upon the first request. Subsequent calls fetch the model instantly from memory, reducing prediction latency to microseconds.

### 2. Fault-Tolerant AI Pipeline
* **Architecture:** To bypass disk storage and increase processing speed, physical reports are rasterized using `PyMuPDF` into a raw image buffer (`io.BytesIO`), which is fed directly to the Google Gemini Vision API.
* **Reliability Engineering:** To handle sudden Gemini API rate limits (HTTP 429 Overload errors), I engineered a recursive **3-try retry loop with exponential backoff**. Strict Prompt Engineering forces the AI to return structured, parseable JSON tokens to map numerical metrics seamlessly to the database schema.

---

## 🚀 Installation & Setup (Local Environment)

To run this project locally, ensure you have Python 3.x and Pip installed.

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/yourusername/insightvault.git](https://github.com/yourusername/insightvault.git)
    cd insightvault
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/with/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    * Create a `.env` file in the root directory and add your Google Gemini API key:
    ```bash
    GEMINI_API_KEY=your_actual_key_here
    ```

5.  **Run Database Migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Start the Server:**
    ```bash
    python manage.py runserver
    ```
    Access the platform at `http://127.0.0.1:8000/`.

---

## 🤝 Contact

**Your Name**
* **LinkedIn:** [www.linkedin.com/in/kamaljot-singh-24b35b2b2](https://www.linkedin.com/in/kamaljot-singh-24b35b2b2)
