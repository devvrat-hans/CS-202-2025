#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ACCOUNTS 100
#define MAX_NAME_LENGTH 50

typedef struct {
    int account_number;
    char name[MAX_NAME_LENGTH];
    double balance;
    int is_active;
} Account;

Account accounts[MAX_ACCOUNTS];
int total_accounts = 0;

void display_menu() {
    printf("\n=== BANKING SYSTEM ===\n");
    printf("1. Create Account\n");
    printf("2. Deposit Money\n");
    printf("3. Withdraw Money\n");
    printf("4. Check Balance\n");
    printf("5. Transfer Money\n");
    printf("6. Display All Accounts\n");
    printf("7. Close Account\n");
    printf("8. Calculate Interest\n");
    printf("9. Exit\n");
    printf("Enter your choice: ");
}

int find_account(int account_number) {
    int i = 0;
    int found_index = -1;
    
    while (i < total_accounts) {
        if (accounts[i].account_number == account_number && accounts[i].is_active == 1) {
            found_index = i;
            break;
        }
        i = i + 1;
    }
    
    return found_index;
}

void create_account() {
    int account_number;
    char name[MAX_NAME_LENGTH];
    double initial_deposit;
    int valid_account = 1;
    
    if (total_accounts >= MAX_ACCOUNTS) {
        printf("Maximum account limit reached!\n");
        return;
    }
    
    printf("Enter account number: ");
    scanf("%d", &account_number);
    
    // Check if account already exists
    int existing_index = find_account(account_number);
    if (existing_index != -1) {
        printf("Account already exists!\n");
        valid_account = 0;
    }
    
    if (valid_account == 1) {
        printf("Enter account holder name: ");
        scanf("%s", name);
        
        printf("Enter initial deposit: ");
        scanf("%lf", &initial_deposit);
        
        if (initial_deposit < 100.0) {
            printf("Minimum initial deposit is $100\n");
            valid_account = 0;
        }
    }
    
    if (valid_account == 1) {
        accounts[total_accounts].account_number = account_number;
        strcpy(accounts[total_accounts].name, name);
        accounts[total_accounts].balance = initial_deposit;
        accounts[total_accounts].is_active = 1;
        total_accounts = total_accounts + 1;
        
        printf("Account created successfully!\n");
        printf("Account Number: %d\n", account_number);
        printf("Account Holder: %s\n", name);
        printf("Initial Balance: $%.2f\n", initial_deposit);
    }
}

void deposit_money() {
    int account_number;
    double deposit_amount;
    int account_index;
    
    printf("Enter account number: ");
    scanf("%d", &account_number);
    
    account_index = find_account(account_number);
    
    if (account_index == -1) {
        printf("Account not found or inactive!\n");
        return;
    }
    
    printf("Enter deposit amount: ");
    scanf("%lf", &deposit_amount);
    
    if (deposit_amount <= 0) {
        printf("Invalid deposit amount!\n");
        return;
    }
    
    accounts[account_index].balance = accounts[account_index].balance + deposit_amount;
    
    printf("Deposit successful!\n");
    printf("New Balance: $%.2f\n", accounts[account_index].balance);
}

void withdraw_money() {
    int account_number;
    double withdraw_amount;
    int account_index;
    double new_balance;
    
    printf("Enter account number: ");
    scanf("%d", &account_number);
    
    account_index = find_account(account_number);
    
    if (account_index == -1) {
        printf("Account not found or inactive!\n");
        return;
    }
    
    printf("Current Balance: $%.2f\n", accounts[account_index].balance);
    printf("Enter withdrawal amount: ");
    scanf("%lf", &withdraw_amount);
    
    if (withdraw_amount <= 0) {
        printf("Invalid withdrawal amount!\n");
        return;
    }
    
    new_balance = accounts[account_index].balance - withdraw_amount;
    
    if (new_balance < 50.0) {
        printf("Insufficient funds! Minimum balance of $50 required.\n");
        return;
    }
    
    accounts[account_index].balance = new_balance;
    
    printf("Withdrawal successful!\n");
    printf("New Balance: $%.2f\n", accounts[account_index].balance);
}

void check_balance() {
    int account_number;
    int account_index;
    
    printf("Enter account number: ");
    scanf("%d", &account_number);
    
    account_index = find_account(account_number);
    
    if (account_index == -1) {
        printf("Account not found or inactive!\n");
        return;
    }
    
    printf("Account Number: %d\n", accounts[account_index].account_number);
    printf("Account Holder: %s\n", accounts[account_index].name);
    printf("Current Balance: $%.2f\n", accounts[account_index].balance);
}

