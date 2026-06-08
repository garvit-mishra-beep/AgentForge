package array;
import java.util.*;
public class findsort {
     public static void main(String[] args) {

        Scanner sc = new Scanner(System.in);

        System.out.print("Enter size of array: ");
        int n = sc.nextInt();

        int[] array = new int[n];

        System.out.println("Enter array elements:");

        for(int i = 0; i < n; i++) {
            array[i] = sc.nextInt();
        }

        boolean sorted = true;

        for(int i = 1; i < n; i++) {
            if(array[i] < array[i - 1]) {
                sorted = false;
                break;
            }
        }

        if(sorted) {
            System.out.println("Array is Sorted");
        } else {
            System.out.println("Array is Not Sorted");
        }
    }
}
