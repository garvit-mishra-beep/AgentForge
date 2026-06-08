package array;
import java.util.*;
public class countvowel {
    public static void main(String[] args) {
           Scanner sc = new Scanner(System.in);
        System.out.println("Enter a string:");
        String str = sc.nextLine();
        int countv = 0,countc=0;
        for (int i = 0; i < str.length(); i++) {
            char ch = str.charAt(i);
            if (ch == 'a' || ch == 'e' || ch == 'i' || ch == 'o' || ch == 'u' ||
                ch == 'A' || ch == 'E' || ch == 'I' || ch == 'O' || ch == 'U') {
                countv++;
            }
            else {
                countc++;
            }
        }
        System.out.println("Number of vowels : " + countv);
        System.out.println("Number of consonants : " + countc);
        System.out.println("Number of characters : " + str.length());
    }
}