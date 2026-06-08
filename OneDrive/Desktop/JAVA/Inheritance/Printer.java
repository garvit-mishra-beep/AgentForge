class Appliance {
    void turnOn() {
        System.out.println("Turning on the appliance...");
    }
}
class Toaster extends Appliance {
    @Override
    void turnOn() {
        System.out.println("Heating up bread.");
    }
}
public class Printer {
    public void printDocument(int copies) {
        System.out.println("Printing " + copies + " copies of the document.");
    }
    public void printDocument(String secretMessage) {
        System.out.println("Printing secret message: " + secretMessage);
    }
    public static void main(String[] args) {
        Printer myPrinter = new Printer();
        myPrinter.printDocument(3); 
        myPrinter.printDocument("Aliens are real!"); 

        Toaster myToaster = new Toaster();
        myToaster.turnOn(); 
    }
}
