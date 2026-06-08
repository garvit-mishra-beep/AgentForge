import java.util.*;
public class list1 {
    public static void main(String[] args) {
        List<Integer> List = new ArrayList<>();
        List.add(0);
        List.add(1);
        List.add(2);
        List.add(3);
        List.add(4);
        List.add(5);
        List.add(3, 6);
        List.add(7);
        List.add(8);
        List.add(9);
        System.out.println("ArrayList: " + List);
        System.out.println("First element: " + List.get(0));
        System.out.println("Size of ArrayList: " + List.size());
        List.remove(1);
        System.out.println("After removing second element: " + List);
        System.out.println("Size of ArrayList: " + List.size());
        List.set(2, 10);
        System.out.println("After updating third element: " + List);
        System.out.println("sorting ArrayList");
        Collections.sort(List, Integer::compareTo);
        System.out.println("Sorted ArrayList: " + List);
        System.out.println("Using for loop:"
        );
        for (int n = 0; n < List.size(); n++) {
            System.out.println("Element" + " "+ (n + 1) + ":" + List.get(n));
        }
        System.out.println("Using for-each loop:");
        for (Integer element : List) {
            System.out.println("Element"+ " "+List.indexOf(element) + ":" + element);
        }
    }

}
