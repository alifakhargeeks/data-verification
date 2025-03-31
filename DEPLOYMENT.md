# Deployment Guide for Marketing Contact Verification Tool

This guide provides detailed instructions for deploying your Marketing Contact Verification Tool to various environments.

## Option 1: Deploying on Streamlit Community Cloud (Easiest)

### Prerequisites
- GitHub account
- OpenAI API key

### Steps

1. **Prepare your repository**:
   - Make sure all your code is committed to a GitHub repository
   - Ensure your `requirements.txt` file includes all dependencies
   - Check that your `.streamlit/config.toml` file has the correct server configuration

2. **Sign up for Streamlit Cloud**:
   - Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)
   - Create an account using your GitHub credentials

3. **Deploy your app**:
   - Click "New app" in the Streamlit Cloud dashboard
   - Select your GitHub repository
   - Choose the main branch and specify the path to your app.py file
   - Add your secret OPENAI_API_KEY in the "Secrets" section:
     ```
     OPENAI_API_KEY = "your_api_key_here"
     ```
   - Click "Deploy"

4. **Share your app**:
   - Streamlit Cloud will provide a public URL for your app
   - You can set up access controls if needed in the app settings

## Option 2: Self-Hosting on a Virtual Private Server (VPS)

### Prerequisites
- A VPS from a provider (AWS, Google Cloud, DigitalOcean, etc.)
- Domain name (optional but recommended)
- Basic knowledge of Linux server administration

### Steps

1. **Set up a VPS**:
   - Create an account with a cloud provider (AWS, Google Cloud, DigitalOcean, etc.)
   - Set up a virtual machine (Ubuntu 20.04 LTS is recommended)
   - Connect to your server via SSH

2. **Install required software**:
   ```bash
   # Update your system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv
   
   # Install Nginx for reverse proxy
   sudo apt install -y nginx
   
   # Install Certbot for SSL (optional)
   sudo apt install -y certbot python3-certbot-nginx
   ```

3. **Set up your application**:
   ```bash
   # Create a directory for the application
   mkdir -p /var/www/streamlit_app
   cd /var/www/streamlit_app
   
   # Copy your application files to this directory
   # (Upload using SFTP or git clone your repository)
   
   # Create and activate a virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create a .env file for environment variables
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

4. **Create a systemd service**:
   ```bash
   sudo nano /etc/systemd/system/streamlit.service
   ```
   
   Add the following content:
   ```
   [Unit]
   Description=Streamlit Web App
   After=network.target
   
   [Service]
   User=www-data
   WorkingDirectory=/var/www/streamlit_app
   ExecStart=/var/www/streamlit_app/venv/bin/streamlit run app.py --server.port 8501
   Restart=always
   Environment="OPENAI_API_KEY=your_api_key_here"
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable streamlit
   sudo systemctl start streamlit
   ```

5. **Configure Nginx as a reverse proxy**:
   ```bash
   sudo nano /etc/nginx/sites-available/streamlit
   ```
   
   Add the following content:
   ```
   server {
       listen 80;
       server_name your_domain.com www.your_domain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   
   Create a symbolic link and test the configuration:
   ```bash
   sudo ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **Set up SSL (optional but recommended)**:
   ```bash
   sudo certbot --nginx -d your_domain.com -d www.your_domain.com
   ```
   Follow the prompts to complete the setup.

7. **Set up automatic renewal for SSL certificate**:
   ```bash
   sudo certbot renew --dry-run
   ```
   Certbot creates a systemd timer to handle automatic renewal.

## Option 3: Deploying on Heroku

### Prerequisites
- Heroku account
- Heroku CLI installed
- Git installed

### Steps

1. **Create necessary files**:
   
   Create a `Procfile` in your project directory:
   ```
   web: streamlit run app.py --server.port $PORT
   ```
   
   Create a `runtime.txt` file:
   ```
   python-3.9.16
   ```

2. **Install Heroku CLI and deploy**:
   ```bash
   # Login to Heroku
   heroku login
   
   # Create a new Heroku app
   heroku create your-app-name
   
   # Set your OpenAI API key as a config variable
   heroku config:set OPENAI_API_KEY=your_api_key_here
   
   # Deploy your application
   git push heroku main
   
   # Open your app in a browser
   heroku open
   ```

## Security Considerations

1. **API Key Security**:
   - Never hardcode API keys in your source code
   - Use environment variables or secrets management
   - Restrict API key permissions to only what's needed
   - Regularly rotate your API keys

2. **Rate Limiting**:
   - Be aware of OpenAI API rate limits and quotas
   - Consider implementing your own rate limiting for users
   - Add proper caching to reduce API calls

3. **Cost Management**:
   - Monitor your OpenAI API usage, especially with DeepSearch
   - Set usage alerts and budgets
   - Consider adding user quotas for shared deployments

4. **Data Privacy**:
   - Implement proper data handling practices
   - Consider data retention policies
   - Inform users about data sent to third-party services (OpenAI)

## Troubleshooting

1. **App not starting**:
   - Check application logs: `sudo journalctl -u streamlit.service`
   - Verify the Python environment and dependencies
   - Ensure the API key is properly set

2. **Nginx configuration issues**:
   - Test Nginx config: `sudo nginx -t`
   - Check Nginx error logs: `sudo cat /var/log/nginx/error.log`

3. **SSL certificate problems**:
   - Run Certbot in debug mode: `sudo certbot --nginx --debug`
   - Check certificate expiry: `sudo certbot certificates`

4. **OpenAI API issues**:
   - Verify your API key is valid and has sufficient quota
   - Check if the OpenAI API is experiencing service disruptions
   - Test with a simple API call to isolate the problem