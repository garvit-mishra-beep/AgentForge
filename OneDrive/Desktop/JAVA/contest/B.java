import java.util.*;
public class B {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int t = sc.nextInt();
        while (t-- > 0) {
            int x = sc.nextInt();
            int n = sc.nextInt();
            if (n % 2 == 0) {
                System.out.println(0);
            } else {
                System.out.println(x);
            }
        }
        sc.close();
    }
}
/*HERE'S A STEP-BY-STEP EXPLANATION OF THE CODE:
1. The program starts by importing the `java.util.*` package, which includes the `Scanner` class for reading input.
2. The `main` method is defined, which is the entry point of the program.
3. A `Scanner` object is created to read input from the standard input.
4. The number of test cases `t` is read from the input.
5. A loop runs for each test case, where:
    a. An integer `x` is read from the input.
    b. An integer `n` is read from the input.
    c. The program checks if `n` is even or odd using the modulus operator `%`.
    d. If `n` is even, it prints `0`. If `n` is odd, it prints the value of `x`.    
6. After processing all test cases, the `Scanner` is closed to free up resources.*/