import java.util.*;

public class Bank {
    private int accountNumber;
    private String accountHolderName;
    private String dob;
    private double balance;

    public Bank(int accNum, String name, String dateOfBirth, double initialBalance) {
        this.accountNumber = accNum;
        this.accountHolderName = name;
        this.dob = dateOfBirth;
        this.balance = initialBalance;
    }
    public void displayInfo() {
        System.out.println("Account Information:");
        System.out.println("Account Number: " + accountNumber);
        System.out.println("Account Holder Name: " + accountHolderName);
        System.out.println("Date of Birth: " + dob);
        System.out.println("Balance: " + balance);
    }

    public void deposit(double amount) {
        if (amount > 0) {
            this.balance += amount;
            System.out.println("Amount deposited successfully. New balance: " + this.balance);
        } else {
            System.out.println("Invalid deposit amount.");
        }
    }

    public void withdraw(double amount) {
        if (amount > 0 && amount <= this.balance) {
            this.balance -= amount;
            System.out.println("Amount withdrawn successfully. New balance: " + this.balance);
        } else if (amount > this.balance) {
            System.out.println("Insufficient balance. Withdrawal failed.");
        } else {
            System.out.println("Invalid withdrawal amount.");
        }
    }
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter the number of account holders: ");
        int numAccounts = sc.nextInt();
        Bank[] accounts = new Bank[numAccounts];
        
        for (int i = 0; i < numAccounts; i++) {
            System.out.println("\n--- Enter details for Account Holder " + (i + 1) + " ---");
            System.out.print("Enter account number: ");
            int accNum = sc.nextInt();
            sc.nextLine(); 
            System.out.print("Enter account holder name: ");
            String name = sc.nextLine();
            System.out.print("Enter date of birth: ");
            String dateOfBirth = sc.nextLine();
            System.out.print("Enter initial balance: ");
            double initialBalance = sc.nextDouble();
            
            accounts[i] = new Bank(accNum, name, dateOfBirth, initialBalance);
            accounts[i].displayInfo();

            System.out.print("Enter amount to deposit: ");
            double depositAmount = sc.nextDouble();
            accounts[i].deposit(depositAmount);

            System.out.print("Enter amount to withdraw: ");
            double withdrawAmount = sc.nextDouble();
            accounts[i].withdraw(withdrawAmount);
        }
        sc.close();
    }
}
