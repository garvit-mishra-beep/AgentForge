import java.util.*;
public class FibonacciSeq {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("Enter the number of terms in the Fibonacci sequence: ");
        int n = sc.nextInt();
        int a = 0, b = 1, c, d ;
        int arr[] = new int[n];
        System.out.println("Fibonacci sequence:");
        for (int i = 1; i <= n; i++) {
            arr[i - 1] = a;
            System.out.print(a+" ");
            c = a + b;
            a = b;
            b = c;
        }
        System.out.print("\nEnter the index to retrieve the Fibonacci number: ");
        d = sc.nextInt();
        System.out.println("Fibonacci number at index " + d + ": " + arr[d - 1]);
    }
}