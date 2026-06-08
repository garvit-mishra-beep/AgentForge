import java.util.*;
public class Findlcmandhcf {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter first number: ");
        int a = sc.nextInt();
        System.out.print("Enter second number: ");
        int b = sc.nextInt();
        int lcm = (a * b)/hcf(a, b);
        System.out.println("LCM of " + a + " and " + b + " is: " + lcm);
    }
    public static int hcf(int a, int b) {
        if (b == 0) {
            return a;
        }
        return hcf(b, a % b);
    }
}
