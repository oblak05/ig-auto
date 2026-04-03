import threading
import requests
import pytempbox
import time
import re

INSTAGRAM_API_URL = "https://www.instagram.com/api/v1"
SESSION = requests.Session()

def extract_confirmation_code(inbox):
    """Extract confirmation code from email inbox"""
    for email_data in inbox:
        # Look for confirmation code in email body
        body = email_data.get('body', '')
        match = re.search(r'(\d{6})', body)
        if match:
            return match.group(1)
    return None

def get_confirmation_code(email):
    """Poll pytempbox inbox for confirmation code"""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            inbox = pytempbox.get_inbox(email)
            code = extract_confirmation_code(inbox)
            if code:
                return code
            time.sleep(2)  # Wait before checking again
        except Exception as e:
            print(f"Error checking inbox for {email}: {e}")
            time.sleep(2)
    
    return None

def create_account(username, password):
    """Create Instagram account with email verification"""
    try:
        # Get temporary email
        email = pytempbox.get_email()
        print(f"[*] Creating account with email: {email}")
        
        # Step 1: Register account with Instagram
        register_data = {
            'email': email,
            'username': username,
            'password': password,
            'first_name': 'Auto',
        }
        
        # Send registration request to Instagram
        response = SESSION.post(
            f"{INSTAGRAM_API_URL}/accounts/create/",
            json=register_data,
            headers={'User-Agent': 'Instagram 4.0'}
        )
        
        if response.status_code != 200:
            print(f"[-] Registration failed for {email}: {response.text}")
            return False
        
        print(f"[+] Account registered: {email}")
        
        # Step 2: Wait for confirmation email
        print(f"[*] Waiting for confirmation email...")
        confirmation_code = get_confirmation_code(email)
        
        if not confirmation_code:
            print(f"[-] No confirmation code received for {email}")
            return False
        
        print(f"[+] Confirmation code received: {confirmation_code}")
        
        # Step 3: Verify email with confirmation code
        verify_data = {
            'email': email,
            'code': confirmation_code
        }
        
        response = SESSION.post(
            f"{INSTAGRAM_API_URL}/accounts/verify/",
            json=verify_data,
            headers={'User-Agent': 'Instagram 4.0'}
        )
        
        if response.status_code == 200:
            print(f"[✓] Account verified and created: {email} / {password}")
            return True
        else:
            print(f"[-] Email verification failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"[-] Error creating account: {e}")
        return False

def main():
    num_accounts = int(input("How many accounts would you like to create? "))
    password = input("Enter the password for the accounts: ")
    
    threads = []
    for i in range(num_accounts):
        username = f"autouser_{int(time.time())}_{i}"
        thread = threading.Thread(target=create_account, args=(username, password))
        threads.append(thread)
        thread.start()
        time.sleep(1)  # Stagger account creation
    
    for thread in threads:
        thread.join()
    
    print("[*] All accounts created!")

if __name__ == "__main__":
    main()