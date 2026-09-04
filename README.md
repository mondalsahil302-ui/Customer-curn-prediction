<div align="center">

<h1>Customer Churn Prediction &amp; Lifetime Value (LTV) - Integration Pipeline</h1>

<p>
    <strong>
        Integrated ML Inference &bull;
        Neon PostgreSQL &bull;
        Change Tracking &bull;
        Scheduler &bull;
        FastAPI &bull;
        Test Console
    </strong>
</p>

<p>
    <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" alt="Python">
    <img src="https://img.shields.io/badge/XGBoost-Churn%20Prediction-green" alt="XGBoost">
    <img src="https://img.shields.io/badge/LTV-Prediction-purple" alt="LTV">
    <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/Neon-PostgreSQL-black" alt="Neon">
    <img src="https://img.shields.io/badge/SQLAlchemy-Database-red" alt="SQLAlchemy">
</p>

</div>

<hr>

<h2>Overview</h2>

<p>
This branch contains the integrated execution pipeline for the
<strong>Customer Churn Prediction &amp; Lifetime Value (LTV) Engine</strong>.
</p>

<p>
The purpose of this branch is to bring the required components together
into a runnable system. It connects customer data, Neon PostgreSQL,
change detection, preprocessing, machine learning models, scheduled
execution, FastAPI services, and controlled test-data generation.
</p>

<p>
Unlike the <strong>machine-learning</strong> branch, which focuses on
model experimentation and comparison, this branch focuses on running
the integrated prediction workflow.
</p>

<hr>

<h2>System Objective</h2>

<p>
The main objective is to detect newly inserted or updated customer
records and generate fresh:
</p>

<ul>
    <li>Churn prediction</li>
    <li>Churn probability</li>
    <li>Customer Lifetime Value (LTV)</li>
</ul>

<p>
The resulting predictions are then written back to Neon PostgreSQL.
</p>

<hr>

<h2>Integrated Architecture</h2>

<pre>
                    TEST CONSOLE
                          |
                          v
                       FastAPI
                          |
                          v
               Test Data Generator
                          |
                          v
                  Neon PostgreSQL
                          |
                          v
                  Change Detection
                          |
                          v
                     Scheduler
                          |
                          v
                    Main Pipeline
                          |
                          v
                    Preprocessing
                          |
                +---------+---------+
                |                   |
                v                   v
          Churn Model          LTV Model
                |                   |
                +---------+---------+
                          |
                          v
                  Prediction Results
                          |
                          v
                  Neon PostgreSQL
</pre>

<hr>

<h2>Core Processing Flow</h2>

<pre>
Customer Records
       |
       v
Check updated_at
       |
       v
Identify changed records
       |
       v
Preprocessing
       |
       v
Feature Validation
       |
       +-----------------------+
       |                       |
       v                       v
Churn Prediction         LTV Prediction
       |                       |
       +-----------+-----------+
                   |
                   v
          Combine Predictions
                   |
                   v
          Update PostgreSQL
</pre>

<hr>

<h2>Neon PostgreSQL</h2>

<p>
Neon PostgreSQL is used as the central database for customer records
and prediction results.
</p>

<h3>Customer Data</h3>

<p>
The database stores the customer attributes required by the prediction
pipeline.
</p>

<h3>Prediction Fields</h3>

<ul>
    <li><code>churn</code></li>
    <li><code>churn_probability</code></li>
    <li><code>predicted_ltv</code></li>
    <li><code>prediction_at</code></li>
</ul>

<h3>Change Tracking Fields</h3>

<ul>
    <li><code>updated_at</code></li>
</ul>

<hr>

<h2>Database Connection</h2>

<p>
Database connection logic is implemented in:
</p>

<p align="center">
    <code>database.py</code>
</p>

<p>
The application uses SQLAlchemy to connect to Neon PostgreSQL.
Database credentials are provided through environment variables.
</p>

<pre>
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
DB_NAME
</pre>

<p>
The actual credentials should remain local and must not be committed
to GitHub.
</p>

<hr>

<h2>Change Detection</h2>

