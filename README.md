# **ICLR Score Analysis & Predictor / ICLR 分数接收率分析助手 🎓**

### **Introduction**

The **ICLR Score Analysis & Predictor** is a data visualization tool designed to help researchers estimate their paper's acceptance probability based on historical data.

Waiting for the final decision after the rebuttal period can be stressful. This tool scrapes real data from **OpenReview** (e.g., ICLR 2024/2025) and analyzes how papers with similar review scores fared in the past.

### **Installation**

1. **Clone the repository:**  
   git clone https://github.com/XiaohanLei/ICLR-Score-Analysis-Predictor.git 

2. **Install dependencies:**  
   pip install streamlit pandas numpy plotly openreview-py tqdm

### **Usage**

#### **Step 1: Get the Data**

Run the crawler script to fetch the latest data from OpenReview. This will generate a CSV file.

python crawl\_iclr\_2025.py

*Note: The crawling process might take a few minutes depending on the OpenReview API speed.*

#### **Step 2: Run the Web App**

Start the Streamlit application:

streamlit run app.py

The tool will open in your default browser (usually at http://localhost:8501).

#### **Step 3: Input Your Scores**

Enter your review scores (comma-separated, e.g., 8, 6, 5, 3\) in the sidebar to see the analysis.

⚠️ **Important Note:**

The scoring scale this year differs from previous years. To get an accurate comparison with historical data, please adjust your scores accordingly (e.g., map 4 to 5, 2 to 3, etc.) before inputting them.
