package practice;

import java.util.*;

public class CheckArraysEqual {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.println("Enter size of first array:");
        int n1 = sc.nextInt();
        int[] arr1 = new int[n1];
        System.out.println("Enter elements of first array:");
        for (int i = 0; i < n1; i++) arr1[i] = sc.nextInt();
        
        System.out.println("Enter size of second array:");
        int n2 = sc.nextInt();
        int[] arr2 = new int[n2];
        System.out.println("Enter elements of second array:");
        for (int i = 0; i < n2; i++) arr2[i] = sc.nextInt();
        
        if (n1 != n2) {
            System.out.println("Arrays are not equal.");
            return;
        }
        
        HashMap<Integer, Integer> map = new HashMap<>();
        for (int num : arr1) {
            map.put(num, map.getOrDefault(num, 0) + 1);
        }
        
        boolean isEqual = true;
        for (int num : arr2) {
            if (!map.containsKey(num) || map.get(num) == 0) {
                isEqual = false;
                break;
            }
            map.put(num, map.get(num) - 1);
        }
        System.out.println("Are Arrays Equal? " + isEqual);
        sc.close();
    }
}