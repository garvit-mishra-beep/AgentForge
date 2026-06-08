import java.util.*;
public class map {
    Map<Integer, String> student = new HashMap<>();
    public void add(Integer key, String value) {
        student.put(key, value);
        System.out.println("Student Map after addition: " + student);
    }

    public void get(Integer key) {
        String value = student.get(key);
        System.out.println("Value for key " + key + ": " + value);
    }
    public void remove(Integer key) {
        student.remove(key);
        System.out.println("Student Map after removal: " + student);
    }
    public void containsKey(Integer key) {
        boolean exists = student.containsKey(key);
        System.out.println("Contains key " + key + ": " + exists);
    }
    public void size() {
        int size = student.size();
        System.out.println("Size of Student Map: " + size);
    }
    
    public static void main(String[] args) {
        map studentMap = new map();
        System.err.println("Initial Student Map: " + studentMap.student);
        studentMap.add(1, "Alice");
        studentMap.add(2, "Bob");
        studentMap.get(1);
        studentMap.containsKey(2);
        studentMap.size();
        studentMap.remove(1);
        studentMap.size();
        System.err.println("Student Map after all operations: " + studentMap.student);
        for (Map.Entry<Integer, String> entry : studentMap.student.entrySet()) {
            System.out.println("Key: " + entry.getKey() + ", Value: " + entry.getValue());
        }
    }
}
