import java.util.*;
public class Stringpalindrome {
        public static void main(String[] args) {
   Scanner sc = new Scanner(System.in);
   String str;
         System.out.println("Enter a string:");
         str = sc.nextLine();
         str = str.toLowerCase();
        String rev = new StringBuilder(str).reverse().toString();
        if (str.equals(rev)) {
            System.out.println("The string is a palindrome.");
        } else {
            System.out.println("The string is not a palindrome.");
        }
    }
}