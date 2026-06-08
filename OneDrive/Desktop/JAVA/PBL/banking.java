import java.io.*;
import java.util.*;
// Custom exception classes for handling specific banking-related errors cleanly
class BankingException extends Exception {
    public BankingException(String message) { super(message); }
}
class AccountNotFoundException extends BankingException {
    public AccountNotFoundException(String message) { super(message); }
}
class InsufficientBalanceException extends BankingException {
    public InsufficientBalanceException(String message) { super(message); }
}
class InvalidTransactionException extends BankingException {
    public InvalidTransactionException(String message) { super(message); }
}
class InvalidAccountDetailsException extends BankingException {
    public InvalidAccountDetailsException(String message) { super(message); }
}

// Represents a single transaction (like a Deposit or Withdraw) made on an account
class Transaction {
    private String type;
    private double amount;
    public Transaction(String type, double amount) {
        this.type = type;
        this.amount = amount;
    }

    public String getType() { 
        return type; 
    }

    public double getAmount() { 
        return amount; 
    }

    @Override
    public String toString() { 
        return type + " | " + amount; 
    }
}
// Represents an individual bank account, storing user details, balance, and transaction history
class BankAccount {
    private int accountNumber;
    private String pin;
    private String customerName;
    private double balance;
    private String accountType;
    private List<Transaction> transactions = new ArrayList<>();

    public BankAccount(int accountNumber, String pin, String customerName, String accountType, double balance) {
        this.accountNumber = accountNumber;
        this.pin = pin;
        this.customerName = customerName;
        this.accountType = accountType;
        this.balance = balance;
    }

    public int getAccountNumber() { 
        return accountNumber; 
    }

    public String getPin() { 
        return pin; 
    }

    public String getCustomerName() { 
        return customerName; 
    }

    public double getBalance() { 
        return balance; 
    }

    public String getAccountType() { 
        return accountType; 
    }

    // Adds money to the account balance and records the deposit transaction
    public void deposit(double amount) throws InvalidTransactionException {
        if (amount <= 0) {
            throw new InvalidTransactionException("Amount must be positive");
        }
        
        balance += amount;
        transactions.add(new Transaction("Deposit", amount));
    }

    // Deducts money from the account if sufficient balance is available, and records the withdrawal
    public void withdraw(double amount) throws InvalidTransactionException, InsufficientBalanceException {
        if (amount <= 0) {
            throw new InvalidTransactionException("Amount must be positive");
        }
        if (amount > balance) {
            throw new InsufficientBalanceException("Insufficient balance");
        }
        
        balance -= amount;
        transactions.add(new Transaction("Withdraw", amount));
    }

    public void addTransactionHistory(String type, double amount) {
        transactions.add(new Transaction(type, amount));
    }

    // Converts transaction history into a specially formatted string (e.g., "Deposit:100,Withdraw:50") for saving to text files
    public String getTransactionData() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < transactions.size(); i++) {
            sb.append(transactions.get(i).getType()).append(":").append(transactions.get(i).getAmount());
            if (i < transactions.size() - 1) {
                sb.append(",");
            }
        }
        return sb.toString();
    }

    public void displayAccount() {
        System.out.println("\n-------------------------");
        System.out.println("Account Number : " + accountNumber);
        System.out.println("Customer Name  : " + customerName);
        System.out.println("Balance        : " + balance);
    }

    public void showTransactions() {
        if (transactions.isEmpty()) {
            System.out.println("No transactions found.");
            return;
        }
        System.out.println("\nTransaction History");
        for (Transaction t : transactions) {
            System.out.println(t);
        }
    }
}

// Utility class that handles saving data to, and reading data from, the local text file (accounts.txt)
class FileManager {
    private static final String FILE_NAME = "accounts.txt";
    private static final String BACKUP_FILE = "accounts_backup.txt";
    
    // Writes all current accounts and their transaction histories to a file in a custom delimited format
    public static void saveData(List<BankAccount> accounts) {
        try {
            File oldFile = new File(FILE_NAME);
            if (oldFile.exists()) {
                copyFile(FILE_NAME, BACKUP_FILE);
            }
            FileWriter writer = new FileWriter(FILE_NAME);
            for (BankAccount account : accounts) {
                String record =
                        account.getAccountNumber() + "|"
                                + account.getPin() + "|"
                                + account.getCustomerName() + "|"
                                + account.getAccountType() + "|"
                                + account.getBalance();
                String txData =
                        account.getTransactionData();
                if (!txData.isEmpty()) {
                    record += "|" + txData;
                }
                writer.write(record + System.lineSeparator());
            }
            writer.close();
            System.out.println("Data saved successfully.");
        } catch (IOException e) {
            System.out.println("Error saving data : "
                    + e.getMessage());
        }
    }
    
