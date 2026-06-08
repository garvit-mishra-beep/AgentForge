import java.util.Scanner;
public class Garland {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int t = sc.nextInt();
        while (t-- > 0) {
            long r = sc.nextLong();
            long g = sc.nextLong();
            long b = sc.nextLong();
            long total = r + g + b;   
            long maxLamps = r;
            if (g > maxLamps) {
                maxLamps = g;
            }
            if (b > maxLamps) {
                maxLamps = b;
            }
            if (maxLamps <= (total + 1) / 2) {
                System.out.println("Yes");
            } else {
                System.out.println("No");
            }
        }
        sc.close();
    }
}