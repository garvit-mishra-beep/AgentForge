import java.util.*;

abstract class AbstractCalculator {
    public abstract void displayInfo();
    
    public final void turnOn() {
        System.out.println("Calculator is turning on...");
    }
}

class BasicCalculator extends AbstractCalculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public double add(double a, double b) {
        return a + b;
    }
    
    public double subtract(double a, double b) {
        return a - b;
    }
    
    public double multiply(double a, double b) {
        return a * b;
    }
    
    public double divide(double a, double b) {
        if (b == 0) {
            throw new ArithmeticException("Cannot divide by zero!");
        }
        return a / b;
    }

    @Override
    public void displayInfo() {
        System.out.println("I am a Basic Calculator. I handle fundamental arithmetic.");
    }
}

class AdvancedCalculator extends BasicCalculator {
    private double memory = 0;

    public double add(double... numbers) {
        double sum = 0;
        for (double num : numbers) {
            sum += num;
        }
        return sum;
    }

    public double power(double base, double exponent) {
        return Math.pow(base, exponent);
    }
    @Override
    public void displayInfo() {
        System.out.println("I am an Advanced Calculator. I support varargs, memory, and powers!");
    }
}

public class Calculator {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        AdvancedCalculator myCalc = new AdvancedCalculator();
        
        myCalc.turnOn();
        myCalc.displayInfo(); 
        
        boolean keepRunning = true;
        while (keepRunning) {
            System.out.println("\n--- Calculator Menu ---");
            System.out.println("1. Add");
            System.out.println("2. Subtract");
            System.out.println("3. Multiply");
            System.out.println("4. Divide");
            System.out.println("5. Add 3 numbers (Varargs)");
            System.out.println("6. Power");
            System.out.println("7. Exit");
            System.out.print("Choose an option: ");
            
            int choice = sc.nextInt();
            
            switch (choice) {
                case 1:
                    System.out.print("Enter first number: ");
                    double add1 = sc.nextDouble();
                    System.out.print("Enter second number: ");
                    double add2 = sc.nextDouble();
                    System.out.println("Addition: " + myCalc.add(add1, add2));
                    break;
                case 2:
                    System.out.print("Enter first number: ");
                    double sub1 = sc.nextDouble();
                    System.out.print("Enter second number: ");
                    double sub2 = sc.nextDouble();
                    System.out.println("Subtraction: " + myCalc.subtract(sub1, sub2));
                    break;
                case 3:
                    System.out.print("Enter first number: ");
                    double mul1 = sc.nextDouble();
                    System.out.print("Enter second number: ");
                    double mul2 = sc.nextDouble();
                    System.out.println("Multiplication: " + myCalc.multiply(mul1, mul2));
                    break;
                case 4:
                    System.out.print("Enter dividend: ");
                    double div1 = sc.nextDouble();
                    System.out.print("Enter divisor: ");
                    double div2 = sc.nextDouble();
                    try {
                        System.out.println("Division: " + myCalc.divide(div1, div2));
                    } catch (ArithmeticException e) {
                        System.out.println("Error caught: " + e.getMessage());
                    }
                    break;
                case 5:
                    System.out.print("Enter first number: ");
                    double v1 = sc.nextDouble();
                    System.out.print("Enter second number: ");
                    double v2 = sc.nextDouble();
                    System.out.print("Enter third number: ");
                    double v3 = sc.nextDouble();
                    System.out.println("Adding all three (Varargs): " + myCalc.add(v1, v2, v3));
                    break;
                case 6:
                    System.out.print("Enter base: ");
                    double base = sc.nextDouble();
                    System.out.print("Enter exponent: ");
                    double exp = sc.nextDouble();
                    System.out.println("Power (" + base + "^" + exp + "): " + myCalc.power(base, exp));
                    break;
                case 7:
                    keepRunning = false;
                    System.out.println("Turning off calculator...");
                    break;
                default:
                    System.out.println("Invalid option. Please try again.");
            }
        }
        sc.close();
    }
}