<p>
Change detection is implemented in:
</p>

<p align="center">
    <code>change_tracker.py</code>
</p>

<p>
The tracker maintains a Python-side checkpoint representing the last
successful processing point.
</p>

<pre>
Previous Successful Run
          |
          v
      Current Run
          |
          v
Changed Customer Records
</pre>

<p>
The prediction pipeline uses the customer's
<code>updated_at</code> timestamp to identify records that have been
inserted or updated during the processing window.
</p>

<hr>

<h2>Why <code>updated_at</code> Is Important</h2>

<p>
A customer can already have an existing prediction and still require a
new prediction if their customer information changes.
</p>

<pre>
Existing Customer
       |
       v
Customer information changes
       |
       v
updated_at changes
       |
       v
Customer selected for reprocessing
       |
       v
New Churn + LTV prediction
</pre>

<p>
The change detection process therefore focuses on changes in customer
data rather than simply checking whether a previous churn prediction
already exists.
</p>

<hr>

<h2>Python Processing Checkpoint</h2>

<p>
The last successful processing timestamp is maintained locally in:
</p>

<p align="center">
    <code>pipeline_state.json</code>
</p>

<pre>
{
    "last_successful_run": "2026-08-27T15:11:19.214499+00:00"
}
</pre>

<p>
The checkpoint is updated only after the prediction results have been
successfully written back to Neon PostgreSQL.
</p>

<hr>

<h2>Preprocessing</h2>

<p>
Customer data is transformed by:
</p>

<p align="center">
    <code>preprocessing.py</code>
</p>

<p>
The preprocessing stage converts database records into the feature
structure required by the trained machine learning models.
</p>

<pre>
Raw Customer Data
        |
        v
Data Preparation
        |
        v
Feature Transformation
        |
        v
Feature Ordering
        |
        v
Model-Ready Features
</pre>

<p>
The saved preprocessing package is:
</p>

<p align="center">
    <code>preprocessing_package.pkl</code>
</p>

<hr>

<h2>Feature Validation</h2>

<p>
Before model inference, the system verifies the processed feature
matrix.
</p>

<ul>
    <li>Expected feature count</li>
    <li>Actual feature count</li>
    <li>Missing-value validation</li>
    <li>Model input shape</li>
</ul>

<p>
Example:
</p>

<pre>
Expected features: 25
Actual features:   25
NaN validation:    Passed
</pre>

<hr>

<h2>Churn Prediction</h2>

<p>
The churn prediction model is stored in:
</p>

<p align="center">
    <code>xgboost_model.json</code>
</p>

<p>
The model generates:
</p>

<ul>
    <li>Churn classification</li>
    <li>Churn probability</li>
</ul>

<pre>
Customer
   |
   v
XGBoost Churn Model
   |
   +----&gt; Churn: Yes / No
   |
   +----&gt; Probability: 0.72
</pre>

<hr>

<h2>Lifetime Value Prediction</h2>

<p>
The Lifetime Value model is stored in:
</p>

<p align="center">
    <code>ltv_model.json</code>
</p>

<p>
The model estimates the expected Lifetime Value of the customer.
</p>

<pre>
Customer
   |
   v
LTV Model
   |
   v
Predicted LTV
</pre>

<p>
Example:
</p>

<pre>
Predicted LTV: ₹4,850
</pre>

<hr>

<h2>Model Implementation</h2>

<p>
The integrated branch contains:
</p>

<table>
<tr>
    <th>File</th>
    <th>Purpose</th>
</tr>

<tr>
    <td><code>final_model.py</code></td>
    <td>Final churn model implementation and related model processing</td>
</tr>

<tr>
    <td><code>ltv_model.py</code></td>
    <td>Lifetime Value model implementation</td>
</tr>
</table>

<hr>

<h2>Main Prediction Pipeline</h2>

<p>
The central execution pipeline is implemented in:
</p>

<p align="center">
    <code>main.py</code>
</p>

<h3>Responsibilities</h3>

