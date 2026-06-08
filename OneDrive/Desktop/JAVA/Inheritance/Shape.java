public class Shape {
    String color = "Red";
    void displayColor() {
        System.out.println("Shape Color: " + color);
    }

}
class Circle extends Shape {
    String color;
    double radius;
    Circle(String clr, double r) {
        color = clr;
        radius = r;
    }
    void displayCircleDetails() {
        System.out.println("Base Shape Color: " + super.color);
        System.out.println("Circle Color: " + color);
        System.out.println("Circle Radius: " + radius);
    }
    void area() {
        double area = 3.14 * radius * radius;
        System.out.println("Circle Area: " + area);
    }
}
class Square extends Shape {
    String color;
    double side;
    Square(String clr, double s) {
        color = clr;
        side = s;
    }
    void displaySquareDetails() {
        System.out.println("Base Shape Color: " + super.color);
        System.out.println("Square Color: " + color);
        System.out.println("Square Side: " + side);
    }
    void area() {
        double area = side * side;
        System.out.println("Square Area: " + area);
    }
}
class Sain {
    public static void main(String[] args) {
        Circle circle = new Circle("Blue", 5.0);
        Square square = new Square("Green", 4.0);
        circle.displayCircleDetails();
        square.displaySquareDetails();
        circle.area();
        square.area();
    }
}