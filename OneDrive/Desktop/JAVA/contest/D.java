import java.util.*;
public class D {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int t = sc.nextInt();
        while (t-- > 0) {
            int n = sc.nextInt();
            long[] count = new long[2 * n + 1];
            long ans = 0;
            for (int i = 1; i <= n; i++) {
                int a = sc.nextInt();
                int val = a - i;
                ans += count[val + n];
                count[val + n]++;
            }
            System.out.println(ans);
        }
    }
}
/*Here's a step-by-step explanation of the code:
1. The program starts by importing the `java.util.*` package, which includes the `Scanner` class for reading input.
2. The `main` method is defined, which is the entry point of the program.  
3. A `Scanner` object is created to read input from the standard input.
4. The number of test cases `t` is read from the input.
5. A loop runs for each test case, where:
    a. The size of the array `n` is read.
    b. A long array `count` of size `2 * n + 1` is created to keep track of the frequency of values.
    c. A long variable `ans` is initialized to store the final answer for the current test case.
    d. A loop runs from `1` to `n`, where:
        i. An integer `a` is read from the input.
        ii. The value `val` is calculated as `a - i`.
        iii. The current count of `val + n` is added to `ans`.
        iv. The count of `val + n` is incremented by 1.
6. After processing all elements of the array, the final answer `ans` is printed for the current test case.
*/  