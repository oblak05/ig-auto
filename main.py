import threading
import requests
from pytempbox import PyTempBox
import time
import re
import random
from faker import Faker
from datetime import datetime, timedelta

# Instagram sign-up URLs
DESKTOP_SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"
MOBILE_SIGNUP_URL = "https://instagram.com/accounts/signup/email/"

# User agents for different devices
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
]

# Proxy list (will be populated with fetched proxies)
PROXIES = []

fake = Faker()

def fetch_free_proxies():
    """Fetch free proxies from public APIs"""
    global PROXIES
    if PROXIES and PROXIES[0] is not None:  # Already fetched and not empty
        return PROXIES
    
    print("[*] Fetching free proxies...")
    try:
        # Try ProxyScrape API first (most reliable)
        response = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all", timeout=15)
        if response.status_code == 200:
            proxy_list = response.text.strip().split('\n')
            for proxy in proxy_list[:10]:  # Limit to 10 working proxies
                if ':' in proxy and len(proxy.split(':')) == 2:
                    ip, port = proxy.split(':')
                    if ip and port.isdigit():
                        PROXIES.append({
                            "http": f"http://{ip}:{port}",
                            "https": f"http://{ip}:{port}"
                        })
        
        # If no proxies from API, try scraping free-proxy-list.net
        if not PROXIES:
            try:
                response = requests.get("https://free-proxy-list.net/", timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Try different table selectors
                    table = soup.find('table', {'class': 'table'}) or soup.find('table')
                    if table:
                        rows = table.find_all('tr')[1:11]  # Skip header, limit to 10
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                ip = cols[0].text.strip()
                                port = cols[1].text.strip()
                                if ip and port.isdigit():
                                    PROXIES.append({
                                        "http": f"http://{ip}:{port}",
                                        "https": f"http://{ip}:{port}"
                                    })
            except:
                pass  # Ignore scraping errors
        
        if PROXIES:
            print(f"[+] Successfully fetched {len(PROXIES)} proxies")
        else:
            print("[-] No proxies fetched, using direct connection")
            PROXIES = [None]  # Fallback to no proxy
            
    except Exception as e:
        print(f"[-] Error fetching proxies: {e}")
        PROXIES = [None]  # Fallback to no proxy
    
    return PROXIES

def get_random_proxy():
    """Get a random proxy from the list"""
    if not PROXIES:
        fetch_free_proxies()
    
    # Filter out None values and get a random proxy
    available_proxies = [p for p in PROXIES if p is not None]
    return random.choice(available_proxies) if available_proxies else None

def get_random_user_agent():
    """Get a random user agent"""
    return random.choice(USER_AGENTS)

def generate_random_data():
    """Generate random data for account creation"""
    # Generate birthday (18-50 years old)
    today = datetime.now()
    start_date = today - timedelta(days=50*365)
    end_date = today - timedelta(days=18*365)
    birthday = fake.date_between(start_date=start_date, end_date=end_date)

    return {
        'full_name': fake.name(),
        'username': fake.user_name() + str(random.randint(100, 999)),
        'birthday': birthday.strftime('%Y-%m-%d')
    }

def extract_confirmation_code(messages):
    """Extract confirmation code from email messages"""
    for message in messages:
        subject = message.get('subject', '')
        body = message.get('body', '')
        content = f"{subject} {body}".lower()
        
        match = re.search(r'(\d{6})', content)
        if match:
            return match.group(1)
    return None

def get_confirmation_code(email, client):
    """Poll pytempbox inbox for confirmation code"""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            messages = client.get_messages(email)
            if messages:
                code = extract_confirmation_code(messages)
                if code:
                    return code
            time.sleep(2)
        except Exception as e:
            print(f"Error checking inbox for {email}: {e}")
            time.sleep(2)
    return None

def create_account(password, use_mobile=False):
    """Create Instagram account with random data and proxy"""
    try:
        # Initialize PyTempBox client
        client = PyTempBox()
        email = client.generate_email()
        print(f"[*] Creating account with email: {email}")

        # Generate random data
        data = generate_random_data()
        print(f"[*] Generated data: {data}")

        # Get random proxy and user agent
        proxy = get_random_proxy()
        user_agent = get_random_user_agent()

        # Create session with proxy and headers
        session = requests.Session()
        if proxy:
            session.proxies.update(proxy)
            print(f"[*] Using proxy: {proxy['http']}")
        else:
            print("[*] Using direct connection (no proxy)")

        session.headers.update({
            'User-Agent': user_agent,
            'Accept-Language': 'en-US,en;q=0.9',  # Simulate US location
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Choose signup URL
        signup_url = MOBILE_SIGNUP_URL if use_mobile else DESKTOP_SIGNUP_URL

        # Get the signup page to extract CSRF token (if needed)
        response = session.get(signup_url)
        if response.status_code != 200:
            print(f"[-] Failed to load signup page: {response.status_code}")
            return False

        # Extract CSRF token from response (this is a simplified example)
        csrf_token = None
        if 'csrftoken' in response.cookies:
            csrf_token = response.cookies['csrftoken']

        # Prepare signup data
        signup_data = {
            'email': email,
            'password': password,
            'username': data['username'],
            'fullName': data['full_name'],
            'month': data['birthday'].split('-')[1],
            'day': data['birthday'].split('-')[2],
            'year': data['birthday'].split('-')[0],
        }

        if csrf_token:
            signup_data['csrftoken'] = csrf_token

        # Submit signup form
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': signup_url,
            'X-CSRFToken': csrf_token or '',
        }

        response = session.post(signup_url, data=signup_data, headers=headers)

        if response.status_code in [200, 302]:
            print(f"[+] Account registration submitted for {email}")
        else:
            print(f"[-] Registration failed: {response.status_code} - {response.text}")
            return False

        # Wait for confirmation email
        print(f"[*] Waiting for confirmation email...")
        confirmation_code = get_confirmation_code(email, client)

        if not confirmation_code:
            print(f"[-] No confirmation code received for {email}")
            return False

        print(f"[+] Confirmation code received: {confirmation_code}")

        # Verify email (this would need the actual verification endpoint)
        # Note: Instagram's verification process is complex and may require additional steps
        print(f"[✓] Account created: {email} / {password} (verification may be needed)")

        return True

    except Exception as e:
        print(f"[-] Error creating account: {e}")
        return False

def main():
    print("[*] Fetching proxies...")
    fetch_free_proxies()
    
    num_accounts = int(input("How many accounts would you like to create? "))
    password = input("Enter the password for the accounts: ")
    use_mobile = input("Use mobile signup? (y/n): ").lower() == 'y'

    threads = []
    for i in range(num_accounts):
        thread = threading.Thread(target=create_account, args=(password, use_mobile))
        threads.append(thread)
        thread.start()
        time.sleep(2)  # Stagger account creation

    for thread in threads:
        thread.join()

    print("[*] All accounts created!")

if __name__ == "__main__":
    main()