<ol>
    <li>Connect to Neon PostgreSQL.</li>
    <li>Create the current processing window.</li>
    <li>Fetch changed customer records.</li>
    <li>Load the preprocessing package.</li>
    <li>Transform customer data.</li>
    <li>Validate the feature matrix.</li>
    <li>Load the churn model.</li>
    <li>Generate churn predictions.</li>
    <li>Load the LTV model.</li>
    <li>Generate LTV predictions.</li>
    <li>Combine the prediction results.</li>
    <li>Write predictions back to Neon.</li>
    <li>Update the processing checkpoint.</li>
</ol>

<hr>

<h2>Scheduler</h2>

<p>
Scheduled execution is implemented in:
</p>

<p align="center">
    <code>scheduler.py</code>
</p>

<p>
The current design uses a five-minute processing interval.
</p>

<pre>
Start Scheduler
      |
      v
Wait 5 Minutes
      |
      v
Run Pipeline
      |
      v
Wait 5 Minutes
      |
      v
Run Pipeline
      |
      v
Repeat
</pre>

<p>
The scheduler acts as the polling mechanism that periodically checks
for customer changes.
</p>

<hr>

<h2>FastAPI</h2>

<p>
The FastAPI test service is implemented in:
</p>

<p align="center">
    <code>test_api.py</code>
</p>

<p>
The main test endpoint is:
</p>

<pre>
POST /generate-test-data
</pre>

<p>
FastAPI provides the API layer between the test console and the
test-data generator.
</p>

<p>
FastAPI does not perform the machine learning prediction itself.
It only triggers the test-data generation process.
</p>

<hr>

<h2>Test Data Generator</h2>

<p>
Controlled test-data generation is implemented in:
</p>

<p align="center">
    <code>test_data_generator.py</code>
</p>

<p>
A test generation cycle creates:
</p>

<table>
<tr>
    <th>Operation</th>
    <th>Quantity</th>
</tr>

<tr>
    <td>Existing customer updates</td>
    <td>150</td>
</tr>

<tr>
    <td>New customer inserts</td>
    <td>50</td>
</tr>

<tr>
    <td><strong>Total affected records</strong></td>
    <td><strong>200</strong></td>
</tr>
</table>

<p>
The generator only creates customer activity. It does not perform
model inference.
</p>

<hr>

<h2>Existing Customer Updates</h2>

<p>
The generator randomly selects existing customers and changes customer
input information such as:
</p>

<ul>
    <li>Tenure</li>
    <li>Contract</li>
    <li>Payment method</li>
    <li>Monthly charges</li>
    <li>Total charges</li>
    <li>Customer service attributes</li>
</ul>

<p>
The customer's <code>updated_at</code> value is refreshed so that the
change-tracking system can detect the update.
</p>

<hr>

<h2>New Customer Inserts</h2>

<p>
New test customers are created with unique identifiers.
</p>

<pre>
TEST-GEN-0001
TEST-GEN-0002
TEST-GEN-0003
...
</pre>

<p>
The generated records follow the same customer feature structure
expected by the preprocessing and prediction pipeline.
</p>

<hr>

<h2>Test Console</h2>

<p>
The test console is located at:
</p>

<p align="center">
    <code>customer-interface/test_console.html</code>
</p>

<p>
It provides a simple interface for triggering controlled test-data
generation.
</p>

<pre>
+--------------------------------------+
|       TEST DATA GENERATOR            |
|                                      |
| Existing Updates       150           |
| New Inserts             50           |
| Total Changes          200           |
|                                      |
|      [ GENERATE TEST DATA ]          |
|                                      |
| Status: Ready                        |
+--------------------------------------+
</pre>

<hr>

<h2>Test Console Architecture</h2>

<pre>
test_console.html
        |
        v
POST /generate-test-data
        |
        v
test_api.py
        |
        v
test_data_generator.py
        |
        v
Neon PostgreSQL
</pre>

<p>
The browser does not directly access Neon PostgreSQL.
Database credentials remain on the backend.
</p>

<hr>

<h2>Complete End-to-End Test</h2>

<h3>Step 1 - Start FastAPI</h3>

