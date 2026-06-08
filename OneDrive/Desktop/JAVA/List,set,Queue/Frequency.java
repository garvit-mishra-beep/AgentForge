import java.util.*;
public class Frequency {
    public static void main(String[] args) {
        List<Integer> numbers = Arrays.asList(2,1,2,3,1,4,2);
        HashMap<Integer, Integer> frequencyMap = new HashMap<>();
        for (Integer n : numbers) {
            frequencyMap.put(n, frequencyMap.getOrDefault(n, 0) + 1);}
        System.out.println("Number Frequency:");
        for (Map.Entry<Integer, Integer> entry : frequencyMap.entrySet()) {
            System.out.println("Number: " + entry.getKey() + ", Frequency: " + entry.getValue());
        }
        frequencyMap.entrySet().removeIf(entry -> entry.getValue() < 2);
        System.out.println("Numbers with frequency >= 2:");
        for (Map.Entry<Integer, Integer> entry : frequencyMap.entrySet()) {
            System.out.println("Number: " + entry.getKey() + ", Frequency: " + entry.getValue());
        }
    }
}
