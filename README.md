# Marketing Contact Verification Tool

This application helps verify marketing contact information against online sources. It analyzes data row by row and highlights cells based on verification status: Green for valid data, Yellow for uncertain data, and Red for incorrect data.

## Features

- Upload CSV or Excel files with contact data
- Verify multiple fields including names, emails, job titles, and company information
- Color-coded verification results
- AI-powered verification with OpenAI integration
- DeepSearch mode for more thorough verification with GPT-4
- Export results to Excel with preserved formatting
- Summary statistics on data quality

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:

```bash
export OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the application:

```bash
streamlit run app.py
```

2. Upload your CSV or Excel file containing contact data, or use the sample data
3. Configure verification settings:
   - Enable/disable AI verification
   - Enable/disable DeepSearch mode for more thorough verification
   - Set the number of rows to verify
4. Click "Start Verification" to begin the process
5. View the results and download the verified data as an Excel file

## Verification Fields

The tool verifies the following fields:
- First Name
- Last Name
- Email
- Contact Job Title
- Company Name
- Company Address
- Company City
- Company State
- Company Country
- Company Postal Code
- Company Industry
- Company Phone
- Company Domain
- Contact LinkedIn
- Company LinkedIn

## Deployment Options

### Streamlit Community Cloud (Easiest)

1. Push your code to a GitHub repository
2. Create an account on [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repo and deploy
4. Add your OPENAI_API_KEY in the secrets management section

### Self-Hosting

Follow the instructions in the deployment guide for:
- Setting up a VPS
- Configuring the application
- Setting up a reverse proxy with Nginx
- Securing with SSL

## Important Notes

- Keep your OpenAI API key secure
- Be aware of rate limits and quotas, especially with DeepSearch mode
- Consider implementing additional data privacy measures if handling sensitive contact information

## License

This project is proprietary and confidential.