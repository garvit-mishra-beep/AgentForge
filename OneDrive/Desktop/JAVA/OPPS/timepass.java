

public class timepass {
    static int count = 90;
    static void compare(){
        Integer a = 10;
        Integer b = 10;
        if(a.equals(b)) {
            System.out.println("a is equal to b");
        } else {
            System.out.println("a is not equal to b");
        }
    }
    static void display() {
        System.out.println("static method called");
    }

    public static void main(String[] args) {
        Integer a = 128;
        Integer b = 128;
        if(a.equals(b)) {
            System.out.println("a is equal to b");
        } else {
            System.out.println("a is not equal to b");
        }
        System.out.println(timepass.count);
        timepass.compare();
        timepass.display();
        Integer c = Integer.valueOf(10);
        System.out.println(c);
     
    }
}