<pre>
uvicorn test_api:app --reload
</pre>

<p>
FastAPI runs locally on:
</p>

<pre>
http://127.0.0.1:8000
</pre>

<h3>Step 2 - Open the Test Console</h3>

<pre>
customer-interface/test_console.html
</pre>

<h3>Step 3 - Generate Test Data</h3>

<p>
Click:
</p>

<pre>
GENERATE TEST DATA
</pre>

<p>
The system generates:
</p>

<pre>
150 updates
+
50 inserts
=
200 affected records
</pre>

<h3>Step 4 - Store Data in Neon</h3>

<p>
The generated customer records are written to Neon PostgreSQL.
</p>

<h3>Step 5 - Start Scheduler</h3>

<pre>
python scheduler.py
</pre>

<h3>Step 6 - Detect Changes</h3>

<p>
The change tracker identifies customer records that changed since the
previous successful processing point.
</p>

<h3>Step 7 - Run Preprocessing</h3>

<p>
Changed records are transformed into model-ready features.
</p>

<h3>Step 8 - Generate Predictions</h3>

<pre>
                 Customer Records
                        |
                        v
                  Preprocessing
                        |
              +---------+---------+
              |                   |
              v                   v
       Churn Prediction      LTV Prediction
              |                   |
              +---------+---------+
                        |
                        v
                 Final Results
</pre>

<h3>Step 9 - Write Results</h3>

<p>
The resulting churn and LTV predictions are written back to Neon
PostgreSQL.
</p>

<hr>

<h2>Example Prediction Output</h2>

<pre>
customerid      churn    churn_probability    predicted_ltv
TEST-GEN-0001  No       0.179605             3107.04
TEST-GEN-0002  No       0.064165             3172.62
TEST-GEN-0003  Yes      0.607105             1020.69
</pre>

<hr>

<h2>Prediction Fields</h2>

<table>
<tr>
    <th>Field</th>
    <th>Description</th>
</tr>

<tr>
    <td><code>churn</code></td>
    <td>Predicted churn classification</td>
</tr>

<tr>
    <td><code>churn_probability</code></td>
    <td>Probability associated with churn</td>
</tr>

<tr>
    <td><code>predicted_ltv</code></td>
    <td>Estimated customer Lifetime Value</td>
</tr>

<tr>
    <td><code>prediction_at</code></td>
    <td>Time when the prediction was generated</td>
</tr>
</table>

<hr>

<h2>Project Files</h2>

<table>
<tr>
    <th>File</th>
    <th>Responsibility</th>
</tr>

<tr>
    <td><code>main.py</code></td>
    <td>Main Churn + LTV inference pipeline</td>
</tr>

<tr>
    <td><code>database.py</code></td>
    <td>Neon PostgreSQL connection and database operations</td>
</tr>

<tr>
    <td><code>preprocessing.py</code></td>
    <td>Customer-data transformation</td>
</tr>

<tr>
    <td><code>change_tracker.py</code></td>
    <td>Processing window and checkpoint management</td>
</tr>

<tr>
    <td><code>scheduler.py</code></td>
    <td>Five-minute scheduled execution</td>
</tr>

<tr>
    <td><code>final_model.py</code></td>
    <td>Final churn model implementation</td>
</tr>

<tr>
    <td><code>ltv_model.py</code></td>
    <td>LTV model implementation</td>
</tr>

<tr>
    <td><code>test_data_generator.py</code></td>
    <td>Controlled customer data generation</td>
</tr>

<tr>
    <td><code>test_api.py</code></td>
    <td>FastAPI test-data endpoint</td>
</tr>

<tr>
    <td><code>customer-interface/test_console.html</code></td>
    <td>Test-data generation interface</td>
</tr>

</table>

<hr>

<h2>Model Artifacts</h2>

<pre>
xgboost_model.json
ltv_model.json
preprocessing_package.pkl
</pre>

<p>
These files are loaded by the prediction pipeline during inference.
</p>

<hr>

<h2>Environment Configuration</h2>

