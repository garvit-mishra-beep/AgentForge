class Vehicle {
    int speed;
    String color;
    String brand;
    String engine;
    Vehicle(int spd, String clr, String brd, String eng) {
        speed = spd;
        color = clr;
        brand = brd;
        engine = eng;
    }
    void displayDetails() {
        System.out.println("Vehicle Details:");
        System.out.println("Speed: " + speed + " km/h");
        System.out.println("Color: " + color);
        System.out.println("Brand: " + brand);
        System.out.println("Engine: " + engine);
    }
}
class Car extends Vehicle {
    int numberOfDoors;
    Car(int spd, String clr, String brd, String eng, int doors) {
        super(spd, clr, brd, eng);
        numberOfDoors = doors;
    }
    void displayCarDetails() {
        displayDetails();
        System.out.println("Number of Doors: " + numberOfDoors);
    }
}
class Bike extends Vehicle {
    boolean hasCarrier;
    Bike(int spd, String clr, String brd, String eng, boolean carrier) {
        super(spd, clr, brd, eng);
        hasCarrier = carrier;
    }
    void displayBikeDetails() {
        displayDetails();
        System.out.println("Has Carrier: " + (hasCarrier ? "Yes" : "No"));
    }
}
class Truck extends Vehicle {
    int loadCapacity;
    Truck(int spd, String clr, String brd, String eng, int capacity) {
        super(spd, clr, brd, eng);
        loadCapacity = capacity;
    }
    void displayTruckDetails() {
        displayDetails();
        System.out.println("Load Capacity: " + loadCapacity + " tons");
    }
}
class Bus extends Vehicle {
    int seatingCapacity; 
    Bus(int spd, String clr, String brd, String eng, int capacity) {
        super(spd, clr, brd, eng);
        seatingCapacity = capacity;
    }
    void displayBusDetails() {
        displayDetails();
        System.out.println("Seating Capacity: " + seatingCapacity + " passengers");
    }
}
class Gain {
    public static void main(String[] args) {
    Car myCar = new Car(150, "Red", "Toyota", "V6", 4);
    myCar.displayCarDetails();
    Bike myBike = new Bike(120, "Blue", "Yamaha", "Single Cylinder", true);
    myBike.displayBikeDetails();
    Truck myTruck = new Truck(100, "White", "Volvo", "Diesel", 20);
    myTruck.displayTruckDetails();
    Bus myBus = new Bus(80, "Yellow", "Mercedes", "Diesel", 50);
    myBus.displayBusDetails();
    }
}