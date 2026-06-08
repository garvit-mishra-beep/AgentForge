package array;
import java.util.Scanner;
public class avrage {
    public static void main(String[] args){
        Scanner sc = new Scanner(System.in);
        System.out.println("Enter the size of the array");
        int size = sc.nextInt();
        int[] arr = new int[size];
        System.out.println("Enter the elements of the array");
        for(int i=0; i<size; i++){
            arr[i] = sc.nextInt();
        }
        int sum = 0;
        for(int i=0; i<size; i++){
            sum += arr[i];
        }
        double average = (double) sum / size;
        System.out.println("The average is: " + average);
        sc.close();
    }
}