<p>
Database configuration is provided through environment variables.
</p>

<pre>
DB_USER=your_neon_user
DB_PASSWORD=your_neon_password
DB_HOST=your_neon_host
DB_PORT=5432
DB_NAME=neondb
</pre>

<p>
The real <code>.env</code> file must remain local and must not be
committed to GitHub.
</p>

<hr>

<h2>Security</h2>

<p>
Sensitive credentials and runtime state should remain outside Git
tracking.
</p>

<p>Recommended <code>.gitignore</code>:</p>

<pre>
.env
pipeline_state.json
__pycache__/
*.pyc
</pre>

<hr>

<h2>Separation of Responsibilities</h2>

<pre>
test_console.html
        |
        | User interaction
        v
test_api.py
        |
        | API request
        v
test_data_generator.py
        |
        | Test customer activity
        v
database.py
        |
        | Neon PostgreSQL
        v
change_tracker.py
        |
        | Processing window
        v
scheduler.py
        |
        | Scheduled execution
        v
main.py
        |
        +---- preprocessing.py
        |
        +---- xgboost_model.json
        |
        +---- ltv_model.json
        |
        v
Neon PostgreSQL
</pre>

<hr>

<h2>Relationship With Other Branches</h2>

<table>
<tr>
    <th>Branch</th>
    <th>Purpose</th>
</tr>

<tr>
    <td><code>main</code></td>
    <td>Stable project version</td>
</tr>

<tr>
    <td><code>machine-learning</code></td>
    <td>ML experimentation, model development and comparison</td>
</tr>

<tr>
    <td><code>customer-portal</code></td>
    <td>Customer-facing web interface</td>
</tr>

<tr>
    <td><code>integration-pipeline</code></td>
    <td>Integrated ML pipeline, database, scheduler, FastAPI and testing</td>
</tr>

</table>

<hr>

<h2>Current Implementation Status</h2>

<table>
<tr>
    <th>Component</th>
    <th>Status</th>
</tr>

<tr>
    <td>Neon PostgreSQL connection</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>Customer data insertion</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>Customer data updates</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>Change detection</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>Five-minute scheduler</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>Customer preprocessing</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>XGBoost churn prediction</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>LTV prediction</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>Prediction write-back</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>FastAPI test endpoint</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>Test-data generator</td>
    <td>Implemented</td>
</tr>

<tr>
    <td>Test console</td>
    <td>Implemented</td>
</tr>

</table>

<hr>

<h2>Future Integration</h2>

<p>
The customer-facing portal can later be connected to the integrated
backend services.
</p>

<pre>
Customer Portal
       |
       v
     FastAPI
       |
       v
Neon PostgreSQL
       |
       v
Change Detection
       |
       v
Scheduled Prediction
       |
       v
Churn + LTV Models
       |
       v
Prediction Results
</pre>

<p>
This will allow customer actions performed through the portal to update
the backend database and participate in the prediction workflow.
</p>

<hr>

<h2>Quick Start</h2>

<h3>1. Install Dependencies</h3>

<pre>
pip install pandas numpy joblib xgboost sqlalchemy psycopg2-binary python-dotenv fastapi uvicorn
</pre>

<h3>2. Configure Environment</h3>

<p>
Create a local <code>.env</code> file containing the Neon PostgreSQL
credentials.
</p>

<h3>3. Start FastAPI</h3>

<pre>
uvicorn test_api:app --reload
</pre>

<h3>4. Open the Test Console</h3>

<pre>
customer-interface/test_console.html
</pre>

<h3>5. Start the Prediction Scheduler</h3>

<pre>
python scheduler.py
</pre>

<hr>

<div align="center">

<h3>Customer Churn Prediction &amp; Lifetime Value Engine</h3>

<p>
<strong>Integration Pipeline</strong>
</p>

</div>
## Current Development

Dashboard integration and customer analytics features are under development.✅ Dashboard section structure
✅ API connection/status indicator
✅ Refresh button
✅ KPI cards
✅ Churn-risk / LTV analytics sections
✅ Customer search/details
✅ Priority-customer section