import java.util.*;
class Student {
    String name;
    int age , rollno ;
    int marks;
    void displayInfo() {
        System.out.println("Student Information:");
        System.out.println("Name: " + name);
        System.out.println("Age: " + age);
        System.out.println("Roll Number: " + rollno);
        System.out.println("Marks: " + marks);
    }
    void getInfo(Scanner sc) {
        System.out.print("Enter name: ");
        name = sc.nextLine();
        System.out.print("Enter age: ");
        age = sc.nextInt();
        System.out.print("Enter roll number: ");
        rollno = sc.nextInt();
        System.out.print("Enter marks: ");
        marks = sc.nextInt();
    }
}
public class Main {
    public static void main(String[] args) {
    Student s1 = new Student();
    Student s2 = new Student();
    Student s3 = new Student(); 
    System.out.println("Enter details for student 1:");
    s1.getInfo();
    System.out.println("Enter details for student 2:");
    s2.getInfo();
    System.out.println("Enter details for student 3:");
    s3.getInfo();
    s1.displayInfo();
    s2.displayInfo();
    s3.displayInfo();
    
}   
}