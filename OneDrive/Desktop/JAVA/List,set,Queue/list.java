import java.util.*;
public class list {
    public static void main(String[] args) {
        ArrayList<String> list = new ArrayList<>();
        list.add("C++");
        list.add("Python");
        list.add("Java");
        list.add("JavaScript");
        list.add("Ruby");
        list.add("Go");
        list.add(3, "Rust");
        list.add("Swift");
        list.add("Kotlin");
        list.add("PHP");
        System.out.println("ArrayList: " + list);
        System.out.println("First element: " + list.get(0));
        System.out.println("Size of ArrayList: " + list.size());
        list.remove(1);
        System.out.println("After removing second element: " + list);
        System.out.println("Size of ArrayList: " + list.size());
        list.set(2, "TypeScript");
        System.out.println("After updating third element: " + list);
        list.sort(String.CASE_INSENSITIVE_ORDER);
        System.out.println("Sorted ArrayList: " + list);
        list.sort(null);
        System.out.println("ArrayList sorted in ascending order: " + list);
        for (int n = 0; n < list.size(); n++) {
            System.out.println("Language" + " "+ (n + 1) + ":" + list.get(n));
        }
    }
}