void transfer_money() {
    int from_account, to_account;
    double transfer_amount;
    int from_index, to_index;
    double new_from_balance;
    
    printf("Enter source account number: ");
    scanf("%d", &from_account);
    
    printf("Enter destination account number: ");
    scanf("%d", &to_account);
    
    from_index = find_account(from_account);
    to_index = find_account(to_account);
    
    if (from_index == -1) {
        printf("Source account not found or inactive!\n");
        return;
    }
    
    if (to_index == -1) {
        printf("Destination account not found or inactive!\n");
        return;
    }
    
    if (from_account == to_account) {
        printf("Cannot transfer to the same account!\n");
        return;
    }
    
    printf("Enter transfer amount: ");
    scanf("%lf", &transfer_amount);
    
    if (transfer_amount <= 0) {
        printf("Invalid transfer amount!\n");
        return;
    }
    
    new_from_balance = accounts[from_index].balance - transfer_amount;
    
    if (new_from_balance < 50.0) {
        printf("Insufficient funds in source account!\n");
        return;
    }
    
    accounts[from_index].balance = new_from_balance;
    accounts[to_index].balance = accounts[to_index].balance + transfer_amount;
    
    printf("Transfer successful!\n");
    printf("From Account %d: $%.2f\n", from_account, accounts[from_index].balance);
    printf("To Account %d: $%.2f\n", to_account, accounts[to_index].balance);
}

void display_all_accounts() {
    int i = 0;
    int active_count = 0;
    
    printf("\n=== ALL ACTIVE ACCOUNTS ===\n");
    printf("%-10s %-20s %-15s\n", "Acc No.", "Name", "Balance");
    printf("-----------------------------------------------\n");
    
    while (i < total_accounts) {
        if (accounts[i].is_active == 1) {
            printf("%-10d %-20s $%-14.2f\n", 
                   accounts[i].account_number, 
                   accounts[i].name, 
                   accounts[i].balance);
            active_count = active_count + 1;
        }
        i = i + 1;
    }
    
    printf("-----------------------------------------------\n");
    printf("Total Active Accounts: %d\n", active_count);
}

void close_account() {
    int account_number;
    int account_index;
    char confirmation;
    
    printf("Enter account number to close: ");
    scanf("%d", &account_number);
    
    account_index = find_account(account_number);
    
    if (account_index == -1) {
        printf("Account not found or already inactive!\n");
        return;
    }
    
    printf("Account Details:\n");
    printf("Account Number: %d\n", accounts[account_index].account_number);
    printf("Account Holder: %s\n", accounts[account_index].name);
    printf("Current Balance: $%.2f\n", accounts[account_index].balance);
    
    printf("Are you sure you want to close this account? (y/n): ");
    scanf(" %c", &confirmation);
    
    if (confirmation == 'y' || confirmation == 'Y') {
        accounts[account_index].is_active = 0;
        printf("Account closed successfully!\n");
        
        if (accounts[account_index].balance > 0) {
            printf("Please collect your remaining balance of $%.2f\n", 
                   accounts[account_index].balance);
        }
    } else {
        printf("Account closure cancelled.\n");
    }
}

void calculate_interest() {
    int i = 0;
    double interest_rate = 0.05; // 5% annual interest
    double total_interest = 0.0;
    double account_interest;
    
    printf("\n=== INTEREST CALCULATION ===\n");
    printf("Annual Interest Rate: %.2f%%\n", interest_rate * 100);
    printf("%-10s %-20s %-15s %-15s\n", "Acc No.", "Name", "Balance", "Interest");
    printf("---------------------------------------------------------------\n");
    
    while (i < total_accounts) {
        if (accounts[i].is_active == 1 && accounts[i].balance > 0) {
            account_interest = accounts[i].balance * interest_rate;
            total_interest = total_interest + account_interest;
            
            printf("%-10d %-20s $%-14.2f $%-14.2f\n", 
                   accounts[i].account_number,
                   accounts[i].name,
                   accounts[i].balance,
                   account_interest);
        }
        i = i + 1;
    }
    
    printf("---------------------------------------------------------------\n");
    printf("Total Interest Payable: $%.2f\n", total_interest);
}

int main() {
    int choice;
    int continue_program = 1;
    
    printf("Welcome to the Banking System!\n");
    
    while (continue_program == 1) {
        display_menu();
        scanf("%d", &choice);
        
        if (choice == 1) {
            create_account();
        } else if (choice == 2) {
            deposit_money();
        } else if (choice == 3) {
            withdraw_money();
        } else if (choice == 4) {
            check_balance();
        } else if (choice == 5) {
            transfer_money();
        } else if (choice == 6) {
            display_all_accounts();
        } else if (choice == 7) {
            close_account();
        } else if (choice == 8) {
            calculate_interest();
        } else if (choice == 9) {
            printf("Thank you for using our Banking System!\n");
            continue_program = 0;
        } else {
            printf("Invalid choice! Please try again.\n");
        }
        
        if (continue_program == 1) {
            printf("\nPress Enter to continue...");
            getchar();
            getchar();
        }
    }
    
    return 0;
}