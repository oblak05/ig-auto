import threading
import requests
import pytempbox

def create_account(password):
    email = pytempbox.get_email()
    # Here you would add the code to create an Instagram account using the email and password
    print(f"Account created with email: {email} and password: {password}")

def main():
    num_accounts = int(input("How many accounts would you like to create? "))
    password = input("Enter the password for the accounts: ")
    
    threads = []
    for _ in range(num_accounts):
        thread = threading.Thread(target=create_account, args=(password,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