    // Reads the file line by line, reconstructing the BankAccount and Transaction objects
    public static List<BankAccount> loadData() {
        List<BankAccount> accounts =
                new ArrayList<>();

        File file = new File(FILE_NAME);

        if (!file.exists()) {
            System.out.println(
                    "No previous records found.");
            return accounts;
        }
        try {
            Scanner scanner = new Scanner(file);
            while (scanner.hasNextLine()) {
                String line = scanner.nextLine();
                try {
                    String[] parts =
                            line.split("\\|");
                    int accNo =
                            Integer.parseInt(parts[0]);
                    String pin = parts[1];
                    String name = parts[2];
                    String type = parts[3];

                    double balance =
                            Double.parseDouble(parts[4]);

                    BankAccount account =
                            new BankAccount(
                                    accNo,
                                    pin,
                                    name,
                                    type,
                                    balance);

                    if (parts.length > 5) {

                        String[] transactions =
                                parts[5].split(",");

                        for (String tx : transactions) {
                            String[] data =
                                    tx.split(":");

                            if (data.length == 2) {
                                account.addTransactionHistory(
                                        data[0],
                                        Double.parseDouble(data[1]));
                            }
                        }
                    }
                    accounts.add(account);
                } catch (Exception ex) {

                    System.out.println(
                            "Skipped Corrupted Record");
                }
            }
            scanner.close();
            System.out.println(
                    "Data loaded successfully.");
        } catch (IOException e) {
            System.out.println(
                    "Error reading file.");
        }
        return accounts;
    }
    private static void copyFile(
            String source,
            String destination)
            throws IOException {
        Scanner scanner = new Scanner(new File(source));
        FileWriter writer = new FileWriter(destination);

        while (scanner.hasNextLine()) {
            writer.write(scanner.nextLine() + System.lineSeparator());
        }
        scanner.close();
        writer.close();
    }
}

// The core banking system that manages the collection of all user accounts and business operations
class Bank {
    private List<BankAccount> accounts = new ArrayList<>();
    private int nextAccountNumber = 1001;

    // Creates a new account, auto-generates a unique account number, and adds it to the system
    public void createAccount(String name, String type, double balance, String pin) throws InvalidAccountDetailsException {
        if (name == null || name.trim().isEmpty()) {
            throw new InvalidAccountDetailsException("Customer name cannot be empty");
        }
        if (pin == null || pin.trim().isEmpty()) {
            throw new InvalidAccountDetailsException("PIN cannot be empty");
        }

        if (balance < 0) {
            throw new InvalidAccountDetailsException("Initial balance cannot be negative");
        }
        BankAccount account = new BankAccount(nextAccountNumber++, pin, name, type, balance);
        accounts.add(account);
        System.out.println("\nAccount Created Successfully");
        System.out.println("Account Number : " + account.getAccountNumber());
    }

    public BankAccount authenticateUser(int accountNumber, String pin) throws BankingException {
        BankAccount account = searchAccount(accountNumber);
        if (!account.getPin().equals(pin)) {
            throw new BankingException("Invalid PIN");
        }
        return account;
    }

    // Searches for an account by ID, throwing an Exception if it is not found
    public BankAccount searchAccount(int accountNumber) throws AccountNotFoundException {
        for (BankAccount account : accounts) {
            if (account.getAccountNumber() == accountNumber) {
                return account;
            }
        }
        throw new AccountNotFoundException("Account not found with ID: " + accountNumber);
    }

    // Removes an account permanently from the application
    public void deleteAccount(int accountNumber) throws AccountNotFoundException {
        accounts.remove(searchAccount(accountNumber));
        System.out.println("Account deleted successfully");
    }

