import java.util.*;
public class A {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (!sc.hasNextInt()) return;
        int t = sc.nextInt();
        while (t-- > 0) {
            int n = sc.nextInt();
            int[] a = new int[n];
            for (int i = 0; i < n; i++) {
                a[i] = sc.nextInt();
            }
            Arrays.sort(a);
            long blue = a[0] + a[1];
            long red = a[n - 1];
            int i = 2, j = n - 2;
            boolean possible = red > blue;
            while (!possible && i < j) {
                blue += a[i++];
                red += a[j--];
                if (red > blue) possible = true;
            }    
            System.out.println(possible ? "YES" : "NO");
        }
    }
}
/*Here's a step-by-step explanation of the code:
1. The program starts by importing the `java.util.*` package, which includes the `  
Scanner` class for reading input and the `Arrays` class for sorting.
2. The `main` method is defined, which is the entry point of the program.
3. A `Scanner` object is created to read input from the standard input.
4. The program checks if there is an integer input available. If not, it returns immediately
5. The number of test cases `t` is read from the input.
6. A loop runs for each test case, where:
    a. The size of the array `n` is read.
    b. An integer array `a` of size `n` is created to store the input values.
    c. A loop reads `n` integers into the array `a`.
    d. The array `a` is sorted in ascending order using `Arrays.sort()`.
    e. The initial "blue" sum is calculated as the sum of the two smallest elements (the first two elements of the sorted array).
    f. The initial "red" sum is set to the largest element (the last element of the sorted array).
    g. Two pointers, `i` and `j`, are initialized to point to the next smallest and next largest elements, respectively.
    h. A boolean variable `possible` is initialized to check if the "red" sum is greater than the "blue" sum.
    */
