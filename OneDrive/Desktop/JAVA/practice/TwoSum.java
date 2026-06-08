package practice;

import java.util.*;

public class TwoSum {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.println("Enter number of elements:");
        int n = sc.nextInt();
        int[] arr = new int[n];
        System.out.println("Enter elements:");
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        
        System.out.println("Enter target sum:");
        int target = sc.nextInt();
        
        HashMap<Integer, Integer> map = new HashMap<>();
        boolean found = false;
        
        for (int i = 0; i < n; i++) {
            int complement = target - arr[i];
            if (map.containsKey(complement)) {
                System.out.println("Indices: [" + map.get(complement) + ", " + i + "]");
                System.out.println("Elements: " + complement + " and " + arr[i]);
                found = true;
                break;
            }
            map.put(arr[i], i);
        }
        if (!found) {
            System.out.println("No two sum solution found.");
        }
        sc.close();
    }
}