    // Moves money securely from one account to another using the withdraw and deposit functions
    public void transferMoney(int senderAcc, int receiverAcc, double amount) throws BankingException {
        if (senderAcc == receiverAcc) {
            throw new InvalidTransactionException("Cannot transfer money to the same account");
        }
        BankAccount sender = searchAccount(senderAcc);
        BankAccount receiver = searchAccount(receiverAcc);
        sender.withdraw(amount);
        receiver.deposit(amount);
        System.out.println("Transfer successful");
    }

    public void displayAllAccounts() {
        if (accounts.isEmpty()) {
            System.out.println("No accounts available");
            return;
        }
        for (BankAccount account : accounts) {
            account.displayAccount();
        }
    }

    public void saveData() {
        FileManager.saveData(accounts);
    }

    // Loads data and recalculates what the next newly created account number should be, based on loaded data
    public void loadData() {
        accounts = FileManager.loadData();
        for (BankAccount account : accounts) {
            if (account.getAccountNumber() >= nextAccountNumber) {
                nextAccountNumber = account.getAccountNumber() + 1;
            }
        }
    }
}

// The main entry point containing the interactive text-based console menu
public class banking {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        Bank bank = new Bank();
        bank.loadData(); // Attempt to load previous records at startup
        
        while (true) {
            System.out.println("\n===== BANKING SYSTEM WELCOME =====");
            System.out.println("1. Create New Account");
            System.out.println("2. Login to Account");
            System.out.println("3. Exit");
            System.out.print("\nEnter Choice : ");
            
            try {
                int choice = sc.nextInt();
                if (choice == 1) {
                    sc.nextLine();
                    System.out.print("Customer Name : "); 
                    String name = sc.nextLine();
                    System.out.print("Account Type (e.g. Savings/Current) : ");
                    String type = sc.nextLine();
                    System.out.print("Set a PIN : ");
                    String pin = sc.nextLine();
                    System.out.print("Initial Balance : "); 
                    double balance = sc.nextDouble();
                    bank.createAccount(name, type, balance, pin);
                    bank.saveData();
                } else if (choice == 2) {
                    System.out.print("Account Number: ");
                    int accNo = sc.nextInt();
                    sc.nextLine();
                    System.out.print("PIN: ");
                    String pin = sc.nextLine();
                    
                    BankAccount loggedInAccount = bank.authenticateUser(accNo, pin);
                    System.out.println("\nLogin Successful! Welcome, " + loggedInAccount.getCustomerName());
                    
                    boolean sessionActive = true;
                    while (sessionActive) {
                        System.out.println("\n===== CUSTOMER MENU =====");
                        System.out.println("1. View Account Details\n2. Deposit Money\n3. Withdraw Money");
                        System.out.println("4. Transfer Money\n5. Transaction History\n6. Logout");
                        System.out.print("\nEnter Choice : ");
                        
                        int userChoice = sc.nextInt();
                        switch (userChoice) {
                            case 1:
                                loggedInAccount.displayAccount();
                                break;
                            case 2:
                                System.out.print("Amount to Deposit : "); 
                                loggedInAccount.deposit(sc.nextDouble());
                                System.out.println("Deposit Successful");
                                bank.saveData();
                                break;
                            case 3:
                                System.out.print("Amount to Withdraw : "); 
                                loggedInAccount.withdraw(sc.nextDouble());
                                System.out.println("Withdrawal Successful");
                                bank.saveData();
                                break;
                            case 4:
                                System.out.print("Receiver Account Number : "); 
                                int to = sc.nextInt();
                                System.out.print("Amount : "); 
                                double amt = sc.nextDouble();
                                bank.transferMoney(loggedInAccount.getAccountNumber(), to, amt);
                                bank.saveData();
                                break;
                            case 5:
                                loggedInAccount.showTransactions();
                                break;
                            case 6:
                                sessionActive = false;
                                System.out.println("Logged out successfully.");
                                break;
                            default:
                                System.out.println("Invalid Choice");
                        }
                    }
                } else if (choice == 3) {
                    bank.saveData();
                    System.out.println("\nThank You for using our Bank System!");
                    System.exit(0);
                } else {
                    System.out.println("Invalid Choice");
                }
            } catch (InputMismatchException e) {
                System.out.println("Invalid Input! Please enter numbers where expected.");
                sc.nextLine();
            } catch (BankingException e) {
                System.out.println("Banking Error : " + e.getMessage());
            } catch (Exception e) {
                System.out.println("Unexpected System Error : " + e.getMessage());
            }
        }
    }
}