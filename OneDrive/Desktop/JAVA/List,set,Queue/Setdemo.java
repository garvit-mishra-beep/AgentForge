import java.util.*;
public class Setdemo {
    public static void main(String[] args) {
        Set<String> Cars1 = new HashSet<>();
        Set<String> Cars2 = new TreeSet<>();
        Cars1.add("Maruti");
        Cars1.add("Hyundai");
        Cars1.add("Tata");
        Cars1.add("Kia");
        Cars1.add("Mahindra");
        Cars1.add("Kia");
        Cars1.add("Renault");
        Cars1.add("Honda");
        System.out.println("HashSet: " + Cars1);
        Cars2.add("Maruti");
        Cars2.add("Hyundai");
        Cars2.add("Tata");
        Cars2.add("Kia");   
        Cars2.add("Mahindra");
        Cars2.add("Kia");
        Cars2.add("Renault");
        Cars2.add("Honda");
        System.out.println("TreeSet: " + Cars2);
        
    